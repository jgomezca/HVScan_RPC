'''Script that merges the output from runInfoChecker.py which maps
files to pairs (hltRun, tier0Run) to another dictionary that maps
an old dropBox run to a single merged pair (hltRun, tier0Run), if possible.
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = ['Giacomo Govi', 'Salvatore Di Guida', 'Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


import json
import logging

import service

import replay


def merge(a, b):
    if a is None:
        return b
    if b is None:
        return a
    if a != b:
        logging.warning('%s != %s' % (a, b))
        #raise Exception('%s != %s' % (a, b))
    return a


def main():
    dropBoxRuns = replay.calculateOldDropBoxRuns()

    with open('/afs/cern.ch/cms/DB/conddb/test/dropbox/replay/runInfoFromLogForReplay.json', 'rb') as f:
        filesPairs = json.load(f)

    dropBoxRunsPairs = {}
    emptyPairs = 0

    # Replay all the runs
    i = 0
    for runTimestamp in sorted(dropBoxRuns):
        i += 1
        logging.info('[%s/%s] %s: Replaying run...', i, len(dropBoxRuns), runTimestamp)

        mergedPair = [None, None]

        j = 0
        for fileName in dropBoxRuns[runTimestamp]:
            j += 1
            fileName = '%s.db' % fileName[:-len('.tar.bz2')]
            if fileName in filesPairs:
                pair = filesPairs[fileName]
            else:
                pair = (None, None)
            logging.info('  [%s/%s] %s: %s...', j, len(dropBoxRuns[runTimestamp]), fileName, pair)

            mergedPair[0] = max(mergedPair[0], pair[0])
            mergedPair[1] = max(mergedPair[1], pair[1])

        if mergedPair[0] is None and mergedPair[1] is None:
            emptyPairs += 1

        dropBoxRunsPairs[runTimestamp.strftime('%Y-%m-%d %H:%M:%S,%f')[:-3]] = mergedPair

    logging.info('Empty pairs: %s', emptyPairs)

    with open('runInfo.json', 'wb') as f:
        f.write(service.getPrettifiedJSON(dropBoxRunsPairs))


if __name__ == '__main__':
    service.setupTest()
    main()

