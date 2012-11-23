import sys
import os

import logging

import cx_Oracle

import coral
from RecoLuminosity.LumiDB import sessionManager,lumiTime,inputFilesetParser,csvSelectionParser,selectionParser,csvReporter,argparse,CommonUtil,lumiCalcAPI,lumiReport,lumiCorrections

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
            delLumi = deliveredLumiForRun( self.session, self.params, runNr )[2]
            if delLumi == 'N/A' : continue   # ignore these ...
            lumisummaryOut.append( { "Run" : runNr, "DeliveredLumi" : delLumi } )

        return lumisummaryOut

class LumiDB_SQL(object):

    def __init__(self):
        pass

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
            print "Unexpected error:", str( e ), sys.exc_info( )
            raise
        finally :
            conn.close( )
        return runNumb
