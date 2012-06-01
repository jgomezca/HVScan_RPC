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
import config


defaultDataDirectory = config.rootDirectory
defaultRepositoryBase = '/afs/cern.ch/cms/DB/rep'
defaultServicesRepository = os.path.join(defaultRepositoryBase, 'cmsDbWebServices.git')
defaultLibsRepository = os.path.join(defaultRepositoryBase, 'cmsDbWebLibs.git')
defaultCmsswRepository = os.path.join(defaultRepositoryBase, 'cmssw.git')

# In the rsync format
secretsSource = '/afs/cern.ch/cms/DB/conddb/internal/webServices/secrets'

utilitiesDirectory = '/afs/cern.ch/cms/DB/utilities'
utilitiesPythonPackages = os.path.join(utilitiesDirectory, 'python-packages')


import sys
import pwd
import grp
import socket
import subprocess
import optparse
import logging
logging.basicConfig(
        format = '[%(asctime)s] %(levelname)s: %(message)s',
        level = logging.INFO
)
logger = logging.getLogger(__name__)


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
		help = 'Forces to deploy if /data exists. It will *remove* cmssw, cmsswNew, docs, libs, secrets and services (without trailing /, i.e. without removing the contents if it is a symlink, e.g. like the docs suggest, developers might have /data/services pointing to ~/scratch0/services for easy development to clone new clean versions of them. However, it will keep logs/, git/, and any other folders. Therefore, this option is used to re-deploy from scratch without removing logs and other files. Also, it can be used to deploy in cases where /data is a mounted device (like in dev/int/pro), so the directory is already there. This option is *not* meant for private development machines: please use git-pull on the individual repositories, as --forced would delete your local repository.'
	)

	parser.add_option('-u', '--update', action = 'store_true',
		dest = 'update',
		default = False,
		help = 'Updates an existing deployment: stops the keeper and the services, rsync\'s the secrets, git fetchs on services/, libs/ and cmssw/, checks out the gitTreeish on services/, checks out the dependencies in libs/ and cmssw/ and starts the keeper (which will start the services). The other options are ignored. This is meant *only* for dev/int/pro.'
	)

	parser.add_option('-d', '--dataDirectory', type = 'str',
		dest = 'dataDirectory',
		default = defaultDataDirectory,
		help = 'The directory where it will be installed. If it is not /data (default), a /data symlink will be created to that location so that CMSSW works properly.'
	)

	parser.add_option('-s', '--servicesRepository', type = 'str',
		dest = 'servicesRepository',
		default = defaultServicesRepository,
		help = 'The path to the Services Git repository.'
	)

	parser.add_option('-l', '--libsRepository', type = 'str',
		dest = 'libsRepository',
		default = defaultLibsRepository,
		help = 'The path to the Libs Git repository.'
	)

	parser.add_option('-c', '--cmsswRepository', type = 'str',
		dest = 'cmsswRepository',
		default = defaultCmsswRepository,
		help = 'The path to the CMSSW Git repository.'
	)

	(options, args) = parser.parse_args()

	if len(args) != 1:
		parser.print_help()
		sys.exit(2)

	return {
		'gitTreeish': args[0],
		'force': options.force,
		'update': options.update,
		'dataDirectory': options.dataDirectory,
		'servicesRepository': options.servicesRepository,
		'libsRepository': options.libsRepository,
		'cmsswRepository': options.cmsswRepository,
		'productionLevel': config.getProductionLevel()
	}


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
	logger.info('Executing: ' + command)
	return check_output(command, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)


def getSecrets():
	'''Gets the secrets.
	'''

	execute('rsync -az ' + secretsSource + ' .')


def generateDocs():
	'''Generates the docs by calling services/docs/generate.py.

	Uses the markdown Python module installed in utilitiesPythonPackages.
	'''

	execute('cd services/docs && PYTHONPATH=' + utilitiesPythonPackages + ' ./generate.py')


def checkRequirementsUpdate(options):
	'''Checks the requirements needed for update().
	'''

	# Test for git
	try:
		execute('git --version')
	except:
		raise Exception('This script requires git.')

	# Test for rsync
	try:
		execute('rsync --version')
	except:
		raise Exception('This script requires rsync.')


def update(options):
	'''Updates an existing instance of the CMS DB Web Services:
		- Stops the keeper and the services.
		- Gets the secrets.
		- Git fetchs on services/, libs/ and cmssw/.
		- Checks out the gitTreeish on services/.
		- Checks out the dependencies in libs/ and cmssw/.
		- Regenerates the docs.
		- Starts the keeper (which will start the services).
	'''

	# Check requirements
	checkRequirementsUpdate(options)

	# Chdir to the dataDirectory
	logger.info('Working directory: ' + options['dataDirectory'])
	os.chdir(options['dataDirectory'])

	# Stop the keeper and the services
	execute('services/keeper/keeper.py stop keeper')
	execute('services/keeper/keeper.py stop all')

	# Get the secrets
	getSecrets()

	# Git fetch on services/, libs/ and cmssw/
	execute('cd services && git fetch')
	execute('cd libs && git fetch')
	execute('cd cmssw && git fetch')

	# Check out the treeish on services/
	execute('cd services && git checkout -q ' + options['gitTreeish'])

	# Get the dependencies' tags
	cmsDbWebLibsTag = open('services/dependencies/cmsDbWebLibs.tag').read().strip()
	cmsswTag = open('services/dependencies/cmssw.tag').read().strip()
	logger.info('Dependency: cmsDbWebLibs ' + cmsDbWebLibsTag)
	logger.info('Dependency: cmssw ' + cmsswTag)

	# Checkout the tags
	execute('cd libs && git checkout -q ' + cmsDbWebLibsTag)
	execute('cd cmssw && git checkout -q ' + cmsswTag)

	# Regenerate the docs
	generateDocs()

	# Start the keeper
	execute('services/keeper/keeper.py start keeper')


