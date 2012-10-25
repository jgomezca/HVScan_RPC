#!usr/bin/env python

import conditionDatabase
import conditionError
import hlt
import tier0

class GlobalTagHandler( object ):
    
    def __init__( self, globalTagConnectionString, runControlConnectionString, runInfoConnectionString, runInfoStartTag, runInfoStopTag, authPath, tier0DataSvcURI, timeOut, retries, retryPeriod, proxy = None, debug = False ):
        """
        Parameters:
        globalTagConnectionString: connection string for connecting to the schema hosting Global Tags;
        runControlConnectionString: connection string for connecting to the schema hosting Run Control FM information;
        runInfoConnectionString: connection string for connecting to the schema hosting RunInfo payloads;
        runInfoStartTag: tag labeling the IOV sequence for RunInfo payloads populated at each start of a run;
        runInfoStopTag: tag labeling the IOV sequence for RunInfo payloads populated at each stop of a run;
        authPath: path for authentication;
        tier0DataSvcURI: Tier0DataSvc URI;
        timeOut: time out for Tier0DataSvc HTTPS calls;
        retries: maximum retries for Tier0DataSvc HTTPS calls;
        retryPeriod: sleep time between two Tier0DataSvc HTTPS calls;
        proxy: (default None) HTTP proxy for accessing Tier0DataSvc HTTPS calls;
        debug: (default False) if set to True, enables debug information.
        """
        self._gt = conditionDatabase.GlobalTagChecker( globalTagConnectionString, authPath )
        self._hlt = hlt.HLTHandler( runInfoConnectionString, runInfoStartTag, runInfoStopTag, authPath )
        self._tier0 = tier0.Tier0Handler( tier0DataSvcURI, timeOut, retries, retryPeriod, proxy, debug )
    
    def getHLTGlobalTag( self ):
        """
        Queries HLT ConfDB to get the most recent Global Tag for HLT.
        @returns: a string with the Global Tag name.
        Raises if connection error, bad response, or if no Global Tags are available.
        """
        return self._hlt.getHLTGlobalTag()
    
    def getExpressGlobalTag( self ):
        """
        Queries Tier0DataSvc to get the most recent Global Tag for express reconstruction.
        @returns: a string with the Global Tag name.
        Raises if connection error, bad response, timeout after retries occur, or if no Global Tags are available.
        """
        expressRecoConfiguration = "express_config"
        return self._tier0.getGlobalTag( expressRecoConfiguration )

    def getPromptGlobalTag( self ):
        """
        Queries Tier0DataSvc to get the most recent Global Tag for prompt reconstruction.
        @returns: a string with the Global Tag name.
        Raises if connection error, bad response, timeout after retries occur, or if no Global Tags are available.
        """
        promptRecoConfiguration = "reco_config"
        return self._tier0.getGlobalTag( promptRecoConfiguration )
    
    def getProductionGlobalTags( self ):
        """
        Queries HLT ConfDB and Tier0DataSvc to get the most recent Global Tags for HLT processing, express and prompt reconstruction.
        @returns: a dictionary for the Global Tags in the production workflow, in the form {'hlt' : hltGT, 'express' : expressGT, 'prompt' : promptGT }.
        Raises if connection error, bad response, timeout after retries occur, or if no Global Tags are available.
        """
        return {'hlt' : self.getHLTGlobalTag(), 'express' : self.getExpressGlobalTag(), 'prompt' : self.getPromptGlobalTag() }
    
    def getWorkflowForTagAndDB( self, dbName, tagName, productionGTsDict ):
        """
        Checks whether a given tag and the corresponding connection string are in the production Global Tags.
        The check is done for the connection string to Oracle.
        Parameters:
        dbName: connection string;
        tagName: name of the tag to be checked;
        productionGTsDict: dictionary for the Global Tags in the production workflows, in the form {'hlt' : hltGT, 'express' : expressGT, 'prompt' : promptGT }.
        @returns: a string with the name of the production worklow where the input DB and tag pair is used, None the DB/tag is not used in any of them. In case it is included in more than one Global Tags, hlt wins over express, express over prompt.
        Raises if the dictionary for production workflows is malformed.
        """
        #first check if the dictionary contains the workflows
        if len( productionGTsDict ) != 3:
            raise conditionError.ConditionError( "The input dictionary for the Global Tags in the production worklows is not correct." )
        workflows = ( 'hlt', 'express', 'prompt' )
        for productionGTWorkflow in productionGTsDict.keys():
            if productionGTWorkflow not in workflows:
                raise conditionError.ConditionError( "The input dictionary for the Global Tags in the production worklows does not contain workflow \"%s\"" %( productionGTWorkflow, ) )
        #now check if the db/tag are in any of the production GTs
        for workflow in workflows:
            self._gt.initGT( productionGTsDict[ workflow ] )
            if self._gt.checkTag( dbName, tagName, True ):
                    return workflow
        return None
