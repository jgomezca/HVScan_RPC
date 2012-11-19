'''Common code for querying HTTP(S) URLs for all CMS DB Web services.
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = ['Giacomo Govi', 'Salvatore Di Guida', 'Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


import time
import logging
import cStringIO

import pycurl
import copy



class HTTPError(Exception):
    '''A common HTTP exception.

    self.code is the response HTTP code as an integer.
    self.response is the response body (i.e. page).
    '''

    def __init__(self, code, response):
        self.code = code
        self.response = response
        self.args = (self.response, )


class HTTP(object):
    '''Class used for querying URLs using the HTTP protocol.
    '''

    retryCodes = frozenset([502, 503])


    def __init__(self):
        self.setBaseUrl()
        self.setRetries()

        self.curl = pycurl.Curl()
        self.curl.setopt(self.curl.COOKIEFILE, '')
        self.curl.setopt(self.curl.SSL_VERIFYPEER, 0)
        self.curl.setopt(self.curl.SSL_VERIFYHOST, 0)


    def discardCookies(self):
        '''Discards cookies.
        '''

        self.curl.setopt(self.curl.COOKIELIST, 'ALL')


    def setBaseUrl(self, baseUrl = ''):
        '''Allows to set a base URL which will be prefixed to all the URLs
        that will be queried later.
        '''

        self.baseUrl = baseUrl


    def setProxy(self, proxy = ''):
        '''Allows to set a proxy.
        '''

        self.curl.setopt(self.curl.PROXY, proxy)


    def setTimeout(self, timeout = 0):
        '''Allows to set a timeout.
        '''

        self.curl.setopt(self.curl.TIMEOUT, timeout)


    def setRetries(self, retries = ()):
        '''Allows to set retries.

        The retries are a sequence of the seconds to wait per retry.

        The retries are done on:
            * PyCurl errors (includes network problems, e.g. not being able
              to connect to the host).
            * 502 Bad Gateway (for the moment, to avoid temporary
              Apache-CherryPy issues).
            * 503 Service Temporarily Unavailable (for when we update
              the frontends).
        '''

        self.retries = retries


    def query(self, url, data = None, files = None, keepCookies = True):
        '''Queries a URL, optionally with some data (dictionary).

        If no data is specified, a GET request will be used.
        If some data is specified, a POST request will be used.

        If files is specified, it must be a dictionary like data but
        the values are filenames.

        By default, cookies are kept in-between requests.

        A HTTPError exception is raised if the response's HTTP code is not 200.
        '''

        if not keepCookies:
            self.discardCookies()

        url = self.baseUrl + url

        # make sure the logs are safe ... at least somewhat :)
        data4log = copy.copy(data)
        if data4log:
            if 'password' in data4log.keys():
                data4log['password'] = '*'

        retries = [0] + list(self.retries)

        while True:
            logging.debug('Querying %s with data %s and files %s (retries left: %s, current sleep: %s)...', url, data4log, files, len(retries), retries[0])

            time.sleep(retries.pop(0))

            try:
                self.curl.setopt(self.curl.URL, url)
                self.curl.setopt(self.curl.HTTPGET, 1)

                if data is not None or files is not None:
                    # If there is data or files to send, use a POST request

                    finalData = {}

                    if data is not None:
                        finalData.update(data)

                    if files is not None:
                        for (key, fileName) in files.items():
                            finalData[key] = (self.curl.FORM_FILE, fileName)

                    self.curl.setopt(self.curl.HTTPPOST, finalData.items())

                response = cStringIO.StringIO()
                self.curl.setopt(self.curl.WRITEFUNCTION, response.write)
                self.curl.perform()

                code = self.curl.getinfo(self.curl.RESPONSE_CODE)

                if code in self.retryCodes and len(retries) > 0:
                    logging.debug('Retrying since we got the %s error code...', code)
                    continue

                if code != 200:
                    raise HTTPError(code, response.getvalue())

                return response.getvalue()

            except pycurl.error as e:
                if len(retries) == 0:
                    raise e

                logging.debug('Retrying since we got the %s pycurl exception...', str(e))

