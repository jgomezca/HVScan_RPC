#!/usr/bin/env python2.6
'''Keeper of the CMS DB Web services.
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = ['Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


import config

services = config.getServicesList(showHiddenServices = True)


import os
import glob
import subprocess
import sys
import signal
import time
import smtplib
import email
import socket
import optparse
import logging
import json
import inspect

import daemon


def _sendEmail(from_address, to_addresses, cc_addresses, subject, body, smtp_server = 'cernmx.cern.ch', password = ''):
    '''Sends an email, optionally logging in if a password for the from_address account is supplied
    '''

    # cernmx.cern.ch
    # smtp.cern.ch

    logging.debug('sendEmail(): Sending email...')
    logging.debug('sendEmail(): Email = ' + str((from_address, to_addresses, cc_addresses, subject, body)))

    mimetext = email.mime.Text.MIMEText(body)
    mimetext['Subject'] = email.Header.Header(subject)
    mimetext['From'] = from_address
    mimetext['To'] = ', '.join(to_addresses)
    if len(cc_addresses) > 0:
        mimetext['Cc'] = ', '.join(cc_addresses)

    smtp = smtplib.SMTP(smtp_server)
    if password != '':
        smtp.starttls()
        smtp.ehlo()
        smtp.login(from_address, password)
    smtp.sendmail(from_address, set(to_addresses + cc_addresses), mimetext.as_string())
    smtp.quit()

    logging.debug('sendEmail(): Sending email... DONE')


def _getPIDs(matchString, notMatchString = 'bash'):
    '''Returns the PIDs where the command line matches the given string and
    does not match the other given string.
    '''

    pids = []

    for line in os.popen('ps -wweo pid,command').readlines():

        (pid, command) = line.split(None, 1)

        if matchString not in command:
            continue

        if notMatchString in command:
            continue

        pids.append(pid)

    return pids


def getPIDs(service):
    '''Returns the PIDs of a service or the keeper itself.
    '''

    if service == 'keeper':
        pids = set(_getPIDs('./keeper.py keep'))
        pids -= set([str(os.getpid())])
    elif service == 'gtc':
        pids = _getPIDs('bin/python src/manage.py runserver')
    else:
        pids = _getPIDs('python %s --name %s --rootDirectory' % (config.servicesConfiguration[service]['filename'], service))

        # At the moment all services run one and only one process
        if len(pids) > 1:
            raise Exception('Please update the code for getting the PID of ' + service)

    return pids


def getPath(service):
    '''Returns the absolute path to a service.
    '''

    return os.path.abspath(os.path.join(config.servicesDirectory, service))


def getLogsList(service):
    '''Returns the list of available logs of a service (without including
    the 'log' hardlink, i.e. the latest log).
    '''

    # Make sure the arguments are valid before listing folders
    # (this is used by the admin service)
    if service != 'keeper':
        checkRegistered(service)

    return sorted(glob.glob(getLogPath(service) + '.*'))


def getJobLogsList(service, job):
    '''Returns the list of available logs of a service's job (without including
    the 'log' hardlink, i.e. the latest log).
    '''

    # Make sure the arguments are valid before listing folders
    # (this is used by the admin service)
    checkJobRegistered(service, job)

    return sorted(glob.glob(getJobLogPath(service, job) + '.*'))


def getLog(service, timestamp):
    '''Returns a log of a service.
    '''

    # Make sure the arguments are valid before opening the file
    # (this is used by the admin service)
    if service != 'keeper':
        checkRegistered(service)
    timestamp = int(timestamp)

    with open('%s.%s' % (getLogPath(service), timestamp), 'r') as f:
        log = f.read()

    return log


def getJobLog(service, job, timestamp):
    '''Returns a log of a service's job.
    '''

    # Make sure the arguments are valid before opening the file
    # (this is used by the admin service)
    checkJobRegistered(service, job)
    timestamp = int(timestamp)

    with open('%s.%s' % (getJobLogPath(service, job), timestamp), 'r') as f:
        log = f.read()

    return log


def _getLatestLogFile(service):
    '''Returns the latest log file of a service, None if there is not any log file.
    '''

    try:
        return getLogsList(service)[-1]
    except:
        return None


def getLogPath(service):
    '''Returns the absolute path to a service's latest log.
    '''

    # Make sure the arguments are valid
    # (this is used by the admin service)
    if service != 'keeper':
        checkRegistered(service)

    return os.path.abspath(config.logsFileTemplate % service)


def getJobLogPath(service, job):
    '''Returns the absolute path to a service's job's latest log.
    '''

    # Make sure the arguments are valid
    # (this is used by the admin service)
    checkJobRegistered(service, job)

    return os.path.abspath(config.logsJobFileTemplate % (service, job))


def isRegistered(service):
    '''Returns whether a service is registered in the keeper or not.
    '''

    return service in services


def checkRegistered(service):
    '''Checks whether a service is registered in the keeper or not.
    '''

    if not isRegistered(service):
        raise Exception('Service "%s" is not registered in the keeper.' % service)


def isJobRegistered(service, job):
    '''Returns whether a service's job is registered in the keeper or not.
    '''

    if service != 'keeper':
        checkRegistered(service)

    for (jobTime, jobName) in config.servicesConfiguration[service].get('jobs', []):
        if job == jobName:
            return True

    return False


def checkJobRegistered(service, job):
    '''Checks whether a service's job is registered in the keeper or not.
    '''

    if not isJobRegistered(service, job):
        raise Exception('Job "%s" of service "%s" is not registered in the keeper.' % (job, service))


def isRunning(service):
    '''Returns whether a service or the keeper itself is running or not.
    '''

    return len(getPIDs(service)) > 0


def killProcess(pid, sigkill = False):
    '''Sends SIGTERM or SIGKILL to a process.
    '''

    if sigkill:
        logging.info('Killing %s', pid)
        s = signal.SIGKILL
    else:
        logging.info('Stopping %s', pid)
        s = signal.SIGTERM

    os.kill(int(pid), s)


def getProcessEnvironment(pid):
    '''Returns the environment of a process as a dictionary.
    '''

    with open('/proc/%s/environ' % pid, 'r') as f:
        return dict([x.split('=', 1) for x in f.read().split('\0') if '=' in x])


def getEnvironment(service):
    '''Returns the environment of a service's processes as a dictionary.
    '''

    ret = {}

    for pid in getPIDs(service):
        ret[pid] = getProcessEnvironment(pid)

    return ret


def run(service, filename, extraCommandLine = '', replaceProcess = True):
    '''Setups and runs a Python script in a service.
        - Changes the working directory to the service's folder.
        - Setups PYTHONPATH.
        - Sources pre.sh, setupEnv.sh and post.sh as needed.
        - Setups the arguments.
        - Runs the Python script.

    Used for starting a service and also running its test suite.
    '''

    checkRegistered(service)

    # Change working directory
    os.chdir(getPath(service))

    # Add services/common/ to the $PYTHONPATH for access to
    # service.py as well as secrets/ for secrets.py.
    # 
    # The config.cmsswSetupEnvScript must keep
    # the contents in $PYTHONPATH.
    #
    # This is not elegant, but avoids guessing in the services
    # and/or modifying the path. Another solution is
    # to use symlinks, although that would be harder to maintain
    # if we move the secrets to another place (i.e. we would
    # need to fix all the symlinks or chain symlinks).
    #
    # This does not keep the original PYTHONPATH. There should not
    # be anything there anyway.
    os.putenv('PYTHONPATH', getPythonPath())

    commandLine = ''

    # If pre.sh is found, source it before setupEnv.sh
    if os.path.exists('./pre.sh'):
        commandLine += 'source ./pre.sh ; '

    # Source the common CMSSW environment
    commandLine += 'source ' + config.cmsswSetupEnvScript + ' ; '

    # If post.sh is found, source it after setupEnv.sh
    if os.path.exists('./post.sh'):
        commandLine += 'source ./post.sh ; '

    # Run the service with the environment
    # Ensure that the path is absolute (although at the moment config returns
    # all paths as absolute)
    commandLine += 'python %s --name %s --rootDirectory %s --secretsDirectory %s --listeningPort %s --productionLevel %s --caches \'%s\' ' % (filename, service, getPath(service), config.secretsDirectory, str(config.servicesConfiguration[service]['listeningPort']), config.getProductionLevel(), json.dumps((config.servicesConfiguration[service]['caches'])))

    # Append the extra command line
    commandLine += extraCommandLine

    # Execute the command line on the shell
    if replaceProcess:
        os.execlp('bash', 'bash', '-c', commandLine)
    else:
        return subprocess.call(['bash', '-c', commandLine])


def start(service, warnIfAlreadyStarted = True, sendEmail = True, maxWaitTime = 30):
    '''Starts a service or the keeper itself.
    '''

    if service == 'all':
        for service in services:
            start(service, warnIfAlreadyStarted = warnIfAlreadyStarted, sendEmail = sendEmail, maxWaitTime = maxWaitTime)
        return

    if service != 'keeper':
        checkRegistered(service)

    pids = getPIDs(service)

    # The service is running
    if len(pids) > 0:
        if warnIfAlreadyStarted:
            logging.warning('Tried to start a service (%s) which is already running: %s', service, ','.join(pids))
        return

    # Before starting, try to get the latest log file
    previousLatestLogFile = _getLatestLogFile(service)

    logging.info('Starting %s.', service)

    # Unset LC_CTYPE in case it is still there (e.g. in OS X or, worse, when
    # ssh'ing from OS X to Linux using the default ssh_config) since some
    # CMSSW code crashes if the locale name is not valid.
    try:
        del os.environ['LC_CTYPE']
    except:
        pass

    # The service is not running, start it
    pid = os.fork()
    if pid == 0:
        daemon.DaemonContext(
            working_directory = getPath(service),
            umask = 0077,
        ).open()

        # Run the service's starting script piping its output to rotatelogs
        # FIXME: Fix the services so that they do proper logging themselves
        extraCommandLine = '2>&1 | LD_LIBRARY_PATH=/lib64:/usr/lib64 /usr/sbin/rotatelogs %s %s' % (getLogPath(service), config.logsSize)

        if service == 'keeper':
            os.execlp('bash', 'bash', '-c', './keeper.py keep ' + extraCommandLine)
        else:
            run(service, config.servicesConfiguration[service]['filename'], extraCommandLine = extraCommandLine)

    # Wait until the service has started
    wait(service, maxWaitTime = maxWaitTime, forStart = True)

    # Clean up the process table
    os.wait()

    # Alert users
    if sendEmail and config.getProductionLevel() != 'private':
        subject = '[keeper@' + socket.gethostname() + '] Started ' + service + ' service.'
        body = subject
        try:
            _sendEmail('mojedasa@cern.ch', config.startedServiceEmailAddresses, [], subject, body)
        except Exception:
            logging.error('The email "' + subject + '"could not be sent.')

    # Try to remove the old hard link to the previous latest log file
    logHardLink = getLogPath(service)
    try:
        os.remove(logHardLink)
    except Exception:
        pass

    # Wait until the service creates some output (i.e. until rotatelogs has created a new file)
    startTime = time.time()
    maxWaitTime = 20
    while True:
        if time.time() - startTime > maxWaitTime:
            raise Exception('Service %s did not create any output after %s seconds.' % (service, maxWaitTime))

        latestLogFile = _getLatestLogFile(service)

        # If there is a log file
        if latestLogFile is not None:
            # If there was not a previous log file, latestLogFile is the new one.
            # If there was a previous log file, latestLogFile should be different than the old one.
            if previousLatestLogFile is None or previousLatestLogFile != latestLogFile:
                break

        time.sleep(1)

    # Create the new hard link
    try:
        os.link(latestLogFile, logHardLink)
    except Exception as e:
        logging.warning('Could not create hard link from %s to %s: %s', latestLogFile, logHardLink, e)

    logging.info('Started %s: %s', service, ','.join(getPIDs(service)))


def wait(service, maxWaitTime = 30, forStart = False):
    '''Waits until a service stops.
    
    Raises exception if a maximum wait time is exceeded.
    '''

    action = 'stop'
    if forStart:
        action = 'start'

    startTime = time.time()

    while True:
        if time.time() - startTime > maxWaitTime:
            raise Exception('Service %s did not %s after %s seconds.' % (service, action, maxWaitTime))

        if forStart == isRunning(service):
            return

        time.sleep(1)


def _stop(service, sigkill = False):
    '''Stops or kills a service or the keeper itself.
    '''

    if service == 'all':
        for service in services:
            _stop(service, sigkill)
        return

    if service != 'keeper':
        checkRegistered(service)

    pids = getPIDs(service)

    # Service not running
    if len(pids) == 0:
        logging.warning('Tried to stop a service (%s) which is not running.', service)
        return

    for pid in pids:
        killProcess(pid, sigkill)

    wait(service)
    logging.info('Stopped %s: %s', service, ','.join(pids))


def stop(service):
    '''Stops a service or the keeper itself.
    '''

    _stop(service, sigkill = False)


def restart(service):
    '''Restarts a service or the keeper itself.
    '''

    if service not in frozenset(['all', 'keeper']):
        checkRegistered(service)

    stop(service)
    start(service)


def kill(service):
    '''Kills -9 (sigkill) a service or the keeper itself.
    '''

    _stop(service, sigkill = True)


def test(service):
    '''Runs the service's (or the keeper's) test suite.

    Returns True if successful, False if failed, None if the suite was not run
    (i.e. the test suite does not exists).
    '''

    if service == 'all':
        logging.info('Testing all services.')
        startTime = time.time()

        success = []
        failure = []
        skipped = []

        for service in services:
            result = test(service)
            if result is None:
                skipped.append(service)
            elif result:
                success.append(service)
            else:
                failure.append(service)

        state = (len(failure) == 0)

        logging.info('Finished testing all services: %s. Took %.2f seconds.', 'SUCCESS' if state else 'FAILED', time.time() - startTime)
        logging.info('Successful services: %s', ','.join(success))
        logging.info('    Failed services: %s', ','.join(failure))
        logging.info('   Skipped services: %s', ','.join(skipped))

        return state

    if service != 'keeper':
        checkRegistered(service)

    if not os.path.exists(os.path.join(getPath(service), 'test.py')):
        logging.warning('Test suite for service %s does not exist.', service)
        return None

    if not isRunning(service):
        logging.warning('Tried to test a service (%s) which is not running.', service)
        return None

    logging.info('Testing %s.', service)
    startTime = time.time()

    # Run the test suite
    returnCode = run(service, 'test.py', replaceProcess = False)

    state = (returnCode == 0)

    logging.info('Finished testing %s: %s. Took %.2f seconds.', service, 'SUCCESS' if state else 'FAILED', time.time() - startTime)

    return state


def getPythonPath():
    '''Returns the Python path that we use to run services.

    This is also used when running other tools, like pylint, so that they can
    find the dependencies.
    '''

    return '%s:%s:%s:%s' % (getPath('common'), config.secretsDirectory, os.path.join(config.utilitiesDirectory, 'lib', 'python2.6', 'site-packages'), os.path.join(config.utilitiesDirectory, 'lib64', 'python2.6', 'site-packages'))


def pylint(*files):
    '''Checks a service's (or the keeper's) code or a file.
    '''

    if len(files) == 1 and (isRegistered(files[0]) or files[0] == 'keeper'):
        # Check a service
        os.chdir(getPath(files[0]))
        files = '*.py'

    #-mo FIXME: In the future we won't need to use the IB from AFS.
    #-mo FIXME: The ruleset will need to be refined.
    subprocess.call(
        'export SCRAM_ARCH=slc5_amd64_gcc462 ; '
        'pushd /afs/cern.ch/cms/$SCRAM_ARCH/cms/cmssw/CMSSW_6_0_1 >/dev/null ; '
        'eval `scramv1 runtime -sh` ; '
        'popd >/dev/null ; '
        'PYTHONPATH=$PYTHONPATH:%s pylint '
        '-iy '
        '--good-names=i,j,k,e,f,s '
        '--module-rgx="[a-z_][a-zA-Z0-9_]{2,30}$" '
        '--const-rgx="[a-z_][a-zA-Z0-9_]{2,30}$" '
        '--function-rgx="[a-z_][a-zA-Z0-9_]{2,30}$" '
        '--method-rgx="[a-z_][a-zA-Z0-9_]{2,30}$" '
        '--attr-rgx="[a-z_][a-zA-Z0-9_]{2,30}$" '
        '--argument-rgx="[a-z_][a-zA-Z0-9_]{2,30}$" '
        '--variable-rgx="[a-z_][a-zA-Z0-9_]{2,30}$" '
        '%s' % (getPythonPath(), ' '.join(files)),
        shell = True
    )


def less(service):
    '''"less" a service\'s log.
    '''

    if service != 'keeper':
        checkRegistered(service)

    # Replacing the process avoids the traceback when issuing ^C
    commandLine = 'less %s' % getLogPath(service)
    os.execlp('bash', 'bash', '-c', commandLine)


def tail(service):
    '''"tail -f" a service\'s log.
    '''

    if service != 'keeper':
        checkRegistered(service)

    # Replacing the process avoids the traceback when issuing ^C
    commandLine = 'tail -f %s' % getLogPath(service)
    os.execlp('bash', 'bash', '-c', commandLine)


def lsof(service):
    '''"lsof" a service's processes.
    '''

    if service != 'keeper':
        checkRegistered(service)

    pids = getPIDs(service)

    # Service not running
    if len(pids) == 0:
        logging.warning('Tried to lsof a service (%s) which is not running.', service)
        return

    subprocess.call('/usr/sbin/lsof -p %s' % ','.join(pids), shell = True)


def env(service):
    '''Prints the environment of a service's processes.
    '''

    if service != 'keeper':
        checkRegistered(service)

    pids = getPIDs(service)

    # Service not running
    if len(pids) == 0:
        logging.warning('Tried to env a service (%s) which is not running.', service)
        return

    for pid in pids:
        environment = getProcessEnvironment(pid)
        for key in sorted(environment):
            print '%s  %s=%s' % (pid, key, environment[key])


def strace(service):
    '''"strace -ft" a service's processes, without the select, futex,
    gettimeofday nor poll system calls.
    '''

    if service != 'keeper':
        checkRegistered(service)

    pids = getPIDs(service)

    # Service not running
    if len(pids) == 0:
        logging.warning('Tried to strace a service (%s) which is not running.', service)
        return

    # Replacing the process avoids the traceback when issuing ^C
    commandLine = 'strace -fte "trace=!select,futex,gettimeofday,poll" -p %s 2>&1' % ' -p '.join(pids)
    os.execlp('bash', 'bash', '-c', commandLine)


def formatTable(matrix, columnSeparator = '  ', floatFormat = '%.2f', rowSeparator = '\n', filler = ' '):
    '''Returns a formatted table given a matrix.
    '''

    def getFormattedCell(cell):
        if not cell:
            cell = ''
        elif isinstance(cell, float):
            cell = floatFormat % cell
        elif not isinstance(cell, str) and not isinstance(cell, unicode):
            cell = str(cell)
        return cell

    sizes = [0] * len(matrix[0])

    for row in matrix:
        index = 0
        for cell in row:
            sizes[index] = max(sizes[index], len(getFormattedCell(cell)))
            index += 1

    table = []
    for row in matrix:
        formattedRow = []
        index = 0
        for cell in row:
            cell = getFormattedCell(cell)
            formattedRow.append(cell + (filler * (sizes[index] - len(cell))))
            index += 1

        table.append(columnSeparator.join(formattedRow))

    return rowSeparator.join(table)


def status():
    '''Print the status of all services.
    '''

    matrix = [
        ['Service', 'Jobs', 'PIDs', 'URL'],
    ]

    for service in ['keeper'] + services:
        row = [service]

        if service != 'keeper' and hasEnabledJobs(service):
            row.append('Enabled')
        else:
            row.append('----')

        pids = getPIDs(service)
        if len(pids) > 0:
            row.append(','.join(pids))
            if service != 'keeper':
                if config.getProductionLevel() == 'private':
                    row.append('https://%s:%s/%s/' % (socket.gethostname(), str(config.servicesConfiguration[service]['listeningPort']), service))
                else:
                    # FIXME: Report the URL of the front-end (more consistent with 'private',
                    #        and also allows us to rely on absolute paths in the future, e.g. /libs)
                    row.append('https://%s:%s/%s/' % (socket.gethostname(), str(config.servicesConfiguration[service]['listeningPort']), service))
            else:
                row.append('---')
        else:
            row.append('----')
            row.append('---')

        matrix.append(row)

    print formatTable(matrix)


def _refreshCrontab():
    '''Installs the crontab with the jobs from all services.
    '''

    crontab = 'SHELL=/bin/bash\nMAILTO=%s\n\n' % config.jobsEmailAddress
    for service in services:
        try:
            f = open(config.jobsFileTemplate % service, 'r')
        except IOError:
            continue
        crontab += f.read()
        f.close()

    with open(config.crontabFile, 'w') as f:
        f.write(crontab)

    subprocess.call(['/usr/bin/crontab', config.crontabFile])


def hasEnabledJobs(service):
    '''Has a service its jobs enabled?
    '''

    try:
        with open(config.jobsFileTemplate % service) as f:
            pass
        return True
    except IOError:
        return False


def enableJobs(service, refreshIfAlreadyEnabled = True):
    '''Enables the jobs for a given service.
    '''

    if service == 'all':
        for service in services:
            enableJobs(service, refreshIfAlreadyEnabled = refreshIfAlreadyEnabled)
        return

    checkRegistered(service)

    if hasEnabledJobs(service):
        if refreshIfAlreadyEnabled:
            logging.warning('Jobs were already enabled for %s, refreshing them.', service)
        else:
            return

    jobs = ''
    for (when, filename) in config.servicesConfiguration[service].get('jobs', []):
        jobs += '%s %s run %s %s > %s.$(date +\\%%s) 2>&1\n' % (when, os.path.join(getPath('keeper'), 'keeper.py'), service, filename, config.logsJobFileTemplate % (service, filename))

    with open(config.jobsFileTemplate % service, 'w') as f:
        f.write(jobs)

    _refreshCrontab()

    logging.info('Enabled jobs for %s.', service)


def disableJobs(service):
    '''Disables the jobs for a given service.
    '''

    if service == 'all':
        for service in services:
            disableJobs(service)
        return

    checkRegistered(service)

    if not hasEnabledJobs(service):
        logging.warning('Tried to disable jobs which were already disabled for %s.', service)
        return

    try:
        os.remove(config.jobsFileTemplate % service)
    except OSError:
        pass

    _refreshCrontab()

    logging.info('Disabled jobs for %s.', service)


def listJobs(service):
    '''Lists the jobs for a given service.
    '''

    if service == 'all':
        for service in services:
            listJobs(service)
        return

    checkRegistered(service)

    try:
        f = open(config.jobsFileTemplate % service)
    except IOError:
        return

    jobs = f.read().rstrip()
    if jobs:
        print jobs
    f.close()


def statusCache():
    '''Prints the status of the cache system.
    '''

    def getStdout(command):
        return subprocess.Popen(command, stdout = subprocess.PIPE, shell = True).communicate()[0]

    # FIXME: We use the redis-cli instead of the redis Python package
    # because it is included by default in the redis package. In SLC5,
    # however, the redis Python package is not available, and the keeper
    # should run with the standard environment, i.e. it does not run with
    # the environment of the servicess, so utilities are not available.
    redisInfo = {}
    for line in getStdout('redis-cli info').splitlines():
        (key, value) = line.split(':')
        redisInfo[key] = value

    # Print the global cache stats
    cacheSize = config.cacheSize / 1024. / 1024.
    usedMemory = float(redisInfo['used_memory']) / 1024. / 1024.
    usedMemoryRSS = float(redisInfo['used_memory_rss']) / 1024. / 1024.
    usedMemoryPeak = float(redisInfo['used_memory_peak']) / 1024. / 1024.
    memoryFragmentationRatio = float(redisInfo['mem_fragmentation_ratio'])
    print formatTable([
        [cacheSize, 'Available cache global size (MB)'],
        [usedMemory, 'Used memory (MB)'],
        [usedMemory / cacheSize, 'Cache usage (%)'],
        [usedMemoryPeak, '(Peak) Used memory (MB)'],
        [usedMemoryPeak / cacheSize, '(Peak) Cache usage (%)'],
        [usedMemoryRSS, 'Used memory RSS (MB)'],
        [memoryFragmentationRatio, 'Memory fragmentation ratio (%)'],
    ])

    # Print the caches status table
    matrix = [
        ['Service', 'Cache', 'ID', '# Keys'],
    ]

    for service in services:
        for cacheID in sorted(config.servicesConfiguration[service]['caches'].values()):
            matrix.append([service, config.getCacheByID(cacheID), str(cacheID), getStdout('redis-cli -n %s dbsize' % cacheID).strip()])

    print
    print formatTable(matrix)


def flushallCache():
    '''Flushes all caches.
    '''

    logging.info('Flushing all caches.')
    subprocess.call('redis-cli flushall', stdout = subprocess.PIPE, shell = True)


def flushCache(service, cache):
    '''Flushes a cache of a service, or all caches of a service
    or all caches.

    Note that this flushes only caches known to the keeper by their ID.

    If you need to flush all caches because (for instance) you added
    a new cache and/or the IDs changed, use flushall.
    '''

    if service == 'all':
        for service in services:
            flushCache(service, cache)
        return

    checkRegistered(service)

    if cache == 'all':
        for cache in config.servicesConfiguration[service]['caches']:
            flushCache(service, cache)
        return

    cacheID = config.getCacheID(service, cache)
    logging.info('Flushing %s\'s %s cache (ID %s).', service, cache, cacheID)
    subprocess.call('redis-cli -n %s flushdb' % cacheID, stdout = subprocess.PIPE, shell = True)


def compass(inputFile, outputFile):
    '''Compiles a Sass/Compass .scss file script.
    '''

    tmpPath = '/tmp/compass'

    logging.info('Compiling %s...', inputFile)

    subprocess.call(
        '    compass create --force %s'
        ' && cp %s %s'
        ' && compass compile --force --output-style compressed --no-line-comments %s'
        ' && cp %s %s'

        % (
            tmpPath,
            inputFile, os.path.join(tmpPath, 'sass/screen.scss'),
            tmpPath,
            os.path.join(tmpPath, 'stylesheets/screen.css'), outputFile,
        ),
        shell = True,
    )


def keep():
    '''Keeps services and its jobs up and running.
    '''

    logging.info('Keeping services up and running...')

    while True:
        time.sleep(config.timeBetweenChecks)

        for service in services:
            try:
                start(service, warnIfAlreadyStarted = False)
                enableJobs(service, refreshIfAlreadyEnabled = False)
            except Exception as e:
                logging.error(e)


usage = '''Usage: %%prog <command> [arguments]

