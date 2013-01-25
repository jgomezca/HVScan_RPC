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
import logging
import hashlib
import cStringIO
import json

import cx_Oracle

import service

import alarm
import config
import dataAccess
import Constants
import logPack


# Global variables used only for tuning behaviour while testing
_holdFiles = False
_runTimestamp = None


# Declared before import check, so that check.py can access it
class DropBoxError(Exception):
    def __init__(self, message):
        self.args = (message, )


import check


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

    if dataAccess.getFileState(fileHash) != 'Pending':
        raise DropBoxError('The pending file %s does not exist.' % fileHash)


def failUpload(fileHash):
    '''Fails an upload moving it to the bad folder.
    '''

    logging.info('uploadFile(): %s: Updating state of the file to Bad...', fileHash)
    dataAccess.updateFileState(fileHash, 'Bad')

    logging.info('uploadFile(): %s: The upload failed.', fileHash)


def loadJson(data):
    '''Loads an object from its JSON representation of the data unless
    it is None (i.e. a NULL in the database).
    '''

    if data is None:
        return None

    return json.loads(data)


def dumpJson(data, maxSize = 4000):
    '''Returns the JSON representation of the data if it fits in the maxSize
    in bytes. If not, it returns None (i.e. a NULL in the database).
    '''

    data = json.dumps(data)

    if len(data) > maxSize:
        return None

    return data


def uploadFile(fileHash, fileContent, username, backend, fileName):
    '''Uploads a file to the dropbox for online.
    '''

    logging.debug('dropBox::uploadFile(%s, %s [len], %s, %s, %s)', fileHash, len(fileContent), username, backend, fileName)

    logging.info('uploadFile(): Checking whether the hash is valid...')
    checkHash(fileHash)

    logging.info('uploadFile(): %s: Checking the file content hash...', fileHash)
    fileContentHash = getHash(fileContent)
    if fileHash != fileContentHash:
        raise DropBoxError('The given file hash %s does not match with the file content hash %s.' % (fileHash, fileContentHash))

    logging.info('uploadFile(): %s: Checking whether the file already exists...', fileHash)
    state = dataAccess.getFileState(fileHash)

    if state == 'Uploaded':
        raise DropBoxError('The uploaded file with hash %s already exists in the Uploaded files (i.e. not yet processed). This probably means that you sent the same request twice in a short time.' % fileHash)

    if state == 'Pending':
        raise DropBoxError('The uploaded file with hash %s already exists in the Pending files (i.e. files that are waiting to be pulled by online that were already checked). This probably means that you sent the same request twice in a short time.' % fileHash)

    if state == 'Acknowledged':
        raise DropBoxError('The uploaded file with hash %s already exists in the Acknowledged files (i.e. files that were already pulled by online not too long ago -- we do not keep all of them forever). This probably means that you sent the same request twice after some time.' % fileHash)

    if state == 'Bad':
        raise DropBoxError('The uploaded file with hash %s already exists in the Bad files (i.e. files that were wrong for some reason). Therefore this file will be skipped since the results of the checks should be the same again (i.e. wrong).' % fileHash)

    logging.info('uploadFile(): %s: Saving the uploaded file in the database...', fileHash)
    dataAccess.insertFile(fileHash, 'Uploaded', backend, username, fileName, fileContent)

    logging.info('uploadFile(): %s: Checking the contents of the file...', fileHash)
    try:
        metadata = check.checkFile(fileHash, fileContent, backend)
    except DropBoxError as e:
        failUpload(fileHash)
        raise e
    except Exception as e:
        # Other kind of exception: this is a bug :(
        alarm.alarm('Non-DropBoxError exception raised in check.py: %s' % e)
        failUpload(fileHash)
        raise DropBoxError('Oops, something went wrong while checking your file. This is most likely a bug in the DropBox. %s' % config.notifiedErrorMessage)

    # Divide the metadata in the userText and the real metadata
    userText = metadata['userText']
    metadata['userText'] = ''

    logging.info('uploadFile(): %s: Inserting entry in the fileLog...', fileHash)
    try:
        dataAccess.insertFileLog(fileHash, Constants.WAITING_FOR_START, dumpJson(metadata), dumpJson(userText))
    except cx_Oracle.IntegrityError:
        failUpload(fileHash)
        raise DropBoxError('The uploaded file %s was already requested in the database.' % fileHash)

    logging.info('uploadFile(): %s: Updating state of the file to Pending...', fileHash)
    dataAccess.updateFileState(fileHash, 'Pending')

    logging.info('uploadFile(): %s: The upload was successful.', fileHash)


def getFileList(backend):
    '''Returns a list of files yet to be pulled from online
    for the matching backend.

    The name of each file is the SHA1 checksum of the file itself.

    Called from online, but also public to allow people to see the list.
    '''

    logging.debug('dropBox::getFileList(%s)', backend)

    logging.info('getFileList(): Getting the list of files for %s...', backend)

    if _holdFiles:
        logging.debug('getFileList(): Holding files, i.e. returning empty list...')
        return []

    fileList = dataAccess.getPendingFiles(backend)

    logging.debug('getFileList(): Found %i files: %s' % (len(fileList), ','.join(fileList)))

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

    logging.info('getFile(): %s: Downloading file from database...', fileHash)
    fileObject = cStringIO.StringIO()
    fileObject.write(dataAccess.getFileContent(fileHash))
    fileObject.seek(0)

    logging.info('getFile(): %s: Serving file...', fileHash)
    return fileObject


