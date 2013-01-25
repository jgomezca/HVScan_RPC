#!/usr/bin/env python2.6
'''Check script for dropBox for check_mk.

Example output:

0 dropBox - OK - There are not non-acknowledged errors in the latest hour.

or:

2 dropBox - CRITICAL - There are non-acknowledged errors in the latest hour.
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = ['Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


import socket
import urllib2
import json


if len(json.loads(urllib2.urlopen('https://%s/logs/dropBox/getStatus' % socket.gethostname()).read())) == 0:
    print '0 dropBox - OK - There are not non-acknowledged errors in the latest hour.'
else:
    print '2 dropBox - CRITICAL - There are non-acknowledged errors in the latest hour.'

