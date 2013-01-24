#!/usr/bin/env python2.6
'''Script that downloads files from the production database
with their original filenames, between two given hashes in time (inclusive).
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

import database
import service


def downloadFiles(beginHash, endHash, outputPath):
    '''Downloads files from the production database with their original
    filenames, between two given hashes in time (inclusive).
    '''

    connection = database.Connection(service.secrets['connections']['pro'])

    fileList = connection.fetch('''
        select fileHash, fileName
        from files
        where creationTimestamp >= (
            select creationTimestamp
            from files
            where fileHash = :s
        ) and creationTimestamp <= (
            select creationTimestamp
            from files
            where fileHash = :s
        ) and state = 'Acknowledged'
        order by creationTimestamp
    ''', (beginHash, endHash))

    if len(fileList) == 0:
        logging.error('Empty file list. Make sure you typed the correct hashes and that the beginHash was first in time.')
        return -1

    logging.info('File list:')
    for (fileHash, fileName) in fileList:
        logging.info('  %s %s', fileHash, fileName)

    if 'y' != raw_input('Download? [y] ').strip().lower():
        logging.error('Aborted by user.')
        return -1

    for (fileHash, fileName) in fileList:
        logging.info('Downloading %s %s...', fileHash, fileName)

        with open(os.path.join(outputPath, '%s.tar.bz2' % fileName), 'wb') as f:
            f.write(connection.fetch('''
            select fileContent
            from files
            where fileHash = :s
        ''', (fileHash, ))[0][0])


def main():
    '''Entry point.
    '''

    beginHash = raw_input('beginHash: ')
    endHash = raw_input('endHash: ')
    outputPath = raw_input('outputPath: ')

    return downloadFiles(beginHash, endHash, outputPath)


if __name__ == '__main__':
    logging.basicConfig(
        format = '[%(asctime)s] %(levelname)s: %(message)s',
        level = logging.INFO,
    )

    sys.exit(main())

