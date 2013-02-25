import sys
import os

import logging

import cx_Oracle

import coral
from RecoLuminosity.LumiDB import sessionManager,lumiTime,CommonUtil,lumiCalcAPI,lumiReport,lumiCorrections,revisionDML

from RecoLuminosity.LumiDB.lumiQueryAPI import *

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

        self.params = ParametersObject()


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
            print "++> Unknown type for runNumbers found:", type( runNumbers )

        return allRuns

    def getRecordedLumiSummaryByRun(self, runNumbers ):

        self.setupConnection()
        lumisummaryOut = []
        for runNr in self.normalizeRunNumbers(runNumbers):
            recLumi = recordedLumiForRun( self.session, self.params, runNr)
            if recLumi == 'N/A': continue   # ignore these ...
            lumisummaryOut.append( { "Run" : runNr, "RecordedLumi" : recLumi } )

        return lumisummaryOut

    def getDeliveredLumiSummaryByRun(self, runNumbers ) :
        self.setupConnection( )
        lumisummaryOut = []
        for runNr in self.normalizeRunNumbers(runNumbers):
            # delLumi = deliveredLumiForRun( self.session, self.params, runNr )[2]
            delLumi = self.getDeliveredLumiForOneRun(self.session, runNr )
            if delLumi == 'N/A' : continue   # ignore these ...
            lumisummaryOut.append( { "Run" : runNr, "DeliveredLumi" : delLumi } )

        return lumisummaryOut

    def getDeliveredLumiForOneRun(self, session, runNumber):

        # set a few defaults (taken from lumiCalc2.py)
        action  = 'overview' # 'delivered'  'overview' or 'recorded'
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
            irunlsdict[runNumber]=None

        finecorrections  = None
        driftcorrections = None
        correctionv3     = False
        rruns=irunlsdict.keys()

        schema=session.nominalSchema()
        session.transaction().start(True)

        if correctionv3:
            cterms=lumiCorrections.nonlinearV3()
        else: # default
            cterms=lumiCorrections.nonlinearV2()
        finecorrections=lumiCorrections.correctionsForRangeV2(schema,rruns,cterms) # constant+nonlinear corrections
        driftcorrections=lumiCorrections.driftcorrectionsForRange(schema,rruns,cterms)

        (datatagid,datatagname)=revisionDML.currentDataTag(session.nominalSchema())
        dataidmap=revisionDML.dataIdsByTagId(session.nominalSchema(),datatagid,runlist=rruns,withcomment=False)
        GrunsummaryData=lumiCalcAPI.runsummaryMap(session.nominalSchema(),irunlsdict)

        session.transaction().commit()

        # now get the data and sum up the delivered/recorded lumis:
        session.transaction().start(True)
        resultInfo=lumiCalcAPI.lumiForIds(session.nominalSchema(),irunlsdict,dataidmap,GrunsummaryData)
        # result=lumiCalcAPI.beamForRange( session.nominalSchema(), irunlsdict )
        session.transaction().commit()

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

        del session

        # print  'got:', result, 'for ', runNumber, 'which is of type', type(runNumber)

        return result

if __name__ == "__main__":
    LumiDB_SQL	= NewLumiDB()
    #print LumiDB_SQL.getRunNumber()
    #runNumbersString    =   LumiDB_SQL.getRunNumberWhereClause(runNumbRance="160001-160010")
    import pprint
    pprint.pprint( LumiDB_SQL.getDeliveredLumiSummaryByRun(runNumbers=[190595]) )
