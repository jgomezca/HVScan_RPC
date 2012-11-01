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

import metadata
import doUpload

import config
import Dropbox

dropBoxReplayFilesFolder = '/afs/cern.ch/work/g/govi/dropbox'
dropBoxSnapshotTimestamp = datetime.datetime(2012, 8, 31, 7, 0, 0)
replayMasterDB = '/afs/cern.ch/cms/DB/conddb/test/dropbox/replay/replayMaster.db'


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

    # Calculate the old dropBox non-empty runs that will be replayed, with their corresponding files
    files = getFiles()
    for fileName in sorted(files, key = lambda x: files[x]):
        dropBoxTimestamp = getNextDropBoxRunTimestamp(files[fileName])
        logging.debug('%s: %s -> %s', fileName.split('@')[1], files[fileName], dropBoxTimestamp)
        dropBoxRuns.setdefault(dropBoxTimestamp, set([])).add(fileName)

    # Validate that the first run is the one expected
    sortedDropBoxRuns = sorted(dropBoxRuns)
    if sortedDropBoxRuns[0] != dropBoxFirstRun[0] or dropBoxRuns[dropBoxFirstRun[0]] != dropBoxFirstRun[1]:
        raise Exception('The expected first dropBox run is not the same as the calculated one.')

    # Ask the frontend to clean up the files and database
    (username, account, password) = netrc.netrc().authenticators('newOffDb')
    frontendHttp = http.HTTP()
    frontendHttp.setBaseUrl(doUpload.frontendBaseUrl)

    logging.info('Signing in the frontend...')
    frontendHttp.query('signIn', {
        'username': username,
        'password': password,
    })

    logging.info('Asking the frontend to clean up files and database...')
    frontendHttp.query('cleanUp')

    logging.info('Signing out the frontend...')
    frontendHttp.query('signOut')

    conf = config.replay()

    cleanUpCommand = "cmscond_schema_manager" + \
                  " -c " + conf.destinationDB + \
                  " -P " + conf.authpath + \
                  " --dropAll "

    logging.info('Cleaning up: executing command %s' %(cleanUpCommand))
    cleanUpProc = subprocess.Popen(cleanUpCommand, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (stdoutdata, stderrdata) =  cleanUpProc.communicate()
    retcode = cleanUpProc.returncode

    if ( retcode != 0 ):
        if(stdoutdata != None ):
            logging.error(stdoutdata)
        if(stderrdata != None ):
            logging.error(stderrdata)
        return False

    exportCommand = "cmscond_export_database" + \
                  " -s sqlite_file:" + replayMasterDB + \
                  " -d " + conf.destinationDB + \
                  " -P " + conf.authpath 

    logging.info('Setting up: executing command %s' %(exportCommand))
    exportUpProc = subprocess.Popen(exportCommand, shell=True, stdout=None, stderr=None, stdin=subprocess.PIPE)
    (stdoutdata, stderrdata) =  exportUpProc.communicate('Y\n')
    retcode = exportUpProc.returncode

    if ( retcode != 0 ):
        if(stdoutdata != None ):
            logging.error(stdoutdata)
        if(stderrdata != None ):
            logging.error(stderrdata)
        return False

    dropBoxBE = Dropbox.Dropbox( conf )

    # Replay all the runs
    i = 0
    for runTimestamp in sortedDropBoxRuns:
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
                doUpload.upload('/tmp/replayRequest')
            except doUpload.UploadError as e:
                # If it is a error from the server (i.e. UploadError),
                # we can continue with the next files.
                # If it is another kind, we do not catch it since in that case
                # it is a real problem with the upload.py script.
                logging.info('  [%s/%s] %s: Upload error: %s', j, len(dropBoxRuns[runTimestamp]), fileName, str(e))

        dropBoxBE.reprocess( runTimestamp )


if __name__ == '__main__':
    # This is a test like test.py (although special)
    service.setupTest()
    main()

