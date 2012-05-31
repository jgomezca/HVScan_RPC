#!/usr/bin/env python
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
logsDirectory = os.path.join(rootDirectory, 'logs')
cmsswDirectory = os.path.join(rootDirectory, 'cmsswNew')
cmsswSetupEnvScript = os.path.join(cmsswDirectory, 'setupEnv.sh')

logsFileTemplate = os.path.join(logsDirectory, '%s.log')
logsSize = '10M' # rotatelogs' syntax


timeBetweenChecks = 30 # seconds


startedServiceEmailAddresses = ['cms-cond-dev@cern.ch']


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
	#    filename:      the (relative) path to the main Python script
	#    listeningPort: the port the server will listen to

	'docs': {
		'filename':       'docs.py',
		'listeningPort':  8089,
	},

	'getLumi': {
		'filename':       'lumidb_server.py',
		'listeningPort':  8086,
	},

	'gtList': {
		'filename':       'GTServerStarter.py',
		'listeningPort':  8081,
	},

	'popcon': {
		'filename':       'popconBackend.py',
		'listeningPort':  8082,
	},

	'regressionTest': {
		'filename':       'webApp.py',
		'listeningPort':  8083,
	},

}

