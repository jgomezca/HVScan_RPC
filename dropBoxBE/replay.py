'''dropBox backend's script that replays the original dropBox files in the new dropBox.
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = ['Giacomo Govi', 'Salvatore Di Guida', 'Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


import os
import datetime
import logging

import service


dropBoxReplayFilesFolder = '/afs/cern.ch/work/m/mojedasa/dropBoxReplayFiles'
dropBoxSnapshotTimestamp = datetime.datetime(2012, 8, 31)


def getNextDropBoxRunTimestamp(timestamp):
    '''Given a timestamp, give the timestamp of the next dropBox run.
    i.e. the closest in the future.
    '''

    closeDropBoxRuns = [
        timestamp.replace(minute = 0, second = 0, microsecond = 0),
        timestamp.replace(minute = 10, second = 0, microsecond = 0),
        timestamp.replace(minute = 20, second = 0, microsecond = 0),
        timestamp.replace(minute = 30, second = 0, microsecond = 0),
        timestamp.replace(minute = 40, second = 0, microsecond = 0),
        timestamp.replace(minute = 50, second = 0, microsecond = 0),
        timestamp.replace(minute = 0, second = 0, microsecond = 0)
            + datetime.timedelta(hours = 1),
    ]

    for run in closeDropBoxRuns:
        if timestamp < run:
            return run

    raise Exception('This should not happen.')


def main():
    dropBoxRuns = {}

    fileNames = os.listdir(dropBoxReplayFilesFolder)

    files = {}
    for fileName in fileNames:
        timestamp = datetime.datetime.fromtimestamp(os.stat(os.path.join(dropBoxReplayFilesFolder, fileName)).st_mtime)
        if timestamp < dropBoxSnapshotTimestamp:
            continue
        files[fileName] = timestamp

    for fileName in sorted(files, key = lambda x: os.stat(os.path.join(dropBoxReplayFilesFolder, x)).st_mtime):
        dropBoxTimestamp = getNextDropBoxRunTimestamp(files[fileName])
        logging.debug('%s: %s -> %s', fileName.split('@')[1], files[fileName], dropBoxTimestamp)
        dropBoxRuns.setdefault(dropBoxTimestamp, set([])).add(fileName)

    # TODO: Prepare database from the sqlite file

    i = 0
    for runTimestamp in sorted(dropBoxRuns):
        i += 1
        logging.info('[%s/%s] Replaying run %s...', i, len(dropBoxRuns), runTimestamp)

        for fileName in dropBoxRuns[runTimestamp]:
            logging.info('      Uploading %s...', fileName)
            # TODO: Upload the fie

        # TODO: Run the DropBox giving the runTimestamp


if __name__ == '__main__':
    main()

