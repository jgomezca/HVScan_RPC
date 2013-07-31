import http
import service
import json
import logging

class Curler( object ) :
    def __init__(self, config) :
        self.curl = http.HTTP()
        if config.proxy:
            self.curl.setProxy(config.proxy)
        self.curl.setRetries(config.retriesPyCurler)
        self.config = config

    def get(self, url, data=None) :
        if data is not None:
            data = dict(data)

        if url.endswith('getFile'):
            self.curl.setTimeout(self.config.payloadTimeout)
        else:
            self.curl.setTimeout(self.config.timeout)

        try:
            result = self.curl.query(url, data)
        except http.HTTPError as e:
            if e.code == 404:
                logging.warning('We got 404 Not Found when querying %s; therefore, we probably lost the session due to a timeout (something went really slow before this call -- e.g. queries to Oracle). We will retry to signIn and do the query again, once.', url)
                baseUrl = url.rsplit('/', 1)[0]
                logging.info('Calculated baseUrl = %s', baseUrl)
                self.curl.query('%s/signIn' % baseUrl, {
                    'username': service.secrets['onlineUser']['user'],
                    'password': service.secrets['onlineUser']['password'],
                })
                result = self.curl.query(url, data)
            else:
                # In other cases, raise as usual
                raise

        try :
            result = json.loads(result)
        except Exception, e :
            if "No JSON object could be decoded" not in str( e ) :
                raise e

        return result

def test() :
    from config import test

    url = 'https://user.web.cern.ch/user/Welcome.asp'

    c = Curler(test())
    print " url = ", url, ' returned ', len( c.get(url) ), ' bytes.'

    url = 'https://cms-conddb-dev.cern.ch/getLumi/'

    print " url = ", url, ' returned ', len( c.get( url ) ), ' items in the JSON list.'

if __name__ == '__main__' :
    test( )
