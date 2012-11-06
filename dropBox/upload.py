#!/usr/bin/env python2.6
'''Script that uploads to the new dropBox.
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = ['Giacomo Govi', 'Salvatore Di Guida', 'Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


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


allowedBackends = set(['online', 'tier0', 'offline', 'private'])
defaultBackend = 'online'
defaultHostname = 'mos-dev-slc6.cern.ch'
defaultTemporaryFile = 'upload.tar.bz2'
defaultNetrcHost = 'newOffDb'


def _uploadFile(username, password, filename, backend = defaultBackend, hostname = defaultHostname):
    '''Uploads a raw file to the new dropBox.

    You should not use this directly. Look at uploadFiles() instead.
    '''

    url = 'https://%s/dropBox/' % hostname

    if backend not in allowedBackends:
        raise Exception('The backend %s is not any of the allowed ones: %s' % (repr(backend), repr(allowedBackends)))

    try:
        response = cStringIO.StringIO()
        curl = pycurl.Curl()
        curl.setopt(curl.POST, 1)
        curl.setopt(curl.COOKIEFILE, '')
        curl.setopt(curl.SSL_VERIFYPEER, 0)
        curl.setopt(curl.SSL_VERIFYHOST, 0)
        curl.setopt(curl.WRITEFUNCTION, response.write)

        logging.info('%s: Signing in...', filename)
        curl.setopt(curl.URL, url + 'signIn')
        curl.setopt(curl.HTTPPOST, [
            ('username', username),
            ('password', password),
        ])
        curl.perform()

        if curl.getinfo(curl.RESPONSE_CODE) != 200:
            raise Exception(response.getvalue())

        logging.info('%s: Uploading file...', filename)
        curl.setopt(curl.URL, url + 'uploadFile')
        curl.setopt(curl.HTTPPOST, [
            ('uploadedFile', (curl.FORM_FILE, filename)),
            ('backend', backend),
        ])
        curl.perform()

        if curl.getinfo(curl.RESPONSE_CODE) != 200:
            raise Exception(response.getvalue())

        logging.info('%s: Signing out...', filename)
        curl.setopt(curl.URL, url + 'signOut')
        curl.setopt(curl.HTTPGET, 1)
        curl.perform()

        if curl.getinfo(curl.RESPONSE_CODE) != 200:
            raise Exception(response.getvalue())

        curl.close()
        response.close()

    except pycurl.error as error:
        logging.error('%s (errno = %s)', error[1], error[0])
        return -2

    except Exception as e:
        logging.error(e.args[0].split('<p>')[1].split('</p>')[0])
        return -1


def uploadFiles(username, password, filenames, backend = defaultBackend, hostname = defaultHostname, temporaryFile = defaultTemporaryFile):
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
        ret = _uploadFile(username, password, fileHash, backend = backend, hostname = hostname)
        os.unlink(fileHash)

        if ret != 0:
            return ret


def main():
    '''Entry point.
    '''

    parser = optparse.OptionParser(usage =
        'Usage: %prog <file> [<file> ...]\n'
    )

    parser.add_option('-b', '--backend',
        dest = 'backend',
        default = defaultHostname,
        help = 'dropBox\'s backend to upload to. Default: %default',
    )

    parser.add_option('-H', '--hostname',
        dest = 'hostname',
        default = defaultHostname,
        help = 'dropBox\'s hostname. Default: %default',
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
    return uploadFiles(username, password, arguments, backend = options.backend, hostname = options.hostname)


if __name__ == '__main__':
    logging.basicConfig(
        format = '[%(asctime)s] %(levelname)s: %(message)s',
        level = logging.INFO,
    )

    sys.exit(main())

