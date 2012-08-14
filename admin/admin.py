'''CMS DB Web admin server.
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = ['Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


import cherrypy
import subprocess


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
	cmd = kwargs.get('args')
	if cmd is None:
		cmd = popenargs[0]
	if returnCode:
		raise subprocess.CalledProcessError(returnCode, cmd)
	return stdout


class Admin:
	'''Admin server.
	'''

	@cherrypy.expose
	def index(self):
		'''Status page.
		'''

		title = 'CMS DB Web Services Status'

		table = '''
			<tr>
				<th>Service</th>
				<th>Jobs</th>
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

		for service in ['keeper'] + config.getServicesList(showHiddenServices = True):
			jobs = ''
			status = ''
			url = ''

			enabledJobs = keeper.hasEnabledJobs(service)
			if enabledJobs:
				jobs = 'Enabled'

			pids = keeper.getPIDs(service)
			running = len(pids) > 0
			if running:
				status = ','.join(pids)

				url = '/%s/' % service
				if service != 'keeper':
					url = '<a href="%s">%s</a>' % (url, url)

			# FIXME: Add the ability to restart/stop/kill the admin service via a proxy process
			#        and returning a proper message to the user.
			actions = ''
			for action in ['tail']:
				actions += makeAction(service, action)
			for action in ['lsof', 'env']:
				actions += makeAction(service, action, not running)
			for action in ['start']:
				actions += makeAction(service, action, running or service == 'admin')
			for action in ['stop', 'restart', 'kill']:
				actions += makeAction(service, action, not running or service == 'admin')
			for action in ['enableJobs']:
				actions += makeAction(service, action, enabledJobs or service == 'keeper')
			for action in ['disableJobs']:
				actions += makeAction(service, action, not enabledJobs or service == 'keeper')

			table += '''
				<tr>
					<td>%s</td>
					<td>%s</td>
					<td>%s</td>
					<td>%s</td>
					<td>%s</td>
				</tr>
			''' % (service, jobs, status, url, actions)

		template = '''
			<html>
				<head>
					<title>%s</title>
					<style type="text/css">
						form {
							display: inline;
						}
					</style>

				</head>
				<body>
					<h1>%s</h1>
					<p>
						<form action="start" method="post"><input name="service" type="hidden" value="all" /><input value="Start all" type="submit" /></form>
					</p>
					<table>%s</table>
				</body>
			</html>
		'''

		return template % (title, title, table)


	@cherrypy.expose
	def start(self, service):
		'''Starts a service.
		'''

		keeper.start(service)
		# FIXME: Wait until it starts implementing something like keeper.wait(service, for = 'start')
		raise cherrypy.HTTPRedirect('./')


	@cherrypy.expose
	def stop(self, service):
		'''Stops a service.
		'''

		keeper.stop(service)
		raise cherrypy.HTTPRedirect('./')


	@cherrypy.expose
	def restart(self, service):
		'''Restarts a service.
		'''

		keeper.restart(service)
		# FIXME: Wait until it starts implementing something like keeper.wait(service, for = 'start')
		raise cherrypy.HTTPRedirect('./')


	@cherrypy.expose
	def kill(self, service):
		'''Kills a service.
		'''

		keeper.kill(service)
		raise cherrypy.HTTPRedirect('./')


	@cherrypy.expose
	def enableJobs(self, service):
		'''Enable the jobs of a service.
		'''

		keeper.enableJobs(service)
		raise cherrypy.HTTPRedirect('./')


	@cherrypy.expose
	def disableJobs(self, service):
		'''Disable the jobs of a service.
		'''

		keeper.disableJobs(service)
		raise cherrypy.HTTPRedirect('./')


	@cherrypy.expose
	def tail(self, service):
		'''Tails the logs of a service.
		'''

		return setResponsePlainText(check_output('tail -n 1000 %s' % keeper.getLogPath(service), shell = True))


	@cherrypy.expose
	def lsof(self, service):
		'''"lsof" a service's processes.
		'''

		return setResponsePlainText(check_output('/usr/sbin/lsof -p %s' % ','.join(keeper.getPIDs(service)), shell = True))


	@cherrypy.expose
	def env(self, service):
		'''Prints the environment of a service's processes.
		'''

		return setResponseJSON(keeper.getEnvironment(service))


def main():
	service.start(Admin())


if __name__ == '__main__':
	main()

