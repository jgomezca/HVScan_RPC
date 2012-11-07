'''Offline new dropBox.

In this file, only the functionality related to checking the contents of
the uploaded files should be implemented.

The handling of the files is done in dropBox.py.
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = ['Giacomo Govi', 'Salvatore Di Guida', 'Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


import logging
import tarfile
import json
import cStringIO
import tempfile
import sqlite3

import typeMatch
import service

import config
import dropBox
import conditionDatabase
import conditionError
import globalTagHandler


dataFilename = 'data.db'
metadataFilename = 'metadata.txt'


def checkSynchronization(synchronizeTo, destinationDatabase, tag, gtHandle, productionGTsDict):
    '''Checks if a connection string and a tag are compatible with the synchronization for a workflow against the production Global Tags.

    If the destination account and the destination tags are not in the production Global Tags, any synchronization is valid.
    If the destination account and the destination tags are in at least one Global Tag, the synchronization must be exactly the same as the one of the Global Tag.

    Raises if the dictionary for production workflow is malformed, or if the synchronization is not correct.
    '''

    workflow = gtHandle.getWorkflowForTagAndDB(destinationDatabase, tag, productionGTsDict)

    #connection string and tag are not in any production Global Tags
    #connection string and tag are in the production Global Tag for the same workflow specified
    #pcl is a particular case for prompt
    if workflow is None \
        or synchronizeTo == workflow \
        or (synchronizeTo == 'pcl' and workflow == 'prompt'):
        return

    raise dropBox.DropBoxError('The synchronization "%s" for tag "%s" in database "%s" provided in the metadata does not match the one in the global tag for workflow "%s".' % (synchronizeTo, tag, destinationDatabase, workflow))


def checkContents(fileHash, dataPath, metadata):
    '''Checks whether the data and metadata are correct.

    data is the filename of the sqlite file.
    metadata is a string with the metadata file itself.
    '''

    logging.debug('check::checkContents(%s, %s, %s)', fileHash, dataPath, repr(metadata))

    logging.info('checkContents(): %s: Checking metadata structure...', fileHash)

    workflows = (u'offline', u'hlt', u'express', u'prompt', u'pcl')

    structure = {
        u'destinationDatabase': (True, unicode),
        u'inputTag': (True, unicode),
        u'since': (True, (int, type(None))),
        u'emails': (False, [unicode]),
        u'userText': (True, unicode),
        u'destinationTags': (True, {
            unicode: {
                u'synchronizeTo': (True, workflows),
                u'dependencies': (False, {
                    unicode: workflows,
                }),
            },
        })
    }

    try:
        typeMatch.match(structure, metadata)
    except typeMatch.MatchError as e:
        raise dropBox.DropBoxError('In the metadata, ' + str(e))

    logging.info('checkContents(): %s: Checking data with respect to metadata...', fileHash)

    db = conditionDatabase.ConditionDBChecker('sqlite_file:%s' % dataPath, '')

    try:
        # Corrupted file
        try:
            tags = db.getAllTags()
        except conditionError.ConditionError as e:
            raise dropBox.DropBoxError('The file is corrupted, as it was not possible to get the list of tags inside it.')

        # Empty file
        if not tags:
            raise dropBox.DropBoxError('The file does not contain any tags, so it is likely not hosting any Condition payloads.')

        # Wrong input tag
        if metadata['inputTag'] not in tags:
            raise dropBox.DropBoxError('The input tag "%s" is not in the input SQLite file.' % metadata['inputTag'])

        # Unsupported service
        destinationDatabase = metadata['destinationDatabase']
        if not destinationDatabase.startswith('oracle:'):
            raise dropBox.DropBoxError('Oracle is the only supported service.')

        # Invalid connection string
        try:
            if not conditionDatabase.checkConnectionString(destinationDatabase, True):
                raise dropBox.DropBoxError('The destination database cannot point to read-only services.')
        except conditionError.ConditionError as err:
            raise dropBox.DropBoxError('The connection string is not correct. The reason is: %s' % err)

        # Invalid since
        since = metadata['since']
        if since is not None:
            firstSince = db.iovSequence(metadata['inputTag']).firstSince()
            if since < firstSince:
                raise dropBox.DropBoxError('The since value "%d" specified in the metadata cannot be smaller than the first IOV since "%d"' % (since, firstSince))

        # Invalid synchronizations
        gtHandle = globalTagHandler.GlobalTagHandler(
            service.getFrontierConnectionString(service.secrets['connections']['dev']['global_tag']),
            service.getCxOracleConnectionString(service.secrets['connections']['dev']['run_control']),
            service.getFrontierConnectionString(service.secrets['connections']['dev']['run_info']),
            'runinfo_start_31X_hlt',
            'runinfo_31X_hlt',
            '',
            'https://cmsweb.cern.ch/tier0',
            30,
            3,
            90,
        )

        try:
            productionGTsDict = gtHandle.getProductionGlobalTags()
        except conditionError.ConditionError:
            productionGTsDict = config.productionGlobalTags

        for tag, synchronizationDict in metadata['destinationTags'].items():
            checkSynchronization(synchronizationDict['synchronizeTo'], destinationDatabase, tag, gtHandle, productionGTsDict)

            for dependentTag, synchronizeTo in synchronizationDict['dependencies'].items():
                checkSynchronization(synchronizeTo, destinationDatabase, dependentTag, gtHandle, productionGTsDict)

    finally:
        db.close()


def checkFile(fileHash, fileContent):
    '''Checks that a tar file and its contents are correct.

    Called from the dropBox to check a file after it was received correctly.
    The received file is guaranteed to be already checksummed.
    '''

    logging.debug('check::checkFile(%s, %s [len])', fileHash, len(fileContent))

    logging.info('checkFile(): %s: Checking whether the file is a valid tar file...', fileHash)
    fileObject = cStringIO.StringIO()
    fileObject.write(fileContent)
    fileObject.seek(0)
    try:
        tarFile = tarfile.open(fileHash, 'r:bz2', fileobj = fileObject)
    except tarfile.TarError as e:
        raise dropBox.DropBoxError('The file is not a valid tar file.')

    with tempfile.NamedTemporaryFile() as temporaryDataFile:
        try:
            logging.info('checkFile(): %s: Checking whether the tar file contains the and only the expected file names...', fileHash)
            if tarFile.getnames() != [dataFilename, metadataFilename]:
                raise dropBox.DropBoxError('The file tar file does not contain the and only the expected file names.')

            logging.info('checkFile(): %s: Checking whether each file has the expected attributes...', fileHash)
            for tarInfo in tarFile.getmembers():
                if tarInfo.mode != 0400 \
                    or tarInfo.uid != 0 \
                    or tarInfo.gid != 0 \
                    or tarInfo.mtime != 0 \
                    or tarInfo.uname != 'root' \
                    or tarInfo.gname != 'root':
                    raise dropBox.DropBoxError('The file %s has unexpected attributes.' % tarInfo.name)

            logging.info('checkFile(): %s: Extracting metadata in memory...', fileHash)
            metadata = tarFile.extractfile(metadataFilename).read()

            logging.info('checkFile(): %s: Extracting data in file %s...', fileHash, temporaryDataFile.name)
            temporaryDataFile.write(tarFile.extractfile(dataFilename).read())
            temporaryDataFile.flush()
            # We do not need os.fsync(temporaryDataFile.fileno()) since
            # we do not care if the file is in the disk or not if we lose it,
            # it is a temporary file. Avoiding the fsync() will perform better.
            # However, we do need flush(), otherwise some files will fail
            # (e.g. small files that do not fill the buffer).
        finally:
            tarFile.close()

        try:
            logging.info('checkFile(): %s: Parsing JSON metadata...', fileHash)
            metadata = json.loads(metadata)
        except ValueError:
            raise dropBox.DropBoxError('The metadata is not valid JSON.')

        try:
            logging.info('checkFile(): %s: Checking the data is a valid SQLite 3 database...', fileHash)
            dataConnection = sqlite3.connect(temporaryDataFile.name)
            dataConnection.execute('select 1 from sqlite_master')
        except sqlite3.DatabaseError as e:
            raise dropBox.DropBoxError('The data is not a valid SQLite 3 database.')
        except Exception as e:
            raise dropBox.DropBoxError('The data could not be read.')
        finally:
            dataConnection.close()

        checkContents(fileHash, temporaryDataFile.name, metadata)

    logging.info('checkFile(): %s: Checking of the file was successful.', fileHash)

    # To avoid uncompressing again the metadata again in dropBox.py
    # (for uploading it to the database), we return it.
    return metadata

