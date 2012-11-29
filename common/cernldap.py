'''Common code for searching in the CERN LDAP server.
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = ['Giacomo Govi', 'Salvatore Di Guida', 'Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


import logging
import ldap


# TODO: It seems the LDAP connection times out, re-connect automatically if so.

class CERNLDAPError(Exception):
    '''A common CERNLDAP exception.
    '''


class CERNLDAP(object):
    '''Class used for searching in the CERN LDAP server.
    '''

    def __init__(self, server = 'ldap://xldap.cern.ch'):
        self.server = server
        self.ldap = ldap.initialize(self.server)


    def __str__(self):
        return 'CERNLDAP %s' % self.server


    def getUserInfo(self, username, attributes = None, timeout = None):
        if timeout is None:
            timeout = -1

        result = self.ldap.search_st('ou=users,ou=organic units,dc=cern,dc=ch', ldap.SCOPE_SUBTREE, '(cn=%s)' % username, attributes, timeout = timeout)
        if len(result) == 0:
            raise CERNLDAPError('%s: Username "%s" not found.' % (self, username))

        return result[0][1]

    def getUserEmail(self, username, timeout = None):
        return self.getUserInfo(username, ['mail'], timeout)['mail'][0]

