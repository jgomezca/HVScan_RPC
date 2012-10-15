
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
import subprocess
import logging
import glob

baseDir = os.path.dirname( __file__ )
print '==> :', baseDir
print '==> :', os.getcwd()
sys.path.append( os.path.join( os.path.dirname( __file__ ), '..', 'modules' ) )
sys.path.append( os.path.join( '/data', 'secrets' ) )
sys.path.append( os.path.join( '/data', 'services', 'common' ) )

from tier0 import Tier0Handler

import config
import Dropbox

class DropBoxBETest():

    def __init__(self):

        self.feHost = 'apvm5be.cern.ch'

    def upload(self, testSubDir):

        folder = os.path.join( baseDir, '..', 'testFiles', testSubDir)

        tests = [ x.partition( '.out' )[ 0 ] for x in glob.glob( os.path.join( folder, '*.out' ) ) ]

        logging.info( 'Uploading %s files from the %s folder...' % (len( tests ), folder ) )

        i = 0
        for test in tests :
            i += 1
            logging.debug( '  %s [%s/%s] Testing %s...', folder, i, len( tests ), os.path.basename( test ) )
            # Use upload.py
            process = subprocess.Popen( os.getcwd()+'/dropBox/upload.py -H %s %s' % (self.feHost, test),
                                        shell=True, stdout=subprocess.PIPE,stderr=subprocess.PIPE )
            result = process.communicate( )
            error = result[ 1 ].rsplit( '\n', 1 )[ -2 ].partition( 'ERROR: ' )[ 2 ]

            if len( error ) > 0 :
                logging.error('upload file %s failed: %s (full msg: %s)' % (test, error, result))
            logging.debug( 'upload for file %s returned %s' % (test, '\n'.join( result ) ) )

        logging.info('upload done ... ')

    def testRun(self):
        from config import test

        tstConfig = test()

        # override baseUrl to use private VM
        tstConfig.baseUrl = 'https://%s/dropBox/' % (self.feHost,)

        # upload files from testFiles dir
        folders = os.listdir( os.path.join( os.getcwd(), 'dropBox', 'online', 'testFiles' ) )
        folders.remove('bad')
        for subDir in folders:
            self.upload( subDir )

            # and process them
            db = Dropbox.Dropbox( tstConfig )
            db.processAllFiles( )
            db.shutdown( )


def testTier0Call():

    from config import test

    tstConfig = test( )

    # getting prompt run from tier0
    t0DataSvc = Tier0Handler( tstConfig.src, tstConfig.timeout, tstConfig.retries, tstConfig.retryPeriod,
                              tstConfig.proxy, False )
    fcsr = t0DataSvc.getFirstSafeRun( '' )
    print "fcsr = ", fcsr


def main():

    logging.basicConfig(
        format='[%(asctime)s] %(levelname)s: %(message)s',
        level=logging.DEBUG,
    )

    # testTier0Call()

    dbbetst = DropBoxBETest()
    sys.exit( dbbetst.testRun() )

if __name__ == "__main__":
    main()

