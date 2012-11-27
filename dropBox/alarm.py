'''New dropBox's alarms.
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = ['Giacomo Govi', 'Salvatore Di Guida', 'Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


import logging

import config
import dataAccess

import service


def alarm(message):
    '''Raise an alarm.

    Currently this means to log and send an email the stripped message.
    '''

    message = message.strip()

    logging.error(message)

    body = '[ALARM] %s: %s' % (service.settings['name'], message)
    dataAccess.insertEmail(body[:100], body, config.fromAddress, config.toAddresses, config.ccAddresses)

