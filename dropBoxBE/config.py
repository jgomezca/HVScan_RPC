import os
import socket

import service


class BaseConfig( object ) :
    def __init__(self) :

        self.maindir = '/This/should/be/overwritten/'

        self.detector = 'Test' # was PopCon
        self.label = 'DropBox'

        # the server from which we download files and upload status and logs to:
        self.baseUrl = None

        self.delay = 30 # to wait if new files are found

        # get info on next run which will be processed for prompt:
        self.src = "https://cmsweb.cern.ch/tier0"
        self.timeout     = 5
        self.retries     = 3
        self.retryPeriod = 30
        self.proxy = None
        if os.environ.has_key('http_proxy'):
            self.proxy = os.environ.get( 'http_proxy' )  # export http_proxy=http://cmsproxy.cms:3128/

        self.debug = False


    def getDropBoxMainDir(self):
        return os.path.join( self.maindir, self.detector + self.label )


class online( BaseConfig ) :
    def __init__(self) :

        super( online, self ).__init__( )

        self.backend = 'online'

        self.maindir = '/nfshome0/popcondev/'
        self.detector = 'Test' # was PopCon
        self.label = 'DropBox'

        self.destinationDB = None

        # should become obsolete with new authentication
        self.authpath = '/nfshome0/popcondev/conddb'

        # this is the URL for the dropBox frontend service:
        self.baseUrl = 'https://cms-conddb-prod.cern.ch/dropBox/'

        #  used for sync to express and hlt
        self.runInfoDbName = "oracle://cms_orcon_prod/CMS_COND_31X_RUN_INFO"  # ... in online (and cms_orcon_adg in offline)
        self.runInfotag = "runinfo_start_31X_hlt"

        # set proxy for the firstconditionsaferun URL
        self.proxy = "http://cmsproxy.cms:3128"

        # this will later go into the main DB:
        self.logdb = 'sqlite_file:/tmp/PopConDevJobLog.db'

        self.gtDbName = "oracle://cms_orcon_prod/CMS_COND_31X_GLOBALTAG"
        self.gtTags = {'hlt' : 'GR10_H_V5', 'express' : 'GR10_E_V5',
                       'prompt' : 'GR10_P_V5'} #-ap: get this from gtList (if we can)


class offline( BaseConfig ) :
    def __init__(self) :

        super(offline, self).__init__()

        self.backend = 'offline'

        self.maindir = os.path.abspath( os.path.join( os.getcwd(), '..', 'NewOfflineDropBoxBaseDir') )
        self.detector = 'Test'
        self.label = 'DropBox'

        self.destinationDB = None

        # should become obsolete with new authentication
        self.authpath = '/afs/cern.ch/cms/DB/conddb'

        # this is the URL for the dropBox frontend service:
        self.baseUrl = 'https://cms-conddb-int.cern.ch/dropBox/'

        #  used for sync to express and hlt
        self.runInfoDbName = "oracle://cms_orcon_adg/CMS_COND_31X_RUN_INFO"  # ... in online (and cms_orcon_adg in offline)
        self.runInfotag = "runinfo_start_31X_hlt"

        # this will later go into the main DB:
        self.logdb = 'oracle://cms_orcoff_prep/CMS_COND_POPCONLOG'

        self.gtDbName = "oracle://cms_orcon_adg/CMS_COND_31X_GLOBALTAG"
        self.gtTags = {'hlt' : 'GR10_H_V5', 'express' : 'GR10_E_V5',
                       'prompt' : 'GR10_P_V5'} #-ap: get this from gtList (if we can)


class tier0( online ) :
    def __init__(self) :
        super( tier0, self ).__init__( )

        self.backend = 'tier0'
        self.detector = 'T0' # was PopCon

        self.delay = None     # flag that we are Tier-0 and need to sleep until the next 10-min boundary

        # take all the other params from the online base class ...


class test( BaseConfig ) :
    def __init__(self) :

        super(test, self).__init__()

        self.maindir = os.path.abspath( os.path.join( os.getcwd(), '..', 'NewOfflineDropBoxBaseDir') )

        # For development, we use the prep dropBox database
        if service.settings['productionLevel'] in set(['dev']):
            self.backend = 'dev'
            self.destinationDB = 'oracle://cms_orcoff_prep/CMS_COND_DROPBOX'
            self.authpath = '/afs/cern.ch/cms/DB/conddb/test/dropbox'

        # In private instances, we take it from netrc
        elif service.settings['productionLevel'] in set(['private']):
            self.backend = 'private'
            connectionDictionary = service.getConnectionDictionaryFromNetrc('dropBoxDatabase')
            self.destinationDB = 'oracle://%s/%s' % (connectionDictionary['db_name'], connectionDictionary['user'])
            # will be pointing to the location where the tester is keeping his test_dropbox key
            # should become obsolete with new authentication
            self.authpath = '/data/secrets'

        else:
            raise Exception('Unknown production level.')

        # this is the URL for the dropBox frontend service, for testing/developing use the current host:
        #self.baseUrl = 'https://%s/dropBox/' % (socket.gethostname(),)
        self.baseUrl = 'https://%s:8095/dropBox/' %(socket.gethostname(),)

        # be quicker in tests
        self.delay = 10

        #  used for sync to express and hlt
        self.runInfoDbName = "oracle://cms_orcon_adg/CMS_COND_31X_RUN_INFO"  # ... in online (and cms_orcon_adg in offline)
        self.runInfotag = "runinfo_start_31X_hlt"

        # this will later go into the main DB:
        self.logdb = 'sqlite_file:/tmp/TestOfflineDropBoxJobLog.db'

        self.gtDbName = "oracle://cms_orcon_adg/CMS_COND_31X_GLOBALTAG"
        self.gtTags = {'hlt' : 'GR10_H_V5', 'express' : 'GR10_E_V5',
                       'prompt' : 'GR10_P_V5'} #-ap: get this from gtList (if we can)

        self.debug = True


class tier0Test( offline ) :
    def __init__(self) :
        super( tier0Test, self ).__init__( )

        self.backend = 'tier0'
        self.detector = 'T0Test'

        self.delay = None     # flag that we are Tier-0 and need to sleep until the next 10-min boundary

        # take all the other params from the test base class ...


class replay( test ) :
    def __init__(self) :

        super(replay, self).__init__()


