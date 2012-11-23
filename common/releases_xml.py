# coding=utf-8

from collections import namedtuple, defaultdict
import xml.etree.ElementTree as etree
#from lxml import etree - if lxml support enabled

Release = namedtuple('Release', ['name', 'arch', 'type', 'state'])

class ReleasesXml(object):
    """
    Parses data and provides API for ReleasesXML file. During writing documentation file is stored at
    https://cmstags.cern.ch/tc/ReleasesXML . Assumed that one software release will have one and only one architecture.
    """

    def __init__(self, data):
        """
        XML data to parse. Data parsing execuded during object construction.

        :param data: ReleasesXML file content provided as string
        """
        self._data = data
        self._root = etree.fromstring(self._data)
        self._parse_data()

    def _parse_data(self):
        """
        Data parsing and internal structures preparation.
        _releases contains data structure {'release_name':ReleseObj, ...}
        _architectures contains data structure {'architecture_nameA': [ReleseObj1, ReleseObj2...],
                                                'architecture_nameB':...}

        """
        self._architectures = defaultdict(list)
        self._releases = {}
        arch_elements = self._root.findall("architecture") #architecture[@name] - for python2.7 or lxml lib
        for arch_element in arch_elements:
            architecture_name = arch_element.attrib.get("name")
            release_elements = arch_element.findall("project") #project[@label] - for python2.7 or lxml lib
            for release_element in release_elements:
                release_name = release_element.attrib.get("label")
                release_type = release_element.attrib.get("type")
                release_state = release_element.attrib.get("state")
                release = Release(name=release_name, arch=architecture_name, type=release_type, state=release_state)
                self._architectures[architecture_name].append(release)
                self._releases[release_name] = release


    def architectures(self):
        """
        Returns list of architectures

        :return: list of strings
        """

        return self._architectures.keys()

    def has_architecture(self, arch_name):
        """
        Returns boolean if achtecture exist or not.

        :param arch_name: name of hardware architecture
        :return: bool
        """

        return self._architectures.has_key(arch_name)

    def releases(self, arch_name=None):
        """
        Returns list of Release objects filtered by architecture name.
        If arch_name not specified specified - returned all Releases.
        If architecture name does not exist - returned empty list.

        :param arch_name: name of hardware architecture
        :return: list of relese objects
        """

        if arch_name: #architectures filtered by architecture
            releases = self._architectures[arch_name]
        else:
            releases = self._releases.values()
        return releases

    def has_release(self, release_name):
        """
        Returns if release with specified name exits

        :param release_name:
        :return: bool
        """
        return self._releases.has_key(release_name)

    def get_release(self, release_name):
        """
        Raises KeyError if release not found

        :param release_name:
        :return: Returns release object
        """
        return self._releases[release_name]

