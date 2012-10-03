import logging

import conditionDatabase
import conditionException
import dropBoxException
import globalTagHandler
import service

def checkCorruptedOrEmptyFile( dbFile ):
    """
    Checks if a SQLite file is corrupted or just empty (i.e. containing only empty tables) by checking if there are tags inside.
    The corrupted or empty files with the corresponding metadata files are skipped from processing and put into a dedicated folder.
    Parameters:
    dbFile: the name of the SQLite file;
    @returns: True if the file is not corrupted nor empty, False elsewhere.
    """
    logging.info( "Checking whether SQLite file \"%s\" is corrupted or empty.", dbFile )
    db = conditionDatabase.ConditionDBChecker( "sqlite_file:"+dbFile, "" )
    try:
        db.getAllTags()
        logging.info( "The SQLite file \"%s\" is neither corrupted nor empty.", dbFile )
        return True
    except conditionException.ConditionException as e:
        logging.error( """The SQLite file \"%s\" is corrupted or empty. The request will not be processed. The issue is: %s""", dbFile, e )
        return False

def checkDestinationDatabase( metaDict ):
    """
    Checks if the destDB field in the metadata dictionary is valid, i.e. point to an Oracle service where updates are allowed.
    @returns: True if the connection string is correct, False elsewhere.
    Raises if destination database is not provided in the metadata, or if it is not a string.
    """
    try:
        connectionString = metaDict[ 'destDB' ]
        if not isinstance( connectionString, str ):
            logging.error( """The destination account specified in the metadata file must be a string. The request will not be processed.""" )
            raise DropBoxError(  """The destination account specified in the metadata file must be a string.""" )
        if not connectionString:
            logging.error( """The destination account is not specified in the metadata file. The request will not be processed.""" )
            return False
        if connectionString.startswith( 'sqlite_file:' ):
            logging.error( """The destination Database in connection string \"%s\" cannot be a SQLite file. The request will not be processed.""", connectionString )
            return False
        check = conditionDatabase.checkConnectionString( connectionString, True )
        if not check:
            logging.error( """The destination Database in connection string \"%s\" cannot point to read-only services. The request will not be processed.""", connectionString )
        else:
            logging.info( """The destination Database is specified by the connection string \"%s\".""", connectionString )
        return check
    except KeyError:
        logging.error( """The destination account is not present in the metadata file. The request will not be processed.""" )
        raise DropBoxError(  """The destination account is not present in the metadata file.""" )

def checkInputTag( dbFile, metaDict ):
    """
    Checks if a SQLite file contains the input tag specified in the metadata dictionary.
    The wrong files with the corresponding metadata files are skipped from processing and put in dedicated folder.
    Parameters:
    dbFile: the name of the SQLite file;
    metaDict: the dictionary extracted from the metadata file.
    @returns: True if the file contains the input tag, False elsewhere.
    Raises if the input tag is not provided in the metadata, or if it is not a string.
    """
    try:
        inputTag = metaDict[ 'inputTag' ]
        if not isinstance( inputTag, str ):
            logging.error( """The input tag specified in the metadata file must be a string. The request will not be processed.""" )
            raise DropBoxError(  """The input tag specified in the metadata file must be a string.""" )
        if not inputTag:
            logging.error( """The input tag is not specified in the metadata file. The request will not be processed.""" )
            return False
        logging.info( "Checking whether SQLite file \"%s\" contains the input tag \"%s\".", dbFile, inputTag )
        db = conditionDatabase.ConditionDBChecker( "sqlite_file:"+dbFile, "" )
        check = db.checkTag( inputTag )
        if not check:
            logging.error( """The SQLite file \"%s\" does not contain the input tag \"%s\". The request will not be processed.""", dbFile, inputTag )
        else:
            logging.info( """The SQLite file \"%s\" contains the input tag \"%s\".""", dbFile, inputTag )
        return check
    except KeyError:
        logging.error( """The input tag is not present in the metadata file. The request will not be processed.""" )
        raise DropBoxError(  """The input tag is not present in the metadata file.""" )

