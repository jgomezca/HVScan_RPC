import os
import subprocess
import logging

class TeeFile( object ) :
    """
        Initiate file
    """

    def __init__(self, filename, loggerName="DropBoxLogger", noName=False) :

        # create a logger
        self.logger = logging.getLogger( loggerName )
        self.logger.removeHandler(None)
        self.logger.setLevel( logging.DEBUG )

        # ... and a formatter
        if noName:
            formatter = logging.Formatter( '[%(asctime)s]  localFileLogger  %(levelname)s: %(message)s' )
        else:
            formatter = logging.Formatter( '[%(asctime)s] %(name)s %(levelname)s: %(message)s' )

        # todo: move the loggers to create a rotating file handler and keep the last two hours of runs (12 files each)

        # create logger 
        fileLogger = logging.FileHandler(filename)

        fileLogger.setLevel( level=logging.DEBUG )
        fileLogger.setFormatter( formatter )

        # create console handler with the same log level
        consLogger = logging.StreamHandler( )
        consLogger.setLevel( logging.DEBUG )
        consLogger.setFormatter( formatter )

        # add the handlers to the logger
        self.logger.addHandler( consLogger )
        self.logger.addHandler( fileLogger )

        self.map = {'debug' : self.logger.debug,
                    'info' : self.logger.info,
                    'warning' : self.logger.warning,
                    'error' : self.logger.error,
        }

        self.debug( '-' * 80 ) # empty line to separate restarts

    def __del__(self):
        del self.logger

    def toBoth(self, msgIn) :
        """
        Keep this method for compatibility with calling in various places.
        The method determines the level from the first part of the message.
        """

        if 'An exception of category' in msgIn: # treat these as errors !
            for msg in msgIn.split('\n'):
                if not msg.strip() : continue
                self.error(msg.replace('DEBUG: ', ''))
            return

        for msg in msgIn.split( "\n" ) :
            level, sep, msgOut = msg.partition( ':' )
            if level.lower() not in self.map:
                self.info(msgIn)
                return
            if not msgOut :
                msgOut = msg
                level = 'debug'
            self.log( msgOut, level )


    def log(self, msg, level='debug') :
        self.map[ level.lower( ) ]( msg.strip() )

    def debug(self, msg) :
        self.logger.debug( msg.strip() )

    def info(self, msg) :
        self.logger.info( msg.strip() )

    def warning(self, msg) :
        self.logger.warning( msg.strip() )

    def error(self, msg) :
        self.logger.error( msg.strip() )

    def doSystem(self, cmd) :
        p = subprocess.Popen( cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            close_fds=True )
        (child_stdin, child_stdout_and_stderr) = (p.stdin, p.stdout)

        if(p) :
            self.debug( child_stdout_and_stderr.read( ).strip( ) )

        p.stdin.close( )
        rc = p.wait( )
        if (rc) != 0 :
            self.log( "command returned with error: %i" % (rc,), "error" )
            return 1 # error occured
        else :
            return 0 # no errors


def test() :
    tf = TeeFile( 'test.log' )
    tf.toBoth( "test to both - no keyword in msg (should be debug) ... " )
    tf.toBoth( 'INFO: only to std' )
    tf.toBoth( 'INFO: only to std - and here with an additional : colon ;) ' )
    tf.toBoth( 'WARNING: only to file' )
    tf.doSystem( "date" )
    tf.doSystem( "this-command-does-not-exist" )

    tf.toBoth(
        """DEBUG: We will start from main directory \"""" + 'self.maindir' + """\" for task \"""" + 'self.detector' + """\" using label \"""" + 'self.label' + """\"
DEBUG: So, we will inspect the directory \"""" + 'self.baseFolder' + """\" on the absolute path \"""" + 'self.folder' + """\" waiting for \"""" + 'str(self.delay)' + """\" seconds if new files are found
DEBUG: Release version: \"""" + 'str(os.environ.get("CMSSW_VERSION"))' + """\"
DEBUG: Authentication path: \"""" + 'self.authpath' + """\"
DEBUG: Run Info DB: \"""" + 'self.dbName' + """\"
DEBUG: Run Info Start Tag: \"""" + 'self.tag' + """\"
DEBUG: Tier0 DAS URL: \"""" + 'self.src' + """\"
DEBUG: HTTP Proxy: \"""" + 'str(self.proxy)' + """\"
DEBUG: HTTP Request timeout: \"""" + 'str(self.timeout)' + """\"
DEBUG: GlobalTag DB: \"""" + 'self.gtDbName' + """\"
DEBUG: Production GT for HLT: \"""" + 'self.gtTags.get("hlt")' + """\"
DEBUG: Production GT for express: \"""" + 'self.gtTags.get("express")' + """\"
DEBUG: Production GT for prompt: \"""" + 'self.gtTags.get("prompt")' + """ \" """ )


    tf.toBoth("""DEBUG: An exception of category 'Conditions' occurred.
Exception Message:
IOVImportIterator::setUp Error: since time out of range, below last since
    """)

if __name__ == '__main__' :
    test( )