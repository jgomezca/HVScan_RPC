'''Offline new dropBox's configuration.
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = ['Giacomo Govi', 'Salvatore Di Guida', 'Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


import os

import jinja2

import service


group = 'cms-cond-dropbox'

shifterPhoneSMSAddress = '0041764875576@mail2sms.cern.ch'

tier0URL = 'https://samir-wmcore.cern.ch/t0wmadatasvc/replay'


# Messages
notifiedErrorMessage = 'This has been notified and we will try to fix it. However, if you urgently need assistance, please write an email to cms-offlinedb-exp@cern.ch and cms-cond-dev@cern.ch. If you need immediate assistance, you can call the Offline DB expert on call (+41 22 76 70817, or 70817 from CERN; check https://twiki.cern.ch/twiki/bin/viewauth/CMS/DBShifterHelpPage if it does not work).'

fcsrProblemMessage = 'Please contact the Tier-0 experts. If we are in data taking, please *also* contact the Offline DB experts as well at cms-offlinedb-exp@cern.ch (if you need immediate assistance, you can call the Offline DB expert on call: +41 22 76 70817, or 70817 from CERN; check https://twiki.cern.ch/twiki/bin/viewauth/CMS/DBShifterHelpPage if it does not work).'


# Notifications
notificationsEgroup = 'cms-cond-dropbox-notifications@cern.ch'


# Email template
subjectLine = '{{statusCode}} - {{fileName}} - {{statusString}}'
smsTemplate = jinja2.Template(subjectLine)
subjectTemplate = jinja2.Template('[DropBox] %s' % subjectLine)
bodyTemplate = jinja2.Template('''[DropBox] %s

         fileName: {{fileName}}
         fileHash: {{fileHash}}

           status: {{statusCode}} ({{statusString}})

  uploadTimestamp: {{uploadTimestamp}}
  finishTimestamp: {{finishTimestamp}}

         username: {{username}}

         userText: {{userText}}

         metadata:

{{metadata}}

              log:

{{log}}
''' % subjectLine)


# For integration and production, we use the production dropBox database
if service.settings['productionLevel'] in set(['int', 'pro']):
    connectionDictionary = service.secrets['connections']['pro']

# For development, we use the prep dropBox database
elif service.settings['productionLevel'] in set(['dev']):
    connectionDictionary = service.secrets['connections']['dev']

# In private instances, we take it from netrc
elif service.settings['productionLevel'] in set(['private']):
    connectionDictionary = service.getConnectionDictionaryFromNetrc('dropBoxDatabase')

else:
    raise Exception('Unknown production level.')


# Allowed backends per production level
allowedBackends = {
    'private': set(['private']),
    'dev': set(['dev']),
    'int': set(['offline', 'online', 'tier0']),
    'pro': set(['offline', 'online', 'tier0']),
}


# Allowed services (i.e. databases) per backend
#
# None means 'same as the dropBox connectionString above', i.e. the user's
# destinationDatabase is ignored, and everything goes into the same database
# as the one used for storing the dropBox-related information (i.e. files,
# fileLog and runLog).
allowedServices = {
    'private': None,
    'dev': None,
    'offline': set(['int', 'prep']),
    'online': set(['int', 'prep', 'prod']),
    'tier0': set(['int', 'prep', 'prod']),
}


#TODO: -sdg Retrieve HLT GT from online DQM: see AlCaDB main Twiki for links.
# Default dictionary for production Global Tags
productionGlobalTags = {
    'hlt': 'GR_H_V32',
    'express': 'GR_E_V33',
    'prompt': 'GR_P_V43D',
}

# Base path for test files
testFilesPath = 'testFiles'

# Files for security testing, crafted by createSecurityTestFiles.py, treated
# specially by test.py and used by copyOnlineTestFiles()
securityTestFilesPath = os.path.join(testFilesPath, 'security')