#FIXME: do we need to update the request if the since in the metadata file is null?
def checkSince( dbFile, metaDict ):
    """
    Checks if the since field in the metadata dictionary is correct.
    If the since field is None, it assumes that the value will be taken from the SQLite file, being the first since of the input tag.
    If the since field is not None, it must be not smaller than the first since of the input tag in the SQLite file.
    Parameters:
    dbFile: the name of the SQLite file;
    metaDict: the dictionary extracted from the metadata file.
    @returns: True if the since is correct, False elsewhere.
    Raises if the input tag is not provided in the metadata, or if it is not a string, or if since is neither None nor integer not long.
    """
    try:
        if not checkInputTag( dbFile, metaDict ):
            return False
        inputTag = metaDict[ 'inputTag' ]
        logging.info( "Checking whether the since value specified in the metadata file is consistent with the first since of the input tag \"%s\" in the SQLite file \"%s\".", inputTag, dbFile )
        since = metaDict[ 'since' ]
        if since is None:
            logging.info( "No since value is specified in the metadata file. Therefore, its value will be taken from the SQLite file \"%s\", being the first since of the input tag \"%s\".", dbFile, inputTag )
            return True
        if ( not isinstance( since, int ) ) or ( not isinstance( since, long ) ):
            logging.error( """The since value specified in the metadata file must be a number. The request will not be processed.""" )
            return False
        db = conditionDatabase.ConditionDBChecker( "sqlite_file:"+dbFile, "" )
        iov = db.iovSequence( inputTag )
        firstSince = iov.firstSince()
        check = ( since >= firstSince )
        if not check:
            logging.error( """The since value \"%d\" specified in the metadata file is smaller than the first since \"%d\" of the input tag \"%s\" in the SQLite file \"%s\". The request will not be processed.""", since, firstSince, inputTag, dbFile )
        else:
            logging.info( """The since value \"%d\" specified in the metadata file is not smaller than the first since \"%d\" of the input tag \"%s\" in the SQLite file \"%s\".""", since, firstSince, inputTag, dbFile )
        return check
    except KeyError:
        logging.error( """The since value is not present in the metadata file. The request will not be processed.""" )
        raise DropBoxError(  """The since value is not present in the metadata file.""" )

## def checkTimeType( dbFile, metaDict ):
##     """
##     Checks if the timeType field in the metadata dictionary is equal to the time type of the input tag.
##     @returns: True if the types are the same, False elsewhere.
##     """
##     timeType = metaDict[ 'timeType' ]
##     inputTag = metaDict[ 'inputTag' ]
##     logging.info( "Checking whether or not the input tag \"%s\" in the SQLite file \"%s\" has an IOV sequence's time type equal to \"%s\" specified in the request.", inputTag, dbFile, timeType )
##     db = conditionDatabase.ConditionDBChecker( "sqlite_file:"+dbFile, "" )
##     iov = db.iovSequence( inputTag )
##     iovTimeType = str( iov.timetype() )
##     check = ( timeType == iovTimeType )
##     if not check:
##         logging.error( """The time type \"%s\" specified in the metadata file differs from the value \"%s\" of the input tag \"%s\" in the SQLite file \"%s\". The request will not be processed.""", timeType, iovTimeType, inputTag, dbFile )
##     else:
##         logging.info( """The time type \"%s\" specified in the metadata file is equal to the value of the input tag \"%s\" in the SQLite file \"%s\".""", timeType, inputTag, dbFile )
##     return check

