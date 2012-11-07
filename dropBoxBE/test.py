'''dropBox backend's test suite.
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = ['Giacomo Govi', 'Salvatore Di Guida', 'Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


import sys
import os
import subprocess
import logging
import glob
import socket
import netrc
import time

import http
import templateMatch
import tier0
import service

import config
import Dropbox
import Constants
import dataAccess
import logPack
import doUpload


# FIXME: Fix the testcases after the replay.py works


class DropBoxBETest(service.TestCase):

    def upload(self, folder, loggingPrefix = ''):

        tests = [ x.partition( '.txt' )[ 0 ] for x in glob.glob( os.path.join( 'testFiles', folder, '*.txt' ) ) ]

        logging.info( '%s Uploading %s files...', loggingPrefix, len( tests ) )

        i = 0
        for test in tests :
            i += 1
            logging.info( '%s   [%s/%s] %s: Uploading...', loggingPrefix, i, len( tests ), os.path.basename( test ) )
            doUpload.upload(test, 'private')


    def testRun(self):
        tstConfig = config.test()

        # override baseUrl to use private VM
        tstConfig.baseUrl = doUpload.frontendUrlTemplate % doUpload.frontendHost

        (username, account, password) = netrc.netrc().authenticators('newOffDb')
        frontendHttp = http.HTTP()
        frontendHttp.setBaseUrl(tstConfig.baseUrl)

        folders = os.listdir( 'testFiles' )

        logging.info('Testing %s bunches...', len(folders))

        i = 0
        for folder in folders:
            i += 1

            loggingPrefix = '  [%s/%s] %s:' % (i, len(folders), folder)
            logging.info('%s Testing bunch...', loggingPrefix)

            logging.info( '%s Signing in the frontend...', loggingPrefix)
            frontendHttp.query('signIn', {
                'username': username,
                'password': password,
            })

            # First ask also to hold the files until we have uploaded all
            # the folder to prevent the backend from taking them in-between.
            logging.info( '%s Asking the frontend to hold files...', loggingPrefix)
            frontendHttp.query('holdFiles')

            # Wait until the dropBox has nothing to do
            logging.info( '%s Waiting for backend to be idle...', loggingPrefix)
            while dataAccess.getLatestRunLogStatusCode() != Constants.NOTHING_TO_DO:
                time.sleep(2)

            # When we reach this point, the server will always report an empty
            # list of files, so even if it starts a new run right now, we can
            # safely manipulate the list of files. Therefore, ask the frontend
            # to do a clean up to delete previous files and database entries
            logging.info( '%s Asking the frontend to clean up files and database...', loggingPrefix)
            frontendHttp.query('cleanUp')

            # Upload all the test files in the folder
            logging.info('%s Uploading files...', loggingPrefix)
            self.upload(folder, loggingPrefix = loggingPrefix)

            # And finally release the files so that the backend can take them
            logging.info( '%s Asking the frontend to release files...', loggingPrefix)
            frontendHttp.query('releaseFiles')

            logging.info( '%s Signing out the frontend...', loggingPrefix)
            frontendHttp.query('signOut')

            # The backend will process the files eventually, so wait for
            # a finished status code
            logging.info('%s Waiting for backend to process files...', loggingPrefix)
            while True:
                statusCode = dataAccess.getLatestRunLogStatusCode()

                if statusCode in frozenset([Constants.DONE_WITH_ERRORS, Constants.DONE_ALL_OK]):
                    break

                time.sleep(2)

            # First compare the runLog's statusCode
            logging.info('%s Comparing runLog results...', loggingPrefix)
            with open(os.path.join('testFiles', folder, 'statusCode'), 'rb') as f:
                self.assertEqual(statusCode, getattr(Constants, f.read().strip()))

            # Then compare the runLog's logs
            (creationTimestamp, downloadLog, globalLog) = dataAccess.getLatestRunLogInfo()

            downloadLog = logPack.unpack(downloadLog)
            globalLog = logPack.unpack(globalLog)

            logging.debug('downloadLog = %s', downloadLog)
            logging.debug('globalLog = %s', globalLog)

            with open(os.path.join('testFiles', folder, 'downloadLog'), 'rb') as f:
                templateMatch.match(f.read(), downloadLog)
            
            with open(os.path.join('testFiles', folder, 'globalLog'), 'rb') as f:
                templateMatch.match(f.read(), globalLog)

            tests = [x.partition('.txt')[0] for x in glob.glob(os.path.join('testFiles', folder, '*.txt'))]

            logging.info('%s Comparing %s fileLogs results...', loggingPrefix, len(tests))

            # Then for each file in the test, compare the fileLog's foreign key, statusCode and log
            j = 0
            for test in tests:
                j += 1

                logging.info('%s   [%s/%s] %s: Comparing file...', loggingPrefix, j, len(tests), os.path.basename(test))

                # Get the expected file hash
                with open('%s.fileHash' % test, 'rb') as f:
                    fileHash = f.read().strip()

                (fileStatusCode, fileLog, runLogCreationTimestamp) = dataAccess.getFileLogInfo(fileHash)

                # Compare the foreign key
                self.assertEqual(creationTimestamp, runLogCreationTimestamp)

                # Compare the statusCode
                with open('%s.statusCode' % test, 'rb') as f:
                    self.assertEqual(fileStatusCode, getattr(Constants, f.read().strip()))

                fileLog = logPack.unpack(fileLog)

                # Compare the fileLog
                with open('%s.fileLog' % test, 'rb') as f:
                    templateMatch.match(f.read(), fileLog)


def main():
    sys.exit(service.test(DropBoxBETest))


if __name__ == "__main__":
    main()

