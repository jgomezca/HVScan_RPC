#!/usr/bin/env python
'''Quick and dirty hack to manage redis server in Mac private deployments.
i.e. start/stop/restart ...  like /etc/init.d/redis
'''

__author__ = 'Andreas Pfeiffer'
__copyright__ = 'Copyright 2013, CERN CMS'
__credits__ = ['Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Andreas Pfeiffer'
__email__ = 'andreas.pfeiffer@cern.ch'


import os
import sys
import subprocess
import logging
import optparse


def getOptions():

    parser = optparse.OptionParser(usage =
        'Usage: %prog command [options]\n'
        '\n'
        'Examples:\n'
        '  %prog start\n'
        '  %prog stop\n'
        '  %prog restart'
    )

    (options, args) = parser.parse_args()

    if len(args) != 1:
        parser.print_help()
        sys.exit(2)

    return args[0], vars(options)


def check_output(*popenargs, **kwargs):
    '''Mimics subprocess.check_output() in Python 2.6
    '''

    process = subprocess.Popen(*popenargs, **kwargs)
    stdout = process.communicate()
    returnCode = process.returncode
    cmd = kwargs.get("args")
    if cmd is None:
        cmd = popenargs[0]
    if returnCode:
        raise subprocess.CalledProcessError(returnCode, cmd)
    return stdout


def execute(command):
    '''Executes a command in a shell:
        - Allowing input
        - Without redirecting stderr
        - Raises an exception if it returns with a non-zero exit code
        - Returns the stdout
    '''

    # Don't redirect stderr: That way we can see the error
    # if the command does not finish correctly
    logging.info('Executing: ' + command)
    return check_output(command, shell=True)


def isRunning():
    try:
        execute('pgrep redis-server >/dev/null')
        return True
    except subprocess.CalledProcessError:
        return False


def start():
    if isRunning():
        logging.warning('Redis is already running.')
        return 1

    subprocess.Popen('nohup redis-server >/data/logs/redis.log 2>&1 &', shell = True)


def stop():
    if not isRunning():
        logging.warning('Redis is not running.')
        return 1

    execute('redis-cli shutdown')


def restart():
    stop()
    return start()


def main():
    '''Entry point.
    '''

    command, options = getOptions()

    if 'start' == command:
        return start()
    elif 'stop' == command:
        return stop()
    elif 'restart' == command:
        return restart()
    else:
        logging.error('Wrong command.')
        return 2


if __name__ == '__main__':
    logging.basicConfig(
        format = '[%(asctime)s] %(levelname)s: %(message)s',
        level = logging.INFO,
    )

    sys.exit(main())