Commands:
  start    <service>  Starts a service.
  stop     <service>  Stops a service.
  restart  <service>  Restarts a service.
  kill     <service>  "kill -9" a service.

  test     <service>  Runs a service\'s test suite.
  pylint   <service>  Checks a service\'s code.
  pylint   <file>     Checks a Python script.

  less     <service>  "less" a service\'s log.
  tail     <service>  "tail -f" a service\'s log.
  lsof     <service>  "lsof" a service\'s processes.
  env      <service>  Prints the environment of a service\'s processes.
  strace   <service>  "strace -ft" a service\'s processes, without
                      the select, futex, gettimeofday nor poll system calls.

  status              Prints the status of the keeper
                      and all the services, with PIDs and jobs.

  jobs  enable   <service>  Enables the jobs of a service.
  jobs  disable  <service>  Disables the jobs of a service.
  jobs  list     <service>  Lists the current jobs of a service.

  cache  status                     Prints the status of the cache system.
  cache  flushall                   Flushes all caches (including ones
                                    unknown by the keeper).
  cache  flush  <service>  <cache>  Flushes a service's cache.

  compass  <inputFile> <outputFile>  Compiles a Sass/Compass .scss file script.

  keep                Keeps the services and its jobs up and running.
                      (this is what the keeper-service runs).

  run      <service>  <filename>  Runs a Python script inside a service.

  <service> can be one of the following:
    all keeper %s
    ("all" does not apply for less, tail, lsof nor env).

  Each command may have additional options. Use -h to see
  the help for them, e.g.: %%prog start -h

  Note: "all" does not include the keeper: this command
        is meant for private development, not dev/int/pro.
        In dev/int/pro, the keeper is supposed to start
        and stop the services itself.
