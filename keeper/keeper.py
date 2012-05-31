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

services = sorted(list(config.servicesConfiguration))


import os
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

	return os.popen("ps aux | grep -F '" + string + "' | grep -F -v 'grep' | grep -F -v 'bash' | awk '{print $2}'", 'r').read().splitlines()


def getPIDs(service):
	'''Returns the PIDs of a service or the keeper itself.
	'''

	if service == 'keeper':
		pids = set(_getPIDs('keeper.py start keeper'))
		pids -= set([str(os.getpid())])
	else:
		pids = _getPIDs('python ' + config.servicesConfiguration[service]['filename'])

		# At the moment all services run one and only one process
		if len(pids) > 1:
			raise Exception('Please update the code for getting the PID of ' + service)

	return pids


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


def kill(pid):
	'''Sends SIGTERM to a process.
	'''

	logger.info('Killing %s', pid)
	os.kill(int(pid), signal.SIGTERM)


def daemonize(stdoutFile = None, stderrFile = None, workingDirectory = '/'):
	'''Daemonize the current process.
	'''

	# Fork off and die
	if os.fork() != 0:
		os._exit(0)

	# Change working directory
	os.chdir(workingDirectory)

	# Get new session
	os.setsid()

	# Use the null device as stdin
	fd = os.open(os.devnull, os.O_RDONLY)
	os.dup2(fd, sys.stdin.fileno())
	os.close(fd)

	# Flush fds
	sys.stdout.flush()
	sys.stderr.flush()

	# Redirect stdout
	if stdoutFile is not None:
		fd = os.open(stdoutFile, os.O_WRONLY | os.O_APPEND | os.O_CREAT)
		os.dup2(fd, sys.stdout.fileno())
		os.close(fd)

	# Redirect stderr
	if stderrFile is not None:
		fd = os.open(stderrFile, os.O_WRONLY | os.O_APPEND | os.O_CREAT)
		os.dup2(fd, sys.stderr.fileno())
		os.close(fd)


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
		# FIXME: Fix the services so that we can chdir to /
		daemonize(
			workingDirectory = os.path.join(config.servicesDirectory, service),
		)

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
		servicePath = os.path.abspath(os.path.join(config.servicesDirectory, 'common'))
		secretsPath = os.path.abspath(os.path.join(config.servicesDirectory, '..', 'secrets'))
		os.putenv('PYTHONPATH', servicePath + ':' + secretsPath)

		# Setup the command line
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
		serviceConfiguration = config.servicesConfiguration[service]
		commandLine += 'python ' + serviceConfiguration['filename'] + ' --rootDirectory ' + os.path.abspath(os.path.join(config.servicesDirectory, service)) + ' --listeningPort ' + str(serviceConfiguration['listeningPort']) + ' --productionLevel ' + config.getProductionLevel()

		# And pipe its output to rotatelogs
		# FIXME: Fix the services so that they do proper logging themselves
		commandLine += ' 2>&1 | /usr/sbin/rotatelogs -L ' + config.logsFileTemplate % service  + ' ' + config.logsFileTemplate % service + ' ' + config.logsSize

		# Execute the command line on the shell
		os.execlp('bash', 'bash', '-c', commandLine)

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


def stop(service):
	'''Stops a service or the keeper itself.
	'''

	if service == 'all':
		for service in services:
			stop(service)
		return

	if service == 'keeper':
		return stopKeeper()

	checkRegistered(service)

	pids = getPIDs(service)

	# Service not running
	if len(pids) == 0:
		logger.warning('Tried to stop a service which is not running.')
		return

	for pid in pids:
		kill(pid)

	logger.info('Stopped %s: %s', service, ','.join(pids))


def restart(service):
	'''Restarts a service or the keeper itself.
	'''

	if service == 'keeper':
		return restartKeeper()

	if service != 'all':
		checkRegistered(service)

	try:
		stop(service)
	except:
		pass

	start(service)


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
		stdoutFile = os.path.join(config.logsDirectory, 'keeper.log'),
		stderrFile = os.path.join(config.logsDirectory, 'keeper.log'),
	)

	logger.info('Started keeper: %s', os.getpid())

	keep()


def stopKeeper():
	'''Stops the keeper (it stops all keepers found).
	'''

	pids = getPIDs('keeper')

	if len(pids) == 0:
		logger.warning('Tried to stop the keeper which is not running.')
		return

	for pid in pids:
		kill(pid)

	logger.info('Stopped keeper: %s', ','.join(pids))


def restartKeeper():
	'''Restarts the keeper.
	'''

	try:
		stopKeeper()
	except:
		pass

	startKeeper()


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
				status += ' at http://' + socket.gethostname() + ':' +  str(config.servicesConfiguration[service]['listeningPort']) + '/' + service + '/'
		else:
			status = ' --------'

		logger.info(service + (' ' * (maxlen - len(service))) +  status)


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
		'  keeper status             Prints the status of the keeper\n'
		'                            and all the services, with PIDs.\n'
		'\n'
		'  <service> can be one of the following:\n'
		'    all keeper ' + ' '.join(services) + '\n'
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
	commandsWith1Arguments = ['start', 'stop', 'restart']
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

