import glob
import os
import tarfile
import hashlib
import shutil
import netrc
import subprocess

import Constants
import TeeFile
import config as config
from   PyCurler import Curler


class FileDownloader( object ) :
    def __init__(self, cfg, updater = None):

        self.baseDir = cfg.getDropBoxMainDir()                   # '/nfshome0/popconpro/OfflineDropboxJob'):
        if cfg : self.baseDir = cfg.getDropBoxMainDir( )

        self.baseUrl = cfg.baseUrl

        self.logger = TeeFile.TeeFile( os.path.join(self.baseDir, 'logs', 'Downloader.log'), 'downloader')
        self.logger.info('Downloader starting ... ')
        self.logger.info( "baseDir = %s " % (self.baseDir, ) )

        self.statUpdater = updater

        self.baseDownloadDir  = os.path.join( self.baseDir, 'download')
        if not os.path.exists(self.baseDownloadDir) : os.makedirs(self.baseDownloadDir)

        self.baseDownloadErrDir = os.path.join( self.baseDir, 'downloadError' )
        if not os.path.exists( self.baseDownloadErrDir ) : os.makedirs( self.baseDownloadErrDir )

        self.baseInDir = os.path.join( self.baseDir, 'input' )
        if not os.path.exists( self.baseInDir ) : os.makedirs( self.baseInDir )

        self.baseProcDir = os.path.join( self.baseDir, 'dropbox' )
        if not os.path.exists( self.baseProcDir ) : os.makedirs( self.baseProcDir )

        self.curl = Curler()

        self.fileList = []

        self.filesProc = 0
        self.filesOK   = 0

    def getFileList(self) :

        try :
            self.login( )
        except Exception, e :
            self.logger.error( "when logging in: %s" % (str( e ), ) )
            return False, 0

        try :
            self.fileList = self.downloadFileList( )
            self.logger.info( "Found %d files" % (len( self.fileList ),) )
            # for item in self.fileList: self.logger.info( " ... %s " % (item, ) )
        except Exception, e :
            self.logger.error( "trying to get file list e= %s" % (str( e ), ) )
            return False, 0

        return True, len( self.fileList )

    def downloadAll(self):

        for fileHash in self.fileList :

            self.filesProc += 1 # increment counter for processed files here

            self.statUpdater.updateFileStatus( fileHash, Constants.DOWNLOADING )
            self.logger.info( "going to download %s " % (fileHash,) )
            OK = True
            if not self.downloadFile( fileHash ) :
                OK = False
                continue
            if OK and not self.untarFile( fileHash ):
                OK = False
                continue
            #-ap if OK and not self.acknowledgeFile( filename ):
            #    OK = False
            #    continue

            if OK :
                self.filesOK += 1 # increment counter for files which are OK
                self.statUpdater.updateFileStatus( fileHash, Constants.DOWNLOADING_OK )

        self.logout()

        self.moveValidFilesToProcess()

        self.logger.info('all files downloaded.')

        return True

    def getSummary(self):
        return self.filesProc, self.filesOK

    def doCmd(self, command):

        process = subprocess.Popen( command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT )
        (stdoutdata, stderrdata) = process.communicate( )
        retcode = process.returncode

        if(retcode == 0) :
            # logging
            if(stdoutdata != None ) :
                self.logger.debug( stdoutdata )
            return True

        # If we get here, we have stderr and/or a returncode != 0, so we should log both as error
        if(stdoutdata != None ):
           self.logger.error(stdoutdata)
        if(stderrdata != None ):
           self.logger.error(stderrdata) # if there is error-output, we need to log as error ...

        return False

    def login(self) :
        nrc = netrc.netrc( )
        (login, account, password) = nrc.authenticators( 'newOffDb' )

        url = self.baseUrl + '/signIn'
        response = self.curl.get( url, [ ('username', login), ('password', password) ] )

        msg = '\n'.join( response ).strip()
        if msg:
            self.logger.debug( ' -- login returned: %s ' % (msg,) )
        else:
            self.logger.debug( ' -- login OK ' )

        return

    def logout(self) :

        url = self.baseUrl + '/signOut'
        response = self.curl.get( url )

        msg = '\n'.join( response ).strip()
        if msg:
            self.logger.debug( ' -- logout returned: %s ' % (msg,) )
        else:
            self.logger.debug( ' -- logout OK ' )

        return

    def downloadFileList(self) :

        fileListUrl = self.baseUrl + 'getFileList'
        self.logger.info( "Retrieving file list from: " + fileListUrl )
        try :
            jsonlist = self.curl.get( fileListUrl )
            return jsonlist
        except Exception, e:
            self.logger.error("could not read file list, got: %s " % (str(e), ) )
            return [ ]


    def acknowledgeFile(self, filename) :
        fileUrl = self.baseUrl + 'acknowledgeFile'
        try :
            self.logger.info( "Going to acknowledge file %s via url: %s " % (filename, fileUrl) )
            webFile = self.curl.get( fileUrl, [ ('fileHash', str( filename )) ] )
        except Exception, e :
            self.logger.error( "Error when acknowledging file %s : %s" % (filename, str( e )) )

        return

    def downloadFile(self, fileHash) :

        fileUrl = self.baseUrl + 'getFile'
        filepath = os.path.join( self.baseDownloadDir, fileHash )

        # Download ...
        try :
            self.logger.info( "Downloading file %s from url: %s to %s" % (fileHash, fileUrl, filepath) )

            webFile = self.curl.get( fileUrl, [ ('fileHash', str(fileHash)) ] )
            self.logger.info( " - size : %i " % (len(''.join(webFile)),) )
        except Exception, e :
            self.statUpdater.updateFileStatus(fileHash, Constants.DOWNLOADING_FAILURE)
            self.logger.error( "when downloading file %s : %s" % (fileHash, str(e)) )
            return False

        # ... and store to file
        try:
            localFile = open( filepath, 'w' )
            localFile.write( ''.join(webFile) )
            localFile.close( )
        except Exception, e :
            self.statUpdater.updateFileStatus(fileHash, Constants.DOWNLOADING_FAILURE)
            self.logger.error( "when storing downloaded file to %s : %s" % (filepath, str(e)) )
            return False

        newChkSum = self.sha1sum(filepath)
        if newChkSum != fileHash.split('.')[0] :

            # todo: retry once more ??

            self.statUpdater.updateFileStatus(fileHash, Constants.CHECKSUM_FAILURE)
            self.logger.error("checksum for tarball not correct: found %s expected %s" % (newChkSum, fileHash.split('.')[0]) )
            # move bad file/dir into downloadError/ dir,
            # ensure there is nothing there before moving.
            self.doCmd('rm -rf %s ; mv %s %s' % (os.path.join(self.baseDownloadErrDir, filepath), filepath, self.baseDownloadErrDir ) )
            return False

        self.logger.debug(' -- file %s downloaded.' % (fileHash,))

        return True

    def sha1sum(self, fileName):

        fileHash = hashlib.sha1()
        with open( fileName, 'rb' ) as f :
            while True :
                data = f.read( 4 * 1024 * 1024 )
                if not data : break
                fileHash.update( data )

        return fileHash.hexdigest()

    def checkTarMembers(self, members):

        allowedItems = [ 'data.db', 'metadata.txt' ]
        for item in members:
            if item not in allowedItems:
                self.logger.error("found illegal member (%s) in tarfile ! " %(item,))
                raise SystemError


    def untarFile(self, fileHash) :

        filepath = os.path.join( self.baseDownloadDir, fileHash )

        try :
            tar = tarfile.open( filepath )
        except Exception as e :
            self.statUpdater.updateFileStatus( fileHash, Constants.UNTARING_FAILURE )
            self.logger.error( "when opening tar file %s/%s: %s " % ( self.baseDownloadDir, fileHash, str(e) ) )
            return False

        destDir  = os.path.join( self.baseInDir, fileHash )
        if not os.path.exists(destDir) : os.makedirs(destDir)
        try:
            self.checkTarMembers( tar.getnames() )
        except:
            # move bad file/dir into downloadError/ dir
            os.rename( filepath, self.baseDownloadErrDir )
            self.statUpdater.updateFileStatus( fileHash, Constants.UNTARING_ILLCONT )
            raise
        try:
            tar.extractall( path=destDir )
            tar.close( )
        except Exception as e :
            self.statUpdater.updateFileStatus( fileHash, Constants.UNTARING_FAILURE )
            self.logger.error( "when un-taring file %s/%s to %s: %s - skipping " % ( self.baseDownloadDir, fileHash, destDir, str(e) ) )
            # move input file away to the downloadError dir
            # ensure there is nothing there before moving.
            self.doCmd('rm -rf %s ; mv %s %s' %
                       ( os.path.join(self.baseDownloadErrDir, fileHash), filepath, self.baseDownloadErrDir ) )
            return False

        # remove input tarfile
        os.remove( os.path.join( self.baseDownloadDir, fileHash ) )

        self.logger.debug(' -- file %s untarred.' % (fileHash,))

    def moveValidFilesToProcess(self) :

        destDir = self.baseProcDir

        list = glob.glob( os.path.join( self.baseInDir, '*' ) )
        for filename in list :
            try:
                shutil.move( filename, destDir )
            except shutil.Error, e:
                if "Destination path" in str(e) and 'already exists' in str(e):
                    # ignore already moved files
                    # todo: do we need a warning for this ? should normally not really happen ....
                    pass
                else:
                    self.logger.error('moving file %s to %s failed: %s' % (filename, destDir, str(e)) )

        self.logger.debug(' -- %i files moved to processing dir' % (len(list),))

def main():
    print "* File downloading starts"
    cfg=config.test()
    d = FileDownloader( cfg )
    stat, nFiles = d.getFileList()
    if not stat:
        return -1
    if nFiles > 0:
        d.downloadAll()

def test():
    print "* File test starts"
    cfg=config.test()
    d = FileDownloader( cfg )
    stat, nFiles = d.getFileList()
    if not stat:
        return -1
    if nFiles > 0:
        d.downloadAll()

if __name__ == "__main__" :
    # main()
    test()
