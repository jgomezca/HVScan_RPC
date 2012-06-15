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

services = config.getServicesList()


import os
import subprocess
import sys
import signal
import time
import datetime
import smtplib
import email
import socket
import optparse
import logging
logging.basicConfig(
	format = '[%(asctime)s] %(levelname)s: %(message)s',
	level = logging.INFO
)
logger = logging.getLogger(__name__)


import daemon


def sendEmail(from_address, to_addresses, cc_addresses, subject, body, smtp_server = 'cernmx.cern.ch', password = ''):
	'''Sends and email, optionally logging in if a password for the from_address account is supplied
	'''

	# cernmx.cern.ch
	# smtp.cern.ch

	logger.debug('sendEmail(): Sending email...')
	logger.debug('sendEmail(): Email = ' + str((from_address, to_addresses, cc_addresses, subject, body)))

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

	logger.debug('sendEmail(): Sending email... DONE')


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
		logger.info('Killing -9 %s', pid)
		s = signal.SIGKILL
	else:
		logger.info('Killing %s', pid)
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


def daemonize(stdout = None, stderr = None):
	'''Daemonize the current process.
	'''

	daemon.DaemonContext(
		stdout = stdout,
		stderr = stderr,
		working_directory = os.getcwd(),
		umask = 0077,
	).open()


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


def start(service, warnIfAlreadyStarted = True):
	'''Starts a service or the keeper itself.
	'''

	if service == 'all':
		for service in services:
			start(service)
		return

	if service == 'keeper':
		return startKeeper()

	checkRegistered(service)

	pids = getPIDs(service)

	# The service is running
	if len(pids) > 0:
		if warnIfAlreadyStarted:
			logger.warning('Tried to start a service (%s) which is already running: %s', service, ','.join(pids))
		return

	# The service is not running, start it
	pid = os.fork()
	if pid == 0:
		daemonize()

		# Run the service's starting script piping its output to rotatelogs
		# FIXME: Fix the services so that they do proper logging themselves
		extraCommandLine = '2>&1 | /usr/sbin/rotatelogs -L %s %s %s' % (config.logsFileTemplate % service, config.logsFileTemplate % service, config.logsSize)
		run(service, config.servicesConfiguration[service]['filename'], extraCommandLine = extraCommandLine, replaceProcess = True)

	logger.info('Started %s.', service)

	# Clean up the process table
	os.wait()

	# Alert users
	if config.getProductionLevel() != 'private':
		subject = '[keeper@' + socket.gethostname() + '] Started ' + service + ' service.'
		body = subject
		try:
			sendEmail('mojedasa@cern.ch', config.startedServiceEmailAddresses, [], subject, body)
		except Exception as e:
			logger.error('The email "' + subject + '"could not be sent.')


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


def stop(service, sigkill = False):
	'''Stops a service or the keeper itself.
	'''

	if service == 'all':
		for service in services:
			stop(service, sigkill)
		return

	if service != 'keeper':
		checkRegistered(service)

	pids = getPIDs(service)

	# Service not running
	if len(pids) == 0:
		logger.warning('Tried to stop a service (%s) which is not running.' % service)
		return

	for pid in pids:
		killProcess(pid, sigkill)

	wait(service)
	logger.info('Stopped %s: %s', service, ','.join(pids))


def restart(service):
	'''Restarts a service or the keeper itself.
	'''

	if service not in frozenset(['all', 'keeper']):
		checkRegistered(service)

	stop(service)
	start(service)


def kill(service):
	'''Kills -9 a service or the keeper itself.
	'''

	stop(service, sigkill = True)


