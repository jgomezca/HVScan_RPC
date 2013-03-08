#!/usr/bin/env python
'''CMS Condition CMSSW Installer

i.e. an installer for a custom release tailored for us.
'''

__author__ = 'Andreas Pfeiffer'
__copyright__ = 'Copyright 2013, CERN CMS'
__credits__ = ['Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Andreas Pfeiffer'
__email__ = 'andreas.pfeiffer@cern.ch'


import os
import sys
import subprocess
import glob
import optparse
import logging


class CondCMSSWInstaller(object):

    def __init__(self):
        self.topDir = '/data'
        self.cmsCondWebTag = 'CMS_CONDWEB_0_2'
        self.arch   = 'slc6_amd64_gcc472'

        self.oldPackages = []
        self.newPackages = []

        self.options = self.getOptions()

        logging.info('arch from options is '+self.options['arch'])
        if self.options['arch'] == 'auto':
            self.arch = 'slc6_amd64_gcc472' # set default
            if 'Darwin' in os.uname()[0]:
                self.arch = 'osx108_amd64_gcc472'
            logging.info("using auto-detected arch:" + self.arch)

        logging.info("using topDir :" + self.options['topDir'])

        self.topDir = os.path.join( self.options['topDir'], 'cmssw' )
        self.cmsCondWebTag = self.options['tag']

        if not os.path.exists(self.topDir):
            msg = "creating top level dir at " + self.topDir
            print msg
            logging.info( msg )
            os.makedirs(self.topDir)

        return

    def getOptions(self):

        parser = optparse.OptionParser(usage =
            'Usage: %prog [options] \n'
            '\n'
            'Examples:\n'
            '  %prog --topDir /data '
        )

        parser.add_option('--topDir', type = 'str',
            dest = 'topDir',
            default = '/data',
            help = 'Top level directory into which to install cmssw. Default: %default'
        )

        parser.add_option('--tag', type = 'str',
            dest = 'tag',
            default = 'CMS_CONDWEB_0_2',
            help = 'CVS Tag to use for installation of cmssw. Default: %default'
        )

        parser.add_option('-a', '--architecture', type = 'str',
            dest = 'arch',
            default = 'auto',
            help = 'SCRAM_ARCH to use. Default: %default'
        )

        (options, args) = parser.parse_args()

        options = vars(options)

        return options

    def doCmd(self, cmd):

        logging.info('going to execute '+cmd)

        process = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        stdout = process.communicate()
        returnCode = process.returncode

        msg = ''
        if stdout:
            for line in stdout:
                if line: msg += line
            logging.debug('cmd returned: %s ' % (msg,) )
        else:
            logging.debug('cmd returned w/o message')

        return

    def getInstalledPackages(self):

        startDir = os.getcwd()
        os.chdir(self.topDir)
        dirList = glob.glob( os.path.join(self.arch, 'external', '*', '*') )
        pkgList = []
        for entry in dirList:
            arch, ext, pkg, vers = entry.split('/')
            pkgList.append(pkg +'/'+ vers)

        os.chdir(startDir)
        return pkgList

    def createSetupFile(self):

        logging.info('creating setup.sh start')

        aptDir = os.path.join(self.topDir, self.arch, 'external', 'apt', '*')
        logging.info('checking for apt version at '+aptDir)

        aptInst = glob.glob( aptDir )[0]
        aptVers = aptInst.split('/')[-1]
        logging.info('found apt version '+aptVers)

        setup = """
export VO_CMS_SW_DIR=%s

export SCRAM_ARCH=%s
export LANG="C"
export LC_CTYPE="C"

source $VO_CMS_SW_DIR/$SCRAM_ARCH/external/apt/%s/etc/profile.d/init.sh
        """ % (self.topDir, self.arch, aptVers)

        logging.info('writing file to '+self.topDir)

        sf = open(self.topDir+'/setup.sh', 'w')
        sf.write(setup)
        sf.close()

        logging.info('creating setup.sh done')
        return

    def createSetupEnvFile(self, pkgList):

        logging.info('creating setupEnv.sh start')

        pkgMap = { 'topDir' : self.topDir,
                   'arch' : self.arch,
                   }

        for pkgVers in pkgList :
            pkg, vers = pkgVers.split('/')
            pkgMap[pkg] = vers

        # needs to be dynamic from install, so take from cherrypy/lib (and rely on cmssw build that the others are the same :)
        cherryPyDir = os.path.join(self.topDir, self.arch, 'external', 'cherrypy', pkgMap['cherrypy'], 'lib')
        pyBaseVers = os.listdir(cherryPyDir)[0]
        pkgMap['pyBaseVers'] = pyBaseVers
        logging.info('using %s as python base version in lib dirs' % (pyBaseVers,) )

        setupEnv = """
export VO_CMS_SW_DIR=%(topDir)s
export SCRAM_ARCH=%(arch)s

source ${VO_CMS_SW_DIR}/${SCRAM_ARCH}/external/oracle/%(oracle)s/etc/profile.d/init.sh

source ${VO_CMS_SW_DIR}/${SCRAM_ARCH}/external/python/%(python)s/etc/profile.d/init.sh
source ${VO_CMS_SW_DIR}/${SCRAM_ARCH}/external/py2-sqlalchemy/%(py2-sqlalchemy)s/etc/profile.d/init.sh
source ${VO_CMS_SW_DIR}/${SCRAM_ARCH}/external/py2-jinja/%(py2-jinja)s/etc/profile.d/init.sh
source ${VO_CMS_SW_DIR}/${SCRAM_ARCH}/external/py2-cx-oracle/%(py2-cx-oracle)s/etc/profile.d/init.sh
source ${VO_CMS_SW_DIR}/${SCRAM_ARCH}/external/cherrypy/%(cherrypy)s/etc/profile.d/init.sh
source ${VO_CMS_SW_DIR}/${SCRAM_ARCH}/external/py2-pyopenssl/%(py2-pyopenssl)s/etc/profile.d/init.sh
source ${VO_CMS_SW_DIR}/${SCRAM_ARCH}/external/curl/%(curl)s/etc/profile.d/init.sh
source ${VO_CMS_SW_DIR}/${SCRAM_ARCH}/external/py2-pycurl/%(py2-pycurl)s/etc/profile.d/init.sh

# set our path so we can make sure it's first:
export NEW_PYTHONPATH=${VO_CMS_SW_DIR}/${SCRAM_ARCH}/external/cherrypy/%(cherrypy)s/lib/%(pyBaseVers)s/site-packages/
export NEW_PYTHONPATH=${NEW_PYTHONPATH}:${VO_CMS_SW_DIR}/${SCRAM_ARCH}/external/py2-sqlalchemy/%(py2-sqlalchemy)s/lib/%(pyBaseVers)s/site-packages/
export NEW_PYTHONPATH=${NEW_PYTHONPATH}:${VO_CMS_SW_DIR}/${SCRAM_ARCH}/external/py2-jinja/%(py2-jinja)s/lib/%(pyBaseVers)s/site-packages/
export NEW_PYTHONPATH=${NEW_PYTHONPATH}:${VO_CMS_SW_DIR}/${SCRAM_ARCH}/external/py2-cx-oracle/%(py2-cx-oracle)s/lib/%(pyBaseVers)s/site-packages/:
export NEW_PYTHONPATH=${NEW_PYTHONPATH}:${VO_CMS_SW_DIR}/${SCRAM_ARCH}/external/py2-pyopenssl/%(py2-pyopenssl)s/lib/%(pyBaseVers)s/site-packages/:
export NEW_PYTHONPATH=${NEW_PYTHONPATH}:${VO_CMS_SW_DIR}/${SCRAM_ARCH}/external/py2-pycurl/%(py2-pycurl)s/lib/%(pyBaseVers)s/site-packages/:
export PYTHONPATH=${NEW_PYTHONPATH}:${PYTHONPATH}

export TNS_ADMIN=/data/secrets/conddb/oracle/admin

        """ % pkgMap

        sf = open(self.topDir+'/setupEnv.sh', 'w')
        sf.write(setupEnv)
        sf.close()

        logging.info('creating setupEnv.sh done')
        return

    def bootstrap(self):
        logging.info('bootstrapping for arch %s tag %s start' % (self.arch, self.cmsCondWebTag) )

        cmd = """
export VO_CMS_SW_DIR=%s
export SCRAM_ARCH=%s
export LANG="C"
export LC_CTYPE="C"

curl -kL -o $VO_CMS_SW_DIR/bootstrap.sh http://cmsrep.cern.ch/cmssw/cms/bootstrap.sh 2>&1 >curlDownload.log

sh -x $VO_CMS_SW_DIR/bootstrap.sh setup -path $VO_CMS_SW_DIR -arch $SCRAM_ARCH >& $VO_CMS_SW_DIR/bootstrap_$SCRAM_ARCH.log
        """ % (self.topDir, self.arch)

        self.doCmd(cmd)

        logging.info('bootstrapping for arch %s tag %s done ' % (self.arch, self.cmsCondWebTag) )
        return

    def install(self):

        self.oldPackages = self.getInstalledPackages()

        if not os.path.exists( os.path.join(self.topDir, self.arch) ):
            self.bootstrap()
            self.createSetupFile()
        else:
            logging.info('found boostrapped area')

        self.installCMSSW()

        self.newPackages = self.getInstalledPackages()

        installedPkgs = [item for item in self.newPackages if item not in self.oldPackages]
        print "installed pkgs: ", installedPkgs

        self.createSetupEnvFile(installedPkgs)

        return

    def installCMSSW(self):

        logging.info('installing for arch %s tag %s start' % (self.arch, self.cmsCondWebTag) )

        cmd = """
export SCRAM_ARCH=%s
export LANG="C"
export LC_CTYPE="C"

cd %s
source ./setup.sh

apt-get update

# apt-cache search cms | grep condweb

apt-get -y install cms+cms-condweb+%s

## # clean out the cache
## apt-get clean
""" % (self.arch, self.topDir, self.cmsCondWebTag)

        self.doCmd(cmd)


        logging.info('installing for arch %s tag %s done ' % (self.arch, self.cmsCondWebTag) )
        return


def main():
    if not os.path.exists('logs'):
        os.makedirs('logs')

    logging.basicConfig(
        filename = 'logs/cmsCondCMSSWInstaller.log',
        format = '[%(asctime)s] %(levelname)s: %(message)s',
        level = logging.DEBUG,
    )

    CondCMSSWInstaller().install()

if __name__ == '__main__':
    main()