def checkRequirementsDeploy(options):
	'''Checks the requirements needed for deploy().
	'''

	# Test for sudo privileges
	try:
		execute('sudo mkdir --version')
	except:
		raise Exception('This script requires sudo privileges for deployment.')

	# Test for git
	try:
		execute('git --version')
	except:
		raise Exception('This script requires git.')

	# Test for rsync
	try:
		execute('rsync --version')
	except:
		raise Exception('This script requires rsync.')

	# Check whether there is an existing deployment
	if options['force']:
		# We are forced, so dataDirectory should exist beforehand.
		# Otherwise, the user should ask for a normal deployment.
		# (it works, but the user should know why he is using --force).
		if not os.path.exists(options['dataDirectory']):
			raise Exception(options['dataDirectory'] + ' does not exist. Please re-check what is happening. If you just want to do a new deployment, please do not specify the --forced option.')

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
				raise Exception(defaultDataDirectory + ' does not exist. Please re-check what is happening. If you just want to do a new deployment, please do not specify the --forced option.')

			if not os.path.islink(defaultDataDirectory) or not os.path.isdir(defaultDataDirectory):
				raise Exception(defaultDataDirectory + ' exists, but is not a symlink to a directory. In order to re-deploy, this script needs to set up ' + defaultDataDirectory + ' as a symlink to ' + options['dataDirectory'] + '. Please re-check what is happening. If you have an existing deployment on ' + defaultDataDirectory + ' and just want to re-deploy there, do not specify the --dataDirectory option.')
	else:
		# Not forced, so we check that there is no symlink
		# nor real data directory (if the dataDirectory is the default,
		# this check would be the same).
		if os.path.exists(defaultDataDirectory):
			raise Exception(defaultDataDirectory + ' exists. Please remove the existing deployment or read the documentation on --forced.')

		if os.path.exists(options['dataDirectory']):
			raise Exception(options['dataDirectory'] + ' exists. Please remove the existing deployment or read the documentation on --forced.')


def deploy(options):
	'''Deploys a new instance of the CMS DB Web Services:
		- Creates the required /data file structure.
		- Clones the Services, Libs and CMSSW repositories.
		- Checks out the given treeish for them.
		- Sets the proper ownership for the files.
		- Generates the docs.
	'''

	# Check requirements
	checkRequirementsDeploy(options)

	# Create the dataDirectory if it does not exist and chdir to it
	execute('sudo mkdir -p ' + options['dataDirectory'])
	logger.info('Working directory: ' + options['dataDirectory'])
	os.chdir(options['dataDirectory'])

	# Change ownership and file mode bits
	userName = pwd.getpwuid(os.getuid())[0]
	groupName = grp.getgrgid(os.getgid())[0]
	execute('sudo chown -R ' + userName + ':' + groupName + ' .')
	execute('sudo chmod g-w,o-rwx .')

	# Remove folders if forced
	if options['force']:
		# Careful: Do not add trailing / in these folders
		# Otherwise, if one of them is a symlink you would remove
		# its contents (e.g. like the docs suggest, developers might
		# have /data/services pointing to ~/scratch0/services
		# for easy development).
		execute('rm -rf cmssw cmsswNew libs secrets services')

	# Create the logs folder if it does not exist and subdirectories
	execute('mkdir -p logs')
	for service in config.servicesConfiguration:
		(head, tail) = os.path.split(service)
		if head != '':
			execute('mkdir -p ' + os.path.join('logs', head))

	# Get the secrets
	getSecrets()

	# Create symlink if /data is not the dataDirectory
	if options['dataDirectory'] != defaultDataDirectory:
		# Remove the old symlink if forced
		if options['force']:
			execute('sudo rm ' + defaultDataDirectory)
		execute('sudo ln -s ' + options['dataDirectory'] + ' ' + defaultDataDirectory)

	# Clone services and checkout the treeish
	execute('git clone -q ' + options['servicesRepository'] + ' services')
	execute('cd services && git checkout -q ' + options['gitTreeish'])

	# Get the dependencies' tags
	cmsDbWebLibsTag = open('services/dependencies/cmsDbWebLibs.tag').read()
	cmsswTag = open('services/dependencies/cmssw.tag').read()
	logger.info('Dependency: cmsDbWebLibs ' + cmsDbWebLibsTag)
	logger.info('Dependency: cmssw ' + cmsswTag)

	# Clone libs and checkout the tag
	execute('git clone -q ' + options['libsRepository'] + ' libs')
	execute('cd libs && git checkout -q ' + cmsDbWebLibsTag)

	# Clone cmsswNew and checkout the tag
	execute('git clone -q ' + options['cmsswRepository'] + ' cmssw')
	execute('cd cmssw && git checkout -q ' + cmsswTag)

	# Give everything proper ownership if we are in dev/int/pro
	# FIXME: We should use a cmsdbweb account & group
	#if options['productionLevel'] != 'private':
	#	execute('sudo chown -R andreasp:cmscdadm .')

	# FIXME: Create symlink cmsswNew -> cmssw
	execute('ln -s cmssw cmsswNew')

	# Generate docs
	generateDocs()

	logger.info('Deployment successful.')


def main():
	try:
		options = getOptions()
		if options['update']:
			update(options)
		else:
			deploy(options)
	except Exception as e:
		logger.error(e)
		sys.exit(1)


if __name__ == '__main__':
	main()

