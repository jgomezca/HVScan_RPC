'''CMS DB Web easymon server.
This is a first, quick-and-dirty hack to get the easymon service
into the new CMS DB web infrastructure.
So far it is using the pre-formatted html snippets as delivered
by the nagios server at cmsdbnagiosvm and simply redirects it
to the user's browser.
'''

#ToDo: sanitize input further, check also return value from nagios server
#ToDo: fix css and update js packages (plus move the js to the weblibs)
#ToDo: rewrite and move to icinga/check_mk and json format from there

__author__ = 'Andreas Pfeiffer'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = [ 'Miguel Ojeda', 'Andreas Pfeiffer' ]
__license__ = 'Unknown'
__maintainer__ = 'Andreas Pfeiffer'
__email__ = 'andreas.pfeiffer@cern.ch'

import cherrypy
import logging

import service
import urllib2
import re

class easymon :
    '''Docs server.
    '''

    def isValidFileName(self, fileName):

        fnRe = re.compile('^[a-zA-Z-_]*$')
        res = False
        if fnRe.match(fileName):
            res = True
        return res

    @cherrypy.expose
    def index(self, *args, **kwargs) :
        '''Redirects to index.html.
        '''
        req = {}
        req[ 'fileName' ] = "main"
        if "fileName" in kwargs.keys( ) :
            req[ 'fileName' ] = kwargs[ 'fileName' ]

        logging.debug( "req is %s" % (str( req ),) )

        newPage = "getInfo"
        if req.has_key('fileName'): newPage += '?fileName='+req['fileName']

        raise cherrypy.HTTPRedirect( newPage )

    @cherrypy.expose
    def getInfo(self, *args, **kwargs) :

        req = {}
        req['fileName'] = "main"
        if "fileName" in kwargs.keys( ) :
            req[ 'fileName' ] = kwargs[ 'fileName' ]

        logging.debug( "req is %s" % (str(req),) )

        content = self.getNagiosInfo( **req )
        indexPage = ''.join( open('index.tmpl','r').readlines() ).replace('{{main}}', content)

        return indexPage

    @cherrypy.expose
    def getNagiosInfo(self, *args, **kwargs):

        fileName="main"
        if "fileName" in kwargs.keys():
            fileName = kwargs['fileName']

        if not self.isValidFileName( fileName ) :
            logging.warning( 'illegal request for fileName: %s - reset to main' % (fileName,) )
            fileName = 'main' # set default if illegal requests

        url = 'http://cmsdbnagiosvm.cern.ch:8081/getFileMobile?fileName=%s' % (fileName,)
        logging.debug( "url is %s" % (url,) )
        try:
            page =  urllib2.urlopen( url )
            content = page.read()
            # content = content.replace("index.html", "getNagiosInfo")
            # print "got: ", content
            return content
        except Exception, e:
            logging.error( "got %s when trying to retrieve %s" % (str(e), url) )
            return str(e)

def main() :

    logging.basicConfig(
        format='[%(asctime)s] %(levelname)s: %(message)s',
        level=logging.DEBUG,
    )
    logging.info( 'starting service easymon' )
    service.start( easymon( ) )

if __name__ == '__main__' :
    main( )
