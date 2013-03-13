#!/usr/bin/env python2.6
'''Script to manage Apache workers.

To debug in case the URLs/parameters change:

  1) ssh to a frontend (the Apache configuration only allows to access to
     the balancer-manager from the machine's IP itself).

  2) Go to the main page for a given virtual host:
       wget -O - --header 'Host: cms-conddb-prod2.cern.ch' 'https://vocms151.cern.ch/balancer-manager' > ~/balancer-manager.html

  3) From there, one can go to the admin page for one of the balancers
     (get the nonce first from the main page):

       wget -O - --header 'Host: cms-conddb-prod2.cern.ch' 'https://vocms151.cern.ch/balancer-manager?b=admin&w=https://cmsdbbe2.cern.ch:8092/admin&nonce=645e0649-4556-41e1-a405-a3e5369b6e02' > ~/balancer-manager-admin.html

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


defaultVirtualHost = 'cms-conddb-prod'
# Use the current hostname since the server may not listen on 127.0.0.1
defaultBalancerManagerUrl = 'https://%s/balancer-manager' % socket.gethostname()


def _query(url, virtualHost = None):
    '''Queries a URL, optionally talking to a specific virtualHost.

    It must set both the SNI and Host header to the virtual host, otherwise
    Apache might complain.
    '''

    logging.debug('Querying: %s', url)

    if virtualHost is not None:
        url = urllib2.Request(url, headers = {
            'Host': virtualHost,
        })

    return urllib2.urlopen(url).read()


class BalancerManager(object):
    '''Class used for managing an Apache's balancer-manager.
    '''

    def __init__(self, url, virtualHost = None):
        self.url = url
        self.virtualHost = virtualHost

        self.refresh()


    def refresh(self):
        '''Parses the balancer-manager page to find out the available balancers,
        the workers of each balancer and its status.
        '''

        page = _query(self.url, self.virtualHost)

        # Find all balancers
        self.balancers = re.findall('<h3>LoadBalancer Status for balancer://(.*?)</h3', page)
        logging.debug('Balancers found: %s', self.balancers)

        # Find all workers for each balancer and their status
        self.workers = {}
        for balancer in self.balancers:
            self.workers[balancer] = {}
            for (url, nonce) in re.findall('<td><a href="/balancer-manager\?b=%s&w=(.*?)&nonce=(.*?)">' % balancer, page):
                self.workers[balancer][url] = {
                    'nonce': nonce,
                }

            logging.debug('[%s] Workers found: %s', balancer, sorted(self.workers[balancer]))

            for worker in self.workers[balancer]:
                matches = re.findall('<td><a href="/balancer-manager\?b=%s&w=%s&nonce=%s">%s</a></td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td></tr>' % (balancer, worker, self.workers[balancer][worker]['nonce'], worker), page)

                if len(matches) != 1:
                    raise Exception('Found more than one status line matching a worker: update the code.')

                # Strip all fields
                matches = [x.strip() for x in matches[0]]

                # Get the status as a boolean
                if 'Ok' in matches[4]:
                    statusBool = True
                elif 'Dis' in matches[4]:
                    statusBool = False
                else:
                    raise Exception('Unknown status of the worker.')

                self.workers[balancer][worker].update({
                    'route': matches[0],
                    'routeRedirection': matches[1],
                    'loadFactor': matches[2],
                    'loadSet': matches[3],
                    'status': matches[4],
                    'statusBool': statusBool,
                    'elected': matches[5],
                    'to': matches[6],
                    'from': matches[7],
                })


    def enableWorker(self, balancer, worker):
        '''Enables a worker.
        '''

        manageWorker(True, balancer, worker)


    def disableWorker(self, balancer, worker):
        '''Disables a worker.
        '''

        manageWorker(False, balancer, worker)


    def manageWorker(self, enable, balancer, worker):
        '''Enables or disables a worker.
        '''

        # Do *not* send the other parameters (lf, ls, wr, rr, status_I, ...)
        # because they would overwrite the current settings.
        _query('%s?%s' % (self.url, urllib.urlencode({
            'b': balancer,
            'w': worker,
            'nonce': self.workers[balancer][worker]['nonce'],
            'dw': 'Enable' if enable else 'Disable',
        })), self.virtualHost)


def printStatus(balancerManagerUrl, virtualHost):
    '''Prints the status of the balancer-manager in this host.
    '''

    balancerManager = BalancerManager(balancerManagerUrl, virtualHost)
    
    for balancer in balancerManager.balancers:
        print '[%s]' % balancer
        for worker in sorted(balancerManager.workers[balancer]):
            data = balancerManager.workers[balancer][worker]
            print '  %s : route = %s, enabled = %s (%s)' % (worker, data['route'], data['statusBool'], data['status'])


def manageBackend(enable, backend, balancerManagerUrl, virtualHost):
    '''Enables or disables all workers (i.e. services) in a backend.
    '''

    # Remove .cern.ch if provided
    if backend.endswith('.cern.ch'):
        backend = backend[:-len('.cern.ch')]

    logging.info('%s all workers for the %s backend in the %s virtual host...', 'Enabling' if enable else 'Disabling', backend, virtualHost)

    balancerManager = BalancerManager(balancerManagerUrl, virtualHost)

    for balancer in balancerManager.balancers:
        match = False

        for worker in balancerManager.workers[balancer]:
            if backend in worker:
                match = True

                # Warn if it was already in the requested state
                if balancerManager.workers[balancer][worker]['statusBool'] == enable:
                    logging.warn('The state of backend %s for balancer %s was already %s', backend, balancer, balancerManager.workers[balancer][worker]['statusBool'])

                balancerManager.manageWorker(enable, balancer, worker)

        if not match:
            logging.warn('No matching workers for the %s backend in balancer %s. Current ones: %s', backend, balancer, sorted(balancerManager.workers[balancer]))

    # Check afterwards (this prevents issues if Apache's version changes
    # which may change the parameters of the balancer-manager forms)
    balancerManager.refresh()

    for balancer in balancerManager.balancers:
        for worker in balancerManager.workers[balancer]:
            if backend in worker and balancerManager.workers[balancer][worker]['statusBool'] != enable:
                logging.warn('The state of backend %s for balancer %s is still %s. Check for misconfiguration or bugs in this script.', backend, balancer, balancerManager.workers[balancer][worker]['statusBool'])


def main():
    '''Entry point.
    '''

    parser = optparse.OptionParser(usage =
        'Usage: %prog status\n'
        '   or: %prog <command> <backend>\n'
        '\n'
        '  where commmand can be status, enable or disable.\n'
        '\n'
        '  e.g.: %prog status  cmsdbbe1 -v cms-conddb-prod2\n'
        '  e.g.: %prog disable cmsdbbe1 -v cms-conddb-prod2\n'
    )

    parser.add_option('-v', '--virtualHost',
        dest = 'virtualHost',
        default = defaultVirtualHost,
        help = 'Virtual host to manage. Use this option to test debugging virtualHosts (e.g. cms-conddb-prod2). Default: %default'
    )

    parser.add_option('-u', '--balancerManagerUrl',
        dest = 'balancerManagerUrl',
        default = defaultBalancerManagerUrl,
        help = 'URL pointing to the balancer-manager. Default: %default'
    )

    (options, arguments) = parser.parse_args()

    if len(arguments) == 1 and arguments[0] in ['status']:
        return printStatus(balancerManagerUrl = options.balancerManagerUrl, virtualHost = options.virtualHost)

    if len(arguments) == 2 and arguments[0] in ['enable', 'disable']:
        return manageBackend(arguments[0] == 'enable', arguments[1], balancerManagerUrl = options.balancerManagerUrl, virtualHost = options.virtualHost)

    parser.print_help()
    return -2


if __name__ == '__main__':
    logging.basicConfig(
        format = '[%(asctime)s] %(levelname)s: %(message)s',
        level = logging.INFO,
    )

    sys.exit(main())

