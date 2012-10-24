import os
import logging
import glob
import json

import TeeFile
import TagHandler
from TarDownloader import FileDownloader
import Constants
import StatusUpdater

from conditionDatabase import ConditionDBChecker
from tier0 import Tier0Handler

import database
import service


# main handler for the new Dropbox

class Dropbox(object) :

    def __init__(self, cfg):

        logging.info('Initialising Dropbox')

        self.config = cfg

        self.createDirs( )

        self.metaData = {}
        self.logDir   = os.path.join( self.config.getDropBoxMainDir(), 'logs' )

        self.inDir = os.path.join( self.config.getDropBoxMainDir( ), 'dropbox' )
        self.hashList = []

        self.sortedFileList = []

        self.statUpdater = StatusUpdater.StatusUpdater( self.config )

        

        self.runChk = { }

        # counters:
        self.donwloadProc = 0
        self.downloadOK   = 0

        self.extractProc = 0
        self.extractOK   = 0

        self.processProc = 0
        self.processOK   = 0

        self.runInfoConnection = database.Connection(service.secrets['runInfo'])

        self.replayTimestamp = None

        logging.info('Dropbox initialised')


    def createDirs(self) :

        dirList = [ 'logs', 'logs/bkp',                # general
                    'download', 'input', 'dropbox',    # downloader
                    'exported', 'processError',        # processing
        ]
        for subdir in dirList :
            path = os.path.join( self.config.getDropBoxMainDir( ), subdir )
            if not os.path.exists( path ) : os.makedirs( path )


    def getFileList(self):

        # check all dirs in "dropbox/' and make list of dirs
        startDir = os.getcwd()

        os.chdir( self.inDir )
        self.hashList = glob.glob('*')

        os.chdir(startDir)

        self.logger.debug(' -- found %i items in %s ' % (len(self.hashList), self.inDir))
        for item in self.hashList:
            self.logger.debug(' -- found %s ' % (item, ) )


    def extractMetaData(self) :

        inTagMap = {}
        for itemHash in self.hashList:
            try:
                self.metaData[itemHash] = json.load( open( os.path.join(self.inDir, itemHash, 'metadata.txt') ) )
                inTag   = self.metaData[itemHash]['inputTag']
                inSince = self.metaData[itemHash]['since']
                # access the data source file to extract since and timeType
                srcDB    = 'sqlite_file:'+os.path.join( self.inDir, itemHash, 'data.db')

                iovInfoDb  = ConditionDBChecker( srcDB, '' )
                iov = iovInfoDb.iovSequence( inTag )
                # iov = IOVChecker( srcDB )

                iov.load( inTag )
                self.metaData[itemHash]['timeType'] = iov.timetype()
                if( inSince == None ):
                    inSince = iov.firstSince()
                    self.metaData[itemHash]['since'] = inSince
                if inTag in inTagMap.keys():
                    inTagMap[ inTag ].append( (inSince, itemHash) )
                else:
                    inTagMap[ inTag ] = [ (inSince, itemHash) ]
            except Exception, e:
                self.logger.error("reading metadata failed for %s, got: %s " % (itemHash, str(e),))

        # for files which have the same tag, sort them by firstSince in their metadata
        itemList = []
        for k, v in inTagMap.items():
            if len(v) == 1 :
                (since, itemHash) = v[0]
                itemList.append( itemHash )
            else:
                for (since, itemHash) in sorted(v):
                    itemList.append( itemHash )

        self.sortedFileList = itemList

        self.logger.debug('metadata extracted, sorted file list: ' )
        for item in self.sortedFileList:
            self.logger.debug('  --  %s tag "%s" since "%s"' % (item, self.metaData[item]['inputTag'], self.metaData[item]['since'] ) )
        self.updateRunStatus(Constants.EXTRACT_OK)


    def checkFile(self) :

        # todo : implement checks for file:

        # checkTypeSince ?? no idea what it does:
        #   "compare since values with hlt/promt and delete old ones"

        # checkTagIOVType: ensure that the tag is consistent with the expertTo request
        # ideally via a naming conventino (..._hlt, ..._express, ...)
        # maybe offline/frontend ??

        # if not checkResult:
        #     self.updateRunStatus( Constants.FILECHECK_FAILED )

        return True


    def getLogFileContent(self, logFileName):

        with open(os.path.join(self.logDir, logFileName), 'r') as f:
            return f.read()


    def uploadLogs(self, fileHash, logFileName):

        self.logger.info('uploading logfile %s for %s ' % (logFileName, fileHash) )

        logBlob = 'error getting logfile'
        try:
            logBlob = self.getLogFileContent(logFileName)
        except Exception, e:
            self.logger.error('trying to get content of logfile %s got: %s' % (logFileName, str(e)) )

        ret = self.statUpdater.uploadFileLog(fileHash, logBlob)
        self.logger.info('uploading logs for %s returned %s.' % (fileHash, str(ret)) )


    def updateFileStatus(self, fileHash, status) :
        self.logger.info('updating status for %s to %s ' % (fileHash, status,) )
        self.statUpdater.updateFileStatus( fileHash, status)


    def updateRunStatus(self, status) :
        self.logger.info( 'updating run status to %s ' % (status,) )
        try:
            self.statUpdater.updateRunStatus( status )
        except Exception, e:
            self.logger.debug('Error from update run status : %s' % (str(e),))
            pass


    def unpackLumiId(self, since):

        kLowMask = 0XFFFFFFFF
        run  = since >> 32
        lumi = since & kLowMask

        self.logger.debug( "Unpacking lumiid: run = \"%s\", lumi = \"%s\"" % (run, lumi) )

        return run, lumi


    def repackLumiId(self, run, lumi):

        since = (run << 32) + lumi
        self.logger.debug( 'Repacking lumiid: "%s" from run = "%s", lumi = "%s"' % ( since, run, lumi ) )

        return since

    def getDestSince(self, fileHash, syncTarget) :

        if syncTarget not in [ 'offline', 'hlt', 'express', 'pcl', 'prompt' ] :
            self.logger.error('getDestSince called with illegal sync target %s ' % (syncTarget,))
            return None

        # todo: check what to do for timeType == timestamp

        firstSince = self.metaData[ fileHash ][ 'since' ]

        lumi = None
        # check on timeType in metadata and extract run number for non-run types
        if self.metaData[ fileHash ].has_key('timeType') and self.metaData[ fileHash ][ 'timeType' ] == 'lumiid' :
            firstSince, lumi = self.unpackLumiId( firstSince )

        # "synchronize": if the target is not offline, and the since the user has given is
        # smaller than the next possible one (i.e. the user gave a run earlier than the one
        # which will be started/processed next in prompt, hlt/express) move the since ahead
        # to go to first safe run instead of the value given by the user:
        syncSince = firstSince
        if syncTarget != 'offline' and \
           firstSince < self.runChk[syncTarget] :
                syncSince = self.runChk[syncTarget]
                self.logger.info( 'Synchronizing to "%s" with run=%d' % (syncTarget, syncSince ) ) 

        # check on timeType in metadata and re-pack run number for non-run types
        if self.metaData[ fileHash ].has_key('timeType') and self.metaData[ fileHash ][ 'timeType' ] == 'lumiid' :
            return self.repackLumiId( syncSince, lumi ) # tool will take care of checking if this IOV is valid
        else :
            return syncSince


    def moveToDir(self, fileHash, dirName):

        targetDir = os.path.join( self.config.getDropBoxMainDir( ), dirName )
        if not os.path.exists( targetDir ) : os.makedirs( targetDir )

        inHashDir  = os.path.join( self.inDir, fileHash )
        targetHashDir = os.path.join( targetDir, fileHash )

        os.system('/bin/mv -f '+inHashDir+' '+targetHashDir)  # assume this will always work.


    def processOneFile(self, fileHash) :

        # create a logger with a file for this processing (so we can upload it later)
        fileLoggerName = os.path.join( self.logDir, fileHash+'.log' )
        fileLogger = TeeFile.TeeFile(filename=fileLoggerName, logDir = self.logDir, loggerName='localLogger-'+fileHash)
        fileLogger.info('starting to process %s ' % (fileHash,) )

        self.updateFileStatus(fileHash, Constants.PROCESSING)

        if not self.checkFile( ) :
            self.moveToDir( fileHash, 'processError' )
            fileLogger.error( "checking file failed ... " )
            self.updateFileStatus( fileHash, Constants.FILECHECK_FAILED )
            return False

        # create the handler which will do the export and duplication
        # (and checks the return from the commands

        srcDB    = 'sqlite_file:'+os.path.join( self.inDir, fileHash, 'data.db')
        destDB   = self.metaData[ fileHash ][ 'destinationDatabase' ]
        inputTag = self.metaData[ fileHash ][ 'inputTag' ]
        comment  = self.metaData[ fileHash ][ 'userText' ]
        destTags  = self.metaData[ fileHash ][ 'destinationTags' ]


        tagHandler = TagHandler.TagHandler( srcDB      = srcDB,
                                            destDB     = destDB,
                                            inputTag   = inputTag,
                                            fileLogger = fileLogger )

        errorInExporting = False
        for dTag, tagSpec in destTags.items():
            syncTarget = tagSpec[ 'synchronizeTo' ]
            destSince = self.getDestSince( fileHash, syncTarget )  # check and validate, return correct value
            msg = 'going to export input tag %s to dest tag %s with destSince %s in %s, user comment: "%s"' % (inputTag, dTag, destSince, destDB, comment)

            self.logger.info( msg )
            fileLogger.info ( msg )

            # export will always be done
            ret = tagHandler.export( destTag     = dTag,
                                     destSince   = destSince,
                                     userComment = comment )
            if not ret:
                msg = 'exportation failed for input tag %s to dest tag %s with destSince %s in %s, user comment: "%s"' % (inputTag, dTag, destSince, destDB, comment)
                self.logger.error(msg)
                fileLogger.error(msg)
                self.updateFileStatus( fileHash, Constants.EXPORTING_FAILURE )
                errorInExporting = True

            else : # do the following only if exporting is OK :

                msg = 'exportation to %s done.' % (syncTarget,)
                self.logger.info( msg )
                fileLogger.info( msg )

                # check what to duplicate and take action
                depTags = tagSpec[ 'dependencies' ]
                for depTag, depSynch in depTags.items():
                    depSince = self.getDestSince( fileHash, depSynch )
                    msg = 'going to duplicate input tag %s for %s inputSince %s to dest tag(s) %s with destSince %s in %s, user comment: "%s"' % (dTag, depSynch, destSince, depTag, depSince, destDB, comment)
                    self.logger.info( msg )
                    fileLogger.info ( msg )

                    ret = tagHandler.duplicate( destTag   = depTag,
                                                destSince = depSince )
                    if not ret:
                        msg = 'duplicating failed for input tag %s for %s inputSince %s to dest tag(s) %s with destSince %s in %s, user comment: "%s"' % (dTag, depSynch, destSince, depTag, destSince, destDB, comment)
                        self.logger.error( msg )
                        fileLogger.error( msg )
                        self.updateFileStatus( fileHash, Constants.EXPORTING_OK_BUT_DUPLICATION_FAILURE )
                        errorInExporting = True
                    else :
                        msg = 'duplication to %s done.' % (depTag,)
                        self.logger.info( msg )
                        fileLogger.info( msg )

        if errorInExporting:
            self.moveToDir( fileHash, 'processError')
        else:
            self.moveToDir( fileHash, 'exported' )
                
        # -----------------------------------------------------------------
        # the following needs to be done even if exportation failed:

        # clean up, close log, flag status and upload log back to server
        msg = 'done handling %s ' % (fileHash,)
        self.logger.info( msg )
        fileLogger.info( msg )

        del tagHandler # delete this one before the logger ...
        del fileLogger

        self.uploadLogs( fileHash, fileLoggerName )
        if errorInExporting:
            return False
        return True


    def updateRunInfo(self):

        hltLastRun = None
        fcsr = None
        
        if( self.replayTimestamp == None):
            self.logger.debug('getting hlt run from runInfo ...')
            hltLastRun = self.runInfoConnection.fetch('''
            select *
            from (
                select IOV_TIME
                from CMS_COND_31X_RUN_INFO.IOV_DATA
                where ID = 3
                order by POS desc
            )
            where rownum = 1
            ''')[0][0]
            self.logger.debug('found hlt run from runInfo to be %i ' % (hltLastRun,) )

            self.logger.debug('getting firstConditionSafeRun run from Tier-0 ...')
            t0DataSvc = Tier0Handler( self.config.src,
                                      self.config.timeout, self.config.retries, self.config.retryPeriod,
                                      self.config.proxy, False )
            fcsr = t0DataSvc.getFirstSafeRun()
            self.logger.debug('found firstConditionSafeRun from Tier-0 to be %i ' % (fcsr,) )

        # replay mode 
        #else:    

        self.runChk = {'hlt'     : hltLastRun+1,
                       'express' : hltLastRun+1,
                       'prompt'  : fcsr,
                       'pcl'     : fcsr,
                      }

    def processAllFiles(self) :

        # Recreate the logger to backup the previous file and start fresh a new file
        logFileName = os.path.join( self.logDir, self.config.detector+self.config.label+'.log' )
        self.logger = TeeFile.TeeFile( filename = logFileName, logDir = self.logDir, loggerName = 'DropboxMainLogger' )

        self.logger.info('starting to download files')
        self.updateRunStatus(Constants.STARTING)

        self.updateRunStatus(Constants.DOWNLOADING)
        dwnldr = FileDownloader( cfg=self.config, updater=self.statUpdater )

        # check if we have any files to handle, if not, set status to NOTHING_TO_DO
        # and return (not moving the logs to backup). In case of error, log and stop
        # processing.
        stat, nFiles = dwnldr.getFileList()
        if not stat: # error
            self.updateRunStatus(Constants.DOWNLOADING_FAILURE)
            return True

        # if nothing to do, update status sleep a bit and return, so we can check more
        if nFiles == 0:
            # todo: update timestamp for logging of main dropbox every time the state changes to 0 files
            self.updateRunStatus( Constants.NOTHING_TO_DO )
            return True

        # now update runChk values from firstsaferun and runInfo, send info back to frontend for logging
        self.updateRunInfo()
        self.statUpdater.updateRunRunInfo(self.runChk['prompt'], self.runChk['hlt'])

        dwnldr.downloadAll()
        ( self.donwloadProc, self.downloadOK ) = dwnldr.getSummary()
        del dwnldr

        self.logger.info('starting to extract metadata from files')
        self.updateRunStatus(Constants.EXTRACTING)

        # get metadata for all files first, so we can
        # check and reorder files by "since" if neccessary
        self.getFileList()
        self.extractMetaData() # sorts files with same tags by firstSince in the metadata

        self.extractProc = len(self.hashList)
        self.extractOK   = len(self.sortedFileList)
        # could check here that extractProc == downloadOK :)

        self.logger.info( 'starting to process %i files ' % (len(self.sortedFileList),) )
        errors = False
        self.updateRunStatus(Constants.PROCESSING)
        for item in self.sortedFileList :
            self.processProc += 1
            if self.processOneFile( item ) :
                self.processOK += 1
            else:
                errors = True

        self.logger.info('uploading the logs')
        self.statUpdater.uploadRunLog(
            self.getLogFileContent( 'Downloader.log' ),
            self.getLogFileContent( '%s%s.log' % ( self.config.detector, self.config.label ) )
        )

        if errors:
            self.logger.info('finished, with errors')
            self.updateRunStatus(Constants.DONE_WITH_ERRORS)
        else:
            self.logger.info('finished, all OK')
            self.updateRunStatus(Constants.DONE_ALL_OK)

        return True

    def reprocess( self, timestamp ):
        self.replayTimestamp = timestamp
        return processAllFiles();


def main():

    from config import test

    db = Dropbox( test() )
    db.processAllFiles()
    db.shutdown()

if __name__ == '__main__':
    main()
