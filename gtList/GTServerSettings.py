import os
import connectstrParser, cacheconfigParser

try:
    default_cmssw_version = os.environ['CMSSW_VERSION']
except:
    default_cmssw_version = None

AUTHPATH = ''
GT_IOV_LIST_TRUNCATED_COUNT = 100
GT_INFO_MAX_AGE = 3600 #seconds
GLOBAL_TAG_SCHEMA = "frontier://PromptProd/CMS_COND_31X_GLOBALTAG"
LOG_SCHEMA = "frontier://PromptProd/CMS_COND_31X_POPCONLOG"
CACHE_DIR = 'cache'
CMSSW_VERSION = default_cmssw_version

PRODUCTION_GTS = {"express": "GR_E_V25", "hlt": "GR_H_V29", "prompt": "GR_P_V32"}
RUN_INFO_SCHEMA="frontier://PromptProd/CMS_COND_31X_RUN_INFO"
RUN_INFO_TAG="runinfo_31X_hlt"
EXPRESS_URL="https://cmsweb.cern.ch/tier0/express_config"
PROMPT_URL = "https://cmsweb.cern.ch/tier0/reco_config"
MAILING_LIST = ["a.tilmantas@gmail.com"]
SEND_FROM = "pdmv.service@cern.ch"
PRODUCTION_GT_PROXY = None
PRODUCTION_GT_TIMEOUT = 1

DEFAULT_CMS_PATH = '/afs/cern.ch/cms/'


def update_frontier_connection(conn_str):
    '''updates frontier connection with proxy server information'''
    parser=connectstrParser.connectstrParser(conn_str)
    parser.parse()
#    print parser.protocol(),parser.service(),parser.schemaname(),parser.needsitelocalinfo(),parser.servlettotranslate()
    if parser.needsitelocalinfo():
        sitelocalconfig = os.environ.get('$CMS_PATH', DEFAULT_CMS_PATH ) + "SITECONF/CERN/JobConfig/site-local-config.xml"
        frontierparser=cacheconfigParser.cacheconfigParser()
        frontierparser.parse(sitelocalconfig)
        return str(parser.fullfrontierStr(parser.schemaname(),frontierparser.parameterdict())) #str because default unicode
    return str(conn_str)
#        print 'full frontier string'
#            print parser.fullfrontierStr(parser.schemaname(),frontierparser.parameterdict())
