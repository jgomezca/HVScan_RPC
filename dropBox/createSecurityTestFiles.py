#!/usr/bin/env python2.6
'''Script that creates the 'security' test files, for reference.
(The generated files are included in git in any case).
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
import hashlib
import tarfile
import tempfile
import json

import config


templateDBFile = os.path.join(config.testFilesPath, 'metadata/wrongKey.db')


def add(tarFile, fileobj, arcname):
    '''Adds a file object to the tarFile with a given name.
    '''

    tarInfo = tarFile.gettarinfo(fileobj = fileobj, arcname = arcname)
    tarInfo.mode = 0400
    tarInfo.uid = tarInfo.gid = tarInfo.mtime = 0
    tarInfo.uname = tarInfo.gname = 'root'
    tarFile.addfile(tarInfo, fileobj)


def wrongBzip2File(temporaryFile):
    # Create normal file
    tarFile = tarfile.open(temporaryFile, 'w:bz2')

    with open(templateDBFile, 'rb') as data:
        add(tarFile, data, 'data.db')

    with tempfile.NamedTemporaryFile() as metadata:
        json.dump({
            'bad': 'json',
            'since': -100,
        }, metadata, sort_keys = True, indent = 4)
        metadata.seek(0)
        add(tarFile, metadata, 'metadata.txt')

    tarFile.close()

    # Then corrupt the header
    with open(temporaryFile, 'r+b') as tarFile:
        tarFile.write('BZ1')


def wrongFileNames(temporaryFile):
    tarFile = tarfile.open(temporaryFile, 'w:bz2')

    with tempfile.NamedTemporaryFile() as metadata:
        metadata.write('###')
        metadata.seek(0)
        add(tarFile, metadata, '../../../../../../../../../../../../../../../../../../../../../../../../../../../../etc/passwd')

    tarFile.close()


def wrongMetadataFile(temporaryFile):
    tarFile = tarfile.open(temporaryFile, 'w:bz2')

    with open(templateDBFile, 'rb') as data:
        add(tarFile, data, 'data.db')

    with tempfile.NamedTemporaryFile() as metadata:
        json.dump({
            'bad': 'json',
            'since': -100,
        }, metadata, sort_keys = True, indent = 4)
        metadata.seek(0)
        add(tarFile, metadata, 'metadata.txt')

    tarFile.close()


def wrongJSON(temporaryFile):
    tarFile = tarfile.open(temporaryFile, 'w:bz2')

    with open(templateDBFile, 'rb') as data:
        add(tarFile, data, 'data.db')

    with tempfile.NamedTemporaryFile() as metadata:
        metadata.write(json.dumps({
            'bad': 'json',
            'since': -100,
        }, sort_keys = True, indent = 4).replace('"json"', 'json"'))
        metadata.seek(0)
        add(tarFile, metadata, 'metadata.txt')

    tarFile.close()


def wrongFileTypes(temporaryFile):
    tarFile = tarfile.open(temporaryFile, 'w:bz2')

    with tempfile.NamedTemporaryFile() as data:
        data.write('O\x01_\x07+#\x0c\xd57\x8e\xb4\xf7,\xca/\x04\x80\xe3\x1a S\xb0o\xafc\x8a\x8b\xf2f\x81\xccG\xe2\x89\xfd\xd19\x9c\xcd\r\xc9]^\x81#\xffp\xc1\xf9\x07\xf4\xea\xc3\xbb"\x04&)\xb5\xd4\xad\x91\xe7\xee\t\x88u\xbf\x08T\x01I\x16\x8a\x90>\xe1u\x00\xceS\x9b6 \xd3\x90\xcey\xfa\xa5\xbe\x95Bc\xff\x92f\x8c\x0bu')
        data.seek(0)
        add(tarFile, data, 'data.db')

    with tempfile.NamedTemporaryFile() as metadata:
        metadata.write('Bzt7025jPichcoj5jXAdkPtpJ4TGOVHjkq\nByEfI9cJ9zCbFmqsiPr4Ro5oGgQE\nax2wYvOettAcwe4HVfjpENnov06yBlCBlkS')
        metadata.seek(0)
        add(tarFile, metadata, 'metadata.txt')

    tarFile.close()


def createTestFile(f, overwriteFileHash = None):
    '''Create test file.
    '''

    temporaryFile = 'upload.tar.bz2'

    logging.info('%s: Creating file...', temporaryFile)
    f(temporaryFile)

    fileHash = hashlib.sha1()

    with open(temporaryFile, 'rb') as f:
        while True:
            data = f.read(4 * 1024 * 1024)
            if not data:
                break
            fileHash.update(data)

    fileHash = fileHash.hexdigest()

    logging.info('%s: Hash: %s', temporaryFile, fileHash)

    if overwriteFileHash is not None:
        logging.info('%s: Overwriting file hash: %s', temporaryFile, overwriteFileHash)
        fileHash = overwriteFileHash

    logging.info('%s: Saving file...', temporaryFile)
    os.rename(temporaryFile, os.path.join(config.securityTestFilesPath, fileHash))


def main():
    '''Entry point.
    '''

    # Wrong checksums
    createTestFile(wrongBzip2File, '123')
    createTestFile(wrongBzip2File, '11a0c09404dddb79a4bd952dfd4b0c37824d6cd51')
    createTestFile(wrongBzip2File, '01a0c09404dddb79a4bd952dfd4b0c37824d6cd5')
    createTestFile(wrongBzip2File, '11a0c09404dddb79a4bd952dfd4b0c37824d6cv5')

    
    createTestFile(wrongBzip2File)
    createTestFile(wrongFileNames)
    createTestFile(wrongMetadataFile)
    createTestFile(wrongJSON)
    createTestFile(wrongFileTypes)


if __name__ == '__main__':
    logging.basicConfig(
        format = '[%(asctime)s] %(levelname)s: %(message)s',
        level = logging.INFO,
    )

    sys.exit(main())

