import sys
import os

import logging

import cx_Oracle

import coral
from RecoLuminosity.LumiDB import sessionManager,lumiTime,CommonUtil,lumiCalcAPI,lumiReport,lumiCorrections,revisionDML

from RecoLuminosity.LumiDB.lumiQueryAPI import *

import service

conn_string = service.getCxOracleConnectionString(service.secrets['connections']['pro'])

class NewLumiDB(object):

    def __init__(self):
        self.session = None
        self.schema  = None
        self.setupConnection()

    def __del__(self):
        self.session.transaction( ).commit( )
        del self.session
        del self.svc

    def setupConnection(self):
        msg = coral.MessageStream( '' )
        #msg.setMsgVerbosity(coral.message_Level_Debug)
        msg.setMsgVerbosity( coral.message_Level_Error )
        # os.environ[ 'CORAL_AUTH_PATH' ] = '/afs/cern.ch/cms/DB/lumi'
        # self.svc = coral.ConnectionService( )
        # connectstr = conn_string   # 'oracle://cms_orcoff_prod/cms_lumi_prod'
        # self.session = self.svc.connect( connectstr, accessMode=coral.access_ReadOnly )
        # self.session.typeConverter( ).setCppTypeForSqlType( "unsigned int", "NUMBER(10)" )
        # self.session.typeConverter( ).setCppTypeForSqlType( "unsigned long long", "NUMBER(20)" )

        authfile="./auth.xml"
        conn_string1 = 'frontier://LumiCalc/CMS_LUMI_PROD'
        self.svc = sessionManager.sessionManager( conn_string1,
                                             authpath=authfile,
                                             siteconfpath=None,
                                             debugON=False )
        self.session = self.svc.openSession( isReadOnly=True, cpp2sqltype=[ ('unsigned int', 'NUMBER(10)'),
                                                                            ('unsigned long long', 'NUMBER(20)') ] )

        self.schema=self.session.nominalSchema()

        return

    def normalizeRunNumbers(self, runNumbers):

        allRuns = [ ]

        # handle request with string for run numbers:
        if type( runNumbers ) == type( "" ) or type( runNumbers ) == type( u"" ) :
            for runNrIn in runNumbers.split( ',' ) :
                if '-' in runNrIn :
                    rStart, rEnd = runNrIn.split( '-' )
                    allRuns += range( int( rStart ), int( rEnd ) + 1 )
                else :
                    allRuns.append( int( runNrIn ) )
        # handle requests with lists of run numbers
        elif type( runNumbers ) == type( [ ] ) :
            allRuns = [ int( x ) for x in runNumbers ]
        else :
            logging.warning("++> Unknown type for runNumbers found: " + str(type(runNumbers)) )

        return sorted(allRuns)

    def getRecordedLumiSummaryByRun(self, runNumbers ):
        return self.getLumiByRun(runNumbers, lumiType='recorded')

    def getDeliveredLumiSummaryByRun(self, runNumbers ) :
        return self.getLumiByRun(runNumbers, lumiType='delivered')

    def getLumiByRun(self, runNumbers, lumiType):

        logging.debug('getLumiSummaryByRun> querying %s lumi for runs [%s]' % (lumiType, ','.join([str(x) for x in runNumbers]) ) )

        self.setupConnection()

        lumisummaryOut = []
        for runNr in self.normalizeRunNumbers(runNumbers):
            recLumi = 'N/A'
            try:
                recLumi = self.getLumiForOneRun(runNr, lumiType)
            except Exception, e:
                logging.error('cannot get %s lumi for run %i : %s ' % (lumiType, runNr, str(e)) )
            if recLumi == 'N/A': continue   # ignore these ...
            lumisummaryOut.append( { "Run" : runNr, lumiType.capitalize()+"Lumi" : recLumi } )

        self.session.transaction().commit()

        return lumisummaryOut

    def getLumiForOneRun(self, runNumber, lumiTypeIn='delivered'):

        # set a few defaults (taken from lumiCalc2.py)
        action  = lumiTypeIn    # 'delivered'  'overview' or 'recorded'

        irunlsdict={}
        iresults=[]
        if runNumber: # if runnumber specified, do not go through other run selection criteria
            irunlsdict[runNumber] = [None] # None

        self.session.transaction().start(True)

        (datatagid,datatagname)=revisionDML.currentDataTag(self.schema)
        dataidmap=lumiCalcAPI.runList(self.schema,datatagid)
        GrunsummaryData=lumiCalcAPI.runsummaryMap(self.schema, irunlsdict, dataidmap)

        # now get the data and sum up the delivered/recorded lumis:
        resultInfo=lumiCalcAPI.lumiForIds(self.schema, irunlsdict, dataidmap, GrunsummaryData)

        self.session.transaction().commit()

        logging.debug('got result for run %i, len(result) is %i' % (runNumber, len(resultInfo[runNumber])) )

        #    output:
        # result {run:[[lumilsnum(0),cmslsnum(1),timestamp(2),beamstatus(3),beamenergy(4),
        #               deliveredlumi(5),recordedlumi(6),calibratedlumierror(7),
        #               (bxidx,bxvalues,bxerrs)(8),(bxidx,b1intensities,b2intensities)(9),
        #               fillnum(10),ncollidingbunches(11)]...]}
        # special meanings:
        # {run:None}  None means no run in lumiDB,
        # {run:[]} [] means no lumi for this run in lumiDB
        # {run:[....deliveredlumi(5),recordedlumi(6)None]} means no trigger in lumiDB
        # {run:cmslsnum(1)==0} means either not cmslsnum or is cms but not selected, therefore set recordedlumi=0,efflumi=0
        # lumi unit: 1/ub

        recLumi = 0
        delLumi = 0
        for ls in resultInfo[runNumber]:
            if ls[5] is not None: delLumi += ls[5]
            if ls[6] is not None: recLumi += ls[6]

        result = 0
        if action == 'delivered':
            result = delLumi

        if action == 'overview':
            result = delLumi

        if action == 'recorded': # recorded actually means effective because it needs to show all the hltpaths...
            result = recLumi

        # print  'got:', result, 'for ', runNumber, 'which is of type', type(runNumber)
        return result

    def getRunNumbers(self, startTime, endTime):

        authfile="./auth.xml"

        conn = cx_Oracle.connect( conn_string )
        startTime = startTime + ":00.000000"
        endTime = endTime + ":00.000000"
        jobList = [ ]
        runNumb = [ ]

        sqlstr = """
SELECT TO_CHAR(runtable.runnumber)
FROM CMS_RUNINFO.RUNNUMBERTBL runtable, CMS_WBM.RUNSUMMARY wbmrun
WHERE (
wbmrun.starttime BETWEEN
TO_TIMESTAMP(:startTime, 'DD-Mon-RR HH24:MI:SS.FF') AND
TO_TIMESTAMP(:stopTime, 'DD-Mon-RR HH24:MI:SS.FF'))
AND (runtable.sequencename = 'GLOBAL-RUN-COSMIC' OR runtable.sequencename = 'GLOBAL-RUN')
AND (wbmrun.key = '/GLOBAL_CONFIGURATION_MAP/CMS/COSMICS/GLOBAL_RUN'
OR wbmrun.key = '/GLOBAL_CONFIGURATION_MAP/CMS/CENTRAL/GLOBAL_RUN')
AND runtable.runnumber = wbmrun.runnumber
"""
        try :
            curs = conn.cursor( )
            params = {"startTime" : startTime, "stopTime" : endTime}
            curs.prepare( sqlstr )
            curs.execute( sqlstr, params )

            for row in curs :
                runNumb.append( row[ 0 ] )
            jobList.append( {'runnumbers' : runNumb} )
        except cx_Oracle.DatabaseError, e :
            msg = "getRunNumber> Error from DB : " + str( e )
            logging.error( msg )
            logging.error( "query was: '" + sqlstr + "'" )
            # print "Unexpected error:", str( e ), sys.exc_info( )
            raise
        finally :
            conn.close( )

        return self.normalizeRunNumbers(runNumb)

    def getLumiForOneRunOld(self, runNumber, lumiType='delivered'):

        # set a few defaults (taken from lumiCalc2.py)
        action  = lumiType    # 'delivered'  'overview' or 'recorded'
        fillnum = None
        begin   = None
        end     = None
        amodetag   = 'PROTPHYS'  # beamChoices=['PROTPHYS','IONPHYS','PAPHYS']
        beamenergy = 3500.
        beamfluctuation = 0.2
        pbeammode   = 'STABLE BEAMS'
        normfactor  = None
        scalefactor = 1.0
        finecorrections=None
        driftcorrections=None

        reqTrg = False
        reqHlt = False
        if action == 'recorded':
            reqTrg = True
            reqHlt = True

        irunlsdict={}
        iresults=[]
        if runNumber: # if runnumber specified, do not go through other run selection criteria
            irunlsdict[runNumber] = [None] # None

        finecorrections  = None
        driftcorrections = None
        correctionv3     = False
        rruns=irunlsdict.keys()

        schema=self.session.nominalSchema()
        self.session.transaction().start(True)

        if correctionv3:
            cterms=lumiCorrections.nonlinearV3()
        else: # default
            cterms=lumiCorrections.nonlinearV2()
        finecorrections=lumiCorrections.correctionsForRangeV2(schema,rruns,cterms) # constant+nonlinear corrections
        driftcorrections=lumiCorrections.driftcorrectionsForRange(schema,rruns,cterms)
        self.session.transaction().commit()

        oldVers = False
        if oldVers:
            schema=self.session.nominalSchema()
            self.session.transaction().start(True)
            (datatagid,datatagname)=revisionDML.currentDataTag(session.nominalSchema())
            dataidmap=revisionDML.dataIdsByTagId(session.nominalSchema(),datatagid,runlist=rruns,withcomment=False)
            try:
                GrunsummaryData=lumiCalcAPI.runsummaryMap(session.nominalSchema(),irunlsdict)
            except:
                logging.error("failed to get runsummaryMap for %s " % (','.join([str(x)+':'+str(y) for (x,y) in irunlsdict.items()])) )
                self.session.transaction().commit()
            raise
        else:
            return self.getLumiForOneRun(session, runNumber, lumiType)

if __name__ == "__main__":
    LumiDB_SQL	= NewLumiDB()
    #print LumiDB_SQL.getRunNumber()
    #runNumbersString    =   LumiDB_SQL.getRunNumberWhereClause(runNumbRance="160001-160010")
    import pprint
    pprint.pprint( LumiDB_SQL.getDeliveredLumiSummaryByRun(runNumbers=[190595]) )
