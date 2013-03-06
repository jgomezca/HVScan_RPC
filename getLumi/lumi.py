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

import cache


dateFormat = '%m/%d/%y %H:%M:%S'
maxProcesses = 2
expirationTime = 4 * 60 * 60 # 4 hours


class LumiError(Exception):
    '''A Lumi exception.
    '''

class BusyLumiError(Exception):
    '''Lumi is busy with other requests.

    i.e. the number of processes have reached the limit.
    '''


def check_output(*popenargs, **kwargs):
    '''Port from Python 2.7.
    '''

    if 'stdout' in kwargs:
        raise ValueError('stdout argument not allowed, it will be overridden.')
    process = subprocess.Popen(stdout=subprocess.PIPE, *popenargs, **kwargs)
    output, unused_err = process.communicate()
    retcode = process.poll()
    if retcode:
        cmd = kwargs.get("args")
        if cmd is None:
            cmd = popenargs[0]
        raise subprocess.CalledProcessError(retcode, cmd)
    return output


def runProcess(begin, end, csvFilename):
    '''Returns the lumiCalc2.py process that will query the Lumi service.
    The range can be specified by run numbers, fill numbers or datetimes.
    '''

    if isinstance(begin, datetime.datetime):
        begin = begin.strftime(dateFormat)

    if isinstance(end, datetime.datetime):
        end = end.strftime(dateFormat)

    # Check that there are not too many queries going on already
    processes = int(check_output("pgrep -f '/lumiCalc2.py --begin' | wc -l", shell = True))
    if processes > maxProcesses:
        raise BusyLumiError

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
    try:
        csvReader.next()
    except StopIteration:
        # Empty CSV file
        return {}

    # CSV fields look like:
    # 161210:1645,44,6.287026587401057,[1-38],5.189176823798077
    output = {}
    for runFill, delLS, delUb, selLS, recUb in csvReader:
        run = int(runFill.split(':')[0])

        if lumiType == 'delivered':
            output[run] = float(delUb)
        elif lumiType == 'recorded':
            output[run] = float(recUb)

        # Cache results, for both kinds of lumiType, since we have the data
        # The repr() is required: we want to keep the float as-is
        cache.delivered.put(run, repr(float(delUb)), expirationTime)
        cache.recorded.put(run, repr(float(recUb)), expirationTime)

    # Cache empty runs in-between the first and the last since
    # we know they are empty
    if len(output) > 0:
        sortedRuns = sorted(output)
        first = sortedRuns[0]
        last = sortedRuns[-1]
        runs = set(range(first, last + 1))
        for run in runs - set(output):
            cache.delivered.put(run, '', expirationTime)
            cache.recorded.put(run, '', expirationTime)

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

    # If it is a run-based only query, try to see if it is cached
    if isinstance(begin, int) and isinstance(end, int):
        result = {}
        for run in range(begin, end + 1):
            value = getattr(cache, lumiType).get(run)
            if value is None:
                break
            if value == '':
                continue
            result[run] = float(value)
        else:
            return result

    with tempfile.NamedTemporaryFile(dir = '/data/files/getLumi') as f:
        result = waitProcess(runProcess(begin, end, f.name), f, lumiType)

    # If it is a run-based only query, we can also cache empty runs in
    # the extremes, since we know we have checked them
    if isinstance(begin, int) and isinstance(end, int):
        for run in range(begin, end + 1):
            if run not in result:
                cache.delivered.put(run, '', expirationTime)
                cache.recorded.put(run, '', expirationTime)

    return result

