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
import unittest
import json
import urllib2


settings = None
secrets = None

def _init():
	'''Setup 'settings' and 'secrets' global variables by parsing
	the command line options.
	'''

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
	global settings
	settings = {
		'name': options.name,
		'rootDirectory': options.rootDirectory,
		'secretsDirectory': options.secretsDirectory,
		'listeningPort': options.listeningPort,
		'productionLevel': options.productionLevel,
	}

	# Set the secrets
	global secrets
	import secrets
	if settings['name'] in secrets.secrets:
		secrets = secrets.secrets[settings['name']]

_init()


def start(mainObject):
	'''Starts the service.
	'''

	cherrypy.config.update({
		'global': {
		'server.socket_host': socket.gethostname(),
		'server.socket_port': settings['listeningPort'],
		'tools.staticdir.root': settings['rootDirectory'],
		'engine.autoreload_on': False,
		'server.ssl_certificate': os.path.join(settings['secretsDirectory'], 'hostcert.pem'),
		'server.ssl_private_key': os.path.join(settings['secretsDirectory'], 'hostkey.pem'),
		},
	})
	cherrypy.quickstart(mainObject, config = 'server.conf', script_name = '/' + settings['name'])


# Functions for generating connection strings and URLs

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



# Functions for testing

baseUrl = 'https://%s:%s/%s/' % (socket.gethostname(), str(settings['listeningPort']), settings['name'])

def query(url, data = None, timeout = 10):
	return urllib2.urlopen(baseUrl + url, data, timeout).read()

def queryJson(url, data = None, timeout = 10):
	return json.loads(query(url, data, timeout))

def test(TestCase):
	return not unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(TestCase)).wasSuccessful()

