'''Common code for alarms all CMS DB Web services.
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = ['Giacomo Govi', 'Salvatore Di Guida', 'Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


import logging
import json

import database
import service

# Provided by each service
import alarmConnection


defaultFromAddress = 'cms-cond-dev@cern.ch'
defaultToAddresses = ('cms-cond-dev@cern.ch', )
defaultCcAddresses = ()


def insertEmail(subject, body, fromAddress, toAddresses, ccAddresses = ()):
    alarmConnection.connection.commit('''
        insert into emails
        (subject, body, fromAddress, toAddresses, ccAddresses)
        values (:s, :s, :s, :s, :s)
    ''', (subject, database.BLOB(body), fromAddress, json.dumps(toAddresses), json.dumps(ccAddresses)))


def alarm(message, fromAddress = defaultFromAddress, toAddresses = defaultToAddresses, ccAddresses = defaultCcAddresses):
    '''Raise an alarm.

    Currently this means to log and send an email the stripped message.
    '''

    message = message.strip()

    logging.error(message)

    body = '[ALARM] %s: %s' % (service.settings['name'], message)
    insertEmail(body[:100], body, fromAddress, toAddresses, ccAddresses)

