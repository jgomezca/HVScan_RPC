'''Code for querying the CMSSW's lumiCalc2.py.

lumiCalc2.py (and related scripts) cannot be easily used as an imported module,
so we decided to create an abstraction layer for the time being.
'''


__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2013, CERN CMS'
__credits__ = ['Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


import os
import subprocess
import datetime
import csv
import tempfile
import logging


dateFormat = '%m/%d/%y %H:%M:%S'


def runProcess(begin, end, csvFilename):
    '''Returns the lumiCalc2.py process that will query the Lumi service.
    The range can be specified by run numbers, fill numbers or datetimes.
    '''

    if isinstance(begin, datetime.datetime):
        begin = begin.strftime(dateFormat)

    if isinstance(end, datetime.datetime):
        end = end.strftime(dateFormat)

    cmd  = 'export PYTHONPATH=/data/utilities/lib/python2.6/site-packages/:$PYTHONPATH ; '
    cmd += 'cd /afs/cern.ch/cms/slc5_amd64_gcc472/cms/cmssw/CMSSW_6_2_0_pre1/src/ ; eval `scram run -sh` ; '
    cmd += "lumiCalc2.py --begin '%s' --end '%s' -o '%s' overview " % (begin, end, csvFilename)

    logging.debug('Running: %s', cmd)

    return subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def parseCSV(csvFile, lumiType):
    '''Parses the CSV files from lumiCalc2, returning a dictionary where
    the keys are the run numbers and the values can be the 'delivered' (/ub)
    or 'recorded' (/ub), depending on lumiType.
    '''

    if lumiType not in ['delivered', 'recorded']:
        raise Exception('Invalid lumiType')

    csvReader = csv.reader(csvFile)

    # Ignore the headers in the first line:
    # Run:Fill,DeliveredLS,Delivered(/ub),SelectedLS,Recorded(/ub)
    csvReader.next()

    # CSV fields look like:
    # 161210:1645,44,6.287026587401057,[1-38],5.189176823798077
    output = {}
    for runFill, delLS, delUb, selLS, recUb in csvReader:
        run = int(runFill.split(':')[0])

        if lumiType == 'delivered':
            output[run] = float(delUb)
        elif lumiType == 'recorded':
            output[run] = float(recUb)

    return output


def waitProcess(process, csvFile, lumiType):
    '''Wait for a process querying the Lumi service to finish and returns
    the results as given by parseCSV.
    '''

    result = process.communicate()

    if '[INFO] No qualified data found, do nothing' in ''.join(result):
        logging.debug('lumiCalc2.py found no data')
        return {}

    if not os.path.exists(csvFile.name):
        logging.error('no CSV file from lumiCalc2.py')
        return {}

    return parseCSV(csvFile, lumiType)


def query(begin, end, lumiType):
    '''Synchronously queries the Lumi service.

    If you need parallel or asynchronous queries, use runProcess()
    and waitProcess() separately instead.
    '''

    with tempfile.NamedTemporaryFile(dir = '/data/files/getLumi') as f:
        return waitProcess(runProcess(begin, end, f.name), f, lumiType)

