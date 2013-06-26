'''Common code for all CMS DB Web services.
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = ['Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


import re
import os
import sys
import optparse
import socket
import logging
import unittest
import json
import urllib
import time
import datetime
import netrc
import xml.sax.saxutils
import xml.dom.minidom

import cherrypy

import http


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

    parser.add_option('-c', '--caches', type = 'str',
        dest = 'caches',
        help = 'The cache to ID mapping of the caches that the service uses.'
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
        'caches': dict([(str(x[0]), x[1]) for x in json.loads(options.caches).items()]),
    }

    # Set the secrets
    global secrets
    import secrets
    if settings['name'] in secrets.secrets:
        secrets = secrets.secrets[settings['name']]

    logLevel = logging.INFO
    if settings['productionLevel'] == 'private':
        logLevel = logging.DEBUG

    # Initialize the logging module with a common format
    logging.basicConfig(
        format = '[%(asctime)s] %(levelname)s: %(message)s',
        level = logLevel
    )

_init()


def start(mainObject):
    '''Starts the service.
    '''

    def getErrorPage(status, message, traceback, version):
        '''Returns an error page like the Apache's one, using only
        the status (e.g. '404 Not Found') and message (e.g. 'Nothing
        matches the given URI') and hiding everything else
        (i.e. server, version, traceback...).

        The CherryPy-defined messages may reveal that CherryPy is the server,
        but some services are already using custom messages and, in any case,
        they are useful for the users.
        '''

        apacheErrorPageTemplate = '''<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">
<html><head>
<title>%s</title>
</head><body>
<h1>%s</h1>
<p>%s</p>
</body></html>'''

        # Apache writes the status without the code in the h1 header
        # e.g. '404 Not Found' -> 'Not Found'
        statusWithoutCode = status.partition(' ')[2]

        return apacheErrorPageTemplate % (status, statusWithoutCode, message)

    cherrypy.config.update({
        'global': {
        'server.socket_host': socket.gethostname(),
        'server.socket_port': settings['listeningPort'],
        'tools.staticdir.root': settings['rootDirectory'],
        'engine.autoreload_on': False,
        'log.screen': False,
        'server.ssl_certificate': os.path.join(settings['secretsDirectory'], 'hostcert.pem'),
        'server.ssl_private_key': os.path.join(settings['secretsDirectory'], 'hostkey.pem'),
        'error_page.default': getErrorPage,
        },
    })
    cherrypy.quickstart(mainObject, config = 'server.conf', script_name = '/' + settings['name'])


# Hostname and URL related functions

def getHostname():
    '''Returns the 'official' hostname where services are run.

    In private deployments, this is the current hostname. However,
    in official ones, could be, for instance, a DNS alias.

    e.g. cms-conddb-dev.cern.ch
    '''

    hostnameByLevel = {
        'pro': 'cms-conddb-prod.cern.ch',
        'int': 'cms-conddb-int.cern.ch',
        'dev': 'cms-conddb-dev.cern.ch',
        'private': socket.getfqdn(),
    }

    return hostnameByLevel[settings['productionLevel']]


def getBaseURL():
    '''Returns the base URL for all the services (without trailing slash).

    The hostname is the one returned by getHostname(), so the same notes
    regarding the returned hostname apply here.

    e.g. https://cms-conddb-dev.cern.ch
    '''

    return 'https://%s' % getHostname()


def getURL():
    '''Returns the URL of the service (without trailing slash).

    The base URL is the one returned by getBaseURL(), so the same notes
    regarding the returned hostname apply here.

    e.g. https://cms-conddb-dev.cern.ch/docs
    '''

    return '%s/%s' % (getBaseURL(), settings['name'])


# Utility functions

def makePath(path):
    '''Makes directories in the path if they do not exist yet.

    Like os.makedirs() but without failing if the exist.

    Note that this function has a race condition, so do not use it
    from multiple callers at the same time.
    '''

    if not os.path.exists(path):
        logging.debug('%s: Creating path...', path)
        os.makedirs(path)


def getFilesPath():
    '''Returns the path to the files folder where a service can store
    permanent files (but local to the backend machine).
    '''

    return os.path.join('/data/files', settings['name'])


def onlyPrivate(f):
    '''Decorator that only defines a function if the productionLevel
    is private.

    Useful to have testing methods in CherryPy, only available
    in private instances.
    '''

    if settings['productionLevel'] == 'private':
        return f


def getPrettifiedJSON(data, sortKeys = True):
    '''Returns prettified JSON (valid and easily read JSON).
    '''

    return json.dumps(data, sort_keys = sortKeys, indent = 4, default = lambda obj: obj.strftime('%Y-%m-%d %H:%M:%S,%f')[:-3] if isinstance(obj, datetime.datetime) else None)

def setResponsePlainText(data = None):
    cherrypy.response.headers['Content-Type'] = 'text/plain;charset=ISO-8859-1'
    return data

def setResponseJSON(data = None, encode = True):
    cherrypy.response.headers['Content-Type'] = 'application/json'

    if encode and data is not None:
        data = getPrettifiedJSON(data)

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


def _getPIDs(string):
    '''Returns the PIDs matching the string, without grep nor bash.
    '''

    return os.popen("ps auxww | grep -F '" + string + "' | grep -F 'python' | grep -F -v 'grep' | grep -F -v 'bash' | awk '{print $2}'", 'r').read().splitlines()


def isAnotherInstanceRunning():
    '''Returns whether another instance of the script is running.
    '''

    return len(_getPIDs(sys.argv[0])) > 1


# Functions for generating connection strings and URLs

def getConnectionDictionaryFromNetrc(entry):
    '''Returns a connection dictionary from a netrc entry.
    (intended for personal/private database accounts and the like, instead
    of the normal production ones from the secrets file).
    '''

    try:
        (user, db_name, password) = netrc.netrc().authenticators(entry)
    except TypeError:
        raise Exception('netrc entry %s could not be found.' % entry)

    return  {
        'user': user,
        'password': password,
        'db_name': db_name,
    }


def getOracleConnectionString(connectionDictionary):
    '''Returns a connection string for Oracle given
    a connection dictionary from the secrets file.
    '''

    return 'oracle://%s/%s' % (connectionDictionary['db_name'], connectionDictionary['account'])


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


def getProtocolServiceAndAccountFromConnectionString(connectionString):
    '''Extract the protocol, the service and the account name from a given connection string.
    Parameters:
    connectionString: the input connection string.
    @returns: a dictionary in the form {'protocol' : protocol_name, 'service' : service_name, 'account' : account_name}, None if parsing error'''

    protocol, serviceAndAccount = connectionString.partition( '://' )[ : : 2 ]
    if protocol != 'frontier' and protocol != 'oracle': #the supported protocols are frontier and oracle
        return None
    serviceConfiguration, account = serviceAndAccount.rpartition( '/' )[ : : 2 ]
    if account == '' or serviceConfiguration == '': #only protocol provided (serviceAndAccount empty, so account and service both empty), or no account provided, but service ends with (account empty) or without (service empty) a /
        return None
    if serviceConfiguration.count( '/' ) > 1 and serviceConfiguration.count( '(' ) == 0: #too many slashes, but no explicit configuration
        return None
    if serviceConfiguration.count( '/' ) == 0: #no server and proxies specified, but other configurations can be there after the service name
        service = serviceConfiguration.partition( '(' )[ 0 ]
    elif serviceConfiguration.count( '/' ) == 1: #only one instance of the server address was provided
        service = serviceConfiguration.partition( '/' )[ 2 ]
    else: #it is a long connection string: find all the serverurl parameter
        tempStr = serviceConfiguration
        service = ''
        for _ in xrange( serviceConfiguration.count( "serverurl=" ) ):
            servletURL = tempStr[ tempStr.find( "serverurl=" ) + len( "serverurl=" ) : tempStr.find( ')', tempStr.find( "serverurl=" ) ) ]
            newServlet = servletURL.rpartition( '/' )[ -1 ]
            if service == '':
                service = newServlet
            elif service != newServlet: # there can be only one servlet, otherwise the connection string is malformed
                return None
            tempStr = tempStr[ tempStr.find( ')', tempStr.find( "serverurl=" ) ) + len( ')' ) : ]
    return {'protocol' : protocol, 'service' : service, 'account' : account}


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


def winServicesSoapSignIn(winServicesUrl, username, password):
    try:
        data = urllib.urlopen('%sGetUserInfo?UserName=%s&Password=%s' % (winServicesUrl, username, password)).read()
        status = int(data[data.find('</auth>') - 1])

        # Status codes:
        #   0 == Account disabled or activation pending or expired
        #   1 == Invalid password
        #   2 == Incorrect login or E-mail
        #   3 == Success
        success = 3
        if status == success:
            return True
    except Exception as e:
        logging.error('login(): %s', e)

    return False


def winServicesSoapIsUserInGroup(winServicesUrl, username, group):
    try:
        # GetGroupsForUser does not return groups that are included in user's groups
        data = urllib.urlopen('%sUserIsMemberOfGroup?UserName=%s&GroupName=%s' % (winServicesUrl, username, group)).read()
        return re.search('<boolean.*>true</boolean>', data) is not None
    except Exception as e:
        logging.error('isUserInGroup(): %s', e)

    return False


# Shibboleth functions

def getUsername():
    return cherrypy.request.headers['Adfs-Login']

def getFullName():
    return cherrypy.request.headers['Adfs-Fullname']

def getGroups():
    return cherrypy.request.headers['Adfs-Group'].split(';')


# Functions for testing

def parseCherryPyErrorPage(errorPage):
    return errorPage.split('<p>')[1].split('</p>')[0]


class HTTPService(http.HTTP):
    '''Same as HTTP, but it queries our own service: the url is prefixed
    with the URL of our service, including an ending slash.

    It also parses the error page to get the real error message from
    our CherryPy servers.

    Typically used for testing in test.py.
    '''

    def __init__(self):
        super(HTTPService, self).__init__()
        self.setBaseUrl('https://%s/%s/' % (socket.gethostname(), settings['name']))


    def query(self, url, data = None, files = None, keepCookies = True):
        try:
            return super(HTTPService, self).query(url, data, files, keepCookies)
        except http.HTTPError as e:
            e.response = parseCherryPyErrorPage(e.response)
            e.args = (e.response, )
            raise e


def setupTest():
    logging.getLogger().setLevel(logging.INFO)


def test(TestCase):
    setupTest()
    return not unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(TestCase)).wasSuccessful()


class TestCase(unittest.TestCase):
    '''An specialized TestCase for our services.
    '''

    warningTime = 4. # seconds


    def __init__(self, methodName = 'runTest'):
        super(TestCase, self).__init__(methodName)
        self.httpService = HTTPService()


    def setUp(self):
        self.startTime = time.time()


    def tearDown(self):
        totalTime = time.time() - self.startTime
        if totalTime > self.warningTime:
            logging.warning('%s took %.2f seconds.', self.id(), totalTime)


    def query(self, url, data = None, files = None, keepCookies = True):
        return self.httpService.query(url, data, files, keepCookies)


    def queryJson(self, url, data = None, files = None, keepCookies = True):
        return json.loads(self.query(url, data, files, keepCookies))


    def assertRaisesHTTPError(self, code, *args, **kwargs):
        '''Like assertRaises(http.HTTPError, self.query, ...),
        but checking that the HTTP error code is the given one.
        '''

        try:
            return self.query(*args, **kwargs)
        except http.HTTPError as e:
            if e.code != code:
                raise self.failureException, "HTTPError's code %s != expected %s" % (e.code, code)

            # Return the error message to allow for detailed checking
            return e.response
        else:
            raise self.failureException, "HTTPError not raised"


    def assertRaisesHTTPErrorMessage(self, code, message, *args, **kwargs):
        '''Like assertRaises(http.HTTPError, self.query, ...),
        but checking that the HTTP error code is the given one and that
        the returned error message matches the given one.
        '''

        self.assertEqual(message, self.assertRaisesHTTPError(code, *args, **kwargs))

