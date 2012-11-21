import logging
import os
import shutil
import subprocess
from cmssw_creator_exceptions import CMSSWReleasePackageException


class NullHandler(logging.Handler):
    def emit(self, record):
        pass


handler = NullHandler()
logger = logging.getLogger("CMSSWRelease")
logger.addHandler(handler)


class CMSSWReleaseConfigurator(object):

    def __init__(self, cmssw_release):
        self._cmssw_release = cmssw_release

    def add_package(self, package_name):
        command = 'export SCRAM_ARCH={arch}; cd "{release_area}"; eval `scramv1 runtime -sh`; addpkg -f {package_name} ; checkdeps -a'.format(
            release_area=self._cmssw_release.release_area, pacakge_name=package_name, arch=self._cmssw_release.architecture)

        p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        (stdout_val, stderr_val) = p.communicate()
        if p.returncode != 0:
            error_msg = "Adding package {package} to release area {release_area} failed".format(
                release_area=self._cmssw_release.release_area, pacakge_name=package_name)
            logger.warning(error_msg)
            logger.warning(stderr_val)
            raise CMSSWReleasePackageException(error_msg)

    def add_packages(self, package_names):
        for package_name in package_names:
            self.add_package(package_name)

    def copy_file(self, src, relative_dest):
        '''
        Copy src file to release. Destination calculated from release area root folder
        '''
        dst = os.path.join(self._cmssw_release.release_area, relative_dest)
        logger.info("Copying file {src} -> {dest}".format(src=src, dest=dst))
        shutil.copy(src, dst)

    def copy_tree(self, src_dir, relative_dest):
        dst = os.path.join(self._cmssw_release.release_area, relative_dest)
        logger.info("Copying dir {src} -> {dest}".format(src=src_dir, dest=relative_dest))
        shutil.copytree(src_dir, dst)