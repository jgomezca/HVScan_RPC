'''CMS DB Web sessionTest server.

Only intended for debugging load balancing and session related issues.

e.g.
    For new requests (new sessions) all the time:

        rm cookiesnew.txt && date && curl -k -c cookiesnew.txt -b cookiesnew.txt 'https://mos-dev-slc6/sessionTest/show'

    Keeping the cookies (edit as needed the cookie file).

        date && curl -k -c cookies1.txt -b cookies1.txt 'https://mos-dev-slc6/sessionTest/show'
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2013, CERN CMS'
__credits__ = ['Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


import os

import cherrypy

import service


# Ensure the sessions folder exist
service.makePath(os.path.join(service.getFilesPath(), 'sessions'))


def prefixInfo(f):
    def newf(*args, **kwargs):
        result = ''

        if 'ROUTEID' in cherrypy.request.cookie:
            result += 'Route = %s\n' % cherrypy.request.cookie['ROUTEID']
        else:
            result += 'Route = (not found)\n'

        if 'session_id' in cherrypy.request.cookie:
            result += 'Session = %s\n' % cherrypy.request.cookie['session_id']
        else:
            result += 'Session = (not found)\n'

        return service.setResponsePlainText('%s%s' % (result, f(*args, **kwargs)))

    return newf


class SessionTest(object):
    '''Session Test server.
    '''

    @cherrypy.expose
    @prefixInfo
    def index(self):
        return 'Index. Use insert(value), delete(), show() and/or expirte().\n'


    @cherrypy.expose
    @prefixInfo
    def insert(self, value):
        if 'value' in cherrypy.session:
            cherrypy.session['value'] = value
            return 'Warning: Overwriting value.\n'
        else:
            cherrypy.session['value'] = value
            return 'OK: Inserted value.\n'


    @cherrypy.expose
    @prefixInfo
    def delete(self):
        if 'value' in cherrypy.session:
            del cherrypy.session['value']
            return 'Deleted correctly.\n'
        else:
            return 'Error: No value to delete.\n'


    @cherrypy.expose
    @prefixInfo
    def show(self):
        if 'value' in cherrypy.session:
            return 'Value = %s\n' % repr(cherrypy.session['value'])
        else:
            return 'Error: No value.\n'


    @cherrypy.expose
    @prefixInfo
    def expire(self):
        cherrypy.lib.sessions.expire()


def main():
	service.start(SessionTest())


if __name__ == '__main__':
	main()