def checkSynchronization( synchronizeTo, connectionString, tag, gtHandle, productionGTsDict = None ):
    """
    Checks if a connection string and a tag are compatible with the synchronization for a workflow against the production Global Tags.
    If the destination account and the destination tags are not in the production Global Tags, any synchronization is valid.
    If the destination account and the destination tags are in at least one Global Tag, the synchronization must be exactly the same as the one of the Global Tag.
    Parameters:
    synchronizeTo: the synchronization for the workflow to be looked for.
    connectionString: the connection string to be looked for.
    tag: the tag to be looked for.
    gtHandle: an instance of GlobalTagHandler.
    productionGTsDict: (default None) dictionary for the Global Tags in the production workflows, in the form {'hlt' : hltGT, 'express' : expressGT, 'prompt' : promptGT }. When set to None (default), it is retrieved by querying HLT ConfDB and Tier0DataSvc.
    @returns: True if the syncronization is correct, False elsewhere.
    Raises if the input workflow is not in supported ones, or if the dictionary for production workflows is malformed.
    """
    synchronizations = ( 'hlt', 'express', 'prompt', 'pcl', 'offline' )
    if synchronizeTo not in synchronizations:
        logging.error( """The synchronization \"%s\" for tag \"%s\" in database \"%s\" is not supported.""", synchronizeTo, tag, connectionString )
        raise DropBoxError(  """The synchronization \"%s\" for tag \"%s\" in database \"%s\" is not supported.""" %( synchronizeTo, tag, connectionString ) )
    try:
        if productionGTsDict is None:
            productionGTsDict = gtHandle.getProductionGlobalTags()
        workflow = gtHandle.getWorkflowForTagAndDB( connectionString, tag, productionGTsDict )
        check = False
        if workflow is None:
            logging.info( "The tag \"%s\" in account \"%s\" is not present in any production Global Tags. The synchronization \"%s\" specified will be kept.",  tag, connectionString, synchronizeTo )
            check = True #connection string and tag are not in any production Global Tags
        elif synchronizeTo == workflow:
            logging.info( "The tag \"%s\" in account \"%s\" is present in the production Global Tag for workflow \"%s\", which is the same as the synchronization specified.",  tag, connectionString, workflow )
            check = True #connection string and tag are in the production Global Tag for the same workflow specified
        elif synchronizeTo == 'pcl' and workflow == 'prompt':
            logging.info( "The tag \"%s\" in account \"%s\" is present in the production Global Tag for workflow \"%s\", which is consistent with the synchronization \"%s\" specified.",  tag, connectionString, workflow, synchronizeTo )
            check = True #pcl is a particular case for prompt
        else:
            logging.error( "The tag \"%s\" in account \"%s\" is present in the production Global Tag for workflow \"%s\", which is not consistent with the synchronization \"%s\" specified.",  tag, connectionString, workflow, synchronizeTo )
        return check
    except conditionException.ConditionException as ce:
        raise DropBoxError( """The dictionary for the Global Tags in the production workflows is not valid.\nThe reason is: \"%s\"""" %( ce, ) )

