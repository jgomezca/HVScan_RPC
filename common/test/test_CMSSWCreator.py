# coding=utf-8
import os
import shutil
import sys
import unittest
import urllib

CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
TEST_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "src"))
sys.path.append(TEST_DIR)


from ReleasesXML import ReleasesXml
from CMSSWCreator import CMSSWReleaseFactory, CMSSWRelease


class TestCMSSWCreate(unittest.TestCase):

    def setUp(self):
        releases_xml_data = urllib.urlopen("https://cmstags.cern.ch/tc/ReleasesXML").read()
        releases_xml = ReleasesXml(releases_xml_data)
        self.releases_xml = releases_xml

    def test_create_release(self):
        cmssw_release = CMSSWRelease("CMSSW_5_3_3", CURRENT_DIR, self.releases_xml)
        cmssw_release.checkout()
        cmssw_release.delete()

    def tearDown(self):
        pass


class TestCMSSWFactory(unittest.TestCase):

    def test_create_releases_from_factory(self):
        test_tmp_dir = os.path.join(CURRENT_DIR, "tmp")
        os.makedirs(test_tmp_dir)
        cmssw_factory = CMSSWReleaseFactory(test_tmp_dir)
        rel1 = cmssw_factory.checkout_release("CMSSW_5_3_3")
        rel2 = cmssw_factory.checkout_release("CMSSW_5_3_2")
        rel1.checkout()
        rel2.checkout()
        rel1.delete()
        rel2.delete()
        shutil.rmtree(test_tmp_dir)


    def tearDown(self):
        pass



if __name__ == '__main__':
    unittest.main()
