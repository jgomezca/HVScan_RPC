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
dropBoxSnapshotTimestamp = datetime.datetime(2012, 8, 31, 7, 0, 0)


# Just for validation
dropBoxFirstRun = (datetime.datetime(2012, 8, 31, 10, 30), set([
    'BeamSpotObjects_PCL_byRun_v0_offline@d5474f75-8f5c-4851-bbb9-937d86409bed.tar.bz2',
    'BeamSpotObjects_PCL_byLumi_v0_prompt@2a13ed55-b5d9-4658-9266-3ad1181b1d75.tar.bz2',
    'SiStripBadChannel_PCL_v0_offline@e5c9f19f-b83f-48d4-85ff-5e6a3b97b75d.tar.bz2',
]))


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


def getFiles():
    '''Returns a dictionary mapping the files to be replayed to their
    modification timestamp.

    This is used by getReplayTags.py as well.
    '''

    files = {}
    for fileName in os.listdir(dropBoxReplayFilesFolder):
        timestamp = datetime.datetime.fromtimestamp(os.stat(os.path.join(dropBoxReplayFilesFolder, fileName)).st_mtime)
        if timestamp < dropBoxSnapshotTimestamp:
            continue
        files[fileName] = timestamp

    return files


def main():
    dropBoxRuns = {}

    files = getFiles()
    for fileName in sorted(files, key = lambda x: files[x]):
        dropBoxTimestamp = getNextDropBoxRunTimestamp(files[fileName])
        logging.debug('%s: %s -> %s', fileName.split('@')[1], files[fileName], dropBoxTimestamp)
        dropBoxRuns.setdefault(dropBoxTimestamp, set([])).add(fileName)

    sortedDropBoxRuns = sorted(dropBoxRuns)
    if sortedDropBoxRuns[0] != dropBoxFirstRun[0] or dropBoxRuns[dropBoxFirstRun[0]] != dropBoxFirstRun[1]:
        raise Exception('The expected first dropBox run is not the same as the calculated one.')

    # TODO: Prepare database from the sqlite file

    i = 0
    for runTimestamp in sortedDropBoxRuns:
        i += 1
        logging.info('[%s/%s] Replaying run %s...', i, len(dropBoxRuns), runTimestamp)

        for fileName in dropBoxRuns[runTimestamp]:
            logging.info('      Uploading %s...', fileName)
            # TODO: Upload the fie

        # TODO: Run the DropBox giving the runTimestamp


if __name__ == '__main__':
    # This is a test like test.py (although special)
    service.setupTest()
    main()