def checkDestinationTags( metaDict, productionGTsDict = None ):
    """
    Checks if the destTags field in the metadata dictionary is correct.
    If the destination account and the destination tags as well as the dependent ones are not in the production Global Tags, the request can be processed.
    If the destination account and the destination tags are as well as the dependent ones in at least one Global Tag, the synchronization must be exactly the same as the one of the Global Tag, otherwise the request will not be processed.
    Parameters:
    metaDict: the dictionary extracted from the metadata file.
    productionGTsDict: (default None) dictionary for the Global Tags in the production workflows, in the form {'hlt' : hltGT, 'express' : expressGT, 'prompt' : promptGT }. When set to None (default), it is retrieved by querying HLT ConfDB and Tier0DataSvc.
    @returns: True if the syncronization is correct, False elsewhere.
    Raises if destination database is not provided in the metadata, or if it is not a string; if destination tags are not provided in the metadata, or if they are not encapsulated in a dictionary; if the dictionary for production workflows is malformed.
    """
    try:
        if not checkDestinationDatabase( metaDict ):
            return False
        connectionString = metaDict[ 'destDB' ]
        destTags = metaDict[ 'destTags' ]

        if not isinstance( destTags, dict ):
            logging.error( """The destination tags specified in the metadata file must be encapsulated in a dictionary. The request will not be processed.""" )
            raise DropBoxError(  """The destination tags specified in the metadata file must be encapsulated in a dictionary.""" )
        if not destTags:
            logging.error( """The destination tags are not specified in the metadata file. The request will not be processed.""" )
            return False

        #check the structure of destTags = { "Tag" : { "synchTo" : synch, "dependencies" : { "DepTag" : synch, ... } }, ... } where synch = 'hlt' or 'express' or 'prompt' or 'pcl' or 'offline'
        for tag in destTags.keys():
            if not isinstance( tag, str ):
                logging.error( """The destination tag specified in the metadata file must be a string. The request will not be processed.""" )
                raise DropBoxError( """The destination tag specified in the metadata file must be a string.""" )
            if not tag:
                logging.error( """The destination tag is not specified in the metadata file. The request will not be processed.""" )
                raise DropBoxError( """The destination tag is not specified in the metadata file.""" )
        for synchronizationDict in destTags.values():
            if "synchTo" not in synchronizationDict or "dependencies" not in synchronizationDict:
                logging.error( """The synchronization for the destination tags are not specified in the metadata file. The request will not be processed.""" )
                raise DropBoxError( """The synchronization for the destination tags are not specified in the metadata file.""" )
            if not isinstance( synchronizationDict[ 'synchTo' ], str ):
                logging.error( """The synchronization for the destination tag specified in the metadata file must be a string. The request will not be processed.""" )
                raise DropBoxError( """The synchronization for the destination tag specified in the metadata file must be a string.""" )
            if not isinstance( synchronizationDict[ 'dependencies' ], dict ):
                logging.error( """The dependent tags specified in the metadata file must be encapsulated in a dictionary. The request will not be processed.""" )
                raise DropBoxError( """The dependent tags specified in the metadata file must be encapsulated in a dictionary.""" )
            for dependentTag, synchronizeTo in synchronizationDict[ 'dependencies' ].items():
                if ( not isinstance( dependentTag, str ) ) or ( not isinstance( synchronizeTo, str ) ):
                    logging.error( """The dependent tags and their synchronizations specified in the metadata file must be a string. The request will not be processed.""" )
                    raise DropBoxError( """The dependent tags and their synchronizations specified in the metadata file must be a string.""" )

        logging.info( "Checking whether the synchronizations specified in the metadata file for destination account \"%s\" is consistent with the current production workflows.", connectionString )
        globalTagConnectionString = service.getFrontierConnectionString( service.secrets[ 'connections' ][ 'dev' ][ 'global_tag' ] )
        runControlConnectionString = service.getCxOracleConnectionString( service.secrets[ 'connections' ][ 'dev' ][ 'run_control' ] )
        runInfoConnectionString = service.getFrontierConnectionString( service.secrets[ 'connections' ][ 'dev' ][ 'run_info' ] )
        runInfoStartTag = "runinfo_start_31X_hlt"
        runInfoStopTag = "runinfo_31X_hlt"
        authPath = ""
        tier0DataSvcURI = "https://cmsweb.cern.ch/tier0"
        timeOut = 30
        retries = 3
        retryPeriod = 90
        gtHandle = globalTagHandler.GlobalTagHandler( globalTagConnectionString, runControlConnectionString, runInfoConnectionString, runInfoStartTag, runInfoStopTag, authPath, tier0DataSvcURI, timeOut, retries, retryPeriod )
        for tag, synchronizationDict in destTags.items():
            if not checkSynchronization( synchronizationDict[ 'synchTo' ], connectionString, tag, productionGTsDict ):
                logging.error( "The destination tag \"%s\" in destination account \"%s\" is present in one of the production Global Tags, which is not consistent with the synchronization \"%s\" specified in the metadata file. The request will not be processed.",  tag, connectionString, synchronizationDict[ 'synchTo' ] )
                return False
            for dependentTag, synchronizeTo in synchronizationDict[ 'dependencies' ].items():
                if not checkSynchronization( synchronizeTo, connectionString, dependentTag, productionGTsDict ):
                    logging.error( "The dependendent tag \"%s\" in destination account \"%s\" is present in one of the production Global Tags, which is not consistent with the synchronization \"%s\" specified in the metadata file. The request will not be processed.",  dependentTag, connectionString, synchronizeTo )
                    return False
        return True
    except KeyError:
        logging.error( """The destination tags are not present in the metadata file. The request will not be processed.""" )
        raise DropBoxError(  """The destination tags are not present in the metadata file.""" )
