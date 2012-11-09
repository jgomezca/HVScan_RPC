'''Offline new dropBox's configuration.
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = ['Giacomo Govi', 'Salvatore Di Guida', 'Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


import os


group = 'cms-cond-dropbox'

allowedBackends = {
    'private': set(['private']),
    'dev': set(['offline', 'tier0Test']),
    'int': set(['online', 'tier0Online', 'offline', 'tier0Offline', 'tier0Test']),
    'pro': set(['online', 'tier0Online', 'offline', 'tier0Offline', 'tier0Test']),
}

# Default dictionary for production Global Tags
productionGlobalTags = {
    'hlt': 'GR_H_V29',
    'express': 'GR_E_V31',
    'prompt': 'GR_P_V42',
}

# Base path for test files
testFilesPath = 'testFiles'

# Files for security testing, crafted by createSecurityTestFiles.py, treated
# specially by test.py and used by copyOnlineTestFiles()
securityTestFilesPath = os.path.join(testFilesPath, 'security')

