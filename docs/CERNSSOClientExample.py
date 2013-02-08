#!/usr/bin/env python
'''Pycurl CERN SSO Client example.

Requires the get-cern-sso-package.

See: http://linux.web.cern.ch/linux/docs/cernssocookie.shtml
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = ['Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


import subprocess
import pycurl
import cStringIO


def getCERNSSOCookie(url, cookieFilename):
    '''Signs in the server via CERN SSO using the current Kerberos tickets.

    Requires the cern-get-sso-cookie package.
    '''

    subprocess.check_call('cern-get-sso-cookie -u %s -o %s' % (url, cookieFilename), shell = True)


def getCERNSSOCurl(url):
    cookieFilename = 'cookie.txt'

    getCERNSSOCookie(url, cookieFilename)

    curl = pycurl.Curl()
    curl.setopt(curl.COOKIEFILE, cookieFilename)
    return curl


def main():
    url = 'https://cms-pdmv-dev.cern.ch/mcm/'

    curl = getCERNSSOCurl(url)

    # Small example of pycurl usage
    response = cStringIO.StringIO()
    curl.setopt(curl.SSL_VERIFYPEER, 1)
    curl.setopt(curl.SSL_VERIFYHOST, 2)
    curl.setopt(curl.CAPATH, '/etc/pki/tls/certs')
    curl.setopt(curl.URL, url)
    curl.setopt(curl.WRITEFUNCTION, response.write)
    curl.perform()
    code = curl.getinfo(curl.RESPONSE_CODE)
    response = response.getvalue()
    print code
    print response


if __name__ == '__main__':
    main()

