import pycurl
import json
import cStringIO

class Curler( object ) :
    def __init__(self) :
        self.curl = pycurl.Curl( )
        self.curl.setopt( self.curl.COOKIEFILE, '' )
        self.curl.setopt( pycurl.SSL_VERIFYPEER, 0 )
        self.curl.setopt( pycurl.SSL_VERIFYHOST, 0 )

    def setVerbose(self, verb):
        if verb:
            self.curl.setopt( pycurl.VERBOSE, 1 )
        else:
            self.curl.setopt( pycurl.VERBOSE, 0 )

    def get(self, url, data=None) :
        response = cStringIO.StringIO( )
        self.curl.setopt( self.curl.WRITEFUNCTION, response.write )

        self.curl.setopt( self.curl.URL, url )

        if data :
            self.curl.setopt( self.curl.HTTPPOST, data )
        else :
            self.curl.setopt( self.curl.HTTPGET, 1 )

        self.curl.perform( )

        if self.curl.getinfo( self.curl.RESPONSE_CODE ) != 200 :
            raise Exception( response.getvalue( ) )

        try :
            result = json.loads( response.getvalue( ) )
        except Exception, e :
            if "No JSON object could be decoded" in str( e ) :
                result = response.getvalue( )
            else :
                raise e
        response.close( )

        return result

def test() :
    from config import test

    url = 'https://cern.ch'

    c = Curler()
    print " url = ", url, ' returned ', len( c.get(url) ), ' bytes.'

    url = 'https://cms-conddb-dev.cern.ch/getLumi'
    data = [ () ]

    print " url = ", url, ' returned ', len( c.get( url ) ), ' bytes.'

if __name__ == '__main__' :
    test( )
