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


import os
import logging
import tarfile
import json
import sqlite3

import config
import dropBox
import checkTodo


def getExtractedFilePath(fileHash):
    '''Returns the path of the given extracted file.
    '''

    return os.path.join(config.extractedFilesPath, fileHash)


def getFilePathInExtractedFile(fileHash, filename):
    '''Returns the path of a file inside the given extracted file.
    '''

    return os.path.join(getExtractedFilePath(fileHash), filename)


dataFilename = 'data.db'
metadataFilename = 'metadata.txt'


def checkStructure(metadata, structure):
    '''Checks the structure of the metadata.
    '''

    #-mos XXX: I will clean this: Explain how it works, add proper error
    #          messages with a proper chain from the top levels, etc...
    #          Then move it to common because it can be useful for others
    #          to some file like type.py or checkType.py.
    #          Also, check that there are no more keys than those specified.

    if type(structure) == tuple:
        if metadata not in structure:
            raise dropBox.DropBoxError('In the metadata, value %s is not any of %s.' % (str(metadata), str(structure),))

    elif type(structure) == set:
        ok = False
        for item in structure:
            try:
                checkStructure(metadata, item)
                ok = True
                break
            except dropBox.DropBoxError:
                pass
        if not ok:
            raise dropBox.DropBoxError('In the metadata, type %s is not any of %s.' % (str(type(metadata)), str(structure),))
        return

    elif type(structure) == dict:
        for key in structure.keys():
            if type(key) == unicode:
                # Key with a fixed name, check value
                (requiredKey, valueStructure) = structure[key]

                try:
                    value = metadata[key]
                except KeyError:
                    if not requiredKey:
                        raise dropBox.DropBoxError('In the metadata, key %s is required.' % key)
                    continue

                checkStructure(value, valueStructure)
            else:
                # Other kind
                for metadataKey in metadata:
                    checkStructure(metadataKey, key)
                    checkStructure(metadata[metadataKey], structure[key])

    elif type(structure) == list:
        for item in metadata:
            checkStructure(item, structure[0])

    elif type(structure) == type(int):
        if type(metadata) != structure:
            raise dropBox.DropBoxError('In the metadata, type %s is not equal to %s.' % (str(type(metadata)), str(structure),))

    else:
        if type(metadata) != type(structure):
            raise dropBox.DropBoxError('In the metadata, type %s is not equal to %s.' % (str(type(metadata)), str(type(structure)),))


def checkContents(fileHash, data, metadata):
    '''Checks whether the data and metadata are correct.

    data is the filename of the sqlite file.
    metadata is a string with the metadata file itself.
    '''

    logging.debug('check::checkContents(%s, %s, %s)', fileHash, data, repr(metadata))

    logging.info('checkContents(): %s: Checking metadata...', fileHash)

    if not isinstance(metadata, dict):
        raise dropBox.DropBoxError('The metadata is not a dictionary.')

    workflows = (u'offline', u'hlt', u'express', u'prompt', u'pcl')

    structure = {
        u'destinationDatabase': (False, unicode),
        u'inputTag': (False, unicode),
        u'since': (False, set([int, None])),
        u'emails': (True, [unicode]),
        u'userText': (False, unicode),
        u'destinationTags': (False, {
            unicode: {
                u'synchronizeTo': (False, workflows),
                u'dependencies': (True, {
                    unicode: workflows,
                }),
            },
        })
    }

    checkStructure(metadata, structure)

    checkTodo.checkCorruptedOrEmptyFile(data)
    checkTodo.checkDestinationDatabase(metadata)
    checkTodo.checkInputTag(data, metadata)
    checkTodo.checkSince(data, metadata)
    checkTodo.checkDestinationTags(metadata)


def checkFile(filename):
    '''Checks that a tar file and its contents are correct.

    Called from the dropBox to check a file after it was received correctly.
    The received file is guaranteed to be already checksummed.
    '''

    logging.debug('check::checkFile(%s)', filename)

    fileHash = os.path.basename(filename)

    logging.info('checkFile(): %s: Checking whether the file is a valid tar file...', fileHash)
    try:
        tarFile = tarfile.open(filename, 'r:bz2')
    except tarfile.TarError as e:
        raise dropBox.DropBoxError('The file is not a valid tar file.')

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

        logging.info('checkFile(): %s: Extracting files...', fileHash)
        extractedFolderPath = getExtractedFilePath(fileHash)
        tarFile.extractall(extractedFolderPath)
    finally:
        tarFile.close()

    try:
        dataPath = getFilePathInExtractedFile(fileHash, dataFilename)
        metadataPath = getFilePathInExtractedFile(fileHash, metadataFilename)

        try:
            logging.info('checkFile(): %s: Reading metadata...', fileHash)
            with open(metadataPath, 'rb') as f:
                metadata = json.load(f)
        except ValueError:
            raise dropBox.DropBoxError('The metadata is not valid JSON.')
        except Exception as e:
            raise dropBox.DropBoxError('The metadata could not be read.')

        try:
            logging.info('checkFile(): %s: Opening connection to data...', fileHash)
            dataConnection = sqlite3.connect(dataPath)
            dataConnection.close()
        except Exception as e:
            raise dropBox.DropBoxError('The data could not be read.')

        logging.info('checkFile(): %s: Checking content of the files...', fileHash)
        checkContents(fileHash, dataPath, metadata)
    finally:
        logging.info('checkFile(): %s: Removing extracted files...', fileHash)
        os.unlink(dataPath)
        os.unlink(metadataPath)
        os.rmdir(extractedFolderPath)

    logging.info('checkFile(): %s: Checking of the file was successful.', fileHash)

