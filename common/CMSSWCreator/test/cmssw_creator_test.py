# coding=utf-8

import os
import sys
import unittest
import urllib

CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
TEST_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "src"))
sys.path.append(TEST_DIR)
TEST_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", "ReleasesXML", "src"))
sys.path.append(TEST_DIR)

from releases import ReleasesXml

from cmssw_creator import CMSSWRelease


class TestReleasesXml(unittest.TestCase):

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


if __name__ == '__main__':
    unittest.main()
