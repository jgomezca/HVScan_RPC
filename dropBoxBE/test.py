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

import http
import tier0
import service

import config
import Dropbox


frontendHost = socket.gethostname()
frontendBaseUrl = 'https://%s/dropBox/' % frontendHost


class DropBoxBETest(service.TestCase):

    def upload(self, testSubDir):

        # First ask the dropBox to do a clean up to delete previous files
        # and database entries
        (username, account, password) = netrc.netrc().authenticators('newOffDb')
        frontendHttp = http.HTTP()
        frontendHttp.query('%s/signIn' % frontendBaseUrl, {
            'username': username,
            'password': password,
        })
        frontendHttp.query('%s/cleanUp' % frontendBaseUrl)
        frontendHttp.query('%s/signOut' % frontendBaseUrl)

        folder = os.path.join( 'testFiles', testSubDir)

        tests = [ x.partition( '.out' )[ 0 ] for x in glob.glob( os.path.join( folder, '*.out' ) ) ]

        logging.info( 'Uploading %s files from the %s folder...' % (len( tests ), folder ) )

        i = 0
        for test in tests :
            i += 1
            logging.info( '  %s [%s/%s] Testing %s...', folder, i, len( tests ), os.path.basename( test ) )
            # Use upload.py
            process = subprocess.Popen( '../dropBox/upload.py -H %s %s' % (frontendHost, test),
                                        shell=True, stdout=subprocess.PIPE,stderr=subprocess.PIPE )
            result = process.communicate( )
            error = result[ 1 ].rsplit( '\n', 1 )[ -2 ].partition( 'ERROR: ' )[ 2 ]

            if len( error ) > 0 :
                raise Exception('Upload failed: %s (full msg: %s)' % (error, result))

        logging.info('Upload done.')


    def testRun(self):
        tstConfig = config.test()

        # override baseUrl to use private VM
        tstConfig.baseUrl = frontendBaseUrl

        folders = os.listdir( 'testFiles' )
        for folder in folders:
            # upload all files in the folder
            self.upload(folder)

            # and trigger the dropBox backend to process all of them
            self.query('runOne')


def testTier0Call():
    tstConfig = config.test( )

    # getting prompt run from tier0
    t0DataSvc = tier0.Tier0Handler( tstConfig.src, tstConfig.timeout, tstConfig.retries, tstConfig.retryPeriod,
                              tstConfig.proxy, False )
    fcsr = t0DataSvc.getFirstSafeRun( '' )
    print "fcsr = ", fcsr


def main():
    sys.exit(service.test(DropBoxBETest))


if __name__ == "__main__":
    main()

