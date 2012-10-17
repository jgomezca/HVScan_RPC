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

import cherrypy

import service

import config
import Dropbox


class DropBoxBE(object):
    '''dropBox backend's web server.
    '''

    def __init__(self):
        '''Initializes the dropBox object with the correct configuration.
        '''

        fqdn = socket.getfqdn()

        if fqdn.endswith('.cms'):
            logging.info('Using online configuration.')
            self.dropBoxConfig = config.online()
        elif fqdn.endswith('.cern.ch'):
            logging.info('Using test configuration.')
            self.dropBoxConfig = config.test()
        else:
            raise Exception('Not running at CERN.')


    @cherrypy.expose
    def run(self):
        '''Triggers the dropBox to process all files.
        '''

        #-mos TODO: Add authentication.

        logging.debug('server::run()')

        dropBox = Dropbox.Dropbox(self.dropBoxConfig)
        dropBox.processAllFiles()
        dropBox.shutdown()


def main():
    service.start(DropBoxBE())


if __name__ == '__main__':
    main()

