'''Shibboleth Test server.
'''

__author__ = 'Andreas Pfeiffer'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = ['Andreas Pfeiffer', 'Miguel Ojeda']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


import os
import time
import socket
import cherrypy

import service


class ShibbolethTest:

    @cherrypy.expose
    def index(self):
        '''Returns debugging information of Shibboleth.
        '''
        
        template = '''
            <html>
                <head>
                    <title>Shibboleth Test</title>
                </head>
                <body>
                    <h1>Shibboleth Test</h1>
                    <form action="signOut" method="get"><input value="Sign Out" type="submit" /></form>
                    <pre>%s</pre>
                </body>
            </html>
        '''

        try:
            service.getUsername()
        except KeyError:
            return template % 'No Shibboleth/Adfs headers found. Probably in a private VM/instance.'

        data = [
            ('Username', service.getUsername()),
            ('Current Time', time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())),
            ('Hostname', '%s:%s' % (socket.gethostname(), str(cherrypy.config.get('server.socket_port')))),
            ('In zh', 'zh' in service.getGroups()),
            ('In cms-cond-dev', 'cms-cond-dev' in service.getGroups()),
            ('In cms-cond-dev-admin', 'cms-cond-dev-admin' in service.getGroups()),
            ('Groups', '\n' + '\n'.join(['    %s' % group for group in sorted(service.getGroups())])),
            ('Headers', '\n' + '\n'.join(['    %s: %s' % header for header in sorted(cherrypy.request.headers.items())])),
        ]

        return template % '\n'.join(['%s: %s' % x for x in data])


    @cherrypy.expose
    def signOut(self):
        '''Redirects to CERN SSO's logout.
        '''

        raise cherrypy.HTTPRedirect('https://login.cern.ch/adfs/ls/?wa=wsignout1.0')


def main():
    service.start(ShibbolethTest())


if __name__ == '__main__':
    main()

