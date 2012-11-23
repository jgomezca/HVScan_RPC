# coding=utf-8
import datetime
import logging
import os
import shutil
import subprocess
import urllib
import uuid
from releases_xml import ReleasesXml


class CMSSWReleaseException(Exception):
    """Parent exception for CMSSWRelease exceptions"""
    pass


class CMSSWReleaseAlreadyCheckedOutException(CMSSWReleaseException):
    """
    Raised when:
    a) CMSSWRelease tries to check out new release before deleting old one
    b) Release with the same name exists in target directory and require_clean_release=True
    """
    pass


class CMSSWReleaseCreationException(CMSSWReleaseException):
    """Raised when actual CMSSW checking out fails"""


class CMSSWReleaseDeletionException(CMSSWReleaseException):
    """Raised when deletion of software release fails"""
    pass


class CMSSWReleasePackageException(CMSSWReleaseException):
    """Failed to add package to release"""
    pass

class CMSSWArchitectureNotDetected(CMSSWReleaseException):
    """Architecture for release can not be founded"""
    pass

class CMSSWReleaseModificationsNotAllowed(CMSSWReleaseException):
    """Raised when trying to change properties of CMSSW Release when it is already created"""


class NullHandler(logging.Handler):
    def emit(self, record):
        pass


handler = NullHandler()
logger = logging.getLogger("CMSSWRelease")
logger.addHandler(handler)


class CMSSWRelease(object):

    def __init__(self, release_name=None, releases_directory=None, releases_xml_obj=None):
        self._created = False
        self._release_name = release_name
        self._releases_directory = releases_directory
        self._releases_xml_obj = releases_xml_obj

    @property
    def release_name(self):
        return self._release_name

    @release_name.setter
    def release_name(self, new_release_name):
        if self._created:
            raise CMSSWReleaseModificationsNotAllowed("Can not change release name")
        self._release_name = new_release_name

    @property
    def releases_directory(self):
        return self._releases_directory

    @releases_directory.setter
    def releases_directory(self, new_releases_directory):
        if self._created:
            raise CMSSWReleaseModificationsNotAllowed("Can not change release directory")
        self._releases_directory = new_releases_directory

    @property
    def release_area(self):
        if self._release_name and self._releases_directory:
            return os.path.join(self._releases_directory, self._release_name)
        else:
            raise ValueError("Release area needs to know release name and releases directory")

    @property
    def releases_xml_obj(self):
        return self._releases_xml_obj

    @releases_xml_obj.setter
    def releases_xml_obj(self, new_releases_xml_obj):
        if self._created:
            raise CMSSWReleaseModificationsNotAllowed("Can not change releasesXml object")
        self._releases_xml_obj = new_releases_xml_obj

    @property
    def architecture(self):
        if self._releases_xml_obj:
            return self._releases_xml_obj.get_release(self._release_name).arch
        else:
            raise ValueError("For architecture needed releasesXml object")

    def _validate_variables(self, require_clean_release):
        if self._created:
            raise CMSSWReleaseAlreadyCheckedOutException("Release alredy checked out. Please delete old release before proceeding")

        if self._release_name is None:
            raise CMSSWReleaseCreationException("Releases name is not set")

        if self._releases_directory is None:
            raise CMSSWReleaseCreationException("Releases directory is not set")

        if self._releases_xml_obj is None:
            raise CMSSWReleaseCreationException("ReleasesXML object is not set")

        if require_clean_release and os.path.exists(self.release_area):
            raise CMSSWReleaseAlreadyCheckedOutException("")

    def checkout(self, require_clean_release=True):

        self._validate_variables(require_clean_release)

        #Create directory for releases if not exist
        if not os.path.exists(self._releases_directory):
            os.makedirs(self._releases_directory)

        starting_working_directory = os.getcwd()
        os.chdir(self._releases_directory)

        command = "export SCRAM_ARCH={arch}; scram project CMSSW {release} && cd {release} && eval `scramv1 runtime -sh`".format(
            release=self._release_name, arch=self.architecture)

        try:
            p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            (stdout_val, stderr_val) = p.communicate()
            if p.returncode != 0:
                error_msg = "Release {release} creation failed with return code {returncode} in path {path}".format(
                    release=self._release_name, returncode=p.returncode, path=self._release_parent_directory)
                logger.critical(error_msg)
                logger.critical(stderr_val)
                raise CMSSWReleaseCreationException(error_msg)
            self._created = True
        except (OSError, ValueError) as e:
            error_msg = "Release creation failed with exception " + str(e)
            raise CMSSWReleaseCreationException(error_msg)
        finally:
            os.chdir(starting_working_directory)

    def delete(self):
        if not self._created:
            raise CMSSWReleaseDeletionException("Cannot delete repository. It is not created yet (must be created by this tool)")
        try:
            shutil.rmtree(self.release_area)
            self._checked_out = False
        except OSError as e:
            error_msg = "Release {release} deletion in path {path} failed with following exception:{exception}".format(
                release=self._release_name, path=self._release_parent_directory, exception=str(e))
            logger.warning(error_msg)
            raise CMSSWReleaseDeletionException(error_msg)


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
