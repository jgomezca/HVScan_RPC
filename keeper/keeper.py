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
import subprocess
import sys
import signal
import time
import smtplib
import email
import socket
import optparse
import logging
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


def _getPIDs(string):
	'''Returns the PIDs matching the string, without grep nor bash.
	'''

	return os.popen("ps aux | grep -F '" + string + "' | grep -F 'python' | grep -F -v 'grep' | grep -F -v 'bash' | awk '{print $2}'", 'r').read().splitlines()


def getPIDs(service):
	'''Returns the PIDs of a service or the keeper itself.
	'''

	if service == 'keeper':
		pids = set(_getPIDs('keeper.py'))
		pids -= set([str(os.getpid())])
	elif service == 'gtc':
		pids = _getPIDs('bin/python src/manage.py')
	else:
		pids = _getPIDs('python ' + config.servicesConfiguration[service]['filename'])

		# At the moment all services run one and only one process
		if len(pids) > 1:
			raise Exception('Please update the code for getting the PID of ' + service)

	return pids


def getPath(service):
	'''Returns the absolute path to a service.
	'''

	return os.path.abspath(os.path.join(config.servicesDirectory, service))


def getLogPath(service):
	'''Returns the absolute path to a service's latest log.
	'''

	return os.path.abspath(os.path.join(config.logsDirectory, service + '.log'))


def isRegistered(service):
	'''Returns whether a service is registered in the keeper or not.
	'''

	return service in services


def checkRegistered(service):
	'''Checks whether a service is registered in the keeper or not.
	'''

	if not isRegistered(service):
		raise Exception('Service "%s" is not registered in the keeper.' % service)


def isRunning(service):
	'''Returns whether a service or the keeper itself is running or not.
	'''

	return len(getPIDs(service)) > 0


def killProcess(pid, sigkill = False):
	'''Sends SIGTERM or SIGKILL to a process.
	'''

	if sigkill:
		logging.info('Killing -9 %s', pid)
		s = signal.SIGKILL
	else:
		logging.info('Killing %s', pid)
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


def run(service, filename, extraCommandLine = '', replaceProcess = False):
	'''Setups and runs a Python script in a service.
		- Changes the working directory to the service's folder.
		- Setups PYTHONPATH.
		- Sources pre.sh, setupEnv.sh and post.sh as needed.
		- Setups the arguments.
		- Runs the Python script.

	Used for starting a service and also running its test suite.
	'''

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
	servicePath = getPath('common')
	secretsPath = config.secretsDirectory
	os.putenv('PYTHONPATH', servicePath + ':' + secretsPath)

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
	commandLine += 'python %s --name %s --rootDirectory %s --secretsDirectory %s --listeningPort %s --productionLevel %s ' % (filename, service, getPath(service), config.secretsDirectory, str(config.servicesConfiguration[service]['listeningPort']), config.getProductionLevel())

	# Append the extra command line
	commandLine += extraCommandLine

	# Execute the command line on the shell
	if replaceProcess:
		os.execlp('bash', 'bash', '-c', commandLine)
	else:
		return subprocess.call(['bash', '-c', commandLine])


def start(service, warnIfAlreadyStarted = True, sendEmail = True):
	'''Starts a service or the keeper itself.
	'''

	if service == 'all':
		for service in services:
			start(service, warnIfAlreadyStarted = warnIfAlreadyStarted, sendEmail = sendEmail)
		return

	if service != 'keeper':
		checkRegistered(service)

	pids = getPIDs(service)

	# The service is running
	if len(pids) > 0:
		if warnIfAlreadyStarted:
			logging.warning('Tried to start a service (%s) which is already running: %s', service, ','.join(pids))
		return

	# The service is not running, start it
	pid = os.fork()
	if pid == 0:
		daemon.DaemonContext(
			working_directory = getPath(service),
			umask = 0077,
		).open()

		# Run the service's starting script piping its output to rotatelogs
		# FIXME: Fix the services so that they do proper logging themselves
		extraCommandLine = '2>&1 | /usr/sbin/rotatelogs -L %s %s %s' % (config.logsFileTemplate % service, config.logsFileTemplate % service, config.logsSize)

		if service == 'keeper':
			os.execlp('bash', 'bash', '-c', './keeper.py keep ' + extraCommandLine)
		else:

			run(service, config.servicesConfiguration[service]['filename'], extraCommandLine = extraCommandLine, replaceProcess = True)

	logging.info('Started %s.', service)

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


