# coding=utf-8
import datetime
import os
import urllib
import uuid
from cmssw_creator import CMSSWRelease
from releases import ReleasesXml


class CMSSWReleaseFactory(object):
    #TODO: Add factory cleaning

    def __init__(self, factory_directory, releases_xml_datasource="https://cmstags.cern.ch/tc/ReleasesXML"):
        self._factory_directory = os.path.abspath(factory_directory)
        self._last_absolute_unique_directory_name = None
        releases_xml_data = urllib.urlopen(releases_xml_datasource).read()
        self._releases_xml = ReleasesXml(releases_xml_data)

    def checkout_release(self, release_name):
        """
        Returns constructed CMSSWRelease object. To have cmssw object needs to be called "checkout"
        method for object
        :param release_name:
        :return:
        """
        unique_directory_name = str(datetime.datetime.now().date()) + "_" +  str(uuid.uuid4().hex)
        absolute_unique_directory_name = os.path.join(self._factory_directory, unique_directory_name)
        self._last_absolute_unique_directory_name = absolute_unique_directory_name
        return CMSSWRelease(release_name, releases_directory=absolute_unique_directory_name, releases_xml_obj=self._releases_xml)

    @property
    def last_absolute_unique_directory_name(self):
        return self._last_absolute_unique_directory_name

    @property
    def factory_top_directory(self):
        return self._factory_directory