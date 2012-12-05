'''Common code for getting information from the Shibboleth headers.
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = ['Giacomo Govi', 'Salvatore Di Guida', 'Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


import cherrypy

import service


if service.settings['productionLevel'] == 'private':
    import getpass
    import cernldap
    userInfo = cernldap.CERNLDAP().getUserInfo(getpass.getuser())
    privateDefaults = {
        'Adfs-Personid': userInfo['employeeID'][0],
        'Adfs-Login': getpass.getuser(),
        'Adfs-Email': userInfo['mail'][0],
        'Adfs-Fullname': userInfo['displayName'][0],
        # FIXME: Looks like LDAP does not return all the groups.
        'Adfs-Group': ';'.join([x.split('CN=')[1].split(',')[0] for x in userInfo['memberOf']]),
    }

def getID():
    if service.settings['productionLevel'] == 'private':
        return privateDefaults['Adfs-Personid']

    return cherrypy.request.headers['Adfs-Personid']

def getUsername():
    if service.settings['productionLevel'] == 'private':
        return privateDefaults['Adfs-Login']

    return cherrypy.request.headers['Adfs-Login']

def getEmail():
    if service.settings['productionLevel'] == 'private':
        return privateDefaults['Adfs-Email']

    return cherrypy.request.headers['Adfs-Email']

def getFullName():
    if service.settings['productionLevel'] == 'private':
        return privateDefaults['Adfs-Fullname']

    return cherrypy.request.headers['Adfs-Fullname']

def getGroups():
    if service.settings['productionLevel'] == 'private':
        return set(privateDefaults['Adfs-Group'].split(';'))

    return set(cherrypy.request.headers['Adfs-Group'].split(';'))

