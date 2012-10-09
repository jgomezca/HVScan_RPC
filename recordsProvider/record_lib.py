"""
Record Library
==============
"""

import subprocess
import os
import re
import itertools
import Settings


software_release_name_pattern = re.compile(Settings.SOFTWARE_RELEASE_NAME_PATTERN)

def hardware_architecture_provider():
    """:return: a list of of currently know hardware architectures."""
    return Settings.HARDWARE_ARCHITECTURES


class SoftwareRelease(object):
    """
    Holds information about software release.

    :param string name: name of software release. E.g. "CMSSW_1_2_3_pre8"
    """

    def __init__(self, name):
        self.name = name
        self._extract_version()
        self._hardware_releases = set()

    def _extract_version(self):
        extracted_pattern = software_release_name_pattern.match(self.name)
        self.version_major, self.version_medium, self.version_minor, self.version_prerelease = extracted_pattern.groups()
        self.version_major = int(self.version_major)
        self.version_medium = int(self.version_medium)
        self.version_minor = int(self.version_minor)
        self.is_prerelease = self.version_prerelease is not None
        if self.is_prerelease:
            self.version_prerelease = int(self.version_prerelease)

    def _add_hardware_release(self, hardware_release):
        self._hardware_releases.add(hardware_release)

    def get_hardware_releases(self):
        """
        :return: set of hardware release names associated to current software release
        """
        return self._hardware_releases

    def get_version_tuple(self):
        """
        :return: tuple containing 4 elements. Software release (major_version,medium_version,minor_version,
        prerelease_version). E.g. for "CMSSW_1_2_3_pre8" version tuple would be ``(1, 2, 3, 8)`` and for "CMSSW_1_2_3" would be
        ``(1, 2, 3, None)``, because prerelease doesn't exist.
        """
        return (self.version_major, self.version_medium, self.version_minor, self.version_prerelease)

    def get_version_dict(self):
        '''
        :return: dictionary containing keys: ``major_version``, ``medium_version`` , ``minor_version`` ,
        ``prerelease_version`` and corresponding values. ``prerelease_version`` is number or ``None``
        '''
        return {'major_version':self.version_major, 'medium_version':self.version_medium,
                'minor_version': self.version_minor, 'prerelease_version':self.version_prerelease}



    def __str__(self):
        return self.name


class SoftwareReleaseManager(object):

    def __init__(self):
        self._hardware_architecture_list = hardware_architecture_provider()
        self._managed_software_releases = {}
        self._collect()

    def _collect(self):
        for hardware_architecture_name in self._hardware_architecture_list:
            path = Settings.RELEASES_PATH.format(hardware_architecture=hardware_architecture_name)
            full_directories_list = os.listdir(path)
            software_release_names = filter(lambda x: software_release_name_pattern.match(x), full_directories_list)
            for software_release_name in software_release_names:
                self._add_software_release(software_release_name, hardware_architecture_name)

    def _add_software_release(self, software_release_name, hardware_architecture_name):
        if self._managed_software_releases.has_key(software_release_name):
            sr = self._managed_software_releases.get(software_release_name)
        else:
            sr = SoftwareRelease(software_release_name)
        sr._add_hardware_release(hardware_architecture_name)
        self._managed_software_releases[software_release_name] = sr

    def _filter_leave_if_eaqual(self, l, attribute_name, value):
        return filter(lambda x: getattr(x, attribute_name) == value, l)

    def _filter_leave_if_not_eaqual(self, l, attribute_name, value):
        return filter(lambda x: getattr(x, attribute_name) != value, l)

    def _filter_leave_if_greater(self, l, attribute_name, value):
        return filter(lambda x: getattr(x, attribute_name) > value, l)

    def _filter_leave_if_greater_or_equal(self, l, attribute_name, value):
        return filter(lambda x: getattr(x, attribute_name) >= value, l)

    def _filter_leave_if_lower(self, l, attribute_name, value):
        return filter(lambda x: getattr(x, attribute_name) < value, l)

    def _filter_leave_if_lower_or_equal(self, l, attribute_name, value):
        return filter(lambda x: getattr(x, attribute_name) <= value, l)


    def list_software_releases(self, include_prereleases=True, from_major=None, till_major=None, group_by_hardware_architecture=False):
        rez = self._managed_software_releases.values()
        if not include_prereleases:
            rez = self._filter_leave_if_eaqual(rez, 'is_prerelease',False)

        if from_major:
            rez = self._filter_leave_if_greater_or_equal(rez, 'version_major', from_major)

        if till_major:
            rez = self._filter_leave_if_lower_or_equal(rez, 'version_major', till_major)

        if group_by_hardware_architecture:
            rez_dict = {}
            for hardware_architecture_name in self._hardware_architecture_list:
                rez_dict[hardware_architecture_name] = []
            for item in rez:
                for hardware_architecture_name in item.get_hardware_releases():
                    rez_dict[hardware_architecture_name].append(item)
            for hardware_architecture_name in self._hardware_architecture_list:
                if not rez_dict[hardware_architecture_name]:
                    del rez_dict[hardware_architecture_name]
            return rez_dict


        return rez

    def major_version_list(self):
        major_versions = set([release.version_major for release in  self.list_software_releases()])
        major_versions = list(major_versions)
        major_versions.sort()
        return major_versions




class ContainerRecordProvider(object):

    def _normalise_container_name(self, container_name):
        return container_name.strip().replace(", ",",")

    def provide(self, architecture_name, release_name):
        dirname = os.path.abspath(os.path.dirname(__file__))
        cmd_args = [dirname + "/get_records.sh", architecture_name, release_name]
        (stdout, stderr) = subprocess.Popen(cmd_args, stdout=subprocess.PIPE).communicate()

        record_object_map = {}
        for line in stdout.splitlines():
            record_name, object_r_name = line.split(", ", 1)
            record_name = record_name.strip()
            object_r_name = self._normalise_container_name(object_r_name)
            record_object_map[record_name] = object_r_name
        return record_object_map # {record_name: container_name, ...}
#
#
#
#print SoftwareRelease("CMSSW_1_2_3_pre1").version_tuple()
#print SoftwareRelease("CMSSW_2_3_4").version_tuple()
#
#srm = SoftwareReleaseManager()
#for release in srm.list_software_releases(include_prereleases=False, from_major=3, till_major=4):
#    print release
#
#r = srm.list_software_releases(include_prereleases=False, from_major=3, till_major=4, group_by_hardware_architecture=True)
#print r
#
#print "major_versions:", srm.major_version_list()
#
#
#print "r", ContainerRecordProvider().provide("slc5_amd64_gcc434", "CMSSW_5_0_0")


#def software_release_for_architecture_provider(hardware_architecture_name):
#
#
#def software_release_provider_by_architecture():
#    rez = {}
#    for hardware_architecture_name in hardware_architecture_provider():
#        rez[hardware_architecture_name] = software_release_for_architecture_provider(hardware_architecture_name)
#    return rez
#
#def software_release_unique_provider():
#    releases_dict = software_release_provider_by_architecture()
#    return set(itertools.chain(*releases_dict.values()))
#
#
#def container_record_provider():
#    pass