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
import tarfile
import netrc
import subprocess

import http
import service
import conditionDatabase

import metadata
import doUpload

import config
import Dropbox

dropBoxReplayFilesFolder = '/afs/cern.ch/work/g/govi/dropbox'
dropBoxStartSnapshotTimestamp = datetime.datetime(2012, 8, 31, 7, 0, 0)
dropBoxEndSnapshotTimestamp = datetime.datetime(2012, 11, 2, 18, 0, 0)
replayMasterDB = '/afs/cern.ch/cms/DB/conddb/test/dropbox/replay/replayMaster.db'


# Just for validation
dropBoxFirstRun = (datetime.datetime(2012, 8, 31, 10, 30), set([
    'BeamSpotObjects_PCL_byRun_v0_offline@d5474f75-8f5c-4851-bbb9-937d86409bed.tar.bz2',
    'BeamSpotObjects_PCL_byLumi_v0_prompt@2a13ed55-b5d9-4658-9266-3ad1181b1d75.tar.bz2',
    'SiStripBadChannel_PCL_v0_offline@e5c9f19f-b83f-48d4-85ff-5e6a3b97b75d.tar.bz2',
]))

dropBoxLastRun = (datetime.datetime(2012, 11, 2, 16, 10), set([
    'BeamSpotObjects_PCL_byRun_v0_offline@fa7d1216-c899-4610-9298-758a43e6a2a8.tar.bz2',
    'BeamSpotObjects_PCL_byLumi_v0_prompt@a4a033a1-1a7e-42b9-b55b-51743e4e9385.tar.bz2',
    'SiStripBadChannel_PCL_v0_offline@d3d46531-7783-483a-9488-c6ec7a9f156b.tar.bz2',
]))


# To simulate manual interventions
truncates = {
    datetime.datetime(2012, 10, 17, 13, 30): {
        205233: [
            'BeamSpotObjects_PCL_byRun_v0_offline',
            'BeamSpotObjects_PCL_byRun_v0_prompt',
            'BeamSpotObjects_PCL_byLumi_v0_prompt',
            'SiStripBadChannel_PCL_v0_offline',
            'SiStripBadChannel_PCL_v0_prompt',
        ],
    },
}


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
        if timestamp < dropBoxStartSnapshotTimestamp:
            continue
        if timestamp > dropBoxEndSnapshotTimestamp:
            continue
        files[fileName] = timestamp

    return files


def execute(command, stdin = None):
    logging.info('Executing %s...', repr(command))

    process = subprocess.Popen(command, shell = True, stdin = subprocess.PIPE, stdout = None, stderr = None)
    (stdout, stderr) = process.communicate(stdin)
    returnCode = process.returncode

    if returnCode != 0:
        raise Exception('Executing %s failed with return code %s: stdout = %s, stderr = %s', repr(command), returnCode, repr(stdout), repr(stderr))


def calculateOldDropBoxRuns():
    '''Returns a dictionary mapping an old dropBox run (timestamp) to its files.

    This is used by runInfoMerger.py as well.
    '''

    dropBoxRuns = {}

    # Calculate the old dropBox non-empty runs that will be replayed, with their corresponding files
    files = getFiles()
    for fileName in sorted(files, key = lambda x: files[x]):
        dropBoxTimestamp = getNextDropBoxRunTimestamp(files[fileName])
        logging.debug('%s: %s -> %s', fileName.split('@')[1], files[fileName], dropBoxTimestamp)
        dropBoxRuns.setdefault(dropBoxTimestamp, set([])).add(fileName)

    # Validate that the first and last run are the expected ones
    sortedDropBoxRuns = sorted(dropBoxRuns)
    if sortedDropBoxRuns[0] != dropBoxFirstRun[0] or dropBoxRuns[dropBoxFirstRun[0]] != dropBoxFirstRun[1]:
        raise Exception('The expected first dropBox run is not the same as the calculated one.')
    if sortedDropBoxRuns[-1] != dropBoxLastRun[0] or dropBoxRuns[dropBoxLastRun[0]] != dropBoxLastRun[1]:
        raise Exception('The expected last dropBox run is not the same as the calculated one.')

    return dropBoxRuns


