#!/usr/bin/env python2.6
'''Script to manage Apache workers.

To debug in case the URLs/parameters change:

  1) ssh to a frontend (the Apache configuration only allows to access to
     the balancer-manage from the machine's IP itself).

  2) Go to the main page for a given virtual host:
       wget -O - --header 'Host: cms-conddb-prod2.cern.ch' https://vocms151.cern.ch/balancer-manager > ~/balancer-manager.html

  3) From there, one can go to the admin page for one of the balancers
     (get the nonce first from the main page):

       wget -O - --header 'Host: cms-conddb-prod2.cern.ch' https://vocms151.cern.ch/balancer-manager?b=admin&w=https://cmsdbbe2.cern.ch:8092/admin&nonce=645e0649-4546-41e1-a405-93e5369b6e02 > ~/balancer-manager-admin.html

  4) In the bottom, there is the form that needs to be read to know which
     parameters/value to use. e.g. last time it changed from "status_D" with
     values 0 and 1 to "dw" with values "Enable" and "Disable".

Looks like SLC6.3's version of curl/libcurl does not change SNI according to
the custom Host header, and therefore Apache answers with a 400 Bad Request.
In its error_log we can read:

  [Mon Jan 14 12:11:04 2013] [error] Hostname vocms151.cern.ch provided via SNI and hostname cms-conddb-prod2.cern.ch provided via HTTP are different.

wget and urllib2 work fine, though.
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = ['Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


import sys
import socket
import urllib
import urllib2
import logging
import optparse
import re

import config


# Open connection to the virtual host in localhost,
# using the current hostname (the server may not listen on 127.0.0.1)
balancerManagerUrl = 'https://%s/balancer-manager' % socket.gethostname()


def _openUrl(url, virtualHost = None):
    '''Opens a URL, optionally talking to a specific virtualHost.
    '''

    if virtualHost is not None:
        url = urllib2.Request(url, headers = {
            'Host': virtualHost,
        })

    return urllib2.urlopen(url)


def findNonce(balancerManagerUrl, virtualHost = None):
    '''Finds the nonce.
    '''

    page = _openUrl(balancerManagerUrl, virtualHost).read()

    match = re.search('&nonce=(.*?)"', page)
    if not match:
        raise Exception('The nonce was not found.')

    return match.groups()[0]


def manageWorker(balancerManagerUrl, balancer, workerUrl, nonce, enable, virtualHost = None):
    '''Enables or disables a worker.
    '''

    if enable:
        status = 'Enable'
    else:
        status = 'Disable'

    # Do *not* send the other parameters (lf, ls, wr, rr, status_I, status_H)
    # because they would overwrite the current settings.
    data = {
        'dw': status,
        'w': workerUrl,
        'b': balancer,
        'nonce': nonce,
    }

    url = '%s?%s' % (balancerManagerUrl, urllib.urlencode(data))
    _openUrl(url, virtualHost)


def getBalancer(service):
    '''Get the balancer name given a service name.
    '''

    return service.replace('/', '_').lower()


def getStatus(virtualHost):
    '''Gets the status of all the load balancers for the given virtual host.
    '''

    lines = _openUrl(balancerManagerUrl, virtualHost).read().splitlines()

    balancers = {}
    for line in lines:
        matches = re.findall('<h3>LoadBalancer Status for balancer://(.*?)</h3', line)
        if len(matches) != 1:
            continue
        balancers[matches[0]] = {}

    for balancer in balancers:
        for line in lines:
            matches = re.findall('<td><a href="/balancer-manager\?b=%s&w=(.*?)&' % balancer, line)
            if len(matches) != 1:
                continue
            workerUrl = matches[0]
            matches = re.findall('<td>(.*?)</td>', line)
            matches = [x.strip() for x in matches]
            status = matches[5]
            if 'Ok' in status:
                statusBool = True
            elif 'Dis' in status:
                statusBool = False
            else:
                raise Exception('Unknown status of the worker.')
            balancers[balancer][workerUrl] = {
                'route': matches[1],
                'routeRedirection': matches[2],
                'loadFactor': matches[3],
                'loadSet': matches[4],
                'status': matches[5],
                'statusBool': statusBool,
                'elected': matches[6],
                'to': matches[6],
                'from': matches[7],
            }

    return balancers


def manageBackend(backendHostname, enable, virtualHost):
    '''Enables or disables all workers (i.e. services) in a backend.
    '''

    if enable:
        action = 'Enabling'
    else:
        action = 'Disabling'

    # Remove .cern.ch if provided
    if backendHostname.endswith('.cern.ch'):
        backendHostname = backendHostname[:-len('.cern.ch')]

    logging.info('%s all workers for the %s virtual host in the %s backend...', action, virtualHost, backendHostname)

    nonce = findNonce(balancerManagerUrl, virtualHost)

    for service in config.servicesConfiguration:
        listeningPort = config.servicesConfiguration[service]['listeningPort']

        balancer = getBalancer(service)

        # FIXME: We could get the list of URLs from the main page directly
        protocol = 'https'
        if service == 'gtc':
            protocol = 'http'

        workerUrl = '%s://%s.cern.ch:%s/%s' % (protocol, backendHostname, listeningPort, service)

        manageWorker(balancerManagerUrl, balancer, workerUrl, nonce, enable, virtualHost = virtualHost)

    status = getStatus(virtualHost)
    for balancer in status:
        for backend in status[balancer]:
            if backendHostname in backend and status[balancer][backend]['statusBool'] != enable:
                logging.warn('The %s backend\'s state is still %s', backendHostname, status[balancer][backend]['statusBool'])


def main():
    '''Entry point.
    '''

    parser = optparse.OptionParser(usage =
        'Usage: %prog status\n'
        '   or: %prog <command> <backendHostname>\n'
        '  where commmand can be status, enable or disable.\n'
    )

    parser.add_option('-v', '--virtualHost',
        dest = 'virtualHost',
        default = 'cms-conddb-prod',
        help = 'Virtual host to manage. Use this option to test debugging virtualHosts (e.g. cms-conddb-prod2). Default: %default'
    )

    (options, arguments) = parser.parse_args()

    if len(arguments) == 1 and arguments[0] in ['status']:
        balancers = getStatus(**vars(options))
        for balancer in balancers:
            print '[%s]' % balancer
            for workerUrl in sorted(balancers[balancer]):
                worker = balancers[balancer][workerUrl]
                print '    %s %s %s (%s)' % (workerUrl, worker['route'], worker['statusBool'], worker['status'])
        return
    elif len(arguments) == 2 and arguments[0] in ['enable', 'disable']:
        return manageBackend(arguments[1], arguments[0] == 'enable', **vars(options))

    parser.print_help()
    return -2


if __name__ == '__main__':
    logging.basicConfig(
        format = '[%(asctime)s] %(levelname)s: %(message)s',
        level = logging.INFO,
    )

    sys.exit(main())

