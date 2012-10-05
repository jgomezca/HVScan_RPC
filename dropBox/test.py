'''Offline new dropBox's test suite.
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = ['Giacomo Govi', 'Salvatore Di Guida', 'Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


import sys
import os
import glob
import netrc
import hashlib
import subprocess
import logging

import service

import config


class DropBoxTest(service.TestCase):

    def signIn(self):
        (username, account, password) = netrc.netrc().authenticators('newOffDb')
        self.query('signIn', {
            'username': username,
            'password': password,
        })


    def signOut(self):
        self.query('signOut', keepCookies = False)


    def testIsServerAnswering(self):
        self.signOut()


    def testGetFileList(self):
        self.signIn()
        self.assertEqual(type(self.queryJson('getFileList')), list)
        self.signOut()


    def testInvalidUsernamePassword(self):
        self.assertRaisesHTTPError(401, 'signIn', {
            'username': 'dropboxtest',
            'password': 'dropboxtest',
        })


    def testNotAFile(self):
        self.signIn()
        self.assertRaisesHTTPError(400, 'uploadFile', {
            'uploadedFile': 'asd',
        })
        self.signOut()


    def testUnauthorized(self):
        self.assertRaisesHTTPError(404, 'uploadFile')
        self.assertRaisesHTTPError(404, 'getFileList')
        self.assertRaisesHTTPError(404, 'getFile')
        self.assertRaisesHTTPError(404, 'acknowledgeFile')
        self.assertRaisesHTTPError(404, 'updateFileStatus')
        self.assertRaisesHTTPError(404, 'updateFileLog')
        self.assertRaisesHTTPError(404, 'updateRunStatus')
        self.assertRaisesHTTPError(404, 'updateRunRuns')
        self.assertRaisesHTTPError(404, 'updateRunLog')


    def testInvalidFileHash(self):
        self.signIn()
        for invalidFileHash in [
            '',
            'asd',
            hashlib.sha1().hexdigest()[:-1],
            hashlib.sha1().hexdigest() + 'a',
            hashlib.sha1().hexdigest().replace('d', 'g'),
            '../../../../../../../etc/passwd',
        ]:
            self.assertRaisesHTTPError(400, 'getFile', {
                'fileHash': invalidFileHash,
            })
            self.assertRaisesHTTPError(400, 'acknowledgeFile', {
                'fileHash': invalidFileHash,
            })
        self.signOut()


    def testFiles(self):
        self.signIn()

        # First clean all files
        for fileName in glob.glob('files/*/*'):
            logging.debug('Unlinking %s...', fileName)
            os.unlink(fileName)

        folders = os.listdir(config.offlineTestFilesPath)

        # FIXME: For the moment, until we correct them
        folders.remove('skip')

        logging.info('Testing files on folders %s...', folders)

        # Then test all of them
        for folder in folders:
            tests = [x.partition('.txt')[0] for x in glob.glob(os.path.join(config.offlineTestFilesPath, folder, '*.txt'))]

            i = 0
            for test in tests:
                i += 1
                logging.info('    %s [%s/%s] Testing file %s...', folder, i, len(tests), os.path.basename(test))

                process = subprocess.Popen('./upload.py %s' % test, shell = True, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
                error = process.communicate()[1].rsplit('\n', 1)[-2].partition('ERROR: ')[2]

                with open('%s.out' % test, 'rb') as f:
                    self.assertEqual(error, f.read().strip())

        
        self.signOut()


def main():
    sys.exit(service.test(DropBoxTest))


if __name__ == "__main__":
    main()

