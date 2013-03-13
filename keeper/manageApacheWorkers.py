#!/usr/bin/env python2.6
'''Script to manage Apache workers.

This script should *not* be used in deployments manually. The deploy script
takes care of all the details about the procedure/policies and uses this script
to accomplish that.

However, if there is a need to do reboots of backends in production machines,
then there is a need to manually intervene using this script, in sync
with the sysadmin. In this case, go one by one:

  0) If debugging is needed, you may run in parallel:

       $ testLoadBalancer.py -s cms-conddb-prod

     Also, you can see the present status of the load balancer with:

       cmsdbfe1 $ manageApacheWorkers.py status -v cms-conddb-prod

     and:

       cmsdbfe2 $ manageApacheWorkers.py status -v cms-conddb-prod


  1) In *all* frontends, take out the first backend, i.e.

       cmsdbfe1 $ manageApacheWorkers.py takeout cmsdbbe1 -v cms-conddb-prod

     and:

       cmsdbfe2 $ manageApacheWorkers.py takeout cmsdbbe1 -v cms-conddb-prod


  2) Wait a while (currently, 15 minutes -- the time should be enough
     to let all sessions expire -- even then sessions are not used for that
     long currently; and only one service uses them: dropBox). Also
     you may check as above with testLoadBalancer.py that the backend
     is already out (for non-session) requests.


  3) In *all* frontends, disable the backend, i.e.:

       cmsdbfe1 $ manageApacheWorkers.py disable cmsdbbe1 -v cms-conddb-prod

     and:

       cmsdbfe2 $ manageApacheWorkers.py disable cmsdbbe1 -v cms-conddb-prod


  4) Request the sysadmin (currently, Jorge) to reboot the machine.


  5) Wait until the reboot is completed (should take few minutes, unless
     fsck runs) and verify everything is running normally after the updates.


  6) In *all* frontends, reenable the backend and take it in, i.e.:

       cmsdbfe1 $ manageApacheWorkers.py enable cmsdbbe1 -v cms-conddb-prod
       cmsdbfe1 $ manageApacheWorkers.py takein cmsdbbe1 -v cms-conddb-prod

     and:

       cmsdbfe2 $ manageApacheWorkers.py enable cmsdbbe1 -v cms-conddb-prod
       cmsdbfe2 $ manageApacheWorkers.py takein cmsdbbe1 -v cms-conddb-prod


  7) Check with testLoadBalancer.py that the backend is again
     in the load balancer cluster.


  8) Now repeat the full procedure with the second backend (i.e. cmsdbbe2).


To debug this script in case the URLs/parameters change:

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
defaultHostname = socket.gethostname()
defaultBalancerManagerUrl = 'https://%s/balancer-manager'


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

    lbsets = {
        'in': '0',
        'out': '1',
    }

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
                    'lbset': matches[3],
                    'status': matches[4],
                    'statusBool': statusBool,
                    'elected': matches[5],
                    'to': matches[6],
                    'from': matches[7],
                })


    def manageWorker(self, balancer, worker, parameters):
        '''Manages a worker.
        '''

        parameters.update({
            'b': balancer,
            'w': worker,
            'nonce': self.workers[balancer][worker]['nonce'],
        })

        # Do *not* send the other parameters (lf, ls, wr, rr, status_I, ...)
        # because they would overwrite the current settings.
        _query('%s?%s' % (self.url, urllib.urlencode(parameters)), self.virtualHost)


    def enableWorker(self, balancer, worker):
        '''Enables a worker.
        '''

        self.manageWorker(balancer, worker, {
            'dw': 'Enable',
        })


    def disableWorker(self, balancer, worker):
        '''Disables a worker.

        Ongoing requests will be still be handled by this worker but
        *all* new requests will move to some other worker. Therefore,
        this *breaks* sessions relying on session stickiness for this worker.
        Use takeOutWorker() first to prevent this and wait a reasonable time
        for sessions to timeout before calling disableWorker().
        '''

        self.manageWorker(balancer, worker, {
            'dw': 'Disable',
        })


    def moveWorker(self, balancer, worker, lbset):
        '''Moves a worker to another set.
        '''

        self.manageWorker(balancer, worker, {
            'ls': lbset,
        })


    def takeInWorker(self, balancer, worker):
        '''Takes in a worker.

        We use the default lbset 0 to give highest priority.
        '''

        self.moveWorker(balancer, worker, self.lbsets['in'])


    def takeOutWorker(self, balancer, worker):
        '''Takes out a worker.

        Ongoing requests and requests with a ROUTEID cookie pointing to
        this worker will still be handled by it, but no other requests will
        come to it. See disableWorker().

        We use the lbset 1 to give a lower priority for new requests,
        since lower numbered sets have higher priority.
        '''

        self.moveWorker(balancer, worker, self.lbsets['out'])


def printStatus(balancerManagerUrl, virtualHost):
    '''Prints the status of the balancer-manager in this host.
    '''

    balancerManager = BalancerManager(balancerManagerUrl, virtualHost)
    
    for balancer in balancerManager.balancers:
        print '[%s]' % balancer
        for worker in sorted(balancerManager.workers[balancer]):
            data = balancerManager.workers[balancer][worker]
            print '  %s : route = %s, enabled = %s (%s), lbset = %s' % (worker, data['route'], data['statusBool'], data['status'], data['lbset'])


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

                if enable:
                    balancerManager.enableWorker(balancer, worker)
                else:
                    balancerManager.disableWorker(balancer, worker)

        if not match:
            logging.warn('No matching workers for the %s backend in balancer %s. Current ones: %s', backend, balancer, sorted(balancerManager.workers[balancer]))

    # Check afterwards (this prevents issues if Apache's version changes
    # which may change the parameters of the balancer-manager forms)
    balancerManager.refresh()

    for balancer in balancerManager.balancers:
        for worker in balancerManager.workers[balancer]:
            if backend in worker and balancerManager.workers[balancer][worker]['statusBool'] != enable:
                logging.warn('The state of backend %s for balancer %s is still %s. Check for misconfiguration or bugs in this script.', backend, balancer, balancerManager.workers[balancer][worker]['statusBool'])


def moveBackend(takeIn, backend, balancerManagerUrl, virtualHost):
    '''Enables or disables all workers (i.e. services) in a backend.
    '''

    # Remove .cern.ch if provided
    if backend.endswith('.cern.ch'):
        backend = backend[:-len('.cern.ch')]

    logging.info('%s all workers for the %s backend in the %s virtual host...', 'Taking in' if takeIn else 'Taking out', backend, virtualHost)

    balancerManager = BalancerManager(balancerManagerUrl, virtualHost)

    for balancer in balancerManager.balancers:
        match = False

        for worker in balancerManager.workers[balancer]:
            if backend in worker:
                match = True

                # Warn if it was already in the requested state
                if balancerManager.workers[balancer][worker]['lbset'] == balancerManager.lbsets['in' if takeIn else 'out']:
                    logging.warn('The lbset of backend %s for balancer %s was already %s', backend, balancer, balancerManager.workers[balancer][worker]['lbset'])

                if takeIn:
                    balancerManager.takeInWorker(balancer, worker)
                else:
                    balancerManager.takeOutWorker(balancer, worker)

        if not match:
            logging.warn('No matching workers for the %s backend in balancer %s. Current ones: %s', backend, balancer, sorted(balancerManager.workers[balancer]))

    # Check afterwards (this prevents issues if Apache's version changes
    # which may change the parameters of the balancer-manager forms)
    balancerManager.refresh()

    for balancer in balancerManager.balancers:
        for worker in balancerManager.workers[balancer]:
            if backend in worker and balancerManager.workers[balancer][worker]['lbset'] != balancerManager.lbsets['in' if takeIn else 'out']:
                logging.warn('The lbset of backend %s for balancer %s is still %s. Check for misconfiguration or bugs in this script.', backend, balancer, balancerManager.workers[balancer][worker]['lbset'])


def main():
    '''Entry point.
    '''

    parser = optparse.OptionParser(usage =
        'Usage: %prog status\n'
        '   or: %prog <command> <backend/worker>\n'
        '\n'
        '  where commmand can be status, enable, disable, takein or takeout.\n'
        '\n'
        '  If you need to use this script in production, please read\n'
        '  its full documentation.\n'
        '\n'
        '  The action will be applied to the backend/worker in *all* proxies.\n'
        '\n'
        '  e.g.: %prog status           -v cms-conddb-prod2\n'
        '  e.g.: %prog disable cmsdbbe1 -v cms-conddb-prod2\n'
        '  e.g.: %prog takein  cmsdbbe1 -v cms-conddb-prod2\n'
    )

    parser.add_option('-H', '--hostname',
        dest = 'hostname',
        default = defaultHostname,
        help = 'Hostname to manage (where the balancer-manager is). Default: %default'
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

    balancerManagerUrl = options.balancerManagerUrl % options.hostname

    if len(arguments) == 1 and arguments[0] in ['status']:
        return printStatus(balancerManagerUrl = balancerManagerUrl, virtualHost = options.virtualHost)

    if len(arguments) == 2 and arguments[0] in ['enable', 'disable']:
        return manageBackend(arguments[0] == 'enable', arguments[1], balancerManagerUrl = balancerManagerUrl, virtualHost = options.virtualHost)

    if len(arguments) == 2 and arguments[0] in ['takein', 'takeout']:
        return moveBackend(arguments[0] == 'takein', arguments[1], balancerManagerUrl = balancerManagerUrl, virtualHost = options.virtualHost)

    parser.print_help()
    return -2


if __name__ == '__main__':
    logging.basicConfig(
        format = '[%(asctime)s] %(levelname)s: %(message)s',
        level = logging.INFO,
    )

    sys.exit(main())

