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
    Raises if the file is corrupted or empty.
    """
    db = conditionDatabase.ConditionDBChecker( "sqlite_file:"+dbFile, "" )
    try:
        db.getAllTags()
    except conditionException.ConditionException as e:
        raise DropBoxError( "The file %s is corrupted or empty." %( dbFile, ) )

def checkDestinationDatabase( metaDict ):
    """
    Checks if the destDB field in the metadata dictionary is valid, i.e. point to an Oracle service where updates are allowed.
    Raises if destination database is not valid.
    """
    try:
        connectionString = metaDict[ 'destDB' ]
        if not connectionString.startswith( 'oracle:' ):
            raise DropBoxError( "Oracle is the only supported service." )
        if not conditionDatabase.checkConnectionString( connectionString, True ):
            raise DropBoxError( "The destination database in connection string \"%s\" cannot point to read-only services." )
    except conditionError.ConditionError as err:
        raise DropBoxError( "The connection string is not correct.\nThe reason is: %s" %( err, ) )

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
        raise DropBoxError( "The input tag \"%s\" is not in the input SQLite file \"%s\"." %( metaDict[ 'inputTag' ], dbFile ) )

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
            raise DropBoxError( "The since value \"%d\" specified in the metadata cannot be smaller than the first IOV since \"%d\"" %( since, firstSince ) )


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
    Raises if the input workflow is not in supported ones, if the dictionary for production workflow is malformed, or if the synchronization is not correct.
    """
    synchronizations = ( 'hlt', 'express', 'prompt', 'pcl', 'offline' )
    if synchronizeTo not in synchronizations:
        raise DropBoxError(  """The synchronization \"%s\" for tag \"%s\" in database \"%s\" is not supported.""" %( synchronizeTo, tag, connectionString ) )
    try:
        if productionGTsDict is None:
            productionGTsDict = gtHandle.getProductionGlobalTags()
        workflow = gtHandle.getWorkflowForTagAndDB( connectionString, tag, productionGTsDict )
        check = False
        if workflow is None:
            check = True #connection string and tag are not in any production Global Tags
        elif synchronizeTo == workflow:
            check = True #connection string and tag are in the production Global Tag for the same workflow specified
        elif synchronizeTo == 'pcl' and workflow == 'prompt':
            check = True #pcl is a particular case for prompt
        if not check:
            raise DropBoxError( "The synchronization \"%s\" for tag \"%s\" in database \"%s\" provided in the metadata does not match the one in the global tag for workflow \"%s\"." %( synchronizeTo, tag, connectionString, workflow ) )
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
    Raises if the dictionary for production workflows is malformed, if one of the input workflows are not supported, or if the synchronization for one of the tags is not correct.
    """
    #check the structure of destTags = { "Tag" : { "synchTo" : synch, "dependencies" : { "DepTag" : synch, ... } }, ... } where synch = 'hlt' or 'express' or 'prompt' or 'pcl' or 'offline'
    connectionString = metaDict[ 'destDB' ]
    destTags = metaDict[ 'destTags' ]
    for tag in destTags.keys():
        if not isinstance( tag, str ):
            raise DropBoxError( """The destination tag specified in the metadata file must be a string.""" )
        if not tag:
            raise DropBoxError( """The destination tag is not specified in the metadata file.""" )
    for synchronizationDict in destTags.values():
        if "synchTo" not in synchronizationDict or "dependencies" not in synchronizationDict:
            raise DropBoxError( """The synchronization for the destination tags are not specified in the metadata file.""" )
        if not isinstance( synchronizationDict[ 'synchTo' ], str ):
            raise DropBoxError( """The synchronization for the destination tag specified in the metadata file must be a string.""" )
        if not isinstance( synchronizationDict[ 'dependencies' ], dict ):
            raise DropBoxError( """The dependent tags specified in the metadata file must be encapsulated in a dictionary.""" )
        for dependentTag, synchronizeTo in synchronizationDict[ 'dependencies' ].items():
            if ( not isinstance( dependentTag, str ) ) or ( not isinstance( synchronizeTo, str ) ):
                raise DropBoxError( """The dependent tags and their synchronizations specified in the metadata file must be a string.""" )

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
        checkSynchronization( synchronizationDict[ 'synchTo' ], connectionString, tag, gtHandle, productionGTsDict )
        for dependentTag, synchronizeTo in synchronizationDict[ 'dependencies' ].items():
            checkSynchronization( synchronizeTo, connectionString, dependentTag, gtHandle, productionGTsDict )