'''dropBox frontend's web server.

In this file, only the functionality related to the web interface of the
dropBox should be implemented.

The handling of the files themselves is done in dropBox.py.
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = ['Giacomo Govi', 'Salvatore Di Guida', 'Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


import os
import logging
import datetime
import json

import cherrypy
import cherrypy.lib.static

import dropBox
import config
import upload

import service


winServicesUrl = service.getWinServicesSoapBaseUrl(service.secrets['winservices'])


# Cache the upload script
with open('upload.py', 'rb') as f:
    uploadScript = f.read()


# Ensure the sessions folder exist
service.makePath(os.path.join(service.getFilesPath(), 'sessions'))


def getUsername():
    '''Returns the username of the current CherryPy session.
    If it fails, returns None (i.e. the user is not signed in).
    '''

    try:
        return cherrypy.session['username']
    except:
        return None


def handleDropBoxExceptions(f):
    '''Decorator that handles DropBox exceptions, raising a 400 Bad Request
    with the proper error message, instead of an Internal Server Error with
    no message. Use it for the server methods that call any dropBox function.
    '''

    def newf(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except dropBox.DropBoxError as e:
            logging.error('dropBox exception: %s', e)
            # 400 Bad Request
            raise cherrypy.HTTPError(400, str(e))

    newf.exposed = True
    return newf


def checkSignedIn(f):
    '''Decorator that checks if the user is signed in before
    running the decorated function, raising 404 Not Found otherwise with
    cherrypy.NotFound to hide the fact that the method exists.
    '''

    def newf(*args, **kwargs):
        if getUsername() is None:
            # 404 Not Found
            raise cherrypy.NotFound()

        return f(*args, **kwargs)

    newf.exposed = True
    return newf


def checkSignedInOnline(f):
    '''Decorator that checks if the user is signed in and that user is
    the online dropBox before running the decorated function, raising
    404 Not Found otherwise with cherrypy.NotFound to hide the fact
    that the method exists.
    '''

    def newf(*args, **kwargs):
        username = getUsername()
        if username is None or username != service.secrets['onlineUser']['user']:
            # 404 Not Found
            raise cherrypy.NotFound()

        return f(*args, **kwargs)

    newf.exposed = True
    return newf


class DropBox(object):
    '''dropBox frontend's web server.
    '''

    @cherrypy.expose
    def signIn(self, username, password):
        '''Signs in a user.

        Called from both offline and online.
        '''

        logging.debug('server::signIn(%s, [not logged])', username)

        # If the username and password are the ones for the online user, bypass the winServices check
        if username != service.secrets['onlineUser']['user'] or password != service.secrets['onlineUser']['password']:

            if not service.winServicesSoapSignIn(winServicesUrl, username, password):
                # 401 Unauthorized
                raise cherrypy.HTTPError(401, 'Invalid username or password.')

            if not service.winServicesSoapIsUserInGroup(winServicesUrl, username, config.group):
                # 403 Forbidden
                raise cherrypy.HTTPError(403, 'Username not in group %s' % config.group)

        cherrypy.session['username'] = username

        logging.info('signIn(): User %s signed in.', username)


    @cherrypy.expose
    def signOut(self):
        '''Signs out a user.

        Called from both offline and online.
        '''

        logging.debug('server::signOut()')

        username = getUsername()
        if username is not None:
            del cherrypy.session['username']
            logging.info('signOut(): User %s signed out.', username)

        cherrypy.lib.sessions.expire()


    @checkSignedIn
    def getUploadScriptVersion(self):
        '''Returns the version of the upload script (of this server).

        Called from offline.
        '''

        logging.debug('server::getUploadScriptVersion()')

        return service.setResponsePlainText(str(upload.__version__))


    @checkSignedIn
    def getUploadScript(self):
        '''Returns the upload script (of this server).

        Called from offline.
        '''

        logging.debug('server::getUploadScript()')

        return uploadScript


    @checkSignedIn
    @handleDropBoxExceptions
    def uploadFile(self, uploadedFile, backend, fileName):
        '''Uploads a file to the dropbox.

        Called from offline.
        '''

        logging.debug('='*80)

        # Check that the parameter is a file
        if not hasattr(uploadedFile, 'file') or not hasattr(uploadedFile, 'filename'):
            raise dropBox.DropBoxError('The parameter must be an uploaded file.')

        logging.debug('server::uploadFile(%s, %s, %s)', uploadedFile.filename, backend, fileName)

        logging.info('server::uploadFile(): Checking whether the backend is allowed...')
        allowedBackends = config.allowedBackends[service.settings['productionLevel']]
        if backend not in allowedBackends:
            raise dropBox.DropBoxError('The given backend %s is not in the allowed ones for this server: %s.' % (backend, allowedBackends))

        # Take out any paths in the fileName
        fileName = os.path.basename(fileName)

        # Most UNIX filesystems restrict names to 255 bytes, so if we get here
        # someone is trying to do something probably wrong, therefore we just stop
        logging.info('server::uploadFile(): Checking whether the length of the filename does not exceed 255 bytes...')
        if len(fileName) > 255:
            raise dropBox.DropBoxError('The length of the filename exceeds 255 bytes.')

        dropBox.uploadFile(uploadedFile.filename, uploadedFile.file.read(), getUsername(), backend, fileName)


    @checkSignedInOnline
    @handleDropBoxExceptions
    def getFileList(self, backend):
        '''Returns a JSON list of files yet to be pulled from online
        for the matching backend.

        Called from online.

        The name of each file is the SHA1 checksum of the file itself.
        '''

        logging.debug('-'*80)
        logging.debug('server::getFileList(%s)', backend)

        return service.setResponseJSON(dropBox.getFileList(backend))


    @checkSignedInOnline
    @handleDropBoxExceptions
    def getFile(self, fileHash):
        '''Returns a file from the list.

        Called from online.

        It does *not* remove the file from the list, even if the transfer
        appears to be successful. Online must call acknowledgeFile()
        to acknowledge that it got the file successfully.
        '''

        logging.debug('server::getFile(%s)', fileHash)

        return cherrypy.lib.static.serve_fileobj(dropBox.getFile(fileHash), 'application/x-download', 'attachment')


    @checkSignedInOnline
    @handleDropBoxExceptions
    def acknowledgeFile(self, fileHash):
        '''Acknowledges that a file was received in online.

        Called from online, after downloading successfully a file.
        '''

        logging.debug('server::acknowledgeFile(%s)', fileHash)

        dropBox.acknowledgeFile(fileHash)


    @checkSignedInOnline
    @handleDropBoxExceptions
    def updateFileStatus(self, fileHash, statusCode):
        '''Updates the status code of a file.

        Called from online, while processing a file.
        '''

        logging.debug('server::updateStatus(%s, %s)', fileHash, statusCode)

        dropBox.updateFileStatus(fileHash, statusCode)


    @checkSignedInOnline
    @handleDropBoxExceptions
    def updateFileLog(self, fileHash, log, runLogCreationTimestamp, runLogBackend):
        '''Uploads the log of a file and the creationTimestamp of the run
        where the file has been processed.

        Called from online, after processing a file.
        '''

        logging.debug('server::updateFileLog(%s, %s [len], %s, %s)', fileHash, len(log), runLogCreationTimestamp, runLogBackend)

        dropBox.updateFileLog(fileHash, log.decode('base64'), runLogCreationTimestamp, runLogBackend)


    @checkSignedInOnline
    @handleDropBoxExceptions
    def updateRunStatus(self, creationTimestamp, backend, statusCode):
        '''Updates the status code of a run.

        Called from online, while it processes zero or more files.
        '''

        logging.debug('server::updateRunStatus(%s, %s, %s)', creationTimestamp, backend, statusCode)

        dropBox.updateRunStatus(creationTimestamp, backend, statusCode)


    @checkSignedInOnline
    @handleDropBoxExceptions
    def updateRunRuns(self, creationTimestamp, backend, firstConditionSafeRun, hltRun):
        '''Updates the runs (run numbers) of a run (online dropBox run).

        Called from online.
        '''

        logging.debug('server::updateRunRuns(%s, %s, %s, %s)', creationTimestamp, backend, firstConditionSafeRun, hltRun)

        dropBox.updateRunRuns(creationTimestamp, backend, firstConditionSafeRun, hltRun)


    @checkSignedInOnline
    @handleDropBoxExceptions
    def updateRunLog(self, creationTimestamp, backend, downloadLog, globalLog):
        '''Uploads the logs and final statistics of a run.

        Called from online, after processing zero or more files.
        '''

        logging.debug('server::updateRunLog(%s, %s, %s [len], %s [len])', creationTimestamp, backend, len(downloadLog), len(globalLog))

        dropBox.updateRunLog(creationTimestamp, backend, downloadLog.decode('base64'), globalLog.decode('base64'))


    @service.onlyPrivate
    @checkSignedInOnline
    def dumpDatabase(self):
        '''Dump contents of the database for testing.
        '''

        logging.debug('server::dumpDatabase()')

        return service.setResponseJSON(dropBox.dumpDatabase())


    @service.onlyPrivate
    @checkSignedInOnline
    def closeDatabase(self):
        '''Close connection to the database for testing.
        '''

        logging.debug('server::closeDatabase()')

        return dropBox.closeDatabase()


    @service.onlyPrivate
    @checkSignedInOnline
    def cleanUp(self):
        '''Clean up all files and database entries.

        Only meant for testing.
        '''

        logging.debug('server::cleanUp()')

        dropBox.cleanUp()


    @service.onlyPrivate
    @checkSignedInOnline
    def holdFiles(self):
        '''Hold files, i.e. make getFileList() return an empty list.

        Only meant for testing. Useful to ensure a bunch of files are processed
        as a single bunch in the backend.
        '''

        logging.debug('server::holdFiles()')

        dropBox.holdFiles()


    @service.onlyPrivate
    @checkSignedInOnline
    def releaseFiles(self):
        '''Release files, i.e. make getFileList() behave normally.

        Only meant for testing.
        '''

        logging.debug('server::releaseFiles()')

        dropBox.releaseFiles()


def main():
    service.start(DropBox())


if __name__ == '__main__':
    main()

