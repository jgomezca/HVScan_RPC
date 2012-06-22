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
import logging
import cherrypy
import unittest
import json
import urllib2
import datetime
import xml.sax.saxutils
import xml.dom.minidom

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

	# Initialize the logging module with a common format
	logging.basicConfig(
		format = '[%(asctime)s] %(levelname)s: %(message)s',
		level = logging.INFO
	)

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
		'log.screen': False,
		'server.ssl_certificate': os.path.join(settings['secretsDirectory'], 'hostcert.pem'),
		'server.ssl_private_key': os.path.join(settings['secretsDirectory'], 'hostkey.pem'),
		},
	})
	cherrypy.quickstart(mainObject, config = 'server.conf', script_name = '/' + settings['name'])


# Utility functions

def setResponsePlainText(data = None):
	cherrypy.response.headers['Content-Type'] = 'text/plain;charset=ISO-8859-1'
	return data

def setResponseJSON(data = None, encode = True):
	cherrypy.response.headers['Content-Type'] = 'application/json'

	if encode and data is not None:
		# Prettified JSON (valid and easily read JSON)
		data = json.dumps(data, sort_keys = True, indent = 4)

	return data

def setResponsePNG(data = None):
	cherrypy.response.headers['Content-Type'] = 'image/png'
	return data


def escape(x):
	'''Escapes data for XML/HTML.
	'''

	tx = type(x)

	if x is None or tx in (bool, int, long):
		return x

	if tx in (str, unicode):
		return xml.sax.saxutils.escape(x)

	if tx in (list, tuple):
		return [escape(y) for y in x]

	if tx in (set, frozenset):
		ret = set([])
		for y in x:
			ret.add(escape(y))
		return ret

	if tx == dict:
		for y in x.items():
			x[y[0]] = escape(y[1])
		return x

	if tx == datetime.datetime:
		return x.replace(microsecond = 0)

	raise Exception('escape(): Type %s not recognized.' % str(type(x)))


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

frontierConnectionStringTemplate = None
def getFrontierConnectionString(connectionDictionary, short = False):
	'''Returns a connection string for Frontier given
	a connection dictionary from the secrets file.
	'''

	if short:
		return 'frontier://%s/%s' % (connectionDictionary['frontier_name'], connectionDictionary['account'])

	global frontierConnectionStringTemplate
	if frontierConnectionStringTemplate is None:
		siteLocalConfigFilename = '/afs/cern.ch/cms/SITECONF/CERN/JobConfig/site-local-config.xml'

		frontierName = ''
		dom = xml.dom.minidom.parse(siteLocalConfigFilename)
		nodes = dom.getElementsByTagName('frontier-connect')[0].childNodes
		for node in nodes:
			if node.nodeType in frozenset([xml.dom.minidom.Node.TEXT_NODE, xml.dom.minidom.Node.COMMENT_NODE]):
				continue

			if node.tagName == 'proxy':
				frontierName += '(proxyurl=%s)' % str(node.attributes['url'].nodeValue)

			if node.tagName == 'server':
				# Override the frontier name
				frontierName += '(serverurl=%s/%s)' % (str(node.attributes['url'].nodeValue).rsplit('/', 1)[0], '%s')

		dom.unlink()

		frontierConnectionStringTemplate = 'frontier://%s/%s' % (frontierName, '%s')
	
	return frontierConnectionStringTemplate % ((frontierConnectionStringTemplate.count('%s') - 1) * (connectionDictionary['frontier_name'], ) + (connectionDictionary['account'], ))

def getFrontierConnectionStringList(connectionsDictionary):
	'''Returns a list of connection strings for Frontier given
	a connections dictionary with multiple accounts from the secrets file.
	'''

	connectionStringList = []

	for account in connectionsDictionary['accounts']:
		connectionStringList.append(getFrontierConnectionString({
			'account': account,
			'frontier_name': connectionsDictionary['frontier_name']
		}))

	return connectionStringList

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


class TestCase(unittest.TestCase):
	'''An specialized TestCase for our services.
	'''

	def assertRaisesHTTPError(self, validCodes, callableObj, *args, **kwargs):
		'''Like assertRaises(urllib2.HTTPError, ...), but checking that
		the HTTP error code is in the given set.
		'''

		try:
			callableObj(*args, **kwargs)
		except urllib2.HTTPError as e:
			if e.code not in validCodes:
				raise self.failureException, "HTTPError's code %s is not in %s" % (e.code, validCodes)
		else:
			raise self.failureException, "HTTPError not raised"

