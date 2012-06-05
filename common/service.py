'''Common code for all CMS DB Web services.
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = ['Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


import os
import optparse
import socket
import cherrypy

import secrets


def getCxOracleConnectionString(connectionDictionary):
	'''Returns a connection string for cx_oracle given
	a connection dictionary from the secrets file.
	'''

	return '%s/%s@%s' % (connectionDictionary['user'], connectionDictionary['password'], connectionDictionary['db_name'])


def getSqlAlchemyConnectionString(connectionDictionary):
	'''Returns a connection string for SQL Alchemy given
	a connection dictionary from the secrets file.
	'''

	return 'oracle://%s:%s@%s' % (connectionDictionary['user'], connectionDictionary['password'], connectionDictionary['db_name'])


def getWinServicesSoapBaseUrl(connectionDictionary):
	'''Returns a winservices-soap base URL given a connection dictionary
	from the secrets file.
	'''

	return 'https://%s:%s@winservices-soap.web.cern.ch/winservices-soap/Generic/Authentication.asmx/' % (connectionDictionary['user'], connectionDictionary['password'])


_settings = None
_secrets = None


def getSettings():
	'''Returns the settings for the service passed through the command line.
	'''

	return _settings


def getSecrets():
	'''Returns the secrets of a service.
	'''

	return _secrets


def start(mainObject):
	'''Starts the service.
	'''

	gridSecurityDirectory = os.path.join(getSettings()['secretsDirectory'], 'grid-security')

	cherrypy.config.update({
		'global': {
		'server.socket_host': socket.gethostname(),
		'server.socket_port': getSettings()['listeningPort'],
		'tools.staticdir.root': getSettings()['rootDirectory'],
		'engine.autoreload_on': False,
		'server.ssl_certificate': os.path.join(gridSecurityDirectory, 'hostcert.pem'),
		'server.ssl_private_key': os.path.join(gridSecurityDirectory, 'hostkey.pem'),
		},
	})
	cherrypy.quickstart(mainObject, config = 'server.conf', script_name = '/' + getSettings()['name'])


def _init():
	# Parse the command line options
	parser = optparse.OptionParser()

	parser.add_option('-n', '--name', type = 'str',
		dest = 'name',
		help = 'The name of the service.'
	)

	parser.add_option('-r', '--rootDirectory', type = 'str',
		dest = 'rootDirectory',
		help = 'The root directory for the service.'
	)

	parser.add_option('-s', '--secretsDirectory', type = 'str',
		dest = 'secretsDirectory',
		help = 'The shared secrets directory.'
	)

	parser.add_option('-p', '--listeningPort', type = 'int',
		dest = 'listeningPort',
		help = 'The port this service will listen to.'
	)

	parser.add_option('-l', '--productionLevel', type = 'str',
		dest = 'productionLevel',
		help = 'The production level this service should run as, which can be one of the following: "dev" == Development, "int" == Integration, "pro" == Production. For instance, the service should use this parameter to decide to which database connect, to which mailing list should send emails, etc.'
	)

	options = parser.parse_args()[0]

	# Set the settings
	global _settings
	_settings = {
		'name': options.name,
		'rootDirectory': options.rootDirectory,
		'secretsDirectory': options.secretsDirectory,
		'listeningPort': options.listeningPort,
		'productionLevel': options.productionLevel,
	}

	# Set the secrets
	global _secrets
	if getSettings()['name'] in secrets.secrets:
		_secrets = secrets.secrets[getSettings()['name']]


_init()

