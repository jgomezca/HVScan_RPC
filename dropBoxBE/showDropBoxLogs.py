#!/usr/bin/env python

import os
import sys
import glob

from pprint import pprint

sys.path.append( '.' )
sys.path.append( 'dropBox/online' )
import modules.config as config

cfg = config.test()

def checkDirs():

    mainDir = cfg.getDropBoxMainDir()

    # get list of subdirs:
    subDirsToCheck = glob.glob(mainDir)

    for entry in subDirsToCheck:
        subDirs = os.listdir( entry )
        for subDir in subDirs:
            items = os.listdir( os.path.join(entry, subDir) )
            print 'checking %20s found %3i items: %s' % (subDir, len(items), ','.join(items))

def checkLogs():

    mainDir = cfg.getDropBoxMainDir( )
    logDir = os.path.join(mainDir, 'logs', 'bkp')

    logFile = logDir + '/Downloader.log.gz'
    print '\n', '=' * 80
    print '-------', logFile
    sys.stdout.flush()
    os.system( 'gunzip -c ' + logFile )
    sys.stdout.flush()

    logFile = logDir + '/TestDropBox.log.gz'
    print '\n', '=' * 80
    print '-------', logFile
    sys.stdout.flush()
    os.system( 'gunzip -c ' + logFile )
    sys.stdout.flush()

    for logFile in glob.glob(logDir+'/*') :
        if os.path.basename( logFile ) in [ 'TestDropBox.log.gz', 'Downloader.log.gz' ] : continue
        print '\n', '='*80
        print '-------', logFile
        sys.stdout.flush()
        os.system('gunzip -c '+logFile)
        sys.stdout.flush()

    return

checkDirs()
checkLogs()

