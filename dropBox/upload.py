#!/usr/bin/env python2.6
'''Script that uploads to the new dropBox.
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = ['Giacomo Govi', 'Salvatore Di Guida', 'Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'
__version__ = 1


import os
import sys
import logging
import optparse
import hashlib
import cStringIO
import tarfile
import netrc
import json
import tempfile


import pycurl


defaultBackend = 'online'
defaultHostname = 'cms-conddb-int.cern.ch'
defaultUrlTemplate = 'https://%s/dropBox/'
defaultTemporaryFile = 'upload.tar.bz2'
defaultNetrcHost = 'newOffDb'


class HTTPError(Exception):
    '''A common HTTP exception.

    self.code is the response HTTP code as an integer.
    self.response is the response body (i.e. page).
    '''

    def __init__(self, code, response):
        self.code = code
        self.response = response
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


def _uploadFile(username, password, filename, backend = defaultBackend, hostname = defaultHostname, urlTemplate = defaultUrlTemplate):
    '''Uploads a raw file to the new dropBox.

    You should not use this directly. Look at uploadFiles() instead.
    '''

    http = HTTP()
    http.setBaseUrl(urlTemplate % hostname)

    logging.info('%s: Signing in...', filename)
    http.query('signIn', {
        'username': username,
        'password': password,
    })

    logging.info('%s: Uploading file...', filename)
    http.query('uploadFile', {
        'backend': backend,
    }, files = {
        'uploadedFile': filename,
    })

    logging.info('%s: Signing out...', filename)
    http.query('signOut')


def uploadFiles(username, password, filenames, backend = defaultBackend, hostname = defaultHostname, urlTemplate = defaultUrlTemplate, temporaryFile = defaultTemporaryFile):
    '''Uploads several files to the new dropBox.

    The filenames can be without extension, with .db or with .txt extension.
    It will be stripped and then both .db and .txt files are used.
    '''

    def add(tarFile, fileobj, arcname):
        tarInfo = tarFile.gettarinfo(fileobj = fileobj, arcname = arcname)
        tarInfo.mode = 0400
        tarInfo.uid = tarInfo.gid = tarInfo.mtime = 0
        tarInfo.uname = tarInfo.gname = 'root'
        tarFile.addfile(tarInfo, fileobj)

    for filename in filenames:
        basename = filename.rsplit('.db', 1)[0].rsplit('.txt', 1)[0]

        logging.info('%s: Creating tar file...', basename)

        tarFile = tarfile.open(temporaryFile, 'w:bz2')

        with open('%s.db' % basename, 'rb') as data:
            add(tarFile, data, 'data.db')

        with tempfile.NamedTemporaryFile() as metadata:
            with open('%s.txt' % basename, 'rb') as originalMetadata:
                json.dump(json.load(originalMetadata), metadata, sort_keys = True, indent = 4)
            metadata.seek(0)
            add(tarFile, metadata, 'metadata.txt')

        tarFile.close()

        logging.info('%s: Calculating hash...', basename)

        fileHash = hashlib.sha1()

        with open(temporaryFile, 'rb') as f:
            while True:
                data = f.read(4 * 1024 * 1024)
                if not data:
                    break
                fileHash.update(data)
        
        fileHash = fileHash.hexdigest()

        logging.info('%s: Hash: %s', basename, fileHash)

        logging.info('%s: Uploading file...', basename)
        os.rename(temporaryFile, fileHash)
        _uploadFile(username, password, fileHash, backend = backend, hostname = hostname, urlTemplate = urlTemplate)
        os.unlink(fileHash)


def checkForUpdates(username, password, hostname = defaultHostname, urlTemplate = defaultUrlTemplate):
    '''Updates this script, if a new version is found.
    '''

    http = HTTP()
    http.setBaseUrl(urlTemplate % hostname)

    logging.info('Signing in...')
    http.query('signIn', {
        'username': username,
        'password': password,
    })

    logging.info('Checking for updates...')
    version = int(http.query('getUploadScriptVersion'))

    if version <= __version__:
        logging.info('Signing out...')
        http.query('signOut')
        return

    logging.info('The version in the server (%s) is newer than the current one (%s).', version, __version__)

    logging.info('Downloading new version...')
    uploadScript = http.query('getUploadScript')

    logging.info('Signing out...')
    http.query('signOut')

    logging.info('Saving new version...')
    with open('upload.py', 'wb') as f:
        f.write(uploadScript)

    logging.info('Executing new version...')
    os.execl(sys.executable, *([sys.executable] + sys.argv))


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
        return -3

    (username, account, password) = netrc.netrc().authenticators(options.netrcHost)

    checkForUpdates(username, password)

    uploadFiles(username, password, arguments, backend = options.backend, hostname = options.hostname, urlTemplate = options.urlTemplate)


if __name__ == '__main__':
    logging.basicConfig(
        format = '[%(asctime)s] %(levelname)s: %(message)s',
        level = logging.INFO,
    )

    sys.exit(main())

