'''CMS DB Web easymon server.
This is a first, quick-and-dirty hack to get the easymon service
into the new CMS DB web infrastructure.
So far it is using the pre-formatted html snippets as delivered
by the nagios server at cmsdbnagiosvm and simply redirects it
to the user's browser.
'''

#ToDo: sanitize input further, check also return value from nagios server
#ToDo: move the jquery-mobile library to the weblibs
#ToDo: rewrite and move to icinga/check_mk and json format from there

__author__ = 'Andreas Pfeiffer'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = [ 'Miguel Ojeda', 'Andreas Pfeiffer' ]
__license__ = 'Unknown'
__maintainer__ = 'Andreas Pfeiffer'
__email__ = 'andreas.pfeiffer@cern.ch'


import re

import cherrypy
import jinja2

import http
import service


with open('index.tmpl', 'r') as f:
    indexTemplate = jinja2.Template(f.read())


class Easymon(object):
    '''Easymon instance which fetches information from a given Nagios server.
    '''

    def __init__(self, urlTemplate):
        self.urlTemplate = urlTemplate


    @cherrypy.expose
    def index(self, fileName = 'main'):
        if not re.match('^[0-9a-zA-Z-_]*$', fileName):
            raise cherrypy.NotFound()

        return indexTemplate.render(body = http.HTTP().query(self.urlTemplate % fileName))


class EasymonServer(object):
    '''Easymon parent server. This contains the real easymon servers, i.e.
    /easymon/offline and /easymon/online, which map to the old /easymon
    and /easymon_online. The index, by default, goes to the offline one.
    '''

    offline = Easymon('http://cmsdbnagiosvm:8081/getFileMobile?fileName=%s')
    online = Easymon('http://cmsdbnagiosvm:8091/getFileMobile?fileName=%s')


    @cherrypy.expose
    def index(self):
        raise cherrypy.HTTPRedirect('offline')


def main() :
    service.start( EasymonServer( ) )

if __name__ == '__main__' :
    main( )

