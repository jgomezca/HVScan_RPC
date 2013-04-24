import DLFCN, sys, os, coral
sys.setdlopenflags(DLFCN.RTLD_GLOBAL+DLFCN.RTLD_LAZY)
import pluginCondDBPyInterface as condDB
import time
import json, urllib, ast
#import T0DASquery
import logging
import T0DASquery
import GTComparison
#import cherrypy
import GTServerSettings as Settings

AUTHPATH = "/afs/cern.ch/cms/DB/conddb"

logger = logging.getLogger(__name__)

#--------
#Playground

class UploadGTLib(object):

    def __init__(self, authpath, global_tag_schema, log_schema, cmssw_version):
        '''
        authpath - place with authentication privileges
        '''
        logger.setLevel(logging.DEBUG)

        self.authpath = authpath
        self.global_tag_schema = global_tag_schema
        self.log_schema = log_schema
        self.cmssw_version = cmssw_version
        self._initGT()


    def _initGT(self, authpath = None, global_tag_schema = None, log_schema=None):
        '''Iniciate connection to DB containing information about GT'''

        #if auth path not given - take from constructor variable
        if(authpath == None):
           authpath = self.authpath
        else:
           self.authpath = authpath

        if(global_tag_schema == None):
           global_tag_schema = self.global_tag_schema
        else:
           self.global_tag_schema = global_tag_schema

        if(log_schema == None):
            log_schema = self.log_schema
        else:
           self.log_schema = log_schema

        self.framework_incantation = condDB.FWIncantation()
        self.rdbms = condDB.RDBMS(self.authpath)
        self.rdbms.setLogger(self.log_schema)

    def getCMSSWVersion(self):
        '''Returns tring with version'''
        return self.cmssw_version

    def getGTList(self):
        '''returns list of GT'''
        svc = coral.ConnectionService()
        config = svc.configuration()
        os.environ['CORAL_AUTH_PATH'] =	self.authpath
        config.setDefaultAuthenticationService('CORAL/Services/XMLAuthenticationService')
        session = svc.connect(self.global_tag_schema, accessMode = coral.access_ReadOnly)
        transaction	= session.transaction()
        os.unsetenv('CORAL_AUTH_PATH')
        transaction.start(True)
        schema = session.nominalSchema()
        tablelist = schema.listTables()
        gt_names = []
        for tablename in tablelist:
            if tablename.startswith("TAGTREE_TABLE_"):
                gt_name	= tablename[len("TAGTREE_TABLE_"):]
                gt_names.append(gt_name)
        transaction.commit()
        del session
        return gt_names

    def getProductionGTs(self):
        return T0DASquery.GTValues(dbName=Settings.RUN_INFO_SCHEMA,
                            authPath=Settings.AUTHPATH,
                            tag=Settings.RUN_INFO_TAG,
                            expressSrc=Settings.EXPRESS_URL,
                            promptSrc = Settings.PROMPT_URL,
                            proxy = Settings.PRODUCTION_GT_PROXY,
                            out = Settings.PRODUCTION_GT_TIMEOUT).getGTDictionary()

#    def getCurrentGT(self):
#        '''Globalt tags used by T0. list'''
#        all_gt_names = []
#        query2Tier0 =   T0DASquery.Query2Tier0()
#        for src in query2Tier0.src: #query2Tier0.src feels unstable
#            query_result = query2Tier0.query_tier0(src = src)
#            gt_names = query2Tier0.get_gt_names(query_result=query_result)
#            all_gt_names += gt_names
#        return all_gt_names #getCurrentGT should be called getCurrentGTs. Also shold be defined meaning of each GT
       

    def getGTInfo(self, GT_name): #==gName
        '''Information about GT. object/dict?'''
        
        globalTag = self.rdbms.globalTag(self.global_tag_schema, GT_name + "::All" ,"" ,"")
        #html_list       =       ['record', 'label', 'pfn', 'tag', 'lastSince','time', 'comment', 'iovlist','size','lastLogEntry' ]
        #html_content    =       []
        gt_content = {}
        current_local_time = time.strftime("%d %B, %Y %H:%M:%S", time.localtime())
        gt_content_header = {
            'GlobalTagName':GT_name,
            'creation_time':current_local_time,
            'CMSSW_VERSION':self.cmssw_version
        }
        gt_content['header'] = gt_content_header
        gt_content['body'] = []

        for tag in globalTag.elements: #element of GT. Iteration
            tag_pfn =   tag.pfn
            logger.debug("TAG_PFN" + tag_pfn)
            #because it works only in online - required update of connection
            # string for working offline
            if((tag.pfn).find('FrontierOnProd') != -1):
                tag_pfn = "frontier://PromptProd/CMS_COND"+(tag_pfn).split('/CMS_COND')[1]
                logger.debug("TAG_PFN_UPDATED" + tag_pfn)

            try:            
            	db = self.rdbms.getReadOnlyDB(tag_pfn)
            	log = db.lastLogEntry(tag.tag)
            	iovlist = []
                db.startReadOnlyTransaction()
                iov = db.iov(tag.tag)
                db.commitTransaction()
            except:
                print "Something wrong"
                continue #TODO review

            timeVal = str(time.asctime(time.gmtime(condDB.unpackTime(iov.timestamp())[0])))
            timeVal = time.strftime("%d %b %Y %H:%M",time.strptime(timeVal, "%a %b %d %H:%M:%S %Y"))

            for elem in iov.elements :
                iovlist.append((elem.since(), elem.till()))
            lastSince = iovlist[-1][0]
            #iov.tail(1)
            #for elem in iov.elements :
                #lastSince = elem.since()
            #iov.resetRange()

            gt_content_element = {'record': tag.record,'label':tag.label,'pfn':tag.pfn,'tag':tag.tag,'size':iov.size(),'time':timeVal,'comment':iov.comment(),'last_since':lastSince,'last_log_entry':log.usertext, 'iov_list':iovlist}
            gt_content['body'].append(gt_content_element)

            del iov
            del db
        return gt_content


    def getGTDiff(self, gt1_name, gt2_name):
        '''Comparing GT. Returns dict'''
        pass
        #    @cherrypy.expose
#    def get_gtlist_diff(self, gt, info = '{}'):
#        if info == '':
#               info = '{}'
#        g = GlobalTag2HTML(authpath=AUTHPATH)
#        return g.get_gtlist_diff_json(gt = gt, info = json.loads(info))
#

