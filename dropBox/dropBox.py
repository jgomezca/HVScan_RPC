'''Offline new dropBox.

In this file, only the functionality related to the handling of the files
for the dropBox should be implemented. This includes the authentication.

The web interface is done in server.py.
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = ['Giacomo Govi', 'Salvatore Di Guida', 'Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


import re
import os
import shutil
import logging
import hashlib

import cx_Oracle

import config
import databaseLog


# Declared before import check, so that check.py can access it
class DropBoxError(Exception):
    def __init__(self, message):
        self.args = (message, )


import check


def getUploadedFilePath(fileHash):
    '''Returns the path of the given uploaded file.
    '''

    return os.path.join(config.uploadedFilesPath, fileHash)


def getPendingFilePath(fileHash):
    '''Returns the path of the given pending file.
    '''

    return os.path.join(config.pendingFilesPath, fileHash)


def getAcknowledgedFilePath(fileHash):
    '''Returns the path of the given acknowledged file.
    '''

    return os.path.join(config.acknowledgedFilesPath, fileHash)


def getBadFilePath(fileHash):
    '''Returns the path of the given bad file.
    '''

    return os.path.join(config.badFilesPath, fileHash)


def getHash(data):
    '''Returns the SHA1 hash of the argument (hex digest).
    '''

    return hashlib.sha1(data).hexdigest()

# Length of a hash
hashLength = len(getHash(''))


def checkHash(fileHash):
    '''Checks whether the argument is a valid SHA1 hash.
    '''

    if re.match('^[0-9a-f]{%s}$' % hashLength, fileHash) is None:
        raise DropBoxError('The hash is not a valid SHA1 hash.')


def checkPendingFile(fileHash):
    '''Checks whether a pending file exists.
    '''

    if not os.path.exists(getPendingFilePath(fileHash)):
        raise DropBoxError('The pending file %s does not exist.' % fileHash)


def failUpload(fileHash):
    '''Fails an upload moving it to the bad folder.
    '''

    logging.info('uploadFile(): %s: Moving file to the bad folder...', fileHash)
    os.rename(getUploadedFilePath(fileHash), getBadFilePath(fileHash))

    logging.info('uploadFile(): %s: The upload failed.', fileHash)


def uploadFile(fileHash, fileContent, username):
    '''Uploads a file to the dropbox for online.
    '''

    logging.debug('dropBox::uploadFile(%s, %s [len])', fileHash, len(fileContent))

    logging.info('uploadFile(): Checking whether the hash is valid...')
    checkHash(fileHash)

    logging.info('uploadFile(): %s: Checking the file content hash...', fileHash)
    fileContentHash = getHash(fileContent)
    if fileHash != fileContentHash:
        raise DropBoxError('The given file hash %s does not match with the file content hash %s.' % (fileHash, fileContentHash))

    logging.info('uploadFile(): %s: Checking whether the file already exists...', fileHash)

    if os.path.exists(getUploadedFilePath(fileHash)):
        raise DropBoxError('The uploaded file with hash %s already exists in the Uploaded files (i.e. not yet processed). This probably means that you sent the same request twice in a short time.' % fileHash)

    if os.path.exists(getPendingFilePath(fileHash)):
        raise DropBoxError('The uploaded file with hash %s already exists in the Pending files (i.e. files that are waiting to be pulled by online that were already checked). This probably means that you sent the same request twice in a short time.' % fileHash)

    if os.path.exists(getAcknowledgedFilePath(fileHash)):
        raise DropBoxError('The uploaded file with hash %s already exists in the Acknowledged files (i.e. files that were already pulled by online not too long ago -- we do not keep all of them forever). This probably means that you sent the same request twice after some time.' % fileHash)

    if os.path.exists(getBadFilePath(fileHash)):
        raise DropBoxError('The uploaded file with hash %s already exists in the Bad files (i.e. files that were wrong for some reason). Therefore this file will be skipped since the results of the checks should be the same again (i.e. wrong).' % fileHash)

    logging.info('uploadFile(): %s: Writing, flushing and fsyncing the uploaded file...', fileHash)
    with open(getUploadedFilePath(fileHash), 'wb') as f:
        f.write(fileContent)
        f.flush()
        os.fsync(f.fileno())

    logging.info('uploadFile(): %s: Checking whether the uploaded file exists...', fileHash)
    if not os.path.exists(getUploadedFilePath(fileHash)):
        raise DropBoxError('The uploaded file %s does not exist.' % fileHash)

    logging.info('uploadFile(): %s: Checking the contents of the file...', fileHash)
    try:
        check.checkFile(getUploadedFilePath(fileHash))
    except DropBoxError as e:
        failUpload(fileHash)
        raise e

    logging.info('uploadFile(): %s: Inserting entry with username %s in the fileLog...', fileHash, username)
    try:
        databaseLog.insertFileLog(fileHash, 100, username)
    except cx_Oracle.IntegrityError:
        failUpload(fileHash)
        raise DropBoxError('The uploaded file %s was already requested in the database.' % fileHash)

    logging.info('uploadFile(): %s: Moving file to pending folder...', fileHash)
    os.rename(getUploadedFilePath(fileHash), getPendingFilePath(fileHash))

    logging.info('uploadFile(): %s: The upload was successful.', fileHash)


def getFileList():
    '''Returns a list of files yet to be pulled from online.

    The name of each file is the SHA1 checksum of the file itself.

    Called from online, but also public to allow people to see the list.
    '''

    logging.debug('dropBox::getFileList()')

    logging.info('getFileList(): Getting the list of files...')

    fileList = os.listdir(config.pendingFilesPath)
    fileList.remove('.gitignore')

    return fileList


def getFile(fileHash):
    '''Returns a file from the list.

    Called from online.

    It does *not* remove the file from the list, even if the transfer
    appears to be successful. Online must call ackFile() to acknowledge
    that it got the file successfully.
    '''

    logging.debug('dropBox::getFile(%s)', fileHash)

    logging.info('getFile(): Checking whether the hash is valid...')
    checkHash(fileHash)

    logging.info('getFile(): %s: Checking whether the pending file exists...', fileHash)
    checkPendingFile(fileHash)

    logging.info('getFile(): %s: Serving file...', fileHash)
    return getPendingFilePath(fileHash)


def acknowledgeFile(fileHash):
    '''Acknowledges that a file was received in online.

    Called from online.
    '''

    logging.debug('dropBox::acknowledgeFile(%s)', fileHash)

    logging.info('acknowledgeFile(): Checking whether the hash is valid...')
    checkHash(fileHash)

    logging.info('acknowledgeFile(): %s: Checking whether the pending file exists...', fileHash)
    checkPendingFile(fileHash)

    logging.info('acknowledgeFile(): %s: Moving file to acknowledge folder...', fileHash)
    os.rename(getPendingFilePath(fileHash), getAcknowledgedFilePath(fileHash))

    logging.info('acknowledgeFile(): %s: Checking whether the acknowledged file exists...', fileHash)
    if not os.path.exists(getAcknowledgedFilePath(fileHash)):
        raise DropBoxError('The acknowledged file %s does not exist.' % fileHash)


def updateFileStatus(fileHash, statusCode):
    '''Updates the status code of a file.

    Called from online.
    '''

    logging.debug('dropBox::updateFileStatus(%s, %s)', fileHash, statusCode)

    databaseLog.updateFileLogStatus(fileHash, statusCode)


def updateFileLog(fileHash, log, runLogCreationTimestamp):
    '''Uploads the log of a file and the creationTimestamp of the run
    where the file has been processed.

    Called from online, after processing a file.
    '''

    logging.debug('dropBox::updateFileLog(%s, %s, %s)', fileHash, log, runLogCreationTimestamp)

    databaseLog.updateFileLogLog(fileHash, log, runLogCreationTimestamp)


def updateRunStatus(creationTimestamp, statusCode):
    '''Updates the status code of a run.

    Called from online, while it processes zero or more files.
    '''

    logging.debug('dropBox::updateRunStatus(%s, %s)', creationTimestamp, statusCode)

    databaseLog.insertOrUpdateRunLog(creationTimestamp, statusCode)


def updateRunRuns(creationTimestamp, firstConditionSafeRun, hltRun):
    '''Updates the runs (run numbers) of a run (online dropBox run).

    Called from online.
    '''

    logging.debug('dropBox::updateRunRuns(%s, %s, %s)', creationTimestamp, firstConditionSafeRun, hltRun)

    databaseLog.updateRunLogRuns(creationTimestamp, firstConditionSafeRun, hltRun)


def updateRunLog(creationTimestamp, downloadLog, globalLog):
    '''Uploads the logs and final statistics of a run.

    Called from online, after processing zero or more files.
    '''

    logging.debug('dropBox::updateRunLog(%s, %s, %s)', creationTimestamp, downloadLog, globalLog)

    databaseLog.updateRunLogInfo(creationTimestamp, downloadLog, globalLog)


def dumpDatabase():
    '''Dump contents of the database for testing.
    '''

    logging.debug('dropBox::dumpDatabase()')

    return databaseLog.dumpDatabase()


def closeDatabase():
    '''Close connection to the database for testing.
    '''

    logging.debug('dropBox::closeDatabase()')

    return databaseLog.close()


def removeOnlineTestFiles():
    '''Removes the online test files from all folders.

    Only meant for testing.

    Called from online.
    '''

    logging.debug('dropBox::removeOnlineTestFiles()')

    for fileHash in os.listdir(config.onlineTestFilesPath):
        try:
            os.unlink(getUploadedFilePath(fileHash))
            logging.info('Removed %s', getUploadedFilePath(fileHash))
        except OSError:
            pass

        try:
            os.unlink(getPendingFilePath(fileHash))
            logging.info('Removed %s', getPendingFilePath(fileHash))
        except OSError:
            pass

        try:
            os.unlink(getAcknowledgedFilePath(fileHash))
            logging.info('Removed %s', getAcknowledgedFilePath(fileHash))
        except OSError:
            pass

        try:
            os.unlink(getBadFilePath(fileHash))
            logging.info('Removed %s', getBadFilePath(fileHash))
        except OSError:
            pass


def copyOnlineTestFiles():
    '''Copies the online test files to the pending folder,
    bypassing the checking of updateFile().

    Only meant for testing.

    Called from online.
    '''

    logging.debug('dropBox::copyOnlineTestFiles()')

    removeOnlineTestFiles()

    for fileHash in os.listdir(config.onlineTestFilesPath):
        logging.info('%s -> %s', os.path.join(config.onlineTestFilesPath, fileHash), getPendingFilePath(fileHash))
        shutil.copyfile(os.path.join(config.onlineTestFilesPath, fileHash), getPendingFilePath(fileHash))