def main():
    dropBoxRuns = calculateOldDropBoxRuns()

    # Ask the frontend to clean up the files and database
    (username, account, password) = netrc.netrc().authenticators('newOffDb')
    frontendHttp = http.HTTP()
    frontendHttp.setBaseUrl(doUpload.frontendUrlTemplate % doUpload.frontendHost)

    logging.info('Signing in the frontend...')
    frontendHttp.query('signIn', {
        'username': username,
        'password': password,
    })

    logging.info('Asking the frontend to clean up files and database...')
    frontendHttp.query('cleanUp')

    logging.info('Signing out the frontend...')
    frontendHttp.query('signOut')

    logging.info('Removing files in the backend...')
    execute('rm -rf ../NewOfflineDropBoxBaseDir/TestDropBox/*/*')

    conf = config.replay()

    logging.info('Cleaning up backend database...')
    execute('cmscond_schema_manager -c %s -P %s --dropAll' % (conf.destinationDB, conf.authpath))

    logging.info('Setting up backend database...')
    execute('cmscond_export_database -s sqlite_file:%s -d %s -P %s' % (replayMasterDB, conf.destinationDB, conf.authpath), 'Y\n')

    dropBoxBE = Dropbox.Dropbox( conf )

    # Replay all the runs
    _fwLoad = conditionDatabase.condDB.FWIncantation()

    i = 0
    for runTimestamp in sorted(dropBoxRuns):
        i += 1
        logging.info('[%s/%s] %s: Replaying run...', i, len(dropBoxRuns), runTimestamp)

        j = 0
        for fileName in dropBoxRuns[runTimestamp]:
            j += 1
            logging.info('  [%s/%s] %s: Converting...', j, len(dropBoxRuns[runTimestamp]), fileName)

            tarFile = tarfile.open(os.path.join(dropBoxReplayFilesFolder, fileName))

            names = tarFile.getnames()
            if len(names) != 2:
                raise Exception('%s: Invalid number of files in tar file.', fileName)

            baseFileName = names[0].rsplit('.', 1)[0]
            dbFileName = '%s.db' % baseFileName
            txtFileName = '%s.txt' % baseFileName
            if set([dbFileName, txtFileName]) != set(names):
                raise Exception('%s: Invalid file names in tar file.', fileName)

            # This one is to easily inspect the old metadata in case the porting fails
            oldMetadata = tarFile.extractfile(txtFileName).read()
            with open('/tmp/replayRequest.old', 'wb') as f:
                f.write(oldMetadata)

            with open('/tmp/replayRequest.txt', 'wb') as f:
                f.write(metadata.port(oldMetadata))

            with open('/tmp/replayRequest.db', 'wb') as f:
                f.write(tarFile.extractfile(dbFileName).read())

            tarFile.close()

            logging.info('  [%s/%s] %s: Uploading...', j, len(dropBoxRuns[runTimestamp]), fileName)

            try:
                doUpload.upload('/tmp/replayRequest', 'private')
            except doUpload.UploadError as e:
                # If it is a error from the server (i.e. UploadError),
                # we can continue with the next files.
                # If it is another kind, we do not catch it since in that case
                # it is a real problem with the upload.py script.
                logging.info('  [%s/%s] %s: Upload error: %s', j, len(dropBoxRuns[runTimestamp]), fileName, str(e))

        dropBoxBE.reprocess(runTimestamp)

        if runTimestamp in truncates:
            for runNumber in truncates[runTimestamp]:
                for tag in truncates[runTimestamp][runNumber]:
                    logging.info('[%s/%s] %s: Truncating up to %s tag %s...', i, len(dropBoxRuns), runTimestamp, runNumber, tag)

                    while True:
                        # FIXME: Why can't we instantiate the RDBMS once?
                        db = conditionDatabase.condDB.RDBMS(conf.authpath).getReadOnlyDB(conf.destinationDB)
                        iov = conditionDatabase.IOVChecker(db)
                        iov.load(tag)

                        lastSince = iov.lastSince()
                        if iov.timetype() == 'lumiid':
                            lastSince >>= 32

                        db.closeSession()

                        logging.info('[%s/%s] %s: lastSince now is %s...', i, len(dropBoxRuns), runTimestamp, lastSince)

                        if lastSince < runNumber:
                            break

                        execute('cmscond_truncate_iov -c %s -P %s -t %s' % (conf.destinationDB, conf.authpath, tag))


if __name__ == '__main__':
    # This is a test like test.py (although special)
    service.setupTest()
    main()

