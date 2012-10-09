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

    #-mos TODO: Improve error messages for nested dictionaries/structures.
    #-mos TODO: Move to common, maybe, since this can be useful for others.
    #-mos TODO: Since this was thought to match JSON, we can use tuple with
    #           a special meaning and other types like set will not be present
    #           in JSON either. However, if want to make this generic, add a
    #           special class to match a possible set of matches (i.e. what
    #           the current tuple does), and then add support for iterating
    #           over sets/tuples/etc. in the "value" case (i.e. else) like
    #           it is done now for lists.

    if type(structure) == tuple:
        # If the type is a tuple, check whether the data matches any of the structures.
        # This can be used to match against several types, values, etc.
        # e.g. 'asdf', 123 and 1.3 matches (int, str, 1.3), but 1.2 does not.

        ok = False
        for item in structure:
            try:
                checkStructure(metadata, item)
                ok = True
                break
            except dropBox.DropBoxError:
                pass

        if not ok:
            raise dropBox.DropBoxError('In the metadata, %s does not match the expected structure.' % metadata)

    elif type(structure) == dict:
        # If the type is a dictionary, the structure can contain two kinds of
        # keys: values or types. First, keys in data are matched with the values
        # i.e. fixed keys. If found, their value is a tuple (isRequiredKey, value).
        # Value is as usual the structure for the value in the data, and isRequiredKey
        # allows to specify whether this key must be in the data.
        # Then, if a key did not match any of the fixed keys, the key is matched
        # against the types.
        #
        # Example:
        #
        # {
        #     u'myRequiredKey': (True, str),
        #     u'myOptionalKey': (False, int),
        #     unicode: int,
        # }
        #
        # This structure tells that the data dictionary must contain a required
        # key with name myRequiredKey and that its value must be a string.
        # Then, the dictionary may contain myOptionalKey, which in that case
        # its value must be an integer.
        # Finally, other keys of type unicode are allowed, which their value
        # must be of type int.

        fixedKeys = set([x for x in structure.keys() if type(x) != type])
        typeKeys = set([x for x in structure.keys() if type(x) == type])

        requiredFixedKeys = set([x for x in fixedKeys if structure[x][0]])

        for key in metadata:
            # First try to match the key with the structure's fixed keys, if any.
            if key in fixedKeys:
                requiredFixedKeys.discard(key)
                checkStructure(metadata[key], structure[key][1])
                continue

            # If the key did not match a fixed one, let's try to match it
            # with one of the types, if any.
            if type(key) in typeKeys:
                checkStructure(metadata[key], structure[type(key)])
                continue

            raise dropBox.DropBoxError('In the metadata, key %s does not match the expected structure.' % key)

        # Now check that all the required keys were found
        if len(requiredFixedKeys) != 0:
            raise dropBox.DropBoxError('In the metadata, keys %s are required and were not found.' % list(requiredFixedKeys))

    elif type(structure) == list:
        # If the type is a list, we match all elements in the data against
        # the element of the list.
        # i.e. we only allow here to match an entire list with one structure,
        # so it is not possible to match by position.
        # e.g. [int] means a list of ints so [1,2,3] would match.
        # e.g. [(int, float)] means a list of int or flots so [1,1.2] would match.
        for item in metadata:
            checkStructure(item, structure[0])

    elif type(structure) == type:
        # If the type is a type itself, e.g. we match against unicode, we check
        # whether the data is an instance of that type.
        if not isinstance(metadata, structure):
            raise dropBox.DropBoxError('In the metadata, type %s is not and instance of %s.' % (type(metadata).__name__, structure.__name__))

    else:
        # If the type is not a tuple, dict or list and it is not a type itself,
        # we consider that this is a value so we compare it directly.
        if metadata != structure:
            raise dropBox.DropBoxError('In the metadata, %s is not equal to %s.' % (metadata, structure))


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
            dataConnection.execute('select 1 from sqlite_master')
        except sqlite3.DatabaseError as e:
            raise dropBox.DropBoxError('The data is not a valid SQLite 3 database.')
        except Exception as e:
            raise dropBox.DropBoxError('The data could not be read.')
        finally:
            dataConnection.close()

        logging.info('checkFile(): %s: Checking content of the files...', fileHash)
        checkContents(fileHash, dataPath, metadata)
    finally:
        logging.info('checkFile(): %s: Removing extracted files...', fileHash)
        os.unlink(dataPath)
        os.unlink(metadataPath)
        os.rmdir(extractedFolderPath)

    logging.info('checkFile(): %s: Checking of the file was successful.', fileHash)

