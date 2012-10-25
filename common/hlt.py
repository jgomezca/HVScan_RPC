import shlex
import subprocess
import logging

import conditionDatabase
import conditionError

class HLTHandler( object ):
    
    def __init__( self, runInfoConnectionString, runInfoStartTag, runInfoStopTag, authPath ):
        """
        Parameters:
        runInfoConnectionString: connection string for connecting to the schema hosting RunInfo payloads;
        runInfoStartTag: tag labeling the IOV sequence for RunInfo payloads populated at each start of a run;
        runInfoStopTag: tag labeling the IOV sequence for RunInfo payloads populated at each stop of a run;
        authPath: path for authentication.
        """
        self._runInfoConnectionString = runInfoConnectionString
        _db = conditionDatabase.ConditionDBChecker( runInfoConnectionString, authPath )
        self._lastStartedRun = _db.iovSequence( runInfoStartTag ).lastSince()
        self._lastStoppedRun = _db.iovSequence( runInfoStopTag ).lastSince()
    
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
            logging.debug( "HLT configuration file for run \"%d\": %s", self._lastStoppedRun, resList )
            resGT = [ l.strip() for l in resList if l.find("globaltag") != -1 ]
            logging.debug( "Global Tag configuration fragment: %s", resGT )
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
