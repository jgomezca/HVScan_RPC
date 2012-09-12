#!/usr/bin/env python2.6
'''Script that (stress) tests the load balancer.

It simulates an external script that queries some URL. The script can be
aware or unaware of cookies.
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = ['Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


import sys
import time
import cookielib
import urllib2
import logging
import optparse


# Keeps track of errors during the testLoadBalancing()
errors = {}

# Used in command line options as well
defaultKeepCookies = False
defaultDelay = 1.0
defaultSendCounter = False


def testLoadBalancer(hostname, keepCookies = defaultKeepCookies, delay = defaultDelay, sendCounter = defaultSendCounter):
    '''Tests the load balancer in an infinite loop, keeping track
    of errors in the global variable so that they can be reported after
    a KeyboardInterrupt.

    Use keepCookies to test for cookie-based session-stickiness
    (i.e. same route).
    '''

    url = 'https://%s/docs/index.html' % hostname
    cookieJar = cookielib.CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookieJar))
    counter = 0

    while True:
        counter += 1

        # If we do not keep the cookies, create a new opener each time.
        # The cookie jar is used to get the route ID, even if we do not keep
        # the cookies between requests.
        if not keepCookies:
            cookieJar = cookielib.CookieJar()
            opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookieJar))

        try:
            finalUrl = url
            if sendCounter:
                finalUrl += '?%s' % counter

            response = opener.open(finalUrl)
            code = response.code

            # Try to get a sample line
            try:
                responseSampleLine = response.read().splitlines()[10].strip()[:36]
            except Exception:
                responseSampleLine = '???'

            # Try to get the route ID
            try:
                route = '?'
                for cookie in cookieJar:
                    if cookie.name == 'ROUTEID':
                        route = cookie.value.lstrip('.')
                        break
            except Exception:
                pass

            logging.info('%3s %s %s %s', counter, route, code, responseSampleLine)

        except urllib2.HTTPError as e:
            code = e.code
            errors.setdefault(code, 0)
            errors[code] += 1
            logging.info('HTTP Error: %s', code)

        except Exception:
            # We may get urllib2 or httplib exceptions
            errors.setdefault('connection', 0)
            errors['connection'] += 1
            logging.info('Connection Error')

        time.sleep(delay)


def main():
    '''Entry point.
    '''

    parser = optparse.OptionParser(usage =
        'Usage: %prog <hostname>\n'
        '  where hostname can be, for instance, cms-conddb-prod.\n'
    )

    parser.add_option('-c', '--keepCookies', action = 'store_true',
        dest = 'keepCookies',
        default = defaultKeepCookies,
        help = 'Keep cookies between requests (i.e. for testing load balacing with cookie-based stickiness). Default: %default'
    )

    parser.add_option('-d', '--delay', type = 'float',
        dest = 'delay',
        default = defaultDelay,
        help = 'Delay between requests. Change to a smaller value for stress testing. Default: %default'
    )

    parser.add_option('-s', '--sendCounter', action = 'store_true',
        dest = 'sendCounter',
        default = defaultSendCounter,
        help = 'Send the request counter as a request parameter (e.g. \'/url?7\', useful for distinguishing each request in the logs, preventing caching, etc.). Default: %default'
    )

    (options, arguments) = parser.parse_args()

    if len(arguments) != 1:
        parser.print_help()
        return -2

    try:
        testLoadBalancer(arguments[0], **vars(options))
    except KeyboardInterrupt:
        logging.info('Errors: %s', errors)

    return 0


if __name__ == '__main__':
    logging.basicConfig(
        format = '[%(asctime)s] %(levelname)s: %(message)s',
        level = logging.INFO,
    )

    sys.exit(main())

