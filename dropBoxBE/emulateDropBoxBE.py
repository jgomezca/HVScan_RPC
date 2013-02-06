#!/usr/bin/env python2.6
'''Script that emulates a dropBoxBE to finish an upload.

This script was written to finish updating the status and uploading the logs
for three uploads done on 2013-02-06, since updating/uploading status/code
failed since the CERN SSO session expired due to extremely long exportations
due to a huge load in the Oracle cms_orcon_prod database which, at the time
of writing, it is still under investigation.

To use it, carefully modify the parameters below and then run:

  keeper.py run dropBoxBE emulateDropBoxBE.py

Note: you will need to extract the real logs from the real backend and divide
them into the fileLog/downloadLog/globalLog as required.

Note: if the run processed more than one file, run the script once for the
first one, and then set updateRunLog to False, since the "runLog" is common
for both and you shouldn't upload it more than once.

Note: you will need to uncomment the dropBoxBE in the keeper/config.py.
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2013, CERN CMS'
__credits__ = ['Giacomo Govi', 'Salvatore Di Guida', 'Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


import sys
import logging

import service

import config
import StatusUpdater


fileHash = '725eec71893884224fee4b0c7638f5ceeceabe99'
creationTimeStamp = '2013-02-06 16:51:02,200'
backend = 'tier0'
fileStatus = 4210
runStatus = 9910
fileLogPath = 'fileLog.log'
downloadLogPath = 'downloadLog.log'
globalLogPath = 'globalLog.log'
updateRunLog = False


def main():
    '''Entry point.
    '''

    if backend == 'online':
        cfg = config.online()
    elif backend == 'tier0':
        cfg = config.tier0()
    elif backend == 'offline':
        cfg = config.offline()
    else:
        raise Exception('Unsupported backend to emulate.')

    cfg.proxy = None

    with open(fileLogPath, 'r') as f:
        fileLog = f.read()

    with open(downloadLogPath, 'r') as f:
        downloadLog = f.read()

    with open(globalLogPath, 'r') as f:
        globalLog = f.read()

    logging.info('downloadLog = \n[[[\n%s\n]]]', downloadLog)
    logging.info('globalLog = \n[[[\n%s\n]]]', globalLog)
    logging.info('fileLog = \n[[[\n%s\n]]]', fileLog)
    logging.info('fileHash = %s', fileHash)
    logging.info('creationTimeStamp = %s', creationTimeStamp)
    logging.info('backend = %s', backend)
    logging.info('fileStatus = %s', fileStatus)
    logging.info('runStatus = %s', runStatus)
    logging.info('updateRunLog = %s', updateRunLog)
    logging.info('baseUrl = %s', cfg.baseUrl)

    if raw_input('Are you sure? ').lower() != 'y':
        logging.error('Stopped.')
        return -1

    statusUpdater = StatusUpdater.StatusUpdater(cfg)
    statusUpdater.creationTimeStamp = creationTimeStamp
    statusUpdater.backend = backend
    statusUpdater.updateFileStatus(fileHash, fileStatus)
    statusUpdater.uploadFileLog(fileHash, fileLog)
    if updateRunLog:
        statusUpdater.uploadRunLog(downloadLog, globalLog)
        statusUpdater.updateRunStatus(runStatus)


if __name__ == '__main__':
    logging.basicConfig(
        format = '[%(asctime)s] %(levelname)s: %(message)s',
        level = logging.INFO,
    )

    sys.exit(main())

