import shlex
import subprocess
import logging

import cx_Oracle

import conditionDatabase
import conditionError

class HLTHandler( object ):

    def __init__( self, runControlConnectionString, runInfoConnectionString, runInfoStartTag, runInfoStopTag, authPath ):
        """
        Parameters:
        globalTagConnectionString: connection string for connecting to the schema hosting Global Tags;
        runControlConnectionString: connection string for connecting to the schema hosting Run Control FM information;
        runInfoConnectionString: connection string for connecting to the schema hosting RunInfo payloads;
        runInfoStartTag: tag labeling the IOV sequence for RunInfo payloads populated at each start of a run;
        runInfoStopTag: tag labeling the IOV sequence for RunInfo payloads populated at each stop of a run;
        authPath: path for authentication.
        """
        self._runControlConnectionString = runControlConnectionString
        self._runInfoConnectionString = runInfoConnectionString
        _db = conditionDatabase.ConditionDBChecker( runInfoConnectionString, authPath )
        self._lastStartedRun = _db.iovSequence( runInfoStartTag ).lastSince()
        self._lastStoppedRun = _db.iovSequence( runInfoStopTag ).lastSince()
    
    def getStartTime( self, run ):
        """
        Retrieves the start of a run from CMS online run control.
        Parameters:
        run: the run number.
        @returns: a datatime object with the start time in UTC.
        """
        date = None
        try:
            connection = cx_Oracle.connect( self._runControlConnectionString )
            try:
                sqlstr = """ 
                select rd.value
                from CMS_RUNINFO.runsession_date rd, CMS_RUNINFO.runsession_parameter rp
                where rp.name = 'CMS.LVL0:START_TIME_T' and rp.runnumber = :run and rd.runsession_parameter_id = rp.id
                order by rp.id
                """
                curs = connection.cursor()
                params = { "run": run }
                curs.prepare( sqlstr )
                curs.execute( sqlstr, params )
                for row in curs:
                    date = row[ 0 ]
            except cx_Oracle.DatabaseError as exc:
                error, = exc.args
                raise conditionError.ConditionError( """Unable to retrieve the start time for run \"%d\".
The reason is: ORA-%d: %s.""" %( run, error.code, error.message ) )
        except cx_Oracle.DatabaseError as exc:
            error, = exc.args
            raise conditionError.ConditionError( """Unable to connect to Oracle for retrieving the start time for run \"%d\".
The reason is: ORA-%d: %s.""" %( run, error.code, error.message ) )
        finally:
            connection.close()
        if date is None:
            raise conditionError.ConditionError( """The start time for run \"%d\" was not found.""" %( run, ) )
        return date
    
    def getStopTime( self, run ):
        """
        Retrieves the end time of a run from CMS online run control.
        Parameters:
        run: the run number.
        @returns: a datatime object with the stop time in UTC.
        """
        date = None
        try:
            connection = cx_Oracle.connect( self._runControlConnectionString )
            try:
                sqlstr = """ 
                select rd.value
                from CMS_RUNINFO.runsession_date rd, CMS_RUNINFO.runsession_parameter rp
                where rp.name = 'CMS.LVL0:STOP_TIME_T' and rp.runnumber = :run and rd.runsession_parameter_id = rp.id
                order by rp.id
                """
                curs = connection.cursor()
                params = { "run": run }
                curs.prepare( sqlstr )
                curs.execute( sqlstr, params )
                for row in curs:
                    date = row[ 0 ]
            except cx_Oracle.DatabaseError as exc:
                error, = exc.args
                raise conditionError.ConditionError( """Unable to retrieve the start time for run \"%d\".
The reason is: ORA-%d: %s.""" %( run, error.code, error.message ) )
        except cx_Oracle.DatabaseError as exc:
            error, = exc.args
            raise conditionError.ConditionError( """Unable to connect to Oracle for retrieving the start time for run \"%d\".
The reason is: ORA-%d: %s.""" %( run, error.code, error.message ) )
        finally:
            connection.close()
        if date is None:
            raise  conditionError.ConditionError( """The end time for run \"%d\" was not found.""" %( run, ) )
        return date

    def getHLTGlobalTag( self ):
        """
        Returns the Global Tag used for the last run completed by HLT.
        """
        try:
            command_line = "edmConfigFromDB --orcoff --runNumber " + str( self._lastStoppedRun )
            args = shlex.split( command_line )
            p = subprocess.Popen( args, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
            result = p.communicate()[ 0 ]
            resList = result.strip().split( "\n" )
            logging.debug("resList %s", resList)
            resGT = [ l.strip() for l in resList if l.find("globaltag") != -1 ]
            logging.debug("restgt %s", resGT)
            globalTag = [l.strip().replace("::All","") for l in resGT[0].split("\"") if l.find("::All") != -1][0]
            return globalTag
        except IndexError as i:
            raise conditionError.ConditionError( "Configuration for run \"%d\" not found." %( self._lastStoppedRun, ) )
        except OSError as o:
            raise conditionError.ConditionError( """Unable to load HLT configuration for run \"%d\".
The reason is: %s """ %( self._lastStoppedRun, o ) )
    
    def getLastCompletedRun( self ):
        """
        Queries RunInfo to get the last run completed by HLT.
        @returns: long, the run number.
        Raises if connection error, or if the run number is not available.
        """
        return self._lastStoppedRun

    def getLastRun( self ):
        """
        Queries RunInfo to get the last run started by HLT.
        @returns: long, the run number.
        Raises if connection error, or if the run number is not available.
        """
        return self._lastStartedRun

    def getFirstSafeRun( self ):
        """
        Queries RunInfo to get the first condition safe run.
        @returns: long, the run number.
        Raises if connection error, or if the run number is not available.
        """
        return self._lastStartedRun + 1

##     def getStopTimeForLastCompletedRun( self ):
##         """
##         Returns the end time of the last run completed by HLT.
##         """
##         return self.getStopTime(self. _lastStoppedRun )

##     def getStartTimeForLastRun( self ):
##         """
##         Returns the start time of the last run started by HLT.
##         """
##         return self.getStartTime( self._lastStartedRun )

##     def getHLTSafeTime( self ):
##         """Returns the last run started by HLT."""
##         if self._lastStartedRun == self._lastStoppedRun: #no runs ongoing: take the stop time of the last one
##             return self.getStopTimeForLastCompletedRun()
##         else: # a run is ongoing: take its start time
##             return self.getStartTimeForLastRun() 
