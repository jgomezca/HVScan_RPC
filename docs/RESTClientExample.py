#!/usr/bin/env python
'''Pycurl REST client example.

See: http://curl.haxx.se/libcurl/c/curl_easy_setopt.html
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = ['Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


import pycurl
import cStringIO


baseUrl = 'http://mos-dev-slc6:8099'


def perform(curl):
    response = cStringIO.StringIO()
    curl.setopt(curl.WRITEFUNCTION, response.write)
    curl.perform()
    code = curl.getinfo(curl.RESPONSE_CODE)
    response = response.getvalue()
    print 'Response code = %s' % code
    print 'Response body = %s' % response
    print '---'


def main():
    # Setup curl (probably adding the CERN SSO cookies, etc.)
    curl = pycurl.Curl()
    curl.setopt(curl.SSL_VERIFYPEER, 1)
    curl.setopt(curl.SSL_VERIFYHOST, 2)
    curl.setopt(curl.CAPATH, '/etc/pki/tls/certs')

    # GET the collection (index)
    curl.setopt(curl.URL, '%s' % baseUrl)
    curl.setopt(curl.HTTPGET, 1)
    perform(curl)

    # GET one of the resources of the collection
    curl.setopt(curl.URL, '%s/teebird' % baseUrl)
    perform(curl)

    # PUT that resource to change it
    data = '''
        <html>
            <div>color:black</div>
            <div>type:stable</div>
            <div>weight:999</div>
            <div>extra:extravalue</div>
        </html>
    '''
    curl.setopt(curl.UPLOAD, 1)
    curl.setopt(curl.READFUNCTION, cStringIO.StringIO(data).read)
    curl.setopt(curl.URL, '%s/teebird' % baseUrl)
    perform(curl)

    # GET again the resource to see the differences
    curl.setopt(curl.URL, '%s/teebird' % baseUrl)
    curl.setopt(curl.HTTPGET, 1)
    perform(curl)


if __name__ == '__main__':
    main()

