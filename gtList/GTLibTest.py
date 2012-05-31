import os, sys
import unittest
import re
from GTLib import UploadGTLib
import  GTServerSettings as Settings


class TestUploadGTLib(unittest.TestCase):

    def setUp(self):
        self.lib = UploadGTLib(
            authpath = "",
            global_tag_schema = Settings.update_frontier_connection("frontier://PromptProd/CMS_COND_31X_GLOBALTAG"),
            log_schema = Settings.update_frontier_connection("frontier://PromptProd/CMS_COND_31X_POPCONLOG"),
            cmssw_version=os.environ.get('CMSSW_VERSION', ''))

    def testCMSSWVersion(self):
        version = self.lib.getCMSSWVersion()
        self.assertNotEquals(version, '')
        match_object = re.search('^CMSSW_(\d+)_(\d+)_(\d+)$', version)
        self.assertNotEqual(match_object, None)

    def testGTList(self):
        gt_list = self.lib.getGTList()
        self.assertTrue(isinstance(gt_list, list))        
        for gt_name in gt_list:
            self.assertTrue(isinstance(gt_name, str)) #string, but not unicode!
            self.assertNotEqual(len(gt_name), 0)


    #def testgetCurrentGT(self):
    #    prod_gts = self.lib.getProductionGTs()
    #    self.assertTrue(isinstance(prod_gts, dict))
    #    self.assertTrue(len(prod_gts.keys())==3)

    # available in python 3.1 and later : @unittest.skipIf(FASTER_TESTING, 'This test too long for rapid testing')   
    '''
    def testgetGTInfo(self):
        gt_info = self.lib.getGTInfo('GR_P_V32')
        self.assertTrue(isinstance(gt_info, dict))
        self.assertTrue(gt_info.has_key('header'))
        self.assertTrue(isinstance(gt_info['header'], dict))
        self.assertTrue(gt_info['header'].has_key('GlobalTagName'))
        self.assertTrue(gt_info['header'].has_key('creation_time'))
        self.assertTrue(gt_info['header'].has_key('CMSSW_VERSION'))
        self.assertTrue(gt_info.has_key('body'))        
        self.assertTrue(isinstance(gt_info['body'], list))
        for body_item in gt_info['body']:
            self.assertTrue(isinstance(body_item, dict))
            self.assertTrue(body_item.has_key('tag'))
            self.assertTrue(body_item.has_key('record'))
            self.assertTrue(body_item.has_key('label'))
            self.assertTrue(body_item.has_key('pfn'))
            self.assertTrue(body_item.has_key('size'))
            self.assertTrue(body_item.has_key('time'))
            self.assertTrue(body_item.has_key('comment'))
            self.assertTrue(body_item.has_key('last_since'))
            self.assertTrue(body_item.has_key('last_log_entry'))
            self.assertTrue(body_item.has_key('iov_list'))
'''

    def testgetProductionGTs(self):
        production_gts = self.lib.getProductionGTs()
        self.assertTrue(isinstance(production_gts, dict))
        self.assertEqual(len(production_gts), 3)

    def testgetExpressGT(self):  
        #TODO conn str should be taken from settings
        expressSrc = "https://cmsweb.cern.ch/tier0/express_config"
        proxy = None
        timeout = 5
        from T0DASquery import Tier0GT
        t0 = Tier0GT()
        rez = t0(expressSrc,proxy,timeout)[0]
        self.assertTrue(isinstance(rez,str))#not unicode and not basestring
        self.assertTrue(rez)

    def testgetHLTGT(self):
        from T0DASquery import HLTGT
        import GTServerSettings as Settings
        hlt = HLTGT()
        dbName=Settings.RUN_INFO_SCHEMA
        authPath=Settings.AUTHPATH
        tag=Settings.RUN_INFO_TAG
        rez = hlt(dbName,authPath,tag) 
        self.assertTrue(isinstance(rez,str))#not unicode and not basestring
        self.assertTrue(rez)

    def testgetPromptGT(self):
        #TODO conn str should be taken from settings
        promptSrc = "https://cmsweb.cern.ch/tier0/reco_config"
        proxy = None
        timeout = 5
        from T0DASquery import Tier0GT
        t0 = Tier0GT()
        rez = t0(promptSrc,proxy,timeout)[0]
        self.assertTrue(isinstance(rez,str))#not unicode and not basestring
        self.assertTrue(rez)

if __name__ == '__main__':
    unittest.main()
    

