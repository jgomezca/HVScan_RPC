import subprocess


class TagHandler( object ):
    def __init__(self, srcDB, destDB, inputTag, fileLogger ):
        self.srcDB = srcDB
        self.inputTag = inputTag
        #self.exportDB = destDB
        # fix me: testing phase!!!
        self.exportDB = destDB
        
        self.exportDB = "oracle://cms_orcoff_prep/CMS_COND_DROPBOX"
        self.exportTag = None
        self.exportSince = None
        self.fileLogger = fileLogger
        self.logDB = "sqlite_file:log.db"
        # fix me : will be removed (no needed with key authentication
        self.authpath = '/afs/cern.ch/cms/DB/conddb/test/dropbox'
        return

    def executeAndLog(self, command, verbose=False):
        # processing
        if( verbose ):
           self.fileLogger.debug("Executing command :\""+command+"\"")
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (stdoutdata, stderrdata) =  process.communicate()
        retcode = process.returncode

        if ( retcode != 0 and stderrdata != None) : # we got an error, report it
            if(stdoutdata != None ):
               self.fileLogger.error(stdoutdata)
            # is it required ?
            if(stderrdata != None ):
               self.fileLogger.error(stderrdata) # if there is error-output, we need to log as error ...
            return False

        else: # no error ... so far ... :(
            if(stdoutdata != None ):
                # todo: parse stdout and see if it contains other errors
                if 'An exception of category' in stdoutdata :
                    self.fileLogger.error(stdoutdata)
                    return False
                else: # no error here, log and return success
                    self.fileLogger.debug(stdoutdata)
                    return True

            # no stdout received ... todo: decide whether this is an error (log and return false if so)
            return True

        # we'll never come here

    def export(self, destTag, destSince, userComment ):
        self.exportTag = destTag
        self.exportSince = str(destSince)
        command = "cmscond_export_iov" + \
                  " -s " + self.srcDB + \
                  " -i " + self.inputTag + \
                  " -d " + self.exportDB + \
                  " -t " + self.exportTag + \
                  " -b " + self.exportSince + \
                  " -l " + self.logDB +\
                  " -x '"+ str(userComment) + "'" +\
                  " -P " + self.authpath

        return self.executeAndLog( command, True )

    def duplicate(self, destTag, destSince):
        duplicateSince = str(destSince)
        if( self.exportTag == None ):
           self.fileLogger.error('Tag Export has not been done.')
           return False
        command = "cmscond_duplicate_iov" + \
                    " -c " + self.exportDB + \
                    " -t " + self.exportTag + \
                    " -f " + self.exportSince + \
                    " -d " + destTag + \
                    " -s " + duplicateSince + \
                    " -l " + self.logDB +\
                    " -P " + self.authpath

        return self.executeAndLog( command, True )

import TeeFile
import sys
import getopt

def test( argv ) :
    try:
        opts, args = getopt.getopt(argv, "i:t:s:", ["inputDB", "tag","since"])
    except getopt.GetoptError:
        print 'TEST ERROR: option parsing failed'
        return
    inputDB = None
    tag = None
    since = None
    for opt, arg in opts:
        if opt in ("-i", "--inputDB"):
           inputDB = arg
        if opt in ("-t","--tag"):
           tag = arg
        if opt in ("-s","--since"):
           since = arg
    if( inputDB == None ):
        print 'TEST ERROR: option \'inputDB\' not provided.'
        return
    if( tag == None ):
        print 'TEST ERROR: option \'tag\' not provided.'
        return
    if( since == None ):
        print 'TEST ERROR: option \'since\' not provided.'
        return
    logger = TeeFile.TeeFile('testTagHandler.log','TestTagHandler')
    destDB = 'sqlite_file:TestTagHandlerDest.db'
    destTag = 'TestTagHandlerDestTag'
    destSinceExp = 9999
    destSinceDup = 1000000
    comment = 'Test TagHandler export'
    th = TagHandler( inputDB, destDB, tag, logger )
    th.exportDB = destDB
    th.export( destTag, destSinceExp, comment )
    tglist = ['duplicate0','duplicate1','duplicate2']
    th.duplicate( tglist, destSinceDup )
    return

if __name__ == '__main__' :
   test(sys.argv[1:])
