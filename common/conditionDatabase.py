#!/usr/bin/env python
import DLFCN
import os
import sys
import time

import conditionError
import service

sys.setdlopenflags(DLFCN.RTLD_GLOBAL+DLFCN.RTLD_LAZY)

try:
    import pluginCondDBPyInterface as condDB
except ImportError:
    raise conditionError.ConditionError( """Unable to import the Condition Python API for accessing condition data.
Please check if the CMSSW environment is correctly initialized.""" )


serviceList = [ {'service_type' : 'OnlineProduction', 'oracle' : [ 'cms_orcon_prod' ], 'frontier': [ 'FrontierOnProd' ] }
              , {'service_type' : 'OfflineProduction', 'oracle' : [ 'cms_orcon_adg' ], 'frontier': [ 'PromptProd', 'FrontierProd' ] }
              , {'service_type' : 'OfflineIntegration', 'oracle' : [ 'cms_orcoff_int' ], 'frontier': [ 'FrontierInt' ] }
              , {'service_type' : 'OfflinePreparation', 'oracle' : [ 'cms_orcoff_prep' ], 'frontier': [ 'FrontierPrep' ] }
              , {'service_type' : 'OfflineArchive', 'oracle' : [ 'CMSARC_LB' ], 'frontier': [ 'FrontierArc' ] }
               ]

def getValidConnectionDictionary( protocolDictionary ):
    """
    Checks whether or not a service for a protocol are available in the condition database.
    Parameters:
    protocolDictionary: the input dictionary in the form { 'protocol' : protocol_name, 'service' : service_name, 'account' : account_name }.
    @returns: a dictionary in the form { 'service_type' : condition_database_service, 'db_name' : oracle_service, 'frontier_name' : frontier_service, 'account' : account_name }, None if parsing error.
    """
    for serviceDict in serviceList: #loop over service dictionaries
        for protocolServiceName in serviceDict[ protocolDictionary[ 'protocol' ] ]: #loop over the input protocol's services
            if protocolServiceName == protocolDictionary[ 'service' ]: #the service is in the list of the services associated to the input protocol
                serviceType = serviceDict[ 'service_type' ]
                if protocolDictionary[ 'protocol' ] == "oracle":
                    # keep the same service name as specified in the input protocol
                    oracleServiceName = protocolServiceName
                else:
                    # take the first of the list
                    oracleServiceName = serviceDict[ 'oracle' ][ 0 ]
                if protocolDictionary[ 'protocol' ] == "frontier":
                    # keep the same service name as specified in the input protocol
                    frontierServiceName = protocolServiceName
                else:
                    # take the first of the list
                    frontierServiceName = serviceDict[ 'frontier' ][ 0 ]
                return { 'service_type' : serviceType
                       , 'db_name' : oracleServiceName
                       , 'frontier_name' : frontierServiceName
                       , 'account' : protocolDictionary[ 'account' ] }

def getValidConnectionDictionaryFromConnectionString( connectionString ):
    # first we parse the connection string in order to get the service name and the account name
    protocolDictionary = service.getProtocolServiceAndAccountFromConnectionString( connectionString )
    if not protocolDictionary:
        raise conditionError.ConditionError( "Invalid connection string: \"%s\"" %( connectionString, ) )
    # next, we check whether the connection string is valid
    connectionDictionary = getValidConnectionDictionary( protocolDictionary )
    if not connectionDictionary: #the oracle or frontier service provided was not found
        raise conditionError.ConditionError( "The service provided in the connection string \"%s\" was not found in the available ones." %( connectionString, ) )
    return connectionDictionary

