import conditionDatabase
import conditionError
import dropBox
import globalTagHandler
import service

import config

def checkCorruptedOrEmptyFile( dbFile ):
    """
    Checks if a SQLite file is corrupted or just empty (i.e. containing only empty tables) by checking if there are tags inside.
    The corrupted or empty files with the corresponding metadata files are skipped from processing and put into a dedicated folder.
    Parameters:
    dbFile: the name of the SQLite file;
    Raises if the file is corrupted or empty.
    """
    db = conditionDatabase.ConditionDBChecker( "sqlite_file:"+dbFile, "" )
    try:
        db.getAllTags()
    except conditionError.ConditionError as e:
        raise dropBox.DropBoxError( "The file %s is corrupted or empty." %( dbFile, ) )

def checkDestinationDatabase( metaDict ):
    """
    Checks if the destinationDatabase field in the metadata dictionary is valid, i.e. point to an Oracle service where updates are allowed.
    Raises if destination database is not valid.
    """
    try:
        connectionString = metaDict[ 'destinationDatabase' ]
        if not connectionString.startswith( 'oracle:' ):
            raise dropBox.DropBoxError( "Oracle is the only supported service." )
        if not conditionDatabase.checkConnectionString( connectionString, True ):
            raise dropBox.DropBoxError( 'The destination database cannot point to read-only services.' )
    except conditionError.ConditionError as err:
        raise dropBox.DropBoxError( 'The connection string is not correct. The reason is: %s' % err )

def checkInputTag( dbFile, metaDict ):
    """
    Checks if a SQLite file contains the input tag specified in the metadata dictionary.
    The wrong files with the corresponding metadata files are skipped from processing and put in dedicated folder.
    Parameters:
    dbFile: the name of the SQLite file;
    metaDict: the dictionary extracted from the metadata file.
    Raises if the input tag in the metadata is not found in the SQLite file.
    """
    db = conditionDatabase.ConditionDBChecker( "sqlite_file:"+dbFile, "" )
    if not db.checkTag( metaDict[ 'inputTag' ] ):
        raise dropBox.DropBoxError( "The input tag \"%s\" is not in the input SQLite file." % metaDict[ 'inputTag' ] )

#FIXME: do we need to update the request if the since in the metadata file is null?
def checkSince( dbFile, metaDict ):
    """
    Checks if the since field in the metadata dictionary is correct.
    If the since field is None, it assumes that the value will be taken from the SQLite file, being the first since of the input tag.
    If the since field is not None, it must be not smaller than the first since of the input tag in the SQLite file.
    Parameters:
    dbFile: the name of the SQLite file;
    metaDict: the dictionary extracted from the metadata file.
    Raises if the since value in the metadata is not None and smaller than the first IOV since in the SQLite file.
    """
    since = metaDict[ 'since' ]
    firstSince = conditionDatabase.ConditionDBChecker("sqlite_file:" + dbFile, "").iovSequence( metaDict[ 'inputTag' ] ).firstSince()
    if since is not None:
        if since < firstSince:
            raise dropBox.DropBoxError( "The since value \"%d\" specified in the metadata cannot be smaller than the first IOV since \"%d\"" %( since, firstSince ) )


def checkSynchronization( synchronizeTo, connectionString, tag, gtHandle ):
    """
    Checks if a connection string and a tag are compatible with the synchronization for a workflow against the production Global Tags.
    If the destination account and the destination tags are not in the production Global Tags, any synchronization is valid.
    If the destination account and the destination tags are in at least one Global Tag, the synchronization must be exactly the same as the one of the Global Tag.
    Parameters:
    synchronizeTo: the synchronization for the workflow to be looked for.
    connectionString: the connection string to be looked for.
    tag: the tag to be looked for.
    gtHandle: an instance of GlobalTagHandler.
    Raises if the dictionary for production workflow is malformed, or if the synchronization is not correct.
    """
    try:
        productionGTsDict = gtHandle.getProductionGlobalTags()
    except conditionError.ConditionError:
        productionGTsDict = config.productionGlobalTags
    workflow = gtHandle.getWorkflowForTagAndDB( connectionString, tag, productionGTsDict )
    check = False
    if workflow is None:
        check = True #connection string and tag are not in any production Global Tags
    elif synchronizeTo == workflow:
        check = True #connection string and tag are in the production Global Tag for the same workflow specified
    elif synchronizeTo == 'pcl' and workflow == 'prompt':
        check = True #pcl is a particular case for prompt
    if not check:
        raise dropBox.DropBoxError( "The synchronization \"%s\" for tag \"%s\" in database \"%s\" provided in the metadata does not match the one in the global tag for workflow \"%s\"." %( synchronizeTo, tag, connectionString, workflow ) )

def checkDestinationTags( metaDict ):
    """
    Checks if the destinationTags field in the metadata dictionary is correct.
    If the destination account and the destination tags as well as the dependent ones are not in the production Global Tags, the request can be processed.
    If the destination account and the destination tags are as well as the dependent ones in at least one Global Tag, the synchronization must be exactly the same as the one of the Global Tag, otherwise the request will not be processed.
    Parameters:
    metaDict: the dictionary extracted from the metadata file.
    Raises if the dictionary for production workflows is malformed, or if the synchronization for one of the tags is not correct.
    """
    connectionString = metaDict[ 'destinationDatabase' ]
    destinationTags = metaDict[ 'destinationTags' ]
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
    for tag, synchronizationDict in destinationTags.items():
        checkSynchronization( synchronizationDict[ 'synchronizeTo' ], connectionString, tag, gtHandle )
        for dependentTag, synchronizeTo in synchronizationDict[ 'dependencies' ].items():
            checkSynchronization( synchronizeTo, connectionString, dependentTag, gtHandle )