def wait(service, maxWaitTime = 20):
	'''Waits until a service stops.
	
	Raises exception if a maximum wait time is exceeded.
	'''

	startTime = time.time()

	while True:
		if time.time() - startTime > maxWaitTime:
			raise Exception('Service %s did not stop after %s seconds.' % (service, maxWaitTime))

		if not isRunning(service):
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
		logging.warning('Tried to stop a service (%s) which is not running.' % service)
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
	returnCode = run(service, 'test.py')

	state = (returnCode == 0)

	logging.info('Finished testing %s: %s. Took %.2f seconds.', service, 'SUCCESS' if state else 'FAILED', time.time() - startTime)

	return state


def pylint(argument):
	'''Checks a service's (or the keeper's) code or a file.
	'''

	#-mo FIXME: Add support for several files, etc.

	files = argument
	if isRegistered(argument) or argument == 'keeper':
		os.chdir(getPath(argument))
		files = '*.py'

	#-mo FIXME: In the future we won't need to use the IB from AFS.
	#-mo FIXME: The ruleset will need to be refined.
	subprocess.call(
		'export SCRAM_ARCH=slc5_amd64_gcc462 ; '
		'pushd `scram l | grep -F 6_0_X | tail -1 | awk \'{print $2}\'` >/dev/null ; '
		'eval `scramv1 runtime -sh` ; '
		'popd >/dev/null ; '
		'pylint '
		'-iy '
		'--good-names=i,j,k,e,f,s '
		'--module-rgx="[a-z_][a-zA-Z0-9_]{2,30}$" '
		'--const-rgx="[a-z_][a-zA-Z0-9_]{2,30}$" '
		'--function-rgx="[a-z_][a-zA-Z0-9_]{2,30}$" '
		'--method-rgx="[a-z_][a-zA-Z0-9_]{2,30}$" '
		'--attr-rgx="[a-z_][a-zA-Z0-9_]{2,30}$" '
		'--argument-rgx="[a-z_][a-zA-Z0-9_]{2,30}$" '
		'--variable-rgx="[a-z_][a-zA-Z0-9_]{2,30}$" '
		'%s' % files,
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
		logging.warning('Tried to lsof a service (%s) which is not running.' % service)
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
		logging.warning('Tried to env a service (%s) which is not running.' % service)
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
		logging.warning('Tried to strace a service (%s) which is not running.' % service)
		return

	# Replacing the process avoids the traceback when issuing ^C
	commandLine = 'strace -fte "trace=!select,futex,gettimeofday,poll" -p %s 2>&1' % ' -p '.join(pids)
	os.execlp('bash', 'bash', '-c', commandLine)


def status():
	'''Print the status of all services.
	'''

	maxlen = len('keeper')
	for service in services:
		maxlen = max(maxlen, len(service))

	for service in ['keeper'] + services:
		pids = getPIDs(service)
		if len(pids) > 0:
			status = ' RUNNING: ' + ','.join(pids)
			if service != 'keeper':
				if config.getProductionLevel() == 'private':
					status += ' at https://%s/%s/' % (socket.gethostname(), service)
				else:
					# FIXME: Report the URL of the front-end (more consistent with 'private',
					#        and also allows us to rely on absolute paths in the future, e.g. /libs)
					status += ' at https://%s:%s/%s/' % (socket.gethostname(), str(config.servicesConfiguration[service]['listeningPort']), service)
		else:
			status = ' --------'

		print service + (' ' * (maxlen - len(service))) +  status


def keep():
	'''Keeps services up and running.
	'''

	logging.info('Keeping services up and running...')

	while True:
		time.sleep(config.timeBetweenChecks)

		for service in services:
			try:
				start(service, warnIfAlreadyStarted = False)
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

  status             Prints the status of the keeper
                     and all the services, with PIDs.

  keep               Keeps the services up and running.
                     (this is what the keeper-service runs).

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


def runCommand(command, arguments):
	'''Runs a command after parsing its arguments, building
	the OptionParser from the function definition.
	'''

	argspec = inspect.getargspec(command)
	defaults = argspec.defaults
	if defaults is None:
		defaults = []
		options = []
		args = argspec.args
	else:
		options = argspec.args[-len(defaults):]
		args = argspec.args[:-len(defaults)]

	parser = optparse.OptionParser(usage =
		'Usage: %%prog %s [options]' % ' '.join([command.__name__] + ['<%s>' % x for x in args])
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
		else:
			raise Exception('Unsupported default type.')

	(options, arguments) = parser.parse_args(arguments)
	if len(arguments) != len(args):
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
		'keep': keep,
	}

	if len(sys.argv) < 2 or sys.argv[1] not in commands:
		optparse.OptionParser(usage).print_help()
		return -2

	try:
		return runCommand(commands[sys.argv[1]], sys.argv[2:])
	except Exception as e:
		logging.error(e)
		return -1


if __name__ == '__main__':
	logging.basicConfig(
		format = '[%(asctime)s] %(levelname)s: %(message)s',
		level = logging.INFO,
	)

	sys.exit(main())