def frontierToOracle( connectionString, updatesOnOracle = False ):
    """
    Transforms a frontier connection string into an Oracle one.
    Parameters:
    connectionString: string for connecting to a condition Database account;
    updatesOnOracle: boolean, default False, if set to True the connection string will contain an Oracle service name allowing for updates.
    @returns: Oracle connection string, raises exception if parsing error or update not allowed.
    """
    connectionDictionary = getValidConnectionDictionaryFromConnectionString( connectionString )

    if updatesOnOracle and connectionDictionary[ 'service_type' ] == 'OfflineProduction':
        # The offline production service is read-only, so if we want to perform updates, we need a connection to the Online production
        for serviceDict in serviceList:
            if serviceDict[ 'service_type' ] == 'OnlineProduction':
                connectionDictionary[ 'service_type' ] = 'OnlineProduction'
                connectionDictionary[ 'db_name' ] = serviceDict[ 'oracle' ][ 0 ]
                connectionDictionary[ 'frontier_name' ] = serviceDict[ 'frontier' ][ 0 ]

    # Moreover, the offline archive is read-only and frozen, so no updates are allowed
    if updatesOnOracle and connectionDictionary[ 'service_type' ] == 'OfflineArchive':
        raise conditionError.ConditionError( "The data stored in the Oracle Database accessed through the service \"%s\" and through frontier servlet \"%s\" for service type OfflineArchive are read-only and cannot be modified." %( connectionDictionary[ 'db_name' ], connectionDictionary[ 'frontier_name' ] ) )

    return service.getOracleConnectionString( connectionDictionary )

onlineFrontierConnectionStringTemplate = None
def oracleToFrontier( connectionString, offlineServlet = False ):
    """
    Transforms an Oracle connection string into a frontier one.
    Parameters:
    connectionString: string for connecting to a condition Database account;
    offlineServlet: boolean, default False, if set to True the connection string will contain a frontier servlet in the offline network, even if the connection string point to an online service.
    @returns: frontier connection string, raises exception if parsing error or update not allowed.
    """
    connectionDictionary = getValidConnectionDictionaryFromConnectionString( connectionString )

    global onlineFrontierConnectionStringTemplate
    if connectionDictionary[ 'service_type' ] == 'OnlineProduction':
        if not offlineServlet:
            # we build the online connection string by hand, as there is no site configuration in that cluster
            onlineFrontierConnectionStringTemplate = "frontier://(proxyurl=http://localhost:3128)(serverurl=http://localhost:8000/%s)(serverurl=http://localhost:8000/%s)(retrieve-ziplevel=0)(failovertoserver=no)/%s"
            return onlineFrontierConnectionStringTemplate %( ( onlineFrontierConnectionStringTemplate.count( "%s" ) - 1 ) * ( connectionDictionary[ 'frontier_name' ], ) + ( connectionDictionary[ 'account' ], ) )
        for serviceDict in serviceList:
            if serviceDict[ 'service_type' ] == 'OfflineProduction':
                connectionDictionary[ 'service_type' ] = 'OfflineProduction'
                connectionDictionary[ 'db_name' ] = serviceDict[ 'oracle' ][ 0 ]
                connectionDictionary[ 'frontier_name' ] = serviceDict[ 'frontier' ][ 0 ]
    return service.getFrontierConnectionString( connectionDictionary )

def checkConnectionString( connectionString, forUpdating = False ):
    if connectionString.startswith( 'sqlite_file:' ):
        # todo FIXME: check that the file is existing
        return True
    protocolDictionary = service.getProtocolServiceAndAccountFromConnectionString( connectionString )
    if not protocolDictionary:
        raise conditionError.ConditionError( "Invalid connection string: \"%s\"" %( connectionString, ) )
    if forUpdating and protocolDictionary[ 'protocol' ] == "frontier":
        # we are explicitly excluding Frontier services, as they are read-only
        return False
    connectionDictionary = getValidConnectionDictionary( protocolDictionary )
    if not connectionDictionary:
        raise conditionError.ConditionError( "The service provided in the connection string \"%s\" was not found in the available ones." %( connectionString, ) )
    if forUpdating and ( connectionDictionary[ 'service_type' ] == "OfflineProduction" or connectionDictionary[ 'service_type' ] == "OfflineArchive" ):
        # we are explicitly excluding read-only services
        return False
    return True

