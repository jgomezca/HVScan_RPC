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

