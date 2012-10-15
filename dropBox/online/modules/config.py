import os


class BaseConfig( object ) :
    def __init__(self) :

        self.maindir = '/This/should/be/overwritten/'

        self.detector = 'Test' # was PopCon
        self.label = 'DropBox'

        # the server from which we download files and upload status and logs to:
        self.baseUrl = 'https://mos-dev-slc6.cern.ch/dropBox/'

        self.delay = 30 # to wait if new files are found

        # get info on next run which will be processed for prompt:
        self.src = "https://cmsweb.cern.ch/tier0/firstconditionsaferun"
        self.timeout     = 3
        self.retries     = 2
        self.retryPeriod = 5
        self.proxy = None
        if os.environ.has_key('http_proxy'):
            self.proxy = os.environ.get( 'http_proxy' )  # export http_proxy=http://cmsproxy.cms:3128/

        self.debug = False

        return

    def getDropBoxMainDir(self):
        return os.path.join( self.maindir, self.detector + self.label )


class online( BaseConfig ) :
    def __init__(self) :

        super( online, self ).__init__( )

        self.maindir = '/nfshome0/popcondev/'
        self.detector = 'Test' # was PopCon
        self.label = 'DropBox'

        # should become obsolete with new authentication
        self.authpath = '/nfshome0/popcondev/conddb'

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

        return


class offline( BaseConfig ) :
    def __init__(self) :

        super(offline, self).__init__()

        self.maindir = '/home/condbdev/'
        self.detector = 'Test'
        self.label = 'DropBox'

        # should become obsolete with new authentication
        self.authpath = '/afs/cern.ch/cms/DB/conddb'

        #  used for sync to express and hlt
        self.runInfoDbName = "oracle://cms_orcon_adg/CMS_COND_31X_RUN_INFO"  # ... in online (and cms_orcon_adg in offline)
        self.runInfotag = "runinfo_start_31X_hlt"

        # this will later go into the main DB:
        self.logdb = 'sqlite_file:/tmp/PopConJobLog.db'

        self.gtDbName = "oracle://cms_orcon_adg/CMS_COND_31X_GLOBALTAG"
        self.gtTags = {'hlt' : 'GR10_H_V5', 'express' : 'GR10_E_V5',
                       'prompt' : 'GR10_P_V5'} #-ap: get this from gtList (if we can)

        return


class test( BaseConfig ) :
    def __init__(self) :

        super(test, self).__init__()

        self.maindir = os.path.abspath( os.path.join( os.getcwd(), '..', 'NewOfflineDropBoxBaseDir') )

        # should become obsolete with new authentication
        self.authpath = '/afs/cern.ch/cms/DB/conddb/' # ADG'

        #  used for sync to express and hlt
        self.runInfoDbName = "oracle://cms_orcon_adg/CMS_COND_31X_RUN_INFO"  # ... in online (and cms_orcon_adg in offline)
        self.runInfotag = "runinfo_start_31X_hlt"

        # this will later go into the main DB:
        self.logdb = 'sqlite_file:/tmp/TestOfflineDropBoxJobLog.db'

        self.gtDbName = "oracle://cms_orcon_adg/CMS_COND_31X_GLOBALTAG"
        self.gtTags = {'hlt' : 'GR10_H_V5', 'express' : 'GR10_E_V5',
                       'prompt' : 'GR10_P_V5'} #-ap: get this from gtList (if we can)

        self.debug = True

        return