''' % ' '.join(services)


def runDictionary(dictionary, arguments, prefixCommandName = ''):
    '''Tries to run a command (given in the arguments list) looking it up
    in the given dictionary which must map a command name to the function.

    It supports subcommands which are represented as subdictionaries.
    '''

    commandName = arguments[0]
    command = dictionary[commandName]
    arguments = arguments[1:]

    if isinstance(command, dict):
        # This is a command with subcommands
        if len(arguments) < 1 or arguments[0] not in command.keys():
            raise Exception('Subcommand should be one one of: %s.' % ','.join(command.keys()))

        return runDictionary(command, arguments, prefixCommandName + commandName + ' ')

    runCommand(command, arguments, prefixCommandName + commandName)


def runCommand(command, arguments, commandName = None):
    '''Runs a command after parsing its arguments, building
    the OptionParser from the function definition.
    '''

    if commandName is None:
        commandName = command.__name__

    argspec = inspect.getargspec(command)
    defaults = argspec.defaults
    if defaults is None:
        defaults = []
        options = []
        args = argspec.args
    else:
        options = argspec.args[-len(defaults):]
        args = argspec.args[:-len(defaults)]
    varargs = argspec.varargs

    parser = optparse.OptionParser(usage =
        'Usage: %%prog %s [options]' % ' '.join([commandName] + ['<%s>' % x for x in args] + ['[%s...]' % varargs for x in [varargs] if x is not None])
    )

    i = -1
    for option in options:
        i += 1
        default = defaults[i]
        if isinstance(default, bool):
            if default:
                name = 'no%s' % option
                action = 'store_false'
            else:
                name = option
                action = 'store_true'

            parser.add_option('--%s' % name, action = action,
                dest = option,
                default = default,
                help = 'Default: %default'
            )
        elif isinstance(default, str) or isinstance(default, int):
            parser.add_option('--%s' % option, type = type(default).__name__,
                dest = option,
                default = default,
                help = 'Default: %default'
            )
        else:
            raise Exception('Unsupported default type.')

    (options, arguments) = parser.parse_args(arguments)

    # If varargs is None, there must be the same number of arguments as the function' ones.
    # If varargs is not None, there must be at least the number of arguments as the function' ones.
    if (varargs is None and len(arguments) != len(args)) or (varargs is not None and len(arguments) < len(args)):
        parser.print_help()
        return -2

    command(*arguments, **vars(options))


def main():
    '''Entry point.
    '''

    commands = {
        'start': start,
        'stop': stop,
        'restart': restart,
        'kill': kill,
        'test': test,
        'pylint': pylint,
        'less': less,
        'tail': tail,
        'lsof': lsof,
        'env': env,
        'strace': strace,
        'status': status,
        'jobs': {
            'enable': enableJobs,
            'disable': disableJobs,
            'list': listJobs,
        },
        'cache': {
            'status': statusCache,
            'flushall': flushallCache,
            'flush': flushCache,
        },
        'compass': compass,
        'keep': keep,
        'run': run,
    }

    if len(sys.argv) < 2 or sys.argv[1] not in commands:
        optparse.OptionParser(usage).print_help()
        return -2

    try:
        return runDictionary(commands, sys.argv[1:])
    except Exception as e:
        logging.error(e)
        return -1


if __name__ == '__main__':
    logging.basicConfig(
        format = '[%(asctime)s] %(levelname)s: %(message)s',
        level = logging.INFO,
    )

    sys.exit(main())