def acknowledgeFile(fileHash):
    '''Acknowledges that a file was received in online.

    Called from online.
    '''

    logging.debug('dropBox::acknowledgeFile(%s)', fileHash)

    logging.info('acknowledgeFile(): Checking whether the hash is valid...')
    checkHash(fileHash)

    logging.info('acknowledgeFile(): %s: Checking whether the pending file exists...', fileHash)
    checkPendingFile(fileHash)

    logging.info('acknowledgeFile(): %s: Updating state of the file to Acknowledged...', fileHash)
    dataAccess.updateFileState(fileHash, 'Acknowledged')


def updateFileStatus(fileHash, statusCode):
    '''Updates the status code of a file.

    Called from online.
    '''

    logging.debug('dropBox::updateFileStatus(%s, %s)', fileHash, statusCode)

    dataAccess.updateFileLogStatus(fileHash, statusCode)


def updateFileLog(fileHash, log, runLogCreationTimestamp, runLogBackend):
    '''Uploads the log of a file and the creationTimestamp of the run
    where the file has been processed.

    Called from online, after processing a file.
    '''

    logging.debug('dropBox::updateFileLog(%s, %s [len], %s, %s)', fileHash, len(log), runLogCreationTimestamp, runLogBackend)

    dataAccess.updateFileLogLog(fileHash, log, runLogCreationTimestamp, runLogBackend)

    # Send email to user
    (fileName, statusCode, uploadTimestamp, finishTimestamp, username, userText, metadata) = dataAccess.getFileInformation(fileHash)

    userText = loadJson(userText)
    if userText is None:
        userText = '(userText too big to be displayed)'

    metadata = loadJson(metadata)
    if metadata is None:
        metadata = '(metadata too big to be displayed)'
    else:
        metadata = service.getPrettifiedJSON(metadata)

    fileInformation = {
        'fileName': fileName,
        'fileHash': fileHash,
        'statusCode': statusCode,
        'statusString': Constants.inverseMapping[statusCode],
        'uploadTimestamp': uploadTimestamp,
        'finishTimestamp': finishTimestamp,
        'username': username,
        'userText': userText,
        'metadata': metadata,
        'log': logPack.unpack(log),
    }

    toAddresses = [username]
    if service.settings['productionLevel'] in set(['int', 'pro']):
        toAddresses.append(config.notificationsEgroup)

    dataAccess.insertEmail(config.subjectTemplate.render(fileInformation), config.bodyTemplate.render(fileInformation), username, toAddresses)

    # If it failed for any reason, send an SMS to the shifter phone via email
    if service.settings['productionLevel'] in set(['int', 'pro']) and int(statusCode) != Constants.PROCESSING_OK:
        dataAccess.insertEmail(config.smsTemplate.render(fileInformation), '.', username, [config.shifterPhoneSMSAddress])


def updateRunStatus(creationTimestamp, backend, statusCode):
    '''Updates the status code of a run.

    Called from online, while it processes zero or more files.
    '''

    logging.debug('dropBox::updateRunStatus(%s, %s, %s)', creationTimestamp, backend, statusCode)

    dataAccess.insertOrUpdateRunLog(creationTimestamp, backend, statusCode)


def updateRunRuns(creationTimestamp, backend, firstConditionSafeRun, hltRun):
    '''Updates the runs (run numbers) of a run (online dropBox run).

    Called from online.
    '''

    logging.debug('dropBox::updateRunRuns(%s, %s, %s, %s)', creationTimestamp, backend, firstConditionSafeRun, hltRun)

    dataAccess.updateRunLogRuns(creationTimestamp, backend, firstConditionSafeRun, hltRun)


def updateRunLog(creationTimestamp, backend, downloadLog, globalLog):
    '''Uploads the logs and final statistics of a run.

    Called from online, after processing zero or more files.
    '''

    logging.debug('dropBox::updateRunLog(%s, %s, %s [len], %s [len])', creationTimestamp, backend, len(downloadLog), len(globalLog))

    dataAccess.updateRunLogInfo(creationTimestamp, backend, downloadLog, globalLog)


def dumpDatabase():
    '''Dump contents of the database for testing.
    '''

    logging.debug('dropBox::dumpDatabase()')

    return dataAccess.dumpDatabase()


def closeDatabase():
    '''Close connection to the database for testing.
    '''

    logging.debug('dropBox::closeDatabase()')

    return dataAccess.close()


def cleanUp():
    '''Clean up all files and database entries.

    Only meant for testing.
    '''

    logging.debug('dropBox::cleanUp()')

    dataAccess.cleanUp()


def holdFiles():
    '''Hold files, i.e. make getFileList() return an empty list.

    Only meant for testing. Useful to ensure a bunch of files are processed
    as a single bunch in the backend.
    '''

    logging.debug('dropBox::holdFiles()')

    global _holdFiles
    _holdFiles = True


def releaseFiles():
    '''Release files, i.e. make getFileList() behave normally.

    Only meant for testing.
    '''

    logging.debug('dropBox::releaseFiles()')

    global _holdFiles
    _holdFiles = False


