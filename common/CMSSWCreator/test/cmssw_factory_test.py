# coding=utf-8

import os
import sys
import shutil
import unittest
from cmssw_factory import CMSSWReleaseFactory

CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
TEST_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "src"))
sys.path.append(TEST_DIR)
TEST_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", "ReleasesXML", "src"))
sys.path.append(TEST_DIR)

from releases import ReleasesXml

from cmssw_creator import CMSSWRelease


class TestReleasesXml(unittest.TestCase):

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
