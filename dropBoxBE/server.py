'''dropBox backend's web server.
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = ['Giacomo Govi', 'Salvatore Di Guida', 'Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


import logging
import socket
import time

# Initialize logging
import service

import config
import Dropbox


def main():
    '''Runs the dropBox forever.
    '''

    logging.info('Starting...')

    fqdn = socket.getfqdn()

    if fqdn.endswith('.cms'):
        logging.info('Using online configuration.')
        dropBoxConfig = config.online()
    elif fqdn.endswith('.cern.ch'):
        logging.info('Using test configuration.')
        dropBoxConfig = config.test()
    else:
        raise Exception('Not running at CERN.')

    logging.info('Configuring object...')

    dropBox = Dropbox.Dropbox(dropBoxConfig)

    logging.info('Running forever...')

    while dropBox.processAllFiles():
        time.sleep(dropBoxConfig.delay)


if __name__ == '__main__':
    main()

