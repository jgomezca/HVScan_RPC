import http
import json

class Curler( object ) :
    def __init__(self, config) :
        self.curl = http.HTTP()
        self.curl.setProxy(config.proxy)
        self.curl.setTimeout(config.timeout)
        self.curl.setRetries(config.retriesPyCurler)

    def get(self, url, data=None) :
        if data is not None:
            data = dict(data)

        result = self.curl.query(url, data)

        try :
            result = json.loads(result)
        except Exception, e :
            if "No JSON object could be decoded" not in str( e ) :
                raise e

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
