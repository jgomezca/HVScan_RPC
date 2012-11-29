#!/usr/bin/env python2.6
'''Sends and deletes the queued emails of the dropBox.
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = ['Giacomo Govi', 'Salvatore Di Guida', 'Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


import sys
import time
import logging

import service
import smtp
import cernldap

import dataAccess


sleepTime = 10 # seconds


def getAddress(address):
    '''Gets an address if the address is not an email but a CERN username:

        If it contains '@', i.e. an email, leave it like that.
        If not, it is a CERN username and we use LDAP to get the real email.

        The advantage of doing the LDAP lookup here is to take out problems
        with the LDAP server from the normal dropBox workflow to here.
    '''

    if '@' in address:
        return address

    return cernldap.CERNLDAP().getUserEmail(address)


def processEmail(emailID, subject, body, fromAddress, toAddresses, ccAddresses):
    logging.info('Processing email %s from %s with subject %s...', emailID, fromAddress, repr(subject))
    fromAddress = getAddress(fromAddress)
    toAddresses = [getAddress(x) for x in toAddresses]
    ccAddresses = [getAddress(x) for x in ccAddresses]

    logging.info('Sending email %s from %s with subject %s...', emailID, fromAddress, repr(subject))
    smtp.SMTP().sendEmail(subject, body, fromAddress, toAddresses, ccAddresses)


def main():
    '''Entry point.
    '''

    logging.info('Sending emails forever...')
    while True:
        try:
            dataAccess.processEmails(processEmail)
        except Exception as e:
            logging.error('Error processing emails: %s', e)

        logging.info('Sleeping %s seconds...', sleepTime)
        time.sleep(sleepTime)


if __name__ == '__main__':
    sys.exit(main())

