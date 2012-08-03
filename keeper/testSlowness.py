#!/usr/bin/env python2.6
'''Script that tests URLs for slowness and/or throttling.
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = ['Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


import sys
import time
import logging
import optparse
import urllib2


def timeRequests(url, numberOfRequests):
    '''Times how long it takes to request several times a URL.
    '''

    startTime = time.time()

    for i in range(numberOfRequests):
        urllib2.urlopen(url)

    endTime = time.time()

    return endTime - startTime


def testSlowness(url, numberOfRequests, expectedTimePerRequest, allowedRatio):
    '''Tests a URL for slowness.
    '''

    expectedTime = numberOfRequests * expectedTimePerRequest
    allowedTime = expectedTime * allowedRatio

    try:
        totalTime = timeRequests(url, numberOfRequests)
        averageTime = totalTime / numberOfRequests
        result = '%s Total: %.3f Average: %.3f' % (url, totalTime, averageTime)

        if totalTime > allowedTime:
            logging.warning(result)
        else:
            logging.info(result)

    except Exception as e:
        logging.error('%s Exception: %s', url, e)


def keepTestingSlowness(hostnames, path, protocols, numberOfRequests, expectedTimePerRequest, allowedRatio, delayBetweenSetOfTests, delayBetweenTests):
    '''Keeps testing for slowness all hostnames for all protocols.
    '''

    while True:
        for hostname in hostnames:
            for protocol in protocols:
                url = '%s://%s%s' % (protocol, hostname, path)
                testSlowness(url, numberOfRequests, expectedTimePerRequest, allowedRatio)
                time.sleep(delayBetweenTests)

        time.sleep(delayBetweenSetOfTests)


def main():
    '''Entry point.
    '''

    parser = optparse.OptionParser(usage =
        'Usage: %prog [options] <hostname(s)>\n'
        'Example: %prog -p /robots.txt -P http -n 4 -e 0.25 apache.org kernel.org python.org\n'
    )

    parser.add_option('-p', '--path', type = 'str',
        dest = 'path',
        default = '/docs/index.html',
        help = 'Path to test for. Default: %default',
    )

    parser.add_option('-P', '--protocols', type = 'str',
        dest = 'protocols',
        default = 'http,https',
        help = 'Protocols to test for (comma-separated). Default: %default',
    )

    parser.add_option('-n', '--numberOfRequests', type = 'int',
        dest = 'numberOfRequests',
        default = 40,
        help = 'Number of requests to perform for each test. Default: %default',
    )

    parser.add_option('-e', '--expectedTimePerRequest', type = 'float',
        dest = 'expectedTimePerRequest',
        default = 0.04,
        help = 'Expected (average) time per request. Default: %default',
    )

    parser.add_option('-r', '--allowedRatio', type = 'float',
        dest = 'allowedRatio',
        default = 2.0,
        help = 'Allowed ratio for a test to take. If a test takes longer than allowedRatio * numberOfRequests * expectedTimePerRequest, it will be reported as a warning. Default: %default',
    )

    parser.add_option('-d', '--delayBetweenSetOfTests', type = 'float',
        dest = 'delayBetweenSetOfTests',
        default = 10,
        help = 'Delay in seconds between each complete set of tests. Default: %default',
    )

    parser.add_option('-D', '--delayBetweenTests', type = 'float',
        dest = 'delayBetweenTests',
        default = 1,
        help = 'Delay in seconds between each test (i.e. between each bunch of requests). Useful to set a delay when testing several protocols/virtual hosts/DNS aliases/... of the same host. Default: %default',
    )

    (options, arguments) = parser.parse_args()

    if len(arguments) < 1:
        parser.print_help()
        return -2

    try:
        options.protocols = options.protocols.split(',')
        keepTestingSlowness(arguments, **vars(options))
    except KeyboardInterrupt:
        return 0
    except Exception as e:
        logging.error(e)

    return 0


if __name__ == '__main__':
    logging.basicConfig(
        format = '[%(asctime)s] %(levelname)s: %(message)s',
        level = logging.INFO,
    )

    sys.exit(main())

