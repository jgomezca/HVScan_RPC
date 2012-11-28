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
import logging

import service
import smtp
import cernldap

import dataAccess


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
    fromAddress = getAddress(fromAddress)
    toAddresses = [getAddress(x) for x in toAddresses]
    ccAddresses = [getAddress(x) for x in ccAddresses]

    logging.info('Sending email %s from %s with subject %s...', emailID, fromAddress, repr(subject))
    smtp.SMTP().sendEmail(subject, body, fromAddress, toAddresses, ccAddresses)


def main():
    '''Entry point.
    '''

    dataAccess.processEmails(processEmail)


if __name__ == '__main__':
    sys.exit(main())

