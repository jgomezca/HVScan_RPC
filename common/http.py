'''Common code for querying HTTP(S) URLs for all CMS DB Web services.
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = ['Giacomo Govi', 'Salvatore Di Guida', 'Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


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

    def __init__(self):
        self.reset()


    def reset(self):
        '''Resets the state of the object.

        Usually used to discard cookies.
        '''

        self.curl = pycurl.Curl()
        self.curl.setopt(self.curl.COOKIEFILE, '')
        self.curl.setopt(self.curl.SSL_VERIFYPEER, 0)
        self.curl.setopt(self.curl.SSL_VERIFYHOST, 0)


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
            self.reset()

        response = cStringIO.StringIO()

        # make sure the logs are safe ... at least somewhat :)
        data4log = copy.copy(data)
        if data4log:
            if 'password' in data4log.keys():
                data4log['password'] = '*'
        logging.debug('Querying %s with data %s and files %s...', url, data4log, files)

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

        self.curl.setopt(self.curl.WRITEFUNCTION, response.write)
        self.curl.perform()

        code = self.curl.getinfo(self.curl.RESPONSE_CODE)

        if code != 200:
            raise HTTPError(code, response.getvalue())

        return response.getvalue()

