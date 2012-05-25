"""
popconJobMonitor
Author: Algirdas Beinaravicius, Antonio Pierro, Salvatore Di Guida
"""
import json
import urllib
import sys
import optparse
import os
import datetime
import smtplib
import email
from email.mime.text import MIMEText
#method name to call popcon backend
query_name = 'PopConCronjobStatus'

#indication of dead job status
status_dead_job = 'dead'

#default port number on which Popcon backend is running
default_port = '8980'

#default number of dead jobs to trigger notification sending
default_numDeadJobs = 4

#default gap time in minutes between notifications
default_gap_time = 60

#sms sending service hostname
sms_host = 'mail2sms.cern.ch'

#email sending server
smtp_server = 'smtp.cern.ch'

#external data file name
#currentdir = os.path.dirname(os.path.abspath(__file__))
external_data_file = '/tmp/.jobMonitor-' + str(os.getuid()) + '.dat'

class NotificationService(object):
	def __init__(self, settings):
		self.__smtpServer = smtp_server
		self.__settings = settings
	def __sendSMS(self, recipients, message):
		for number in recipients:
			send_command = 'echo \"' + message + '\" | mail ' + number + '@' + sms_host
			os.system(send_command)
			print ('SMS sent: ' + send_command)
			
	def __sendEmail(self, recipients, subject, message):
                print "recipients: ",recipients
		msg = MIMEText(message)
		msg['To'] = email.utils.formataddr(('Recipient', recipients))
		msg['From'] = email.utils.formataddr(('PopCon monitoring system', self.__settings['smtpSender']))
		msg['Subject'] = subject
		try:
			server = smtplib.SMTP(self.__smtpServer)
			server.set_debuglevel(True)
			server.ehlo()
			server.starttls()
			server.ehlo()
			server.login(self.__settings['smtpLogin'], self.__settings['smtpPass'])
			server.sendmail(self.__settings['smtpSender'], recipients, msg.as_string())
			server.quit()
			print ('EMAIL sent: ' + str(recipients))
		except smtplib.SMTPException, e:
			print 'ERROR: unable to send email'
			print e
		
	def notify(self, notificationData):
                print "notificationData: ",notificationData
		if (notificationData['sms']['recipients']):
			self.__sendSMS(notificationData['sms']['recipients'], notificationData['sms']['message'])
		if (notificationData['email']['recipients']):
			self.__sendEmail(notificationData['email']['recipients'], notificationData['email']['subject'], notificationData['email']['message'])

class ExternalData(object):
	def __init__(self, fname):
		self.__fname = fname
	
	def readFile(self):
		if os.path.isfile(self.__fname):
			f = open(self.__fname, 'r')
			data = f.read()
			f.close()
			return json.loads(data)
		return None
	
	def writeFile(self, data):
		f = open(self.__fname, 'w')
		f.write(json.dumps(data))
		f.close()
		
class PopConStatusReader(object):
	def __init__(self, settings):
		self.__query_name = query_name
		self.__status_service = urllib.urlopen(settings['url'] + ':' + settings['port'] + '/' + self.__query_name)
	
	def getDeadJobs(self):
		#print '#'*40 
		#print self.__status_service
		deadJobs = {'total' : 0, 'names' : []}
		data = json.loads(self.__status_service.read())
		for job in data:
			if job['status'] == status_dead_job:
				deadJobs['total'] += 1
				deadJobs['names'].append(job['job'])
		return deadJobs 
		
