#!/usr/bin/env python2.6
'''Deployment script for CMS DB Web Services.
Can be used to deploy to dev/int/pro as well as private machines (e.g. VMs).
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = ['Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


import os
import sys
import pwd
import grp
import subprocess
import optparse
import logging
import platform


import config
defaultDataDirectory = config.rootDirectory


onOSX = platform.system() == 'Darwin'


def getOptions():
    '''Parses the arguments from the command line.
    '''

    parser = optparse.OptionParser(usage =
        'Usage: %prog [options] <gitTreeish>\n'
        '\n'
        'Examples:\n'
        '  %prog HEAD\n'
        '  %prog v1.0\n'
        '  %prog 1c002d'
    )

    parser.add_option('-f', '--force', action = 'store_true',
        dest = 'force',
        default = False,
        help = 'Forces to deploy if /data exists. It will *remove* cmssw, cmsswNew, docs, libs, secrets and services (without trailing /, i.e. without removing the contents if it is a symlink, e.g. like the docs suggest, developers might have /data/services pointing to ~/scratch0/services for easy development to clone new clean versions of them. However, it will keep logs/, git/, and any other folders. Therefore, this option is used to re-deploy from scratch without removing logs and other files. Also, it can be used to deploy in cases where /data is a mounted device (like in dev/int/pro), so the directory is already there. This option is *not* meant for private development machines: please use git-fetch on the individual repositories, as --force would delete your local repository. Default: %default'
    )

    parser.add_option('-u', '--update', action = 'store_true',
        dest = 'update',
        default = False,
        help = 'Updates an existing deployment (i.e. with services running): after checking the requirements, but before deploying, stop the keeper and then all the services. Later, after deployment, start the services and then the keeper. Default: %default'
    )

    parser.add_option('--noApache', action = 'store_false',
        dest = 'apache',
        default = True,
        help = 'Disables writing Apache configuration. Intended for OS X, to prevent overwriting your configuration -- but if you are not using the Apache for something else, go ahead and use it. Default: %default'
    )

    parser.add_option('-n', '--nosendEmail', action = 'store_false',
        dest = 'sendEmail',
        default = True,
        help = 'Disables sending emails when starting the services after on --update. Default: %default'
    )

    parser.add_option('-l', '--linkServicesRepository', action = 'store_true',
        dest = 'linkServicesRepository',
        default = False,
        help = 'Instead of cloning the Services Git repository, create a symbolic link to it. This is intended to be used in private deployments where you want a symbolic link to your repository in AFS, e.g. /data/services to ~/scratch0/services. Note: git checkout is still executed. Default: %default'
    )

    parser.add_option('-d', '--dataDirectory', type = 'str',
        dest = 'dataDirectory',
        default = defaultDataDirectory,
        help = 'The directory where it will be installed. If it is not /data (default), a /data symlink will be created to that location so that CMSSW works properly. Default: %default'
    )

    parser.add_option('-s', '--servicesRepository', type = 'str',
        dest = 'servicesRepository',
        default = config.servicesRepository,
        help = 'The path to the Services Git repository. Default: %default'
    )

    parser.add_option('-L', '--libsRepository', type = 'str',
        dest = 'libsRepository',
        default = config.libsRepository,
        help = 'The path to the Libs Git repository. Default: %default'
    )

    parser.add_option('-U', '--utilitiesRepository', type = 'str',
        dest = 'utilitiesRepository',
        default = config.utilitiesRepository,
        help = 'The path to the Utilities Git repository. Default: %default'
    )

    parser.add_option('-c', '--cmsswRepository', type = 'str',
        dest = 'cmsswRepository',
        default = config.cmsswRepository,
        help = 'The path to the CMSSW Git repository. Default: %default'
    )

    (options, args) = parser.parse_args()

    if len(args) != 1:
        parser.print_help()
        sys.exit(2)

    options = vars(options)
    options['gitTreeish'] = args[0]
    options['productionLevel'] = config.getProductionLevel()
    return options


def check_output(*popenargs, **kwargs):
    '''Mimics subprocess.check_output() in Python 2.6
    '''

    process = subprocess.Popen(*popenargs, **kwargs)
    stdout = process.communicate()
    returnCode = process.returncode
    cmd = kwargs.get("args")
    if cmd is None:
        cmd = popenargs[0]
    if returnCode:
        raise subprocess.CalledProcessError(returnCode, cmd)
    return stdout


def execute(command):
    '''Executes a command in a shell:
        - Allowing input
        - Without redirecting stderr
        - Raises an exception if it returns with a non-zero exit code
        - Returns the stdout
    '''

    # Don't redirect stderr: That way we can see the error
    # if the command does not finish correctly
    logging.info('Executing: ' + command)
    return check_output(command, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)


def tryExecute(command):
    '''Tries to execute a command, printing a warning if there is an error.
    '''

    try:
        execute(command)
    except Exception as e:
        logging.warning('Exception %s: %s', str(type(e)), e)


def getDependencyTag(dependency):
    '''Gets a dependency tag of cmsDbWebServices.
    '''

    tag = open('services/dependencies/%s.tag' % dependency).read().strip()
    logging.info('Dependency: %s %s', dependency, tag)
    return tag


def configureApache():
    '''Generates the Apache configuration by calling services/keeper/makeApacheConfiguration.py,
    asks for a 'graceful' restart to Apache and sets SELinux's httpd_can_network_connect to 'on'.
    '''

    # Only meant for private machines. In official deployments the fabfile
    # takes care of updating Apache in the frontend.
    if config.getProductionLevel() != 'private':
        return

    # Generate Apache configuration
    if onOSX:
        execute('chown %s:%s %s' % (config.httpdUser, config.httpdGroup, config.httpdConfigFile))
        execute('mkdir -p %s %s %s %s %s' % (config.httpdServerRoot, config.httpdDocumentRoot, config.httpdIncludeDirectory, os.path.join(config.httpdServerRoot, 'run'), os.path.join(config.httpdServerRoot, 'logs')))
        execute('services/keeper/makeApacheConfiguration.py httpd -f private')
        execute('services/keeper/makeApacheConfiguration.py vhosts -f private')
    else:
        execute('sudo services/keeper/makeApacheConfiguration.py httpd -f private')
        execute('sudo services/keeper/makeApacheConfiguration.py vhosts -f private')

    # Set required SELinux policies
    if not onOSX:
        execute('sudo /usr/sbin/setsebool -P httpd_can_network_connect on')

    # Restart gracefully
    if onOSX:
        execute('sudo apachectl graceful')
    else:
        execute('sudo /etc/init.d/httpd graceful')


def configureRedis():
    '''Generates the Redis configuration.
    '''

    # Only meant for private machines. In official deployments the fabfile
    # takes care of updating Redis in the backend.
    if config.getProductionLevel() != 'private':
        return

    # Generate Redis configuration
    if not onOSX:
        execute('sudo services/keeper/makeRedisConfiguration.py')

    # Restart
    if onOSX:
        execute('sudo services/keeper/manageRedis.py restart')
    else:
        execute('sudo /etc/init.d/redis restart')


def openPort(port):
    '''Open a port in iptables. Returns True if the table was modified.
    '''

    # Try to find the rule in iptables
    try:
        execute('sudo /sbin/iptables -L -n | grep -F \'state NEW tcp dpt:%s\' | grep -F ACCEPT' % port)
    except:
        # Ask the user whether it should be opened
        logging.warning('The port %s does not *seem* open.', port)
        command = 'sudo /sbin/iptables -I INPUT -p tcp -m state --state NEW -m tcp --dport %s -j ACCEPT' % port
        answer = raw_input('\nWould you like to run:\n\n    %s\n\nto insert the rule in the top of the INPUT chain? [y/N] ' % command)
        if answer == 'y':
            execute(command)

            return True


def updateIptables():
    '''Updates iptables and saves the results.
    
    Only meant for Linux private machines.
    '''

    # Only meant for private machines. We do not want to mess around with
    # the quattor / NCM rules in vocms*.
    if config.getProductionLevel() != 'private':
        return

    # No iptables in OS X, intended for local development
    # (for the moment at least)
    if onOSX:
        return

    ports = [80, 443]

    if any([openPort(port) for port in ports]):
        # Ask the user whether we should save the new table
        command = 'sudo /sbin/service iptables save'
        answer = raw_input('\nAs the current iptables changed, would you like to run:\n\n    %s\n\nto save them? (note: this *replaces* the current /etc/sysconfig/iptables with the current table) [y/N] ' % command)
        if answer == 'y':
            execute(command)


def checkPackage(package, testCommand = None):
    '''Checks whether a package is installed. If not, gives the option
    to the user to install it.
    '''

    logging.info('Checking package: %s', package)

    # If we have a way to test the command, try it first
    # This avoids running rpm -qi on other platforms like OS X
    if testCommand is not None:
        try:
            execute(testCommand)
            return
        except:
            if onOSX:
                raise Exception('Package %s is not installed, but you are deploying on OS X; therefore, you will need to manually install it.' % package)
            pass

    try:
        try:
            execute('rpm -qi %s' % package)
        except Exception as e:
            logging.warning('Package %s is not installed.', package)
            text = raw_input('Would you like to install it? [y/N] ')
            if text != 'y':
                raise e
            execute('sudo yum -y install %s 1>&2' % package)

        if testCommand is not None:
            execute(testCommand)
    except:
        raise Exception('This script requires %s.' % package)


def checkFile(path, checkReadAccess = False):
    '''Checks whether a file exists and is a regular file. Optionally, also
    checks whether the file can be open for read access.
    '''

    logging.info('Checking file: %s', path)

    if not os.path.exists(path):
        raise Exception('This script requires that the %s file exists.' % path)

    if not os.path.isfile(path):
        raise Exception('This script requires that %s is a regular file.' % path)

    if checkReadAccess:
        try:
            with open(path, 'r') as f:
                pass
        except:
            raise Exception('This script requires read access to %s.' % path)


def checkRequirements(options):
    '''Checks the requirements needed for deploy().
    '''

    # Test the script is not being run with root capabilities in a private deployment
    # and test that the script is being run with root capabilities in official deployments
    # (i.e. because we need to setuid() later on).
    if config.getProductionLevel() == 'private':
        if os.geteuid() == 0:
            raise Exception('This script should not be run with root capabilities in private deployments.')
    else:
        if os.geteuid() != 0:
            raise Exception('This script should be run with root capabilities in official deployments.')

    # Test for sudo privileges
    try:
        execute('sudo echo ""')
    except:
        raise Exception('This script requires sudo privileges for deployment.')

    # Test for packages
    checkPackage('git', 'git --version')
    checkPackage('rsync', 'rsync --version')
    checkPackage('redis', 'redis-cli -v')

    # httpd and mod_ssl are required for private deployments
    # (i.e. in order to set up the private frontend)
    if config.getProductionLevel() == 'private':
        checkPackage('httpd', '/usr/sbin/httpd -v')
        if not onOSX:
            checkPackage('mod_ssl')

    # Test for rotatelogs (httpd package)
    try:
        try:
            execute('echo "" | /usr/sbin/rotatelogs /tmp/rotatelogstest 10M')
        except subprocess.CalledProcessError:
            pass
    except:
        raise Exception('This script requires rotatelogs (httpd package).')

    # Test for the secrets
    checkFile(os.path.join(config.secretsSource, 'secrets.py'), checkReadAccess = True)

    # Test for the host certificate
    level = 'devintpro'
    if config.getProductionLevel() == 'private':
        level = 'private'

    if onOSX and options['apache']:
        text = raw_input('You are deploying on OS X but you did not ask to disable overwriting the Apache configuration (which is the default). Since maybe you are using Apache for something else in your Mac, would you like to continue? [y/N] ')
        if 'y' != text:
            raise Exception('Stopped on request of the user.')

    if options['apache']:
        checkFile(config.hostCertificateFiles[level]['crt'])
        checkFile(config.hostCertificateFiles[level]['key'])

    # Check whether there is an existing deployment
    if options['force']:
        # We are forced, so dataDirectory should exist beforehand.
        # Otherwise, the user should ask for a normal deployment.
        # (it works, but the user should know why he is using --force).
        if not os.path.exists(options['dataDirectory']):
            raise Exception(options['dataDirectory'] + ' does not exist. Please re-check what is happening. If you just want to do a new deployment, please do not specify the --force option.')

        if options['dataDirectory'] == defaultDataDirectory:
            # We are forced and dataDirectory is the default,
            # so it should be a real folder (i.e. not symlink).
            if os.path.exists(defaultDataDirectory):
                if os.path.islink(defaultDataDirectory) or not os.path.isdir(defaultDataDirectory):
                    raise Exception(defaultDataDirectory + ' exists, but is not a real (i.e. not symlink) directory. Please re-check what is happening. If you have an existing deployment on some other place and ' + defaultDataDirectory + ' is a symlink, please provide the --dataDirectory option.')
        else:
            # We are forced and the dataDirectory is not
            # the default, so the defaultDataDirectory should be
            # a symlink to a directory instead of a real directory,
            # a real file or a symlink to a file.
            if not os.path.exists(defaultDataDirectory):
                raise Exception(defaultDataDirectory + ' does not exist. Please re-check what is happening. If you just want to do a new deployment, please do not specify the --force option.')

            if not os.path.islink(defaultDataDirectory) or not os.path.isdir(defaultDataDirectory):
                raise Exception(defaultDataDirectory + ' exists, but is not a symlink to a directory. In order to re-deploy, this script needs to set up ' + defaultDataDirectory + ' as a symlink to ' + options['dataDirectory'] + '. Please re-check what is happening. If you have an existing deployment on ' + defaultDataDirectory + ' and just want to re-deploy there, do not specify the --dataDirectory option.')
    else:
        # Not forced, so we check that there is no symlink
        # nor real data directory (if the dataDirectory is the default,
        # this check would be the same).
        if os.path.exists(defaultDataDirectory):
            raise Exception(defaultDataDirectory + ' exists. Please remove the existing deployment or read the documentation on --force.')

        if os.path.exists(options['dataDirectory']):
            raise Exception(options['dataDirectory'] + ' exists. Please remove the existing deployment or read the documentation on --force.')


def deploy(options):
    '''Deploys a new instance of the CMS DB Web Services:
        - Creates the required /data file structure.
        - Clones the Services, Libs and CMSSW repositories.
        - Checks out the given treeish for them.
        - Sets the proper ownership for the files.
        - Updates iptables.
        - Generates the docs.
    '''

    logging.info('Production level: ' + config.getProductionLevel())

    # Check requirements
    checkRequirements(options)

    # Get the user/group name and ID
    if config.getProductionLevel() == 'private':
        userId = os.getuid()
        groupId = os.getgid()
        userName = pwd.getpwuid(userId)[0]
        groupName = grp.getgrgid(groupId)[0]
    else:
        userName = config.officialUserName
        groupName = config.officialGroupName
        userId = pwd.getpwnam(config.officialUserName)[2]
        groupId = grp.getgrnam(config.officialGroupName)[2]

    # Set a private umask
    os.umask(077)

    # Create the dataDirectory if it does not exist
    execute('sudo mkdir -p ' + options['dataDirectory'])

    # Stop the keeper and then all the services if updating
    if options['update']:
        tryExecute('sudo %s stop keeper' % os.path.join(options['dataDirectory'], 'services/keeper/keeper.py'))
        tryExecute('sudo %s jobs disable all' % os.path.join(options['dataDirectory'], 'services/keeper/keeper.py'))
        tryExecute('sudo %s stop all' % os.path.join(options['dataDirectory'], 'services/keeper/keeper.py'))

    # Remove folders if forced
    if options['force']:
        # Careful: Do not add trailing / in these folders
        # Otherwise, if one of them is a symlink you would remove
        # its contents (e.g. like the docs suggest, developers might
        # have /data/services pointing to ~/scratch0/services
        # for easy development).
        foldersToRemove = ['secrets', 'services', 'libs', 'utilities', 'cmssw', 'cmsswNew']
        foldersToRemove = [os.path.join(options['dataDirectory'], x) for x in foldersToRemove]
        execute('sudo rm -rf %s' % ' '.join(foldersToRemove))

    # Get the secrets, before switching user (i.e. we need AFS tokens)
    if onOSX:
        execute('rsync -az %s %s' % (config.secretsSource, '/tmp/secrets'))
        execute('sudo rsync -az %s %s' % ('/tmp/secrets/.', os.path.join(options['dataDirectory'], '.')))
        execute('sudo rm -rf %s' % '/tmp/secrets')
    else:
        execute('sudo rsync -az %s %s' % (config.secretsSource, os.path.join(options['dataDirectory'], '.')))

    # In a private machine (e.g. VM), copy the certificates installed by the mod_ssl package.
    # In official deployments, copy the grid-security certificates.
    if config.getProductionLevel() == 'private':
        hostCertificateCrt = config.hostCertificateFiles['private']['crt']
        hostCertificateKey = config.hostCertificateFiles['private']['key']
    else:
        hostCertificateCrt = config.hostCertificateFiles['devintpro']['crt']
        hostCertificateKey = config.hostCertificateFiles['devintpro']['key']

    if options['apache']:
        execute('sudo rsync -a %s %s' % (hostCertificateCrt, os.path.join(options['dataDirectory'], 'secrets/hostcert.pem')))
        execute('sudo rsync -a %s %s' % (hostCertificateKey, os.path.join(options['dataDirectory'], 'secrets/hostkey.pem')))

    # Set the proper ownership for everything before switching to the new user and group
    # and restrict file mode bits for everything (this must include the secrets).
    execute('sudo chown -R %s:%s %s' % (userName, groupName, options['dataDirectory']))
    execute('sudo chmod -R go-rwx %s' % options['dataDirectory'])

    # Switch to the proper user. After this, sudo should not be used
    # for any other command and tokens will not be available.
    logging.info('Setting user identity: %s (%s)', userName, userId)
    os.setuid(userId)

    # Chdir to the data directory
    logging.info('Working directory: ' + options['dataDirectory'])
    os.chdir(options['dataDirectory'])

    # Create the logs, jobs and files folders if they do not exist and their subdirectories
    execute('mkdir -p logs/keeper jobs')
    for service in config.servicesConfiguration:
        # logs' subdirectories
        execute('mkdir -p %s' % os.path.join('logs', service))
        for job in config.servicesConfiguration[service].get('jobs', []):
            execute('mkdir -p %s' % os.path.join('logs', service, job[1]))

        # jobs' subdirectories
        (head, tail) = os.path.split(service)
        if head != '':
            execute('mkdir -p %s' % os.path.join('jobs', head))

        # files
        execute('mkdir -p %s' % os.path.join('files', service))

    # Create symlink if /data is not the dataDirectory
    if options['dataDirectory'] != defaultDataDirectory:
        # Remove the old symlink if forced
        if options['force']:
            execute('sudo rm ' + defaultDataDirectory)
        execute('sudo ln -s ' + options['dataDirectory'] + ' ' + defaultDataDirectory)

    # Clone or link services and checkout the treeish
    if options['linkServicesRepository']:
        execute('ln -s %s services' % options['servicesRepository'])
    else:
        execute('git clone -q ' + options['servicesRepository'] + ' services')
    execute('cd services && git checkout -q ' + options['gitTreeish'])

    # Clone libs and checkout the tag
    execute('git clone -q ' + options['libsRepository'] + ' libs')
    execute('cd libs && git checkout -q %s' % getDependencyTag('cmsDbWebLibs'))

    # Clone utilities and checkout the tag
    execute('git clone -q ' + options['utilitiesRepository'] + ' utilities')
    execute('cd utilities && git checkout -q %s' % getDependencyTag('cmsDbWebUtilities'))

    # Install the CMS Conditions CMSSW release
    # FIXME: Only gtc crashes at the moment with cmsCondCMSSWInstaller.py
    #        When we solve the problem, drop the CMSSW repository and use
    #        the script in both platforms.
    if onOSX:
        execute('services/keeper/cmsCondCMSSWInstaller.py --topDir %s' % defaultDataDirectory)
    else:
        # Clone cmsswNew and checkout the tag
        execute('git clone -q ' + options['cmsswRepository'] + ' cmssw')
        execute('cd cmssw && git checkout -q %s' % getDependencyTag('cmssw'))

    # FIXME: Create symlink cmsswNew -> cmssw
    execute('ln -s cmssw cmsswNew')

    # Generate docs
    execute('cd services/docs && ./generate.py')

    # Configure Apache in private machines
    if options['apache']:
        configureApache()

    # Update iptables in private machines
    updateIptables()

    # Configure Redis in private machines
    configureRedis()

    # Flush redis' cache to prevent problems with changes
    # in the format of the stored objects
    execute('redis-cli flushall')
    execute('redis-cli save')

    # Start all the services and then the keeper if updating
    if options['update']:
        keeperStartOptions = '--maxWaitTime 20 '
        if not options['sendEmail']:
            keeperStartOptions += '--nosendEmail'
        execute('services/keeper/keeper.py start %s all' % keeperStartOptions)
        execute('services/keeper/keeper.py jobs enable all')
        execute('services/keeper/keeper.py start %s keeper' % keeperStartOptions)

    logging.info('Deployment successful.')


def main():
    '''Entry point.
    '''

    try:
        deploy(getOptions())
    except Exception as e:
        logging.error(e)
        return -1


if __name__ == '__main__':
    logging.basicConfig(
        format = '[%(asctime)s] %(levelname)s: %(message)s',
        level = logging.INFO,
    )

    sys.exit(main())

