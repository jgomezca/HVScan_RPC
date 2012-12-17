'''Logs service configuration.
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = ['Giacomo Govi', 'Salvatore Di Guida', 'Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


import service


if service.settings['productionLevel'] in set(['int', 'pro']):
    connections = {
        # For integration and production, we use the (reader) production dropBox database
        'dropBox': service.secrets['dropBoxConnections']['pro'],
    }

elif service.settings['productionLevel'] in set(['dev']):
    connections = {
        # For development, we use the prep dropBox database
        'dropBox': service.secrets['dropBoxConnections']['dev'],
    }


elif service.settings['productionLevel'] in set(['private']):
    connections = {
        # In private instances, we take connections from netrc
        'dropBox': service.getConnectionDictionaryFromNetrc('dropBoxDatabase'),
    }

else:
    raise Exception('Unknown production level.')


def getBackendOldThreshold(backend):

    backendsOldThreshold = {
        # Online and offline backends run every 30 seconds, so 60 seconds should note a problem
        'online': 60,
        'offline': 60,

        # Tier0 backend runs at 10-min boundaries, so 20 minutes should note a problem
        'tier0': 20 * 60,

        # Private instances run every 10 seconds, so 20 seconds should note a problem
        'private': 20,
    }

    if backend in backendsOldThreshold:
        return backendsOldThreshold[backend]

    return backendsOldThreshold['private']