class IOVChecker( object ):
    """
    This class allows to connect to a condition database account, load an IOVSequence, and check its contents.
    """

    def __init__( self, db ):
        self._db = db
        self._iovSequence = None

    def load( self, tag ):
        self._tag = str(tag)  # ensure we pass on a string even if we get a unicode object
        try:
            self._db.startReadOnlyTransaction()
            self._iovSequence = self._db.iov( self._tag )
            self._db.commitTransaction()
        except RuntimeError as err:
            raise conditionError.ConditionError( """Cannot retrieve the IOV sequence associated to tag \"%s\".
The CMSSW exception is: %s""" %( self._tag, err ) )

    def getAllElements( self ):
        elementList = [ ( elem.since(), elem.till() ) for elem in self._iovSequence.elements ]
        if not elementList:
            raise conditionError.ConditionError( """IOV tag \"%s\" does not contain any IOV elements.
Please check the status of this tag and inform Condition DB experts if the issue is not solved.""" %( self._tag, ) )
        return elementList

    def getAllSinceValues( self ):
        elementList = [ elem.since() for elem in self._iovSequence.elements ]
        if not elementList:
            raise conditionError.ConditionError( """IOV tag \"%s\" does not contain any IOV elements.
Please check the status of this tag and inform Condition DB experts if the issue is not solved.""" %( self._tag, ) )
        return elementList

    def comment( self ):
        return self._iovSequence.comment()

    def firstSince( self ):
        return self._iovSequence.firstSince()

    def iovToken( self ):
        return self._iovSequence.token()

    def lastSince( self ):
        iovRange = self._iovSequence.tail( 1 )
        return iovRange.back().since()

    def lastTill( self ):
        return self._iovSequence.lastTill()

    def payloadClasses( self ):
        payloads = self._iovSequence.payloadClasses()
        return tuple( payloads )

    def payloadContainer( self ):
        try:
            return self.payloadClasses()[0]
        except KeyError:
            raise conditionError.ConditionError( """IOV tag \"%s\" does not contain any payloads.
Please check the status of this tag and inform Condition DB experts if the issue is not solved.""" %( self._tag, ) )

    def revision( self ):
        return self._iovSequence.revision()

    def size( self ):
        iovSize = self._iovSequence.size()
        if not iovSize:
            raise conditionError.ConditionError( """IOV tag \"%s\" does not contain any IOV elements.
Please check the status of this tag and inform Condition DB experts if the issue is not solved.""" %( self._tag, ) )
        return iovSize

    def timestamp( self ):
        return time.asctime( time.gmtime( condDB.unpackTime( self._iovSequence.timestamp() )[ 0 ] ) )

    def timetype( self ):
        return self._iovSequence.timetype()

class ConditionDBChecker( object ):
    """
    This class allows to connect to a condition database account and check its contents.
    """

    def __init__( self, connectionString, authPath ):
        """Parameters:
        connectionString: connection string for connecting to the account hosting Global Tags;
        authPath: path to authentication key.
        """
        checkConnectionString( connectionString )
        self._connectionString = str(connectionString)  # ensure we pass on a string even if we get a unicode object
        self._authPath = authPath
        self._dbStarted = False
        self._fwLoad = condDB.FWIncantation()

    def _initDB( self, connectionString, authPath = None ):
        """
        Initiates the connection to the database, or re-initiates it in case one of the connection parameters is changed.
        Parameters:
        connectionString: connection string for connecting to the account specified by the connection string;
        authPath: path to authentication key  (default None if unchanged w.r.t. c'tor).
        @returns: a boolean set to True if the connection has been (re-)opened; raises if the connection cannot be established.
        """
        isReconnected = False
        if authPath != None and self._authPath != authPath:
            self._authPath = authPath
            self._dbStarted = False
        if self._connectionString == connectionString and self._dbStarted :
            return isReconnected
        if self._connectionString != connectionString :
            checkConnectionString( connectionString )
            self._connectionString = str(connectionString) # ensure we pass on a string even if we get a unicode object
            self._dbStarted = False
        try:
            self._rdbms = condDB.RDBMS( self._authPath )
            self._db = self._rdbms.getReadOnlyDB( str(self._connectionString) )  # ensure we pass on a string even if we get a unicode object
            isReconnected = True
            self._dbStarted = True
        except RuntimeError as err :
            raise conditionError.ConditionError( """Cannot connect to condition database \"%s\" for RDBMS in \"%s\".
The CMSSW exception is: %s""" %( self._connectionString, self._authPath, err ) )
        return isReconnected

    def getAllTags( self ):
        """
        @returns: list of all IOV tags available in the account, raises if no tags are there, or if the file is not correct.
        """
        if not self._dbStarted:
            self._initDB( self._connectionString, self._authPath )
        try:
            self._db.startReadOnlyTransaction()
            tags = self._db.allTags().strip().split()
            self._db.commitTransaction()
            return tags
        except RuntimeError as err:
            raise conditionError.ConditionError( """Cannot retrieve tags from condition database \"%s\" for RDBMS in \"%s\"
The CMSSW exception is: %s""" %( self._connectionString, self._authPath, err ) )

    def checkTag( self, tag ):
        """
        Checks whether or not a given tag is in the database.
        Parameters:
        tag: the tag to be looked for.
        @returns: True if present, raises if the database is not correct.
        """
        tags = self.getAllTags()
        index = next( (i for i in xrange( len( tags ) ) if tags[ i ] == tag ), None )
        if index == None:
            return False
        else:
            return True
        # # alternative 1:
        # return reduce(lambda x,y: x | y, map(lambda x: x == tag, self.getAllTags()))
        # # alternative 2:
        # return tag in self.getAllTags()

    def iovSequence( self, tag ):
        """
        Gives access to the IOV sequence labelled by a given tag.
        Parameters:
        tag: the tag labelling the IOV sequence to be loaded.
        @returns: an instance of IOVChecker, raises if invalid tag.
        """
        if not self._dbStarted:
            self._initDB( self._connectionString, self._authPath )
        iovChecker = IOVChecker( self._db )
        iovChecker.load( tag )
        return iovChecker

