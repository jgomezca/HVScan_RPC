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


import config
defaultDataDirectory = config.rootDirectory


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


def getSecrets():
	'''Gets the secrets and the host certificate.
	'''

	execute('rsync -az %s . ' % config.secretsSource)

	if config.getProductionLevel() == 'private':
		# In a private machine (e.g. VM), copy the localhost
		# certificates installed by the mod_ssl package
		execute('sudo rsync -a %s secrets/hostcert.pem' % config.hostCertificateFiles['private']['crt'])
		execute('sudo rsync -a %s secrets/hostkey.pem'  % config.hostCertificateFiles['private']['key'])
	else:
		# In dev/int/pro, copy the grid-security certificates
		execute('sudo rsync -a %s secrets/hostcert.pem' % config.hostCertificateFiles['devintpro']['crt'])
		execute('sudo rsync -a %s secrets/hostkey.pem'  % config.hostCertificateFiles['devintpro']['key'])

	# Ensure that ownership and file mode bits are strict for secrets
	# First change the bits so that no one from the new group (e.g. zh)
	# can read the secrets between both commands (in any case the services
	# should not be deployed in machines open for ssh to many people...)
	userName = pwd.getpwuid(os.getuid())[0]
	groupName = grp.getgrgid(os.getgid())[0]
	execute('sudo chmod -R go-rwx secrets')
	execute('sudo chown -R ' + userName + ':' + groupName + ' secrets')


def getDependencyTag(dependency):
	'''Gets a dependency tag of cmsDbWebServices.
	'''

	tag = open('services/dependencies/%s.tag' % dependency).read().strip()
	logging.info('Dependency: %s %s' % (dependency, tag))
	return tag


def generateDocs():
	'''Generates the docs by calling services/docs/generate.py.

	Uses the markdown Python module installed in utilitiesPythonPackages.
	'''

	execute('cd services/docs && ./generate.py')


def configureApache():
	'''Generates the Apache configuration by calling services/keeper/makeApacheConfiguration.py,
	asks for a 'graceful' restart to Apache and sets SELinux's httpd_can_network_connect to 'on'.
	'''

	# FIXME: For the moment, only meant for private machines.
	if config.getProductionLevel() != 'private':
		return

	# Generate Apache configuration
	execute('sudo services/keeper/makeApacheConfiguration.py httpd -f private')
	execute('sudo services/keeper/makeApacheConfiguration.py vhosts -f private')

	# Disable unneeded .conf files
	execute('ls /etc/httpd/conf.d/*.conf | grep -E \'fcgid|nagios|proxy_ajp|welcome|mod_dnssd\' | xargs -n1 -Ifile sudo mv file file.original')

	# Disable AddType directives in ssl.conf to avoid using mod_mime
	execute('sudo sed -i \'s/^AddType/#AddType/g\' /etc/httpd/conf.d/ssl.conf')

	# Set required SELinux policies
	execute('sudo /usr/sbin/setsebool -P httpd_can_network_connect on')

	# Restart gracefully
	execute('sudo /etc/init.d/httpd graceful')


def openPort(port):
	'''Open a port in iptables. Returns True if the table was modified.
	'''

	# Try to find the rule in iptables
	try:
		execute('sudo /sbin/iptables -L -n | grep -F \'state NEW tcp dpt:%s\' | grep -F ACCEPT' % port)
	except:
		# Ask the user whether it should be opened
		logging.warning('The port %s does not *seem* open.' % port)
		command = 'sudo /sbin/iptables -I INPUT -p tcp -m state --state NEW -m tcp --dport %s -j ACCEPT' % port
		answer = raw_input('\nWould you like to run:\n\n    %s\n\nto insert the rule in the top of the INPUT chain? [y/N] ' % command)
		if answer == 'y':
			execute(command)

			return True


def updateIptables():
	'''Updates iptables and saves the results.
	
	Only meant for private machines.
	'''

	# Only meant for private machines. We do not want to mess around with
	# the quattor / NCM rules in vocms*.
	if config.getProductionLevel() != 'private':
		return

	ports = [80, 443]

	if any([openPort(port) for port in ports]):
		# Ask the user whether we should save the new table
		command = 'sudo /sbin/service iptables save'
		answer = raw_input('\nAs the current iptables changed, would you like to run:\n\n    %s\n\nto save them? (note: this *replaces* the current /etc/sysconfig/iptables with the current table) [y/N] ' % command)
		if answer == 'y':
			execute(command)


