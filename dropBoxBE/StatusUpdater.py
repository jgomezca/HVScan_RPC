import logging
import netrc
import datetime
import PyCurler
import logPack

class StatusUpdater( object ) :
    def __init__(self, cfg):
        self.config = cfg
        self.baseUrl = self.config.baseUrl

        self.creationTimeStamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # works: '2012-02-20 22:53:48,140'

        self.curler = PyCurler.Curler()
        # self.curler.setVerbose(True)

        self.login()

    def __del__(self):
        self.logout()

    def login(self) :
        nrc = netrc.netrc( )
        (login, account, password) = nrc.authenticators( 'newOffDb' )

        url = self.baseUrl + '/signIn'
        response = self.curler.get( url, [ ('username', login), ('password', password) ] )

        msg = '\n'.join( response ).strip( )
        if msg :
            logging.info( ' -- login returned: %s ' % (msg,) )
        else :
            logging.info( ' -- login OK ' )


    def logout(self) :
        url = self.baseUrl + '/signOut'
        response = self.curler.get( url )

        msg = '\n'.join( response ).strip( )
        if msg :
            logging.info( ' -- logout returned: %s ' % (msg,) )
        else :
            logging.info( ' -- logout OK ' )


    def updateFileStatus(self, hash, status) :
        '''
        Update the status one file, identified by the hash
        '''

        logging.info('going to update status for '+hash+' code: '+str(status))
        ret = self.curler.get( self.baseUrl+'updateFileStatus',
                               [ ('fileHash', str(hash) ) ,
                                 ('statusCode', str(int(status)) ),
                               ] # make sure we send a str of an int :)
                             )

        retMsg = '\n'.join(ret).strip()
        if retMsg:
            logging.info( "updating file status returned "+retMsg )


    def uploadFileLog(self, hash, log) :
        '''
        Upload the log for one file, identified by the hash
        '''

        logging.info('going to upload log of size %i for %s ' % ( len(log), hash))
        ret = self.curler.get( self.baseUrl + 'updateFileLog',
                               [ ('fileHash', hash),
                                 ('log', logPack.pack(log).encode('base64') ),
                                 ( 'runLogCreationTimestamp', str(self.creationTimeStamp) ),
                                ] )

        retMsg = '\n'.join( ret ).strip( )
        if retMsg :
            logging.info( "uploading file log returned " + retMsg )



    def updateRunRunInfo(self, fcsr, hltRun) :
        '''
        Updates the status code of a run.
        '''

        logging.info('going to update run numbers for run of "%s" fcsr: %i, hlt: %s' % (self.creationTimeStamp, fcsr, hltRun ))

        ret = ''
        ret = self.curler.get( self.baseUrl + 'updateRunRuns',
                               [ ( 'creationTimestamp', str( self.creationTimeStamp ) ),
                                 ( 'firstConditionSafeRun', str( int( fcsr   ) ) ),    # make sure we send a str of an int :)
                                 ( 'hltRun'               , str( int( hltRun ) ) ),    # make sure we send a str of an int :)
                               ]
        )

        retMsg = '\n'.join( ret ).strip( )
        if retMsg :
            logging.info( "updating run run-numbers returned " + retMsg )


    def updateRunStatus(self, statusCode) :
        '''
        Updates the status code of a run.
        '''

        logging.info('going to update status for run of "%s" code: %i ' % (self.creationTimeStamp, statusCode ))

        ret = ''
        ret = self.curler.get( self.baseUrl + 'updateRunStatus',
                               [ ( 'creationTimestamp', str(self.creationTimeStamp) ),
                                 ( 'statusCode', str(int(statusCode)) ) ] # make sure we send a str of an int :)
                              )

        retMsg = '\n'.join( ret ).strip( )
        if retMsg :
            logging.info( "updating run status returned " + retMsg )


    def uploadRunLog(self, downloadLog, globalLog) :
        '''
        Uploads the logs (and final statistics) of a run.
        '''

        logging.info('going to upload logs for run of "%s" of size %i (download) and %i (global) ' % \
              (self.creationTimeStamp , len( downloadLog ), len(globalLog) ))

        ret = ''
        ret = self.curler.get( self.baseUrl + 'updateRunLog',
                               [ ( 'creationTimestamp', self.creationTimeStamp ),
                                 ( 'downloadLog', logPack.pack(downloadLog).encode('base64') ),
                                 ( 'globalLog'  , logPack.pack(globalLog).encode('base64') )
                               ]
                             )

        retMsg = '\n'.join( ret ).strip( )
        if retMsg :
            logging.info( "uploading run logs returned " + retMsg )


def test() :
    from config import test

    someHash = '42'*20

    print ' == '
    print ' -- '
    su = StatusUpdater( test() )

    print ' -- '
    su.updateFileStatus(someHash, 2000 )

    print ' -- '
    su.uploadFileLog(someHash, "dummy log string")

    print ' -- '
    try:
        su.updateRunStatus( 1000 )
    except Exception, e:
        print "ERROR updating run status: " + str(e)

    print ' -- '
    try:
        su.uploadRunLog( "dummy download log string", 'dummy global log string' )
    except Exception, e:
        print "ERROR uploading run logs: " + str(e)

    print ' -- '
    try:
        su.updateRunRunInfo(1234, 4321)
    except Exception, e:
        print "ERROR uploading run run info: " + str(e)

    print ' -- '
    del su
    print ' == '

if __name__ == '__main__' :
    test( )
