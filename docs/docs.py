'''CMS DB Web docs server.
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = ['Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


import cherrypy

import service


class Docs:
    '''Docs server.
    '''

    @cherrypy.expose
    def index(self):
        '''Redirects to index.html.
        '''

        raise cherrypy.HTTPRedirect("index.html")


def main():
    service.start(Docs())


if __name__ == '__main__':
    main()