def checkPackage(package):
	'''Checks whether a package is installed. If not, gives the option
	to the user to install it.
	'''

	try:
		execute('rpm -qi %s' % package)
	except Exception as e:
		logging.warning('Package %s is not installed.' % package)
		text = raw_input('Would you like to install it? [y/N] ')
		if text != 'y':
			raise e
		execute('sudo yum -y install %s 1>&2' % package)


def checkRequirements(options):
	'''Checks the requirements needed for deploy().
	'''

	# Test the script is not being run as root
	if os.geteuid() == 0:
		raise Exception('This script should not be run as root.')

	# Test for sudo privileges
	try:
		execute('sudo mkdir --version')
	except:
		raise Exception('This script requires sudo privileges for deployment.')

	# Test for git
	try:
		checkPackage('git')
		execute('git --version')
	except:
		raise Exception('This script requires git.')

	# Test for rsync
	try:
		checkPackage('rsync')
		execute('rsync --version')
	except:
		raise Exception('This script requires rsync.')

	# Test for rotatelogs (httpd package)
	try:
		checkPackage('httpd')
		try:
			execute('echo "" | /usr/sbin/rotatelogs /tmp/rotatelogstest 10M')
		except subprocess.CalledProcessError:
			pass
	except:
		raise Exception('This script requires rotatelogs (httpd package).')

	# Test for the host certificate
	level = 'devintpro'
	if config.getProductionLevel() == 'private':
		level = 'private'
		try:
			checkPackage('mod_ssl')
		except:
			raise Exception('This script requires mod_ssl to be installed (in private machines, the host certificate is taken from mod_ssl.')
	try:
		execute('test -f %s' % config.hostCertificateFiles[level]['crt'])
		execute('test -f %s' % config.hostCertificateFiles[level]['key'])
	except:
		raise Exception('This script requires the host certificate to be installed: %s and %s must exist.' % (config.hostCertificateFiles[level]['crt'], config.hostCertificateFiles[level]['key']))

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

	# Create the dataDirectory if it does not exist
	execute('sudo mkdir -p ' + options['dataDirectory'])

	# Change its ownership and file mode bits
	userName = pwd.getpwuid(os.getuid())[0]
	groupName = grp.getgrgid(os.getgid())[0]
	execute('sudo chown -R %s:%s %s' % (userName, groupName, options['dataDirectory']))
	execute('sudo chmod g-w,o-rwx %s' % options['dataDirectory'])

	# Chdir to it
	logging.info('Working directory: ' + options['dataDirectory'])
	os.chdir(options['dataDirectory'])

	# Stop the keeper and then all the services if updating
	if options['update']:
		execute('services/keeper/keeper.py stop keeper')
		execute('services/keeper/keeper.py jobs disable all')
		execute('services/keeper/keeper.py stop all')

	# Remove folders if forced
	if options['force']:
		# Careful: Do not add trailing / in these folders
		# Otherwise, if one of them is a symlink you would remove
		# its contents (e.g. like the docs suggest, developers might
		# have /data/services pointing to ~/scratch0/services
		# for easy development).
		execute('rm -rf secrets services libs utilities cmssw cmsswNew')

	# Create the logs and jobs folders if they do not exist and their subdirectories
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

	# Get the secrets
	getSecrets()

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

	# Clone cmsswNew and checkout the tag
	execute('git clone -q ' + options['cmsswRepository'] + ' cmssw')
	execute('cd cmssw && git checkout -q %s' % getDependencyTag('cmssw'))

	# Give everything proper ownership if we are in dev/int/pro
	# FIXME: We should use a cmsdbweb account & group
	#if options['productionLevel'] != 'private':
	#	execute('sudo chown -R andreasp:cmscdadm .')

	# FIXME: Create symlink cmsswNew -> cmssw
	execute('ln -s cmssw cmsswNew')

	# Generate docs
	generateDocs()

	# Configure Apache frontend(s)
	configureApache()

	# Update iptables
	updateIptables()

	# Start all the services and then the keeper if updating
	if options['update']:
		keeperStartOptions = ''
		if not options['sendEmail']:
			keeperStartOptions = '--nosendEmail'
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

