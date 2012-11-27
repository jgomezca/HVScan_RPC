#!/usr/bin/env python2.6
'''Script that uploads to the new dropBox.
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = ['Giacomo Govi', 'Salvatore Di Guida', 'Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'
__version__ = 2


import os
import sys
import logging
import optparse
import hashlib
import cStringIO
import tarfile
import netrc
import getpass
import errno
import sqlite3
import json
import tempfile


import pycurl


defaultBackend = 'online'
defaultHostname = 'cms-conddb-int.cern.ch'
defaultUrlTemplate = 'https://%s/dropBox/'
defaultTemporaryFile = 'upload.tar.bz2'
defaultNetrcHost = 'DropBox'


class HTTPError(Exception):
    '''A common HTTP exception.

    self.code is the response HTTP code as an integer.
    self.response is the response body (i.e. page).
    '''

    def __init__(self, code, response):
        self.code = code
        self.response = response

        # Try to extract the error message if possible (i.e. known error page format)
        try:
            self.args = (response.split('<p>')[1].split('</p>')[0], )
        except Exception:
            self.args = (self.response, )


class HTTP(object):
    '''Class used for querying URLs using the HTTP protocol.
    '''

    def __init__(self):
        self.setBaseUrl()
        self.discardCookies()


    def discardCookies(self):
        '''Discards cookies.
        '''

        self.curl = pycurl.Curl()
        self.curl.setopt(self.curl.COOKIEFILE, '')
        self.curl.setopt(self.curl.SSL_VERIFYPEER, 0)
        self.curl.setopt(self.curl.SSL_VERIFYHOST, 0)


    def setBaseUrl(self, baseUrl = ''):
        '''Allows to set a base URL which will be prefixed to all the URLs
        that will be queried later.
        '''

        self.baseUrl = baseUrl


    def query(self, url, data = None, files = None, keepCookies = True):
        '''Queries a URL, optionally with some data (dictionary).

        If no data is specified, a GET request will be used.
        If some data is specified, a POST request will be used.

        If files is specified, it must be a dictionary like data but
        the values are filenames.

        By default, cookies are kept in-between requests.

        A HTTPError exception is raised if the response's HTTP code is not 200.
        '''

        if not keepCookies:
            self.discardCookies()

        response = cStringIO.StringIO()

        url = self.baseUrl + url

        self.curl.setopt(self.curl.URL, url)
        self.curl.setopt(self.curl.HTTPGET, 1)

        if data is not None or files is not None:
            # If there is data or files to send, use a POST request

            finalData = {}

            if data is not None:
                finalData.update(data)

            if files is not None:
                for (key, fileName) in files.items():
                    finalData[key] = (self.curl.FORM_FILE, fileName)

            self.curl.setopt(self.curl.HTTPPOST, finalData.items())

        self.curl.setopt(self.curl.WRITEFUNCTION, response.write)
        self.curl.perform()

        code = self.curl.getinfo(self.curl.RESPONSE_CODE)

        if code != 200:
            raise HTTPError(code, response.getvalue())

        return response.getvalue()


def addToTarFile(tarFile, fileobj, arcname):
    tarInfo = tarFile.gettarinfo(fileobj = fileobj, arcname = arcname)
    tarInfo.mode = 0400
    tarInfo.uid = tarInfo.gid = tarInfo.mtime = 0
    tarInfo.uname = tarInfo.gname = 'root'
    tarFile.addfile(tarInfo, fileobj)


class DropBox(object):
    '''A dropBox API class.
    '''

    def __init__(self, hostname = defaultHostname, urlTemplate = defaultUrlTemplate):
        self.hostname = hostname
        self.http = HTTP()
        self.http.setBaseUrl(urlTemplate % hostname)


    def signIn(self, username, password):
        '''Signs in the server.
        '''

        logging.info('%s: Signing in...', self.hostname)
        self.http.query('signIn', {
            'username': username,
            'password': password,
        })


    def signOut(self):
        '''Signs out the server.
        '''

        logging.info('%s: Signing out...', self.hostname)
        self.http.query('signOut')


    def _checkForUpdates(self):
        '''Updates this script, if a new version is found.
        '''

        logging.info('%s: Checking for updates...', self.hostname)
        version = int(self.http.query('getUploadScriptVersion'))

        if version <= __version__:
            logging.info('%s: Up to date.', self.hostname)
            return

        logging.info('%s: There is a newer version (%s) than the current one (%s): Updating...', self.hostname, version, __version__)

        logging.info('%s: Downloading new version...', self.hostname)
        uploadScript = self.http.query('getUploadScript')

        self.signOut()

        logging.info('%s: Saving new version...', self.hostname)
        with open(sys.argv[0], 'wb') as f:
            f.write(uploadScript)

        logging.info('%s: Executing new version...', self.hostname)
        os.execl(sys.executable, *([sys.executable] + sys.argv))


    def uploadFile(self, filename, backend = defaultBackend, temporaryFile = defaultTemporaryFile):
        '''Uploads a file to the dropBox.

        The filename can be without extension, with .db or with .txt extension.
        It will be stripped and then both .db and .txt files are used.
        '''

        basepath = filename.rsplit('.db', 1)[0].rsplit('.txt', 1)[0]
        basename = os.path.basename(basepath)

        logging.info('%s: %s: Creating tar file...', self.hostname, basename)

        tarFile = tarfile.open(temporaryFile, 'w:bz2')

        with open('%s.db' % basepath, 'rb') as data:
            addToTarFile(tarFile, data, 'data.db')

        with tempfile.NamedTemporaryFile() as metadata:
            with open('%s.txt' % basepath, 'rb') as originalMetadata:
                json.dump(json.load(originalMetadata), metadata, sort_keys = True, indent = 4)

            metadata.seek(0)
            addToTarFile(tarFile, metadata, 'metadata.txt')

        tarFile.close()

        logging.info('%s: %s: Calculating hash...', self.hostname, basename)

        fileHash = hashlib.sha1()
        with open(temporaryFile, 'rb') as f:
            while True:
                data = f.read(4 * 1024 * 1024)

                if not data:
                    break

                fileHash.update(data)

        fileHash = fileHash.hexdigest()

        logging.info('%s: %s: Hash: %s', self.hostname, basename, fileHash)

        logging.info('%s: %s: Uploading file for the %s backend...', self.hostname, basename, backend)
        os.rename(temporaryFile, fileHash)
        self.http.query('uploadFile', {
            'backend': backend,
            'fileName': basename,
        }, files = {
            'uploadedFile': fileHash,
        })
        os.unlink(fileHash)


def getInput(default, prompt = ''):
    '''Like raw_input() but with a default and automatic strip().
    '''

    answer = raw_input(prompt)
    if answer:
        return answer.strip()

    return default.strip()


def getInputChoose(optionsList, default, prompt = ''):
    '''Makes the user choose from a list of options.
    '''

    while True:
        index = getInput(default, prompt)

        try:
            return optionsList[int(index)]
        except ValueError:
            logging.error('Please specify an index of the list (i.e. integer).')
        except IndexError:
            logging.error('The index you provided is not in the given list.')


def getInputRepeat(prompt = ''):
    '''Like raw_input() but repeats if nothing is provided and automatic strip().
    '''

    while True:
        answer = raw_input(prompt)
        if answer:
            return answer.strip()

        logging.error('You need to provide a value.')


def main():
    '''Entry point.
    '''

    parser = optparse.OptionParser(usage =
        'Usage: %prog <file> [<file> ...]\n'
    )

    parser.add_option('-b', '--backend',
        dest = 'backend',
        default = defaultBackend,
        help = 'dropBox\'s backend to upload to. Default: %default',
    )

    parser.add_option('-H', '--hostname',
        dest = 'hostname',
        default = defaultHostname,
        help = 'dropBox\'s hostname. Default: %default',
    )

    parser.add_option('-u', '--urlTemplate',
        dest = 'urlTemplate',
        default = defaultUrlTemplate,
        help = 'dropBox\'s URL template. Default: %default',
    )

    parser.add_option('-f', '--temporaryFile',
        dest = 'temporaryFile',
        default = defaultTemporaryFile,
        help = 'Temporary file that will be used to store the first tar file. Note that it then will be moved to a file with the hash of the file as its name, so there will be two temporary files created in fact. Default: %default',
    )

    parser.add_option('-n', '--netrcHost',
        dest = 'netrcHost',
        default = defaultNetrcHost,
        help = 'The netrc host (machine) from where the username and password will be read. Default: %default',
    )

    (options, arguments) = parser.parse_args()

    if len(arguments) < 1:
        parser.print_help()
        return -2


    # Retrieve username and password
    try:
        (username, account, password) = netrc.netrc().authenticators(options.netrcHost)
    except Exception:
        logging.info('netrc entry %s not found: if you wish not to have to retype your password, you can add an entry in your .netrc file. However, beware of the risks of having your password stored as plaintext.', options.netrcHost)

        defaultUsername = getpass.getuser()
        if defaultUsername is None:
            defaultUsername = '(not found)'

        username = getInput(defaultUsername, 'Username [%s]: ' % defaultUsername)
        password = getpass.getpass('Password: ')


    # Check that we can read the data and metadata files
    # If the metadata file does not exist, start the wizard
    for filename in arguments:
        basepath = filename.rsplit('.db', 1)[0].rsplit('.txt', 1)[0]
        basename = os.path.basename(basepath)
        dataFilename = '%s.db' % basepath
        metadataFilename = '%s.txt' % basepath

        logging.info('Checking %s...', basename)

        # Data file
        try:
            with open(dataFilename, 'rb') as dataFile:
                pass
        except IOError as e:
            logging.error('Impossible to open SQLite data file %s', dataFilename)
            return -3

        # Metadata file
        try:
            with open(metadataFilename, 'rb') as metadataFile:
                pass
        except IOError as e:
            if e.errno != errno.ENOENT:
                logging.error('Impossible to open file %s (for other reason than not existing)', metadataFilename)
                return -4

            if getInput('y', '\nIt looks like the metadata file %s does not exist. Do you want me to create it and help you fill it?\nAnswer [y]: ' % metadataFilename).strip().lower() != 'y':
                logging.error('Metadata file %s does not exist', metadataFilename)
                return -5

            # Wizard
            while True:
                print '''\nWizard for metadata for %s

