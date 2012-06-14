'''CMS DB Web docs server.
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = ['Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


import cherrypy
import socket
import subprocess
import json


import service
from service import setResponsePlainText, setResponseJSON


import sys
sys.path.append('../keeper')
import keeper
import config


def check_output(*popenargs, **kwargs):
	'''Mimics subprocess.check_output() in Python 2.6
	'''

	process = subprocess.Popen(*popenargs, stdout=subprocess.PIPE, **kwargs)
	stdout = process.communicate()[0]
	returnCode = process.returncode
	cmd = kwargs.get("args")
	if cmd is None:
		cmd = popenargs[0]
	if returnCode:
		raise subprocess.CalledProcessError(returnCode, cmd)
	return stdout


def isSignedIn():
	try:
		return cherrypy.session['user']
	except:
		return


def checkSignedIn(f):
	def newf(*args, **kwargs):
		if isSignedIn() is None:
			raise cherrypy.HTTPRedirect("admin")
		return f(*args, **kwargs)
	newf.exposed = True
	return newf


class Docs:
	'''Docs server.
	'''


	@cherrypy.expose
	def signIn(self, username, password):
		'''Sign in.
		'''

		if username not in service.secrets['users'] or password != service.secrets['users'][username]:
			raise cherrypy.HTTPRedirect("admin")

		cherrypy.session['user'] = username

		raise cherrypy.HTTPRedirect("status")


	@cherrypy.expose
	def admin(self):
		return '''
			<html>
				<head>
					<title>Sign In</title>
					<link rel="stylesheet" type="text/css" href="docs.css" />
				</head>
				<body>
					<form action="signIn" method="post">
						<table>
							<tr>
								<td><label for="username">Username</label></td>
								<td><input name="username" type="text" size="15" /></td>
							</tr>
							<tr>
								<td><label for="password">Password</label></td>
								<td><input name="password" type="password" size="15" /></td>
							</tr>
							<tr>
								<td></td>
								<td><input value="Sign In" type="submit" /></td>
							</tr>
						</table>
					</form>
				</body>
			</html>
		'''


	@checkSignedIn
	def status(self):
		'''Status page.
		'''

		title = 'CMS DB Web Services Status'

		table = '''
			<tr>
				<th>Service</th>
				<th>Status</th>
				<th>Link</th>
				<th>Actions</th>
			</tr>
		'''

		def makeAction(service, action, disabled = False):
			actionTemplate = '''
				<form action="%s" method="get"><input name="service" type="hidden" value="%s" /><input value="%s" type="submit" %s /></form>
			'''

			disabledText = ''
			if disabled:
				disabledText = 'disabled="disabled"'

			return actionTemplate % (action, service, action, disabledText)

		for service in ['keeper'] + config.getServicesList():
			status = ''
			url = ''
			pids = keeper.getPIDs(service)
			running = len(pids) > 0
			if running:
				status = 'RUNNING: ' + ','.join(pids)

				# On private machines there is no proxy so we need to specify the port
				if config.getProductionLevel() == 'private':
					if service != 'keeper':
						url = 'https://%s:%s/%s/' % (socket.gethostname(), str(config.servicesConfiguration[service]['listeningPort']), service)
				else:
					url = '/%s/' % service

				if service != 'keeper':
					url = '<a href="%s">%s</a>' % (url, url)

			actions = ''
			for action in ['tail']:
				actions += makeAction(service, action)
			for action in ['lsof', 'env']:
				actions += makeAction(service, action, not running)
			for action in ['start']:
				actions += makeAction(service, action, running or service in ['keeper', 'docs'])
			for action in ['stop', 'restart', 'kill']:
				actions += makeAction(service, action, not running or service in ['keeper', 'docs'])

			table += '''
				<tr>
					<td>%s</td>
					<td>%s</td>
					<td>%s</td>
					<td>%s</td>
				</tr>
			''' % (service, status, url, actions)

		template = '''
			<html>
				<head>
					<title>%s</title>
					<link rel="stylesheet" type="text/css" href="docs.css" />
				</head>
				<body>
					<h1>%s</h1>
					<p>
						<form action="start" method="post"><input name="service" type="hidden" value="all" /><input value="Start all" type="submit" /></form>
						<form action="stop" method="post"><input name="service" type="hidden" value="all" /><input value="Stop all" type="submit" disabled="disabled" /></form>
						<form action="restart" method="post"><input name="service" type="hidden" value="all" /><input value="Restart all" type="submit" disabled="disabled" /></form>
						<form action="kill" method="post"><input name="service" type="hidden" value="all" /><input value="Kill all" type="submit" disabled="disabled" /></form>
					</p>
					<table>%s</table>
				</body>
			</html>
		'''

		return template % (title, title, table)


	@checkSignedIn
	def start(self, service):
		'''Starts a service.
		'''

		keeper.start(service)
		raise cherrypy.HTTPRedirect("status")


	@checkSignedIn
	def stop(self, service):
		'''Stops a service.
		'''

		keeper.stop(service)
		raise cherrypy.HTTPRedirect("status")


	@checkSignedIn
	def restart(self, service):
		'''Restarts a service.
		'''

		keeper.restart(service)
		raise cherrypy.HTTPRedirect("status")


	@checkSignedIn
	def kill(self, service):
		'''Kills a service.
		'''

		keeper.kill(service)
		raise cherrypy.HTTPRedirect("status")


	@checkSignedIn
	def tail(self, service):
		'''Tails the logs of a service.
		'''

		return setResponsePlainText(check_output('tail -n 1000 %s' % keeper.getLogPath(service), shell = True))


	@checkSignedIn
	def lsof(self, service):
		'''"lsof" a service's processes.
		'''

		return setResponsePlainText(check_output('/usr/sbin/lsof -p %s' % ','.join(keeper.getPIDs(service)), shell = True))


	@checkSignedIn
	def env(self, service):
		'''Prints the environment of a service's processes.
		'''

		return setResponseJSON(keeper.getEnvironment(service))


	@cherrypy.expose
	def index(self):
		'''Redirects to index.html.
		'''

		raise cherrypy.HTTPRedirect("index.html")


def main():
	service.start(Docs())


if __name__ == '__main__':
	main()