class GlobalTagChecker( object ):
    """
    This class allows to connect to the database account hosting Global Tags, load one of them, and check its contents.
    """

    def __init__( self, connectionString, authPath ):
        """
        Parameters:
        connectionString: connection string for connecting to the account hosting Global Tags;
        authPath: path to authentication key.
        """
        self._globalTagName = None
        checkConnectionString( connectionString )
        self._connectionString = connectionString
        self._authPath = authPath
        self._dbStarted = False
        self.fwLoad = condDB.FWIncantation()

    def initGT( self, globalTagName, connectionString = None, authPath = None ):
        """
        Initiates the connection to the GT database, or re-initiates it in case one of the connection parameters is changed, and loads the Global Tag.
        Parameters:
        globalTagName: name of the Global Tag;
        connectionString: connection string for connecting to the account hosting Global Tags (default None if unchanged w.r.t. c'tor);
        authPath: path to authentication key (default None if unchanged w.r.t. c'tor).
        @returns: a boolean set to True if the connection has been (re-)opened; raises if the connection cannot be established.
        """
        isReconnected = False
        if authPath != None and self._authPath != authPath :
            self._authPath = authPath
            self._dbStarted = False
        if connectionString != None and self._connectionString != connectionString :
            checkConnectionString( connectionString )
            self._connectionString = connectionString
            self._dbStarted = False
        if self._globalTagName == globalTagName and self._dbStarted:
            return isReconnected
        if self._globalTagName != globalTagName:
            self._globalTagName = globalTagName
            self._dbStarted = False
        try:
            self._rdbms = condDB.RDBMS( self._authPath )
            self._globalTag = self._rdbms.globalTag( self._connectionString, "::".join( [self._globalTagName, "All" ] ), "", "" )
            self._dbStarted = True
            isReconnected = True
        except RuntimeError as err:
            raise conditionError.ConditionError( """Cannot connect to Global Tag \"%s\" on account \"%s\" for RDBMS in \"%s\".
The CMSSW exception is: %s""" %( self._globalTagName, self._connectionString, self._authPath, err ) )
        return isReconnected

    def checkTag( self, dbName, tagName, updatesOnOracle = False ):
        """
        Checks whether a given tag and the corresponding connection string are in the loaded Global Tag.
        The check is done for the connection string to Oracle.
        Parameters:
        dbName: connection string;
        tagName: name of the tag to be checked;
        updatesOnOracle: boolean, default False, if set to True the chech is done w.r.t. a connection string for an Oracle service name allowing for updates.
        @returns: True if db/tag are in, False elsewhere.
        Raises if there is an error in parsing the input connection string, and, when updatesOnOracle is set True, if the connection string points to a service where updates are not allowed.
        """
        if self._globalTagName is None:
            raise conditionError.ConditionError( """The Global Tag on account \"%s\" for RDBMS in \"%s\" has not yet been initialized.
Please run the GlobalTagChecker.initGT function.""" %( self._connectionString, self._authPath ) )
        if not self._dbStarted:
            self.initGT( self._globalTagName )
        listTag = [ ( frontierToOracle( x.pfn, updatesOnOracle ), x.tag ) for x in self._globalTag.elements ]
        if ( frontierToOracle( dbName, updatesOnOracle ), tagName ) in listTag:
            return True
        return False
