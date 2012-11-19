# coding=utf-8

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