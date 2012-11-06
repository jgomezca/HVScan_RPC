# coding=utf-8

import collections
import os
import sys
import unittest

CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
TEST_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "src"))
sys.path.append(TEST_DIR)

from releases import ReleasesXml, Release

class TestReleasesXml(unittest.TestCase):

    def setUp(self):
        #URLReleasesXML = "https://cmstags.cern.ch/tc/ReleasesXML"#r = requests.get(URLReleasesXML, verify=False)#r.text
        curr_dir = os.path.dirname(os.path.abspath(__file__))
        test_file = os.path.join(curr_dir, "releases.test.xml")
        data = open(test_file,"rb").read()
        self.rx = ReleasesXml(data)

    def test_architectures(self):
        architectures = self.rx.architectures()
        self.assertTrue(isinstance(architectures, collections.Iterable), "Architectures has be iterable")
        for arch in architectures:
            self.assertTrue(isinstance(arch, basestring), "Architecture has to be string or unicode")

    def test_has_architecture(self):
        self.assertTrue(self.rx.has_architecture("slc5_amd64_gcc472"))

    def test_releases(self):
        releases = self.rx.releases()
        self.assertTrue(isinstance(releases, collections.Iterable), "Releases has to be iterable")
        for rel in releases:
            self.assertTrue(isinstance(rel, Release), "Release ahs to be object of Release")

        filtered_releases = self.rx.releases("slc5_amd64_gcc472")
        self.assertEqual(len(filtered_releases), 1)
        self.assertTrue(isinstance(filtered_releases, collections.Sequence))
        self.assertTrue(isinstance(filtered_releases[0], Release))
        r = Release(name="CMSSW_6_0_0_patch1",arch="slc5_amd64_gcc472", type="Production", state="Announced")
        self.assertEqual(filtered_releases[0], r)

    def test_has_release(self):
        self.assertTrue(self.rx.has_release("CMSSW_6_0_0_patch1"))
        self.assertFalse(self.rx.has_release("NotExistingReleaseName"))

    def test_get_release(self):
        r = Release(name="CMSSW_6_0_0_patch1",arch="slc5_amd64_gcc472", type="Production", state="Announced")
        self.assertEqual(self.rx.get_release("CMSSW_6_0_0_patch1"), r)

        self.assertRaises(KeyError, self.rx.get_release, "NotExistingReleaseName")


if __name__ == '__main__':
    unittest.main()