def test(service):
	'''Runs the service's (or the keeper's) test suite.

	Returns True if successful, False if failed, None if the suite was not run
	(i.e. the test suite does not exists).
	'''

	if service == 'all':
		logger.info('Testing all services.')
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

		logger.info('Finished testing all services: %s. Took %.2f seconds.', 'SUCCESS' if state else 'FAILED', time.time() - startTime)
		logger.info('Successful services: %s', ','.join(success))
		logger.info('    Failed services: %s', ','.join(failure))
		logger.info('   Skipped services: %s', ','.join(skipped))

		return state

	if service != 'keeper':
		checkRegistered(service)

	if not os.path.exists(os.path.join(getPath(service), 'test.py')):
		logger.warning('Test suite for service %s does not exist.', service)
		return None

	if not isRunning(service):
		logger.warning('Tried to test a service (%s) which is not running.', service)
		return None

	logger.info('Testing %s.', service)
	startTime = time.time()

	# Run the test suite
	returnCode = run(service, 'test.py')

	state = (returnCode == 0)

	logger.info('Finished testing %s: %s. Took %.2f seconds.', service, 'SUCCESS' if state else 'FAILED', time.time() - startTime)

	return state


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
		logger.warning('Tried to lsof a service (%s) which is not running.' % service)
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
		logger.warning('Tried to env a service (%s) which is not running.' % service)
		return

	for pid in pids:
		environment = getProcessEnvironment(pid)
		for key in sorted(environment):
			print '%s  %s=%s' % (pid, key, environment[key])


def keep():
	'''Keeps services up and running.
	'''

	while True:
		time.sleep(config.timeBetweenChecks)

		for service in services:
			try:
				start(service, warnIfAlreadyStarted = False)
			except Exception as e:
				logger.error(e)


def startKeeper():
	'''Starts the keeper.
	'''

	pids = getPIDs('keeper')

	if len(pids) > 0:
		logger.warning('Tried to start the keeper which is already running: %s', ','.join(pids))
		return

	logger.info('Starting keeper.')

	daemonize(
		stdout = os.path.join(config.logsDirectory, 'keeper.log'),
		stderr = os.path.join(config.logsDirectory, 'keeper.log'),
	)

	logger.info('Started keeper: %s', os.getpid())

	keep()


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
				status += ' at https://' + socket.gethostname() + ':' +  str(config.servicesConfiguration[service]['listeningPort']) + '/' + service + '/'
		else:
			status = ' --------'

		print service + (' ' * (maxlen - len(service))) +  status


def getCommand():
	'''Parses the arguments from the command line.
	'''

	parser = optparse.OptionParser(usage =
		'Usage: keeper [command] [args]\n'
		'\n'
		'Commands:\n'
		'  keeper start   <service>  Starts a service.\n'
		'  keeper stop    <service>  Stops a service.\n'
		'  keeper restart <service>  Restarts a service.\n'
		'  keeper kill    <service>  "kill -9" a service.\n'
		'\n'
		'  keeper test    <service>  Runs a service\'s test suite.\n'
		'\n'
		'  keeper less    <service>  "less" a service\'s log.\n'
		'  keeper tail    <service>  "tail -f" a service\'s log.\n'
		'  keeper lsof    <service>  "lsof" a service\'s processes.\n'
		'  keeper env     <service>  Prints the environment of a service\'s processes.\n'
		'\n'
		'  keeper status             Prints the status of the keeper\n'
		'                            and all the services, with PIDs.\n'
		'\n'
		'  <service> can be one of the following:\n'
		'    all keeper ' + ' '.join(services) + '\n'
		'    ("all" does not apply for less, tail, lsof nor env).\n'
		'\n'
		'  Note: "all" does not include the keeper: this command\n'
		'        is meant for private development, not dev/int/pro.\n'
		'        In dev/int/pro, the keeper is supposed to start\n'
		'        and stop the services itself.'
	)

	(options, arguments) = parser.parse_args()

	if len(arguments) < 1:
		parser.print_help()
		sys.exit(2)

	command = arguments[0]
	arguments = arguments[1:]

	commandsWith0Arguments = ['status']
	commandsWith1Arguments = ['start', 'stop', 'restart', 'kill', 'test', 'less', 'tail', 'lsof', 'env']
	commands = commandsWith0Arguments + commandsWith1Arguments

	if command not in commands:
		parser.print_help()
		sys.exit(2)

	if command in commandsWith0Arguments and len(arguments) != 0:
		parser.print_help()
		sys.exit(2)

	if command in commandsWith1Arguments and len(arguments) != 1:
		parser.print_help()
		sys.exit(2)

	return (command, arguments)


def main():
	(command, arguments) = getCommand()
	try:
		globals()[command](*arguments)
	except Exception as e:
		logger.error(e)


if __name__ == '__main__':
	main()

