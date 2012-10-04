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


def checkContents(fileHash, data, metadata):
    '''Checks whether the data and metadata are correct.

    data is a sqlite3 cursor ready to be used.
    metadata is a string with the metadata file itself.
    '''

    logging.debug('check::checkContents(%s, %s, %s)', fileHash, data, repr(metadata))

    logging.info('checkContents(): %s: Checking metadata...', fileHash)

    if not isinstance(metadata, dict):
        raise dropBox.DropBoxError('The metadata is not a dictionary.')

    if not set(metadata.keys()).issubset([
        u'destDB',
        u'destTag',
        u'duplicateTo',
        u'exportTo',
        u'inputTag',
        u'timeType',
        u'since',
        u'usertext',
    ]):
        raise dropBox.DropBoxError('The metadata contains invalid keys.')

    if u'timeType' in metadata and metadata[u'timeType'] not in [
        u'runnumber',
        u'lumiid',
        u'timestamp',
        u'hash',
        u'user',
    ]:
        raise dropBox.DropBoxError('The metadata\'s timeType key contains an invalid value.')

    if 'exportTo' in metadata and metadata[u'exportTo'] not in [
        u'offline',
        u'hlt',
        u'express',
        u'prompt',
        u'pcl',
    ]:
        raise dropBox.DropBoxError('The metadata\'s exportTo key contains an invalid value.')


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
        except Exception as e:
            raise dropBox.DropBoxError('The data could not be read.')

        try:
            logging.info('checkFile(): %s: Checking content of the files...', fileHash)
            data = dataConnection.cursor()
            checkContents(fileHash, data, metadata)
        finally:
            data.close()
            dataConnection.close()
    finally:
        logging.info('checkFile(): %s: Removing extracted files...', fileHash)
        os.unlink(dataPath)
        os.unlink(metadataPath)
        os.rmdir(extractedFolderPath)

    logging.info('checkFile(): %s: Checking of the file was successful.', fileHash)

