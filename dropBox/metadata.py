#!/usr/bin/env python2.6
'''Script that ports old dropBox metadata to the new JSON format.
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = ['Giacomo Govi', 'Salvatore Di Guida', 'Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


import json

import service
import globalTagHandler


def port(metadata):
    '''Ports metadata into the new format.
    '''

    # Defaults
    outputMetadata = {
        'userText': '',
    }

    allowDependencies = False

    for line in metadata.splitlines():
        line = line.strip()

        # Ignore empty lines
        if line == '':
            continue

        # Ignore comment lines
        if line.startswith('#'):
            continue

        (key, x, value) = line.partition(' ')

        key = key.lower()
        value = value.strip()

        if key == 'destdb':
            outputMetadata['destinationDatabase'] = value

        elif key == 'tag':
            outputMetadata['destinationTags'] = {
                value: {}
            }

        elif key == 'inputtag':
            if value == '':
                value = outputMetadata['destinationTags'].keys()[0]

            outputMetadata['inputTag'] = value

        elif key == 'since':
            if value != '':
                outputMetadata['since'] = int(value)
            else:
                outputMetadata['since'] = None

        elif key == 'iovcheck':
            # from dropBox/config.py
            productionGTsDict = {
                'hlt': 'GR_H_V29',
                'express': 'GR_E_V31',
                'prompt': 'GR_P_V42'
            }

            # from dropBox/checkTodo.py
            globalTagConnectionString = service.getFrontierConnectionString( service.secrets[ 'connections' ][ 'dev' ][ 'global_tag' ] )
            runControlConnectionString = service.getCxOracleConnectionString( service.secrets[ 'connections' ][ 'dev' ][ 'run_control' ] )
            runInfoConnectionString = service.getFrontierConnectionString( service.secrets[ 'connections' ][ 'dev' ][ 'run_info' ] )
            runInfoStartTag = "runinfo_start_31X_hlt"
            runInfoStopTag = "runinfo_31X_hlt"
            authPath = ""
            tier0DataSvcURI = "https://cmsweb.cern.ch/tier0"
            timeOut = 30
            retries = 3
            retryPeriod = 90
            gtHandle = globalTagHandler.GlobalTagHandler( globalTagConnectionString, runControlConnectionString, runInfoConnectionString, runInfoStartTag, runInfoStopTag, authPath, tier0DataSvcURI, timeOut, retries, retryPeriod )

            workflow = gtHandle.getWorkflowForTagAndDB( outputMetadata['destinationDatabase'], outputMetadata['destinationTags'].keys()[0], productionGTsDict )

            replaceValue = True
            if workflow is None:
                replaceValue = False #connection string and tag are not in any production Global Tags
            elif value == workflow:
                replaceValue = False #connection string and tag are in the production Global Tag for the same workflow specified
            elif value == 'pcl' and workflow == 'prompt':
                replaceValue = False #pcl is a particular case for prompt

            # If IOVCheck was 'All', and the tag is in a global tag
            # (e.g. workflow is not None, replaceValue == True),
            # we replace it with something else (e.g. 'hlt') and therefore
            # there will not allow dependencies since this is what the user
            # should have used in the first place.
            #
            # If IOVCheck was 'All', and the tag is not in a global tag
            # (e.g. workflow is None, replaceValue == False),
            # we do not replace it, so it means it was offline + allow
            # dependencies, which we will reach since value still is 'All'.
            if replaceValue:
                value = workflow

            if value == 'All':
                allowDependencies = True
                value = 'offline'

            outputMetadata['destinationTags'][outputMetadata['destinationTags'].keys()[0]] = {
                'synchronizeTo': value,
                'dependencies': {},
            }

        elif key in ['duplicatetaghlt', 'duplicatetagexpress', 'duplicatetagprompt', 'duplicatetagpcl']:
            if allowDependencies and value != '':
                outputMetadata['destinationTags'][outputMetadata['destinationTags'].keys()[0]]['dependencies'][value] = key.partition('duplicatetag')[2]

        elif key == 'usertext':
            outputMetadata['userText'] = value

        # Deprecated stuff
        elif key == 'timetype':
            continue

        # Tier0 stuff that we do not need
        elif key == 'source':
            continue

        elif key == 'fileclass':
            continue

        # Wrong stuff
        elif key == 'es':
            # Bad userText in ESRecHitRatioCuts_V03_offline@a57546b2-03d2-11e2-84ae-003048d2bf28.tar.bz2
            outputMetadata['userText'] = '%s %s' % (key, value)

        elif key == 'gains':
            # Bad userText in SiPixelGainCalibrationHLT_2009runs_hlt@429bd0b6-0b6a-11e2-893f-003048f0e2c4.tar.bz2
            outputMetadata['userText'] = '%s %s' % (key, value)

        elif key == 'pixel':
            # Bad userText in SiPixelQuality_v11_bugfix_mc@97ccde9c-1784-11e2-b160-001e4f3da51f.tar.bz2
            outputMetadata['userText'] = '%s %s' % (key, value)

        elif key == 'es-ee':
            # Bad userText in ESEEIntercalibConstants_LG_V03_mc@a7238182-1ad8-11e2-85cc-001e4f3da513.tar.bz2
            outputMetadata['userText'] = '%s %s' % (key, value)

        elif key == 'lorentz':
            # Bad userText in SiPixelLorentzAngle_r194912_v1@4c10ccb4-1ee8-11e2-be80-003048d2bc9a.tar.bz2
            outputMetadata['userText'] = '%s %s' % (key, value)

        elif key == 'produced':
            # Bad userText in SiPixelTemplateDBObject_38T_2012_for_alignment_v1_offline@db41edfc-1fae-11e2-9aab-003048d2bf8c.tar.bz2
            # Bad userText in SiPixelTemplateDBObject_38T_IOV1_r194912@efb22762-1fa3-11e2-9fdd-003048d2bf8c.tar.bz2
            outputMetadata['userText'] = '%s %s' % (key, value)

        elif key == 'fed':
            # Bad userText in SiPixelQuality_v19@3beb7522-247a-11e2-a986-001e4f3e5c33.tar.bz2
            outputMetadata['userText'] = '%s %s' % (key, value)

        elif key == 'bugfix':
            # Bad userText in SiPixelQuality_v04_offline@eff63846-247e-11e2-969c-001e4f3e5c33.tar.bz2
            outputMetadata['userText'] = '%s %s' % (key, value)

        else:
            raise Exception('Invalid key: %s', key)

    return json.dumps(outputMetadata, sort_keys = True, indent = 4)

