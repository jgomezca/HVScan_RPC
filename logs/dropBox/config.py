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