I will ask you some questions to fill the metadata file. For some of the questions there are defaults between square brackets (i.e. []), leave empty (i.e. hit Enter) to use them.''' % basename

                # Try to get the available inputTags
                try:
                    dataConnection = sqlite3.connect(dataFilename)
                    dataCursor = dataConnection.cursor()
                    dataCursor.execute('select name from sqlite_master where type == "table"')
                    tables = set(zip(*dataCursor.fetchall())[0])

                    # Old POOL format
                    if 'POOL_RSS_DB' in tables:
                        dataCursor.execute('select NAME from METADATA')

                    # Good ORA DB (i.e. skip the intermediate unsupported format)
                    elif 'ORA_DB' in tables and 'METADATA' not in tables:
                        dataCursor.execute('select OBJECT_NAME from ORA_NAMING_SERVICE')

                    # In any other case, do not try to get the inputTags
                    else:
                        raise Exception()

                    inputTags = dataCursor.fetchall()
                    if len(inputTags) == 0:
                        raise Exception()
                    inputTags = zip(*inputTags)[0]

                except Exception:
                    inputTags = []

                if len(inputTags) == 0:
                    print '\nI could not find any input tag in your data file, but you can still specify one manually.'

                    inputTag = getInputRepeat('\nWhich is the input tag (i.e. the tag to be read from the SQLite data file)?\ne.g. BeamSpotObject_ByRun\ninputTag: ')

                else:
                    print '\nI found the following input tags in your SQLite data file:'
                    for (index, inputTag) in enumerate(inputTags):
                        print '   %s) %s' % (index, inputTag)

                    inputTag = getInputChoose(inputTags, '0', '\nWhich is the input tag (i.e. the tag to be read from the SQLite data file)?\ne.g. 0 (you select the first in the list)\ninputTag [0]: ')

                destinationDatabase = getInputRepeat('\nWhich is the destination database where the tags should be exported and/or duplicated?\ne.g. oracle://cms_orcoff_prep/CMS_COND_BEAMSPOT\ndestinationDatabase: ')

                while True:
                    since = getInput('', '\nWhich is the given since (if not specified, the one from the SQLite data file will be taken)?\ne.g. 1234\nsince []: ')
                    if not since:
                        since = None
                        break
                    else:
                        try:
                            since = int(since)
                            break
                        except ValueError:
                            logging.error('The since value has to be an integer or empty (null).')

                userText = getInput('', '\nWrite any comments/text you may want to describe your request\ne.g. Muon alignment scenario for...\nuserText []: ')

                print '''
