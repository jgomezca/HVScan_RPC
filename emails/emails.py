#!/usr/bin/env python2.6
'''Sends and deletes queued emails from the services.
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
import json

import service
import smtp
import cernldap
import database

import config


connections = {}
for serviceName in config.services:
    connections[serviceName] = database.Connection(config.connections['dropBox'])


@database.transaction
def _processEmail(connection, cursor, processFunction):
    '''Returns True if an email was processed (i.e. if there may be
    more emails to process).
    '''

    # We will probably have only one consumer and performance is not an issue
    emailID = connection._fetch(cursor, '''
        select id
        from emails
        where rownum <= 1
        for update skip locked
    ''')

    if emailID == []:
        return

    emailID = emailID[0][0]

    (subject, body, fromAddress, toAddresses, ccAddresses) = connection._fetch(cursor, '''
        select subject, body, fromAddress, toAddresses, ccAddresses
        from emails
        where id = :s
    ''', (emailID, ))[0]

    processFunction(emailID, subject, body, fromAddress, json.loads(toAddresses), json.loads(ccAddresses))

    connection.commit('''
        delete from emails
        where id = :s
    ''', (emailID, ))

    return True

    # This one is commit() instead of _commit(), i.e. transaction,
    # since we want to retry only this piece in case of lost connection,
    # because if we reach this after sending the email and we lose
    # the connection here, we would send twice the same email if we retry
    # the full transaction. In addition, if there is more than one consumer
    # and we lose the connection, the other consumer may pick up the row
    # since we would have lost the lock. However, we do not expect several
    # consumers and, in any case, the only harmful effect of this quite
    # rare scenario (Oracle not reachable several times in a row) would be
    # a duplicated email sent.
    #
    # A solution for this would be to store some state, like a flag,
    # in the database [1]; and then splitting this into two transactions
    # that manipulate the flag. However, even if that solves the problem
    # of sending an email twice, it arises more problems, like emails
    # not sent (dead rows) in the same scenario, unless we also check
    # and send emails from dead rows if they are older than twice
    # the frequency of email sending. Since a duplicate email is not a critical
    # issue and Oracle not being reachable several times in a row should
    # be a rare event, we just went for the simple solution. Other solutions
    # include using local storage in case of network problems, etc.
    #
    # [1]
    #
    #     # First transaction to atomically update the flag and fetch the email
    #     email = _atomicallyFetchEmail(connection)
    #     if email is None:
    #         break
    #
    #     # Second transaction after the email is sent
    #     try:
    #         processFunction(*email)
    #     except:
    #         connection.commit('''
    #             update emails
    #             set state = 'Pending'
    #             where id = :s
    #         ''', (email[0], ))
    #         break
    #
    #     connection.commit('''
    #         delete from emails
    #         where id = :s
    #     ''', (email[0], ))


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
        for serviceName in connections:
            try:
                logging.info('%s: Sending emails...', serviceName)
                while _processEmail(connections[serviceName], processEmail):
                    pass
            except Exception as e:
                logging.error('%s: Error processing emails: %s', serviceName, e)

        logging.info('Sleeping %s seconds...', config.sleepTime)
        time.sleep(config.sleepTime)


if __name__ == '__main__':
    sys.exit(main())