class ArgumentParser(object):
	def __init__(self):
		self.__parser = optparse.OptionParser()
		usageStr = 'Usage: ' + sys.argv[0] + ' [options] url\n'
		usageStr += 'Example: \n'
		usageStr += 'python ' + sys.argv[0] + ' -s 37067331922,37067331923 http://cms-conddb-backend\n'
		usageStr += 'python ' + sys.argv[0] + ' -p 8980 -n 4 -s 37067331922 http://cms-conddb-backend\n'
		usageStr += 'python ' + sys.argv[0] + ' -p 8980 -e my.email@cern.ch,another.email@cern.ch --smtp-login=login --smtp-pass=pass --smtp-sender=name.sender@cern.ch http://cms-conddb-backend'
		
		self.__parser.set_usage(usageStr)
		self.__parser.add_option('-p', '--port',
								dest='port',
								type='string',
								action='store',
								default=default_port,
								help='remote popcon service port')
		self.__parser.add_option('-n', '--numDead',
								dest='numDeadJobs',
								type='int',
								default=default_numDeadJobs,
								action='store',
								help='minimal number of dead jobs to send sms')
		
		self.__parser.add_option('-g', '--gapTime',
								dest='gapTime',
								type='int',
								default=default_gap_time,
								action='store',
								help='gap time in minutes')
		
		self.__parser.add_option('-s', '--sms',
								dest='recipientsSMS',
								type='string',
								default=None,
								action='store',
								help='list of sms notification recipients, separated by commas "," withous spaces')
		
		self.__parser.add_option('-e', '--email',
								dest='recipientsEmail',
								type='string',
								default=None,
								action='store',
								help='list of email notification recipients, separated by commas "," without spaces')
		
		self.__parser.add_option('--smtp-login',
								dest='smtpLogin',
								type='string',
								default=None,
								action='store',
								help='login name to smtp server')
		self.__parser.add_option('--smtp-pass',
								dest='smtpPass',
								type='string',
								default=None,
								action='store',
								help='smtp server password')
		self.__parser.add_option('--smtp-sender',
								dest='smtpSender',
								type='string',
								default=None,
								action='store',
								help='email of the sender')
								
	def __checkArguments(self, options, remainder):
		if len(remainder) == 0:
			print 'Specify url. Use -h to get more help'
			exit(-1)
		if (not options.recipientsSMS) and (not options.recipientsEmail):
			print 'Specify at least one recipient. Use -h to get more help'
			exit(-1)
		if (options.recipientsEmail):
			if (not options.smtpLogin):
				print 'Specify login name to smtp server (--smtp-login). Use -h to get more help'
				exit(-1)
			if (not options.smtpPass):
				print 'Specify password for smtp server (--smtp-pass). Use -h to get more help'
				exit(-1)
			if (not options.smtpSender):
				print 'Specify sender for smtp server (--smtp-sender). Use -h to get more help'
				exit(-1)
			
	def parse(self, cmd_args):
		settings = {}
		options, remainder = self.__parser.parse_args(cmd_args)
		self.__checkArguments(options, remainder)
		settings['url'] = remainder[0]
		settings['port'] = options.port
		settings['numDeadJobs'] = options.numDeadJobs
		settings['gapTime'] = options.gapTime
		if (options.recipientsSMS):
			settings['recipientsSMS'] = options.recipientsSMS.split(',')
		else:
			settings['recipientsSMS'] = None
		if (options.recipientsEmail):
			settings['recipientsEmail'] = options.recipientsEmail.split(',')
			settings['smtpLogin'] = options.smtpLogin
			settings['smtpPass'] = options.smtpPass
			settings['smtpSender'] = options.smtpSender
		else:
			settings['recipientsEmail'] = None
		return settings

class JobMonitor(object):
	def __init__(self, settings):
		self.__settings = settings
		self.__statusReader = PopConStatusReader(settings)
		self.__notificationService = NotificationService(settings)
		self.__extData = ExternalData(external_data_file)
		self.__timestampFormat = '%Y-%m-%d %H:%M:%S'
		self.__notificationData = {'sms' : {}, 'email' : {}}
		self.__notificationData['sms']['recipients'] = settings['recipientsSMS']
		self.__notificationData['email']['recipients'] = settings['recipientsEmail'] 

	def run(self):
		deadJobs = self.__statusReader.getDeadJobs()
                print "XXX",deadJobs['total'], "TTT",settings['numDeadJobs']
		if (deadJobs['total'] >= settings['numDeadJobs']):
			smsMessage = 'PopCon job monitor: ' + str(deadJobs['total']) + ' jobs dead'
			emailSubject = 'PopCon job monitor: ' + str(deadJobs['total']) + ' jobs dead'
			emailMessage = 'Dead jobs:\n'
			for name in deadJobs['names']:
				emailMessage += '\t' + name + '\n'
			emailMessage += 'http://condb.web.cern.ch/condb/popcon/PopConCronjobTailFetcher.html'	
			
			self.__notificationData['sms']['message'] = smsMessage
			self.__notificationData['email']['message'] = emailMessage
			self.__notificationData['email']['subject'] = emailSubject
			currentTime = datetime.datetime.now()
			data = self.__extData.readFile()
			if (data):
				notificationTime = datetime.datetime.strptime(data['notificationTimestamp'], self.__timestampFormat)
				timedelta = currentTime - notificationTime
                                print "timedelta",timedelta
				if (timedelta.seconds > self.__settings['gapTime'] * 60):
					self.__notificationService.notify(self.__notificationData)
					data['notificationTimestamp'] = currentTime.strftime(self.__timestampFormat)
					self.__extData.writeFile(data)
			else:
				self.__notificationService.notify(self.__notificationData)
				data = {'notificationTimestamp' : currentTime.strftime(self.__timestampFormat)}
				self.__extData.writeFile(data)
	
if __name__ == '__main__':
	argParser = ArgumentParser()
	settings = argParser.parse(sys.argv[1:])
	jobMonitor = JobMonitor(settings)
	jobMonitor.run()
	