Finally, we are going to add the destination tags. There must be at least one.
The tags (and its dependencies) can be synchronized to several workflows. You can synchronize to the following workflows:
   * "offline" means no checks/synchronization will be done.
   * "hlt" and "express" means that the IOV will be synchronized to the last online run number plus one (as seen by RunInfo).
   * "prompt" means that the IOV will be synchronized to the smallest run number waiting for Prompt Reconstruction not having larger run numbers already released (as seen by the Tier0 monitoring).
   * "pcl" is like "prompt", but the exportation will occur if and only if the begin time of the first IOV (as stored in the SQLite file or established by the since field in the metadata file) is larger than the first condition safe run number obtained from Tier0.'''

                defaultWorkflow = 'offline'
                destinationTags = {}
                while True:
                    destinationTag = getInput('', '\nWhich is the next destination tag to be added (leave empty to stop)?\ne.g. BeamSpotObjects_PCL_byRun_v0_offline\ndestinationTag []: ')
                    if not destinationTag:
                        if len(destinationTags) == 0:
                            logging.error('There must be at least one destination tag.')
                            continue
                        break

                    if destinationTag in destinationTags:
                        logging.warning('You already added this destination tag. Overwriting the previous one with this new one.')

                    synchronizeTo = getInput(defaultWorkflow, '\n  * To which workflow (see above) this tag %s has to be synchronized to?\n    e.g. offline\n    synchronizeTo [%s]: ' % (destinationTag, defaultWorkflow))

                    print '''
    If you need to add dependencies to this tag (i.e. tags that will be duplicated from this tag to another workflow), you can specify them now. There may be none.'''

                    dependencies = {}
                    while True:
                        dependency = getInput('', '\n  * Which is the next dependency for %s to be added (leave empty to stop)?\n    e.g. BeamSpotObjects_PCL_byRun_v0_hlt\n    dependency []: ' % destinationTag)
                        if not dependency:
                            break

                        if dependency in dependencies:
                            logging.warning('You already added this dependency. Overwriting the previous one with this new one.')

                        workflow = getInput(defaultWorkflow, '\n     + To which workflow (see above) this dependency %s has to be synchronized to?\n       e.g. offline\n       synchronizeTo [%s]: ' % (dependency, defaultWorkflow))

                        dependencies[dependency] = workflow

                    destinationTags[destinationTag] = {
                        'synchronizeTo': synchronizeTo,
                        'dependencies': dependencies,
                    }

                metadata = {
                    'destinationDatabase': destinationDatabase,
                    'destinationTags': destinationTags,
                    'inputTag': inputTag,
                    'since': since,
                    'userText': userText,
                }

                metadata = json.dumps(metadata, sort_keys = True, indent = 4)
                logging.info('This is the generated metadata:\n\n%s', metadata)

                if getInput('n', '\nIs it fine (i.e. save in %s and continue)?\nAnswer [n]: ' % metadataFilename).strip().lower() == 'y':
                    break

            logging.info('Saving generated metadata in %s...', metadataFilename)
            with open(metadataFilename, 'wb') as metadataFile:
                metadataFile.write(metadata)

    # Upload files
    try:
        dropBox = DropBox(options.hostname, options.urlTemplate)
        dropBox.signIn(username, password)
        dropBox._checkForUpdates()

        for filename in arguments:
            dropBox.uploadFile(filename, options.backend, options.temporaryFile)

        dropBox.signOut()
    except HTTPError as e:
        logging.error(e)
        return -1


if __name__ == '__main__':
    logging.basicConfig(
        format = '[%(asctime)s] %(levelname)s: %(message)s',
        level = logging.INFO,
    )

    sys.exit(main())

