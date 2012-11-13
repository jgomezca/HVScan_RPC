'''Common code for sending emails from/to CERN via its SMTP servers for all CMS DB Web services.
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = ['Giacomo Govi', 'Salvatore Di Guida', 'Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


import logging
import smtplib
import email.mime.text
import email.header


class SMTP(object):
    '''Class used for sending emails from/to CERN via its SMTP servers.
    '''

    def __init__(self, password = None, server = None):
        '''If password is None, the anonymous SMTP server, cernmx.cern.ch will be used.
        Otherwise, the normal SMTP server, smtp.cern.ch, will be used.

        The server can also be overriden if it is not None.

        STARTTLS authentication will be used if password is not None.

        Note that the anonymous SMTP server has restrictions, see:
        https://espace.cern.ch/mmmservices-help/ManagingYourMailbox/Security/Pages/AnonymousPosting.aspx
        '''

        self.password = password

        if self.password is None:
            self.server = 'cernmx.cern.ch'
        else:
            self.server = 'smtp.cern.ch'

        if server is not None:
            self.server = server


    def __str__(self):
        return 'SMTP %s' % self.server


    def sendEmail(self, subject, body, fromAddress, toAddresses, ccAddresses = []):
        '''Sends an email.

        Note that toAddresses and ccAddresses are lists of emails.
        '''

        logging.debug('%s: Email from %s with subject %s: Preparing...', self, fromAddress, repr(subject))
        text = email.mime.text.MIMEText(body)
        text['Subject'] = email.header.Header(subject)
        text['From'] = fromAddress
        text['To'] = ', '.join(toAddresses)
        if len(ccAddresses) > 0:
            text['Cc'] = ', '.join(ccAddresses)

        logging.debug('%s: Email from %s with subject %s: Connecting...', self, fromAddress, repr(subject))
        smtp = smtplib.SMTP(self.server)
        if self.password is not None:
            logging.debug('%s: Email from %s with subject %s: Logging in...', self, fromAddress, repr(subject))
            smtp.starttls()
            smtp.ehlo()
            smtp.login(fromAddress, self.password)

        logging.debug('%s: Email from %s with subject %s: Sending...', self, fromAddress, repr(subject))
        smtp.sendmail(fromAddress, set(toAddresses + ccAddresses), text.as_string())

        smtp.quit()

