import datetime
import sqlite3

import database

class RunDataError( Exception ):
    '''Exception raised by modules related to run data.
    '''

    def __init__(self, message):
        self.args = (message, )

class RunData( object ):
    
    tier0Delay = datetime.timedelta( hours = 47, minutes = 45 )
    
    def __init__( self, connectionDictionary ):
        """
        Parameters:
        runControlConnectionString: connection string for connecting to the schema hosting Run Control FM information.
        """
        self._runControlConnection = database.Connection( connectionDictionary )
        self._localSQLiteFile = "runs.db"
        self._runsDumped = False
        self._sqliteConnection = connection = sqlite3.connect( self._localSQLiteFile )

    def _createSQLite( self ):
        cursor = self._sqliteConnection.cursor()
        cursor.execute( """
        CREATE TABLE RUNS 
        (
          RUN INTEGER NOT NULL 
          , START_TIME TIMESTAMP(9) NOT NULL 
          , STOP_TIME TIMESTAMP(9) NOT NULL 
          , CONSTRAINT RUNS_PK PRIMARY KEY 
          (
            RUN 
          )
          , CONSTRAINT RUNS_UK1 UNIQUE 
          (
            START_TIME 
          )
          , CONSTRAINT RUNS_UK2 UNIQUE 
          (
            STOP_TIME 
          )
        )
        """ )
    
    def _dumpRunsInSQLite( self ):
        self._createSQLite()
        sqlstr = """
        SELECT STOP_VIEW.RUN, START_VIEW.START_TIME, STOP_VIEW.STOP_TIME
        FROM (
               SELECT RUNNUMBER AS RUN
               FROM CMS_RUNINFO.RUNSESSION_PARAMETER RP 
               WHERE RP.NAME = 'CMS.LVL0:SEQ_NAME'
                     AND (
                           RP.STRING_VALUE = 'GLOBAL-RUN-COSMIC'
                           OR RP.STRING_VALUE = 'GLOBAL-RUN'
                         )
             ) SEQUENCE_VIEW,
             (
               SELECT RUNNUMBER AS RUN
               FROM CMS_RUNINFO.RUNSESSION_PARAMETER RP 
               WHERE RP.NAME = 'CMS.LVL0:GLOBAL_CONF_KEY'
                     AND (
                           RP.STRING_VALUE = '/GLOBAL_CONFIGURATION_MAP/CMS/COSMICS/GLOBAL_RUN'
                           OR RP.STRING_VALUE = '/GLOBAL_CONFIGURATION_MAP/CMS/CENTRAL/GLOBAL_RUN'
                         )
             ) KEY_VIEW,
             (
               SELECT RP.RUNNUMBER AS RUN, RD.VALUE AS START_TIME
               FROM CMS_RUNINFO.RUNSESSION_PARAMETER RP, CMS_RUNINFO.RUNSESSION_DATE RD
               WHERE RP.NAME = 'CMS.LVL0:START_TIME_T'
                     AND RD.RUNSESSION_PARAMETER_ID = RP.ID
             ) START_VIEW,
             (
               SELECT RP.RUNNUMBER AS RUN, RD.VALUE AS STOP_TIME
               FROM CMS_RUNINFO.RUNSESSION_PARAMETER RP, CMS_RUNINFO.RUNSESSION_DATE RD
               WHERE RP.NAME = 'CMS.LVL0:STOP_TIME_T'
                     AND RD.RUNSESSION_PARAMETER_ID = RP.ID
             ) STOP_VIEW
        WHERE SEQUENCE_VIEW.RUN = KEY_VIEW.RUN
              AND KEY_VIEW.RUN = START_VIEW.RUN
              AND START_VIEW.RUN = STOP_VIEW.RUN
        """
        runList = self._runControlConnection.fetch( sqlstr )
        cursor = self._sqliteConnection.cursor()
        cursor.executemany( """INSERT INTO RUNS( RUN, START_TIME, STOP_TIME ) VALUES ( ?, ?, ? )""", runList )
        self._sqliteConnection.commit()
        self._runsDumped = True
    
    def getStartTime( self, run ):
        """
        Retrieves the start of a run from CMS online run control.
        Parameters:
        run: the run number.
        @returns: a datatime object with the start time in UTC.
        """
        sqlstr = """
        SELECT RD.VALUE
        FROM CMS_RUNINFO.RUNSESSION_DATE RD, CMS_RUNINFO.RUNSESSION_PARAMETER RP
        WHERE RP.NAME = 'CMS.LVL0:START_TIME_T' AND RP.RUNNUMBER = :s AND RD.RUNSESSION_PARAMETER_ID = RP.ID
        """
        date = self._connection.fetch( sqlstr, (run, ) )
        if not date:
            raise RunDataError( """The start time for run \"%d\" was not found.""" %( run, ) )
        return date[0]
    
    def getStopTime( self, run ):
        """
        Retrieves the end time of a run from CMS online run control.
        Parameters:
        run: the run number.
        @returns: a datatime object with the stop time in UTC.
        """
        sqlstr = """
        SELECT RD.VALUE
        FROM CMS_RUNINFO.RUNSESSION_DATE RD, CMS_RUNINFO.RUNSESSION_PARAMETER RP
        WHERE RP.NAME = 'CMS.LVL0:STOP_TIME_T' AND RP.RUNNUMBER = :s AND RD.RUNSESSION_PARAMETER_ID = RP.ID
        """
        date = self._connection.fetch( sqlstr, (run, ) )
        if not date:
            raise RunDataError( """The start time for run \"%d\" was not found.""" %( run, ) )
        return date[0]
    
    def getHLTSafeRunAtTime( self, timestamp ):
        """
        Retrieves the first condition safe run for HLT at a given time from CMS online run control.
        Parameters:
        timestamp: a datetime object with the time in UTC.
        @returns: an integer, the number of the run ongoing at the input time, or the last stopped at that moment.
        """
        if not self._runsDumped:
            self._dumpRunsInSQLite()
        sqlstr = """
        SELECT RUN
        FROM RUNS
        WHERE START_TIME <= ?
        ORDER BY RUN DESC
        LIMIT 1
        """
        cursor = self._sqliteConnection.cursor()
        cursor.execute( sqlstr, ( timestamp, ) )
        run = cursor.fetchone()
        if run is None:
            raise RunDataError( """The first condition safe run for HLT at \"%s\" was not found.""" %( timestamp, ) )
        #the run was ongoing or completed at that time, so the first safe is the next one.
        return run[0] + 1
    
    def getPromptRecoSafeRunAtTime( self, timestamp ):
        """
        Retrieves the first condition safe run for HLT at a given time from CMS online run control.
        Parameters:
        timestamp: a datetime object with the time in UTC.
        @returns: an integer, the number of the Tier0 first condition safe run at the input time.
        """
        #subtracting 48 hours to the input timestamp but 15 minutes
        #in order to take into account the Prompt Reco delay at Tier0
        #and the condition turnaround
        delayedTimestamp = timestamp - RunData.tier0Delay
        if not self._runsDumped:
            self._dumpRunsInSQLite()
        sqlstr = """
        SELECT RUN
        FROM RUNS
        WHERE STOP_TIME > ?
        ORDER BY RUN
        LIMIT 1
        """
        cursor = self._sqliteConnection.cursor()
        cursor.execute( sqlstr, ( delayedTimestamp, ) )
        run = cursor.fetchone()
        if run is None:
            raise RunDataError( """The first condition safe run for prompt reconstruction at \"%s\" was not found.""" %( timestamp, ) )
        return run[0]

    def __del__( self ):
        self._runControlConnection.close()
        self._sqliteConnection.close()
