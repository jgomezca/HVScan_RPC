'''Configuration for the keeper of the CMS' DB Web services.
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = ['Miguel Ojeda']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


import os
import socket


rootDirectory = '/data'
servicesDirectory = os.path.join(rootDirectory, 'services')
secretsDirectory = os.path.join(rootDirectory, 'secrets')
utilitiesDirectory = os.path.join(rootDirectory, 'utilities')
logsDirectory = os.path.join(rootDirectory, 'logs')
jobsDirectory = os.path.join(rootDirectory, 'jobs')
cmsswDirectory = os.path.join(rootDirectory, 'cmsswNew')
cmsswSetupEnvScript = os.path.join(cmsswDirectory, 'setupEnv.sh')

logsFileTemplate = os.path.join(logsDirectory, '%s', 'log')
logsSize = '10M' # rotatelogs' syntax
logsJobFileTemplate = os.path.join(logsDirectory, '%s', '%s', 'log')

jobsFileTemplate = os.path.join(jobsDirectory, '%s')
crontabFile = os.path.join(jobsDirectory, 'crontab')

repositoryBase = '/afs/cern.ch/cms/DB/rep'
servicesRepository = os.path.join(repositoryBase, 'cmsDbWebServices.git')
libsRepository = os.path.join(repositoryBase, 'cmsDbWebLibs.git')
utilitiesRepository = os.path.join(repositoryBase, 'cmsDbWebUtilities.git')
cmsswRepository = os.path.join(repositoryBase, 'cmssw.git')

# In the rsync format
secretsSource = '/afs/cern.ch/cms/DB/conddb/internal/webServices/secrets'


timeBetweenChecks = 30 # seconds

# Our mailing list
_mailingList = 'cms-cond-dev@cern.ch'


# Emails
jobsEmailAddress = _mailingList
startedServiceEmailAddresses = [_mailingList]


# For deployments in -dev/-int/-prod
officialUserName = 'cmscdadm'
officialGroupName = 'cmscdadm'


# Used by deploy.py to add a rule in iptables' INPUT chain in private VMs.
listeningPortsRange = (8080, 8099)


# Maximum number of caches
maxCaches = 16

# Available cache global size in bytes (at the moment this is just the maximum
# memory that we tell Redis to use, so the actual cache size is probably lower)
cacheSize = 2 * 1024 * 1024 * 1024


hostCertificateFiles = {
	'private': {
		'crt': '/etc/pki/tls/certs/localhost.crt',
		'key': '/etc/pki/tls/private/localhost.key',
	},

	'devintpro': {
		'crt': '/etc/grid-security/hostcert.pem',
		'key': '/etc/grid-security/hostkey.pem',
	},
}


productionLevels = {
	'vocms145.cern.ch': 'dev',
	'vocms146.cern.ch': 'int',
	'vocms148.cern.ch': 'pro',
	'vocms149.cern.ch': 'pro',
}

def getProductionLevel(hostName = None):
	'''Returns the production level given a hostname (or current hostname by default). If the hostname is not found, returns 'private'.
	'''

	if not hostName:
		hostName = socket.gethostname()

	level = 'private'
	try:
		level = productionLevels[hostName]
	except:
		pass

	return level


servicesConfiguration = {
	# The key of each entry must be the same as the directory name
	# in services/, which, in turn, is the same as the URL/vHost.
	#
	# The parameters for each service are:
	#
	#    filename       The (relative) path to the main Python script.
	#
	#    listeningPort  The port the server will listen to
	#                   (please keep them within the listeningPortsRange
	#                   or update the range if needed).
	#
	#    hidden         The service will not show up in public lists
	#                   (e.g. in the docs/index.html list).
	#
	#    jobs           List of jobs to run periodically.
	#
	#                   Optional, default: [].
	#
	#                   Each job must a tuple (when, filename):
	#                     * when is a string in the crontab format
	#                     * filename is the name of the Python script to run
	#                       which must be inside the service's folder.
	#
	#                   The jobs are run the same way as the services:
	#                     * With the same environment.
	#                     * Without AFS tokens.
	#                     * With arguments passed by the keeper.
	#                       which means the job can import service,
	#                       import secrets, etc.
	#
	#                   The output (both stdout and stderr) from each run
	#                   of each job is saved in:
	#                       /data/logs/service/job/log.timestamp
	#
	#    caches         List of caches (names) the service will use.
	#
	#                   Optional, default: [].
	#
	#                   Each cache is accessible by the service as
	#                   the cache.name instance of the cache.Cache class.

	'admin': {
		'filename':       'admin.py',
		'listeningPort':  8092,
		'hidden':         False,
	},

	'docs': {
		'filename':       'docs.py',
		'listeningPort':  8089,
		'hidden':         False,
	},

	'dropBox': {
		'filename':       'server.py',
		'listeningPort':  8095,
		'hidden':         False,
	},

	#'dropBoxBE': {
	#	'filename':       'server.py',
	#	'listeningPort':  8096,
	#	'hidden':         True,
	#},

	#'emails': {
	#	'filename':       'emails.py',
	#	'listeningPort':  8097,
	#	'hidden':         True,
	#},

	'getLumi': {
		'filename':       'lumidb_server.py',
		'listeningPort':  8086,
		'hidden':         False,
	},

	'gtc': {
		'filename':       'gtc.py',
		'listeningPort':  8093,
		'hidden':         False,
		'jobs':           [
			('*/20 * * * *', 'global_update.py'),
		],
	},

	'gtList': {
		'filename':       'GTServerStarter.py',
		'listeningPort':  8081,
		'hidden':         False,
		'caches':         ['gts'],
	},

	'libs': {
		'filename':       'libs.py',
		'listeningPort':  8094,
		'hidden':         True,
	},

	'logs': {
		'filename':       'logs.py',
		'listeningPort':  8097,
		'hidden':         False,
		'caches':         ['logs'],
	},

	'payloadInspector': {
		'filename':       'PayloadInspector_backend.py',
		'listeningPort':  8087,
		'hidden':         False,
		'jobs':           [
			('*/20 * * * *', 'BuildTableFiles.py'),
		],
	},

	'PdmV/valdb': {
		'filename':       'ajax_app.py',
		'listeningPort':  8080,
		'hidden':         False,
	},

	'popcon': {
		'filename':       'popconBackend.py',
		'listeningPort':  8082,
		'hidden':         False,
	},

	'recordsProvider': {
		'filename':       'Server.py',
		'listeningPort':  8088,
		'hidden':         False,
	},

	'regressionTest': {
		'filename':       'webApp.py',
		'listeningPort':  8083,
		'hidden':         False,
	},

	'shibbolethTest': {
		'filename':       'shibbolethTest.py',
		'listeningPort':  8090,
		'hidden':         True,
	},

}


# Replace 'caches' lists with a mapping to globally unique IDs
nextFreeCacheID = 0
for service in sorted(servicesConfiguration):
	servicesConfiguration[service].setdefault('caches', [])
	caches = {}
	for cache in servicesConfiguration[service]['caches']:
		caches[cache] = nextFreeCacheID
		nextFreeCacheID += 1
	servicesConfiguration[service]['caches'] = caches


def checkCacheID(service, cacheID):
	'''Checks whether a cache ID is valid for a given service.
	'''

	for (cache, thisCacheID) in servicesConfiguration[service]['caches'].items():
		if cacheID == thisCacheID:
			return

	raise Exception('Invalid cache ID %s for service %s.' % (cacheID, service))


def getCacheID(service, cache):
	'''Returns the cache ID of a given cache of a service.
	'''

	try:
		return servicesConfiguration[service]['caches'][cache]
	except KeyError:
		raise Exception('Invalid cache name %s for service %s.' % (cache, service))


def getCacheByID(cacheID):
	'''Returns the cache by its ID (i.e. reverse mapping).
	'''

	for service in servicesConfiguration:
		for (cache, thisCacheID) in servicesConfiguration[service]['caches'].items():
			if cacheID == thisCacheID:
				return cache

	raise Exception('Cache ID not found in any service.')


def getServicesList(showHiddenServices = False):
	'''Returns a sorted list of the services' names.
	'''

	services = list(servicesConfiguration)

	if not showHiddenServices:
		services = [service for service in services if not servicesConfiguration[service]['hidden']]

	return sorted(services, key = str.lower)

