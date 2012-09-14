#!/usr/bin/env python2.6
'''Script that ports old dropBox metadata to the new JSON format.
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
import json


def portMetadata(inputFilename):
    '''Ports metadata.
    '''

    logging.info('%s: Porting...', inputFilename)

    outputFilename = '%s.out' % inputFilename
    backupFilename = '%s.backup' % inputFilename
    outputMetadata = {}

    with open(inputFilename, 'rb') as f:
        try:
            json.load(f)
            logging.warning('%s: Looks like JSON, i.e. probably already ported to the new format. Skipping...', inputFilename)
            return
        except ValueError:
            pass

        f.seek(0)

        for line in f.readlines():
            (key, x, value) = line.strip().partition(' ')

            # Ignore empty lines
            if key == '':
                continue

            key = key.lower()

            if key == 'destdb':
                outputMetadata['destDB'] = value
            elif key == 'tag':
                outputMetadata['destTag'] = value
            elif key == 'inputtag':
                outputMetadata['inputTag'] = value
            elif key == 'since':
                if value != '':
                    outputMetadata['since'] = int(value)
            elif key == 'iovcheck':
                outputMetadata['exportTo'] = value
            elif key == 'timetype':
                outputMetadata['timeType'] = value
            elif key in ['duplicatetaghlt', 'duplicatetagexpress', 'duplicatetagprompt', 'duplicatetagpcl']:
                if value != '':
                    outputMetadata.setdefault('duplicateTo', {}).setdefault(key.split('duplicatetag')[1], []).append(value)
            elif key == 'usertext':
                outputMetadata['usertext'] = value
            else:
                raise Exception('Invalid key')


    with open(outputFilename, 'wb') as f:
        json.dump(outputMetadata, f, sort_keys = True, indent = 4)


    os.rename(inputFilename, backupFilename)
    os.rename(outputFilename, inputFilename)


def main():
    '''Entry point.
    '''

    parser = optparse.OptionParser(usage =
        'Usage: %prog <file> [<file> ...]\n'
    )

    (options, arguments) = parser.parse_args()

    if len(arguments) < 1:
        parser.print_help()
        return -3

    for argument in arguments:
        portMetadata(argument)


if __name__ == '__main__':
    logging.basicConfig(
        format = '[%(asctime)s] %(levelname)s: %(message)s',
        level = logging.INFO,
    )

    sys.exit(main())

