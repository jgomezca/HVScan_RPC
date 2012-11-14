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

import dataAccess


def processEmail(emailID, subject, body, fromAddress, toAddresses, ccAddresses):
    logging.info('Sending email %s from %s with subject %s...', emailID, fromAddress, repr(subject))
    smtp.SMTP().sendEmail(subject, body, fromAddress, toAddresses, ccAddresses)


def main():
    '''Entry point.
    '''

    dataAccess.processEmails(processEmail)


if __name__ == '__main__':
    sys.exit(main())

