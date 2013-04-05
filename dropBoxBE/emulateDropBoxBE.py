#!/usr/bin/env python2.6
'''Script that emulates a dropBoxBE to finish an upload.

This script was written to finish updating the status and uploading the logs
for three uploads done on 2013-02-06, since updating/uploading status/code
failed since the CERN SSO session expired due to extremely long exportations
due to a huge load in the Oracle cms_orcon_prod database.

Then it was improved to allow for multiple uploads easily and to avoid having
to split the web logs into the downloadLog and globalLog, since we needed
to perform 5 manual updates after the daylight saving time issue.

To use it, carefully craft the required files at runPath and then run:

  keeper.py run dropBoxBE emulateDropBoxBE.py

Note: You will need to uncomment the dropBoxBE in the keeper/config.py.

The script asks before doing something, so you can do only a subset of
the operations as needed and review them beforehand.

Create a folder which contains:

  * files.json: a list of runs with their properties and files. Looks like [1].
  * <fileHash>.log: the fileLog per file, you can copy it directly from
    the backend unchanged, including the filename.
  * <runCreationTimestamp>.log: the web log per file. See below.

The hard part about the procedure is to get the proper downloadLogs and runLogs.
Therefore, instead of manually splitting them into downloadLogs and runLogs,
we just simple use empty downloadLogs with just this line:

    # Manual upload: see the globalLog for the full web log.

And for the globalLogs, we copy the relevant portion of the web log, from:

    INFO: Processing all files...

to:

    INFO: Processing all files done; waiting 30 seconds for the next run.

and we add this line in the top:

    # Manual upload: this is the full web log.

This simplifies things and allows for more automatic uploads,
without lose of information. Adding these lines is automatic and is done by
this script. Therefore, you only need to provide the web log in
the <runCreationTimestamp>.log files.

See an example of the files in the folder in [2] for [1].

Note: The <runCreationTimestamp>.log files contain a space in the name.

[1]

[
["2013-04-03 10:20:27,821", "online", 9999, -10, 212234, [["a2fd5987b989a9c57e091ec42ff7f9dd0e71aa69", 4999], ["bcc394929086b313fc47dce67d23bc0b604102ff", 4999]]],
["2013-04-03 10:21:04,146", "online", 9999, -10, 212234, [["e881544be662aee0c288357d0724968c4ecfb35d", 4999]]],
["2013-04-03 10:21:37,720", "online", 9999, -10, 212234, [["5e94c68b203c610037dc56dc3250a2cce0daa40a", 4999], ["83512bc95265f70c0cc5ad35007223d2b940f816", 4999]]],
["2013-04-03 17:20:02,276", "online", 9999, -10, 212234, [["6baa28e382c79f20be74caa40b230d6f3548c4ac", 4999]]],
["2013-04-03 17:28:58,632", "online", 9999, -10, 212234, [["a0143e8075e79c762671d409f63ec3ba6ff48dc1", 4999]]]
]

[2]

files.json
2013-04-03 10:20:27,821.log
2013-04-03 10:21:04,146.log
2013-04-03 10:21:37,720.log
2013-04-03 17:20:02,276.log
2013-04-03 17:28:58,632.log
5e94c68b203c610037dc56dc3250a2cce0daa40a.log
6baa28e382c79f20be74caa40b230d6f3548c4ac.log
83512bc95265f70c0cc5ad35007223d2b940f816.log
a0143e8075e79c762671d409f63ec3ba6ff48dc1.log
a2fd5987b989a9c57e091ec42ff7f9dd0e71aa69.log
bcc394929086b313fc47dce67d23bc0b604102ff.log
e881544be662aee0c288357d0724968c4ecfb35d.log
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2013, CERN CMS'
__credits__ = ['Giacomo Govi', 'Salvatore Di Guida', 'Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


import sys
import logging
import os
import json

import service

import config
import StatusUpdater


runsPath = '~/dropBoxEmulate/'

downloadLog = '# Manual upload: see the globalLog for the full web log.\n'
globalLogPrefix = '# Manual upload: this is the full web log.\n'


def main():
    '''Entry point.
    '''

    with open(os.path.join(os.path.expanduser(runsPath), 'files.json'), 'rb') as f:
        runs = json.loads(f.read())

    for (runLogCreationTimestamp, runBackend, runStatus, fcsRun, hltRun, files) in runs:
        runLogCreationTimestamp = str(runLogCreationTimestamp)
        runBackend = str(runBackend)

        logging.info('Run %s: %s, %s, %s, %s', runLogCreationTimestamp, runBackend, runStatus, fcsRun, hltRun)


        # Create the emulated statusUpdater

        if runBackend == 'online':
            cfg = config.online()
        elif runBackend == 'tier0':
            cfg = config.tier0()
        elif runBackend == 'offline':
            cfg = config.offline()
        else:
            raise Exception('Unsupported backend to emulate.')

        cfg.proxy = None

        statusUpdater = StatusUpdater.StatusUpdater(cfg)
        statusUpdater.creationTimeStamp = runLogCreationTimestamp
        statusUpdater.backend = runBackend


        # Ask and run actions

        if raw_input('updateRunStatus(%s). Are you sure? ' % runStatus).lower() == 'y':
            statusUpdater.updateRunStatus(runStatus)
        else:
            logging.warning('Skipped.')

        if raw_input('updateRunRunInfo(%s, %s). Are you sure? ' % (fcsRun, hltRun)).lower() == 'y':
            statusUpdater.updateRunRunInfo(fcsRun, hltRun)
        else:
            logging.warning('Skipped.')

        with open(os.path.join(os.path.expanduser(runsPath), '%s.log' % runLogCreationTimestamp), 'rb') as f:
            globalLog = globalLogPrefix + f.read()

        if raw_input('uploadRunLog(%s, %s). Are you sure? ' % (repr(downloadLog), repr(globalLog))).lower() == 'y':
            statusUpdater.uploadRunLog(downloadLog, globalLog)
        else:
            logging.warning('Skipped.')

        for (fileHash, fileStatus) in files:
            fileHash = str(fileHash)

            logging.info('    File %s: %s', fileHash, fileStatus)

            with open(os.path.join(os.path.expanduser(runsPath), '%s.log' % fileHash), 'rb') as f:
                fileLog = f.read()

            if raw_input('statusUpdater.updateFileStatus(%s, %s). Are you sure? ' % (repr(fileHash), fileStatus)).lower() == 'y':
                statusUpdater.updateFileStatus(fileHash, fileStatus)
            else:
                logging.warning('Skipped.')

            if raw_input('statusUpdater.uploadFileLog(%s, %s). Are you sure? ' % (repr(fileHash), repr(fileLog))).lower() == 'y':
                statusUpdater.uploadFileLog(fileHash, fileLog)
            else:
                logging.warning('Skipped.')


if __name__ == '__main__':
    logging.basicConfig(
        format = '[%(asctime)s] %(levelname)s: %(message)s',
        level = logging.INFO,
    )

    sys.exit(main())

