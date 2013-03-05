'''CMS DB Web easymon server.
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2013, CERN CMS'
__credits__ = ['Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


import cherrypy
import jinja2

import html
import http
import json
import service


localAgentHost = 'vocms226'
serviceUrlTemplate = '/monitoring/check_mk/view.py?view_name=service&site=&service=%s&host=%s' % ('%s', localAgentHost)
dataUrl = '%s/view.py?view_name=host&site=&host=%s&st0=on&st1=on&st2=on&st3=on&stp=on&output_format=json' % (service.secrets['url'], localAgentHost)


# Easymon's tree is a nested ordered dictionary.
#
# Items of a list are tuples (name, weight, info), where info be either
# another list (subpage with more items) or a string (Check_MK's check name).
#
# Weitghts can be used in parents to give an idea of the importance of an item
# e.g. a parent's healthy value may be a weighted sum of the leafs. In our case,
# we currently use them to make the status boxes in the parent.
#
# Weights should add up to 100. This allows for weights that may be None:
# the rest of the weight up to 100 not yet used is assigned to the None weights.
# proportionally. Normally used to assign equal weights to all the entries.
#
# Critical errors in leafs propagate up.
tree = (
    ('DropBox', None, (
        ('srv-C2C05-11 (tier0) Load', None, 'DropBoxBE_Tier0_srv-C2C05-11_status'),
        ('srv-C2C05-15 (online) Load', None, 'DropBoxBE_Online_srv-C2C05-15_status'),
    )),

    ('Frontier', None, (
        ('Online', None, (
            ('srv-C2C03-19 Load', None, 'OnlineFrontier_srv-C2C03-19_status'),
            ('srv-C2C05-19 Load', None, 'OnlineFrontier_srv-C2C05-19_status'),
        )),
        ('Offline', None, (
            ('Global SLS Availability', None, 'OfflineFrontier_Global_availability'),
            ('Launchpad SLS Availability', None, 'OfflineFrontier_Launchpad_availability'),
            ('Tier0 SLS Availability', None, 'OfflineFrontier_Tier0_availability'),
        )),
    )),

    ('DB', None, (
        ('Online', None, (
            ('CMSONR SLS Availability', 40, 'OnlineDB_CMSONR_availability'),
            ('CMSONR1 CPU Load', None, 'OnlineDB_CMSONR1_cpuLoad'),
            ('CMSONR2 CPU Load', None, 'OnlineDB_CMSONR2_cpuLoad'),
            ('CMSONR3 CPU Load', None, 'OnlineDB_CMSONR3_cpuLoad'),
            ('CMSONR4 CPU Load', None, 'OnlineDB_CMSONR4_cpuLoad'),
            ('CMSONRADG1 CPU Load', None, 'OnlineDB_CMSONRADG1_cpuLoad'),
            ('CMSONRADG2 CPU Load', None, 'OnlineDB_CMSONRADG2_cpuLoad'),
        )),
        ('Offline', None, (
            ('CMSR SLS Availability', 40, 'OfflineDB_CMSR_availability'),
            ('CMSR1 CPU Load', None, 'OfflineDB_CMSR1_cpuLoad'),
            ('CMSR2 CPU Load', None, 'OfflineDB_CMSR2_cpuLoad'),
            ('CMSR3 CPU Load', None, 'OfflineDB_CMSR3_cpuLoad'),
        )),
    )),

    ('O2O', None, (
        ('Run Based Jobs', None, (
            ('Run Info Start', None, 'PopCon_RunInfoStart'),
            ('Run Info Stop', None, 'PopCon_RunInfoStop'),
            ('Ecal DAQ', None, 'PopCon_EcalDAQO2O'),
            ('Ecal DCS', None, 'PopCon_EcalDCSO2O'),
        )),
        ('Time Based Jobs', None, (
            ('Ecal Laser', None, 'PopCon_EcalLaserTimeBasedO2O'),
            ('Ecal Laser Express', None, 'PopCon_EcalLaserExpressTimeBasedO2O'),
            ('Ecal Pedestals', None, 'PopCon_EcalPedestalsTimeBasedO2O'),
            ('SiStripDetVOff', None, 'PopCon_SiStripDetVOffTimeBasedO2O'),
        )),
        ('ECAL Laser Online', None, (
            ('Correction Delay', None, 'ECAL_CorrectionDelay'),
            ('emtc_logger', None, 'ECAL_emtc_logger'),
            ('setup_logger', None, 'ECAL_setup_logger'),
            ('corr_writing', None, 'ECAL_corr_writing'),
            ('db_writing', None, 'ECAL_db_writing'),
            ('matacq_xfer', None, 'ECAL_matacq_xfer'),
            ('prim_gen', None, 'ECAL_prim_gen'),
            ('monitoring', None, 'ECAL_monitoring'),
            ('sorting', None, 'ECAL_sorting'),
            ('matacq_feedback', None, 'ECAL_matacq_feedback'),
            ('clean_stream', None, 'ECAL_clean_stream'),
        )),
    )),
)


def getCheckMKStatus():
    '''Returns the status of CheckMK as a dictionary. The keys are
    the check (service) names, i.e. those used in the global tree; and
    the values are tuples (status, message, state age, check age). e.g.

        output = {
            'OfflineDB_CMSR1_cpuLoad': (
                'OK',
                'OK - ioWait: 0.19 (OK), idle: 91.4 (OK), user: 7.53 (OK), system: 0.49 (OK),',
                '2013-03-01 15:05:48',
                '17 sec'
            ),

            'OfflineDB_CMSR2_cpuLoad': ...

            ...
        }

    Note:
      * Status is in ['OK', 'CRIT', 'WARN', 'UNKNOWN']. UNKNOWN is used
        for any case that is not OK, CRIT or WARN (this would include
        the PENDING and UNAVAILABLE Check_MK states).
      * The state age shows how long the service's state did not change.
      * The check age shows the last time the service was checked.

    Could be cached for some seconds if the load proves too high for Check_MK.
    '''

    h = http.HTTP()
    h.setTimeout(5)
    h.setRetries([1])
    h.setUsernamePassword(service.secrets['username'], service.secrets['password'])
    data = h.query(dataUrl)

    # Bug in Check_MK: does not return valid JSON strings in the first
    # list/line (the header): single quotes must be converted to double ones
    lines = data.splitlines()
    lines[1] = lines[1].replace("'", '"')
    data = json.loads('\n'.join(lines))

    headers = data[0]
    nameIndex = headers.index('service_description')
    statusIndex = headers.index('service_state')
    statusMessageIndex = headers.index('svc_plugin_output')
    stateAgeIndex = headers.index('svc_state_age')
    checkAgeIndex = headers.index('svc_check_age')

    output = {}

    for row in data[1:]:
        status = row[statusIndex]
        if status not in ['OK', 'CRIT', 'WARN']:
            status = 'UNKNOWN'
        output[row[nameIndex]] = (
            status,
            row[statusMessageIndex],
            row[stateAgeIndex],
            row[checkAgeIndex],
        )

    return output


# Precompile the template
with open('index.tmpl', 'rb') as f:
    treeTemplate = jinja2.Template(f.read())


def getStatus(checkMKStatus, title, item):
    '''Returns the status in ['OK', 'CRIT', 'WARN', 'UNKNOWN'] of the item.

    If the item is a group, inspect the children recursively:
        * If there is any critical error, return critical.
        * If not, and there is any unknown, return unknown.
        * If not, and there is any warning, return warning.
        * Else, return OK.

    i.e. We give more priority to unknown than warnings, since an unknown
    could potentially be a hidden error. On the other hand, we give more
    priority to critical errors, since we do not want unknowns to hide the fact
    that there is an error somewhere which was already spotted.
    '''

    if item is None:
        return 'UNKNOWN'

    if not isinstance(item, tuple):
        # Check_MK Service, return its status
        return checkMKStatus[item][0]

    # Group, recurse
    status = 'OK'

    for (childTitle, childWeight, childItem) in item:
        childStatus = getStatus(checkMKStatus, childTitle, childItem)
        if childStatus == 'CRIT':
            # If there is a critical error we already know the result
            return 'CRIT'

        if childStatus == 'UNKNOWN':
            status = 'UNKNOWN'

        if childStatus == 'WARN' and status == 'OK':
            status = 'WARN'

    return status


class Easymon(object):
    '''Easymon class: represents a tree of items.
    '''

    @cherrypy.expose
    def index(self):
        checkMKStatus = getCheckMKStatus()

        items = []
        for (title, weight, item) in self.tree:
            if isinstance(item, tuple):
                # Group

                # Calculate the remainder weights
                remainderWeight = 100.
                noneWeights = 0
                for (childTitle, childWeight, childItem) in item:
                    if childWeight is None:
                        noneWeights += 1
                    else:
                        remainderWeight -= childWeight

                # Calculate final status and assign weights
                status = []
                for (childTitle, childWeight, childItem) in item:
                    if childWeight is None:
                        childWeight = remainderWeight / noneWeights
                    status.append((childTitle, childWeight, getStatus(checkMKStatus, childTitle, childItem)))

                items.append({
                    'isGroup': True,
                    'title': title,
                    'status': status,
                })
            else:
                # Check_MK Service
                if item is None:
                    (status, message, stateAge, checkAge) = ('UNKNOWN', 'UNKNOWN - Check is not enabled.', '???', '???')
                    url = None
                else:
                    (status, message, stateAge, checkAge) = checkMKStatus[item]
                    url = serviceUrlTemplate % item

                items.append({
                    'isGroup': False,
                    'title': title,
                    'status': status,
                    'message': html.urlize(message),
                    'stateAge': stateAge,
                    'checkAge': checkAge,
                    'url': url,
                })

        return treeTemplate.render(title = self.title, items = items)


def build(obj, tree, title):
    obj.title = title
    obj.tree = tree
    for (title, weight, item) in tree:
        if isinstance(item, tuple):
            # Create a subpage for groups
            child = obj.__class__()
            build(child, item, title)
            setattr(obj, title, child)


def main():
    # Create the root object and build the full tree on it
    easymon = Easymon()
    build(easymon, tree, 'CMS ConditionDB EasyMon')

    service.start(easymon)

if __name__ == '__main__' :
    main( )

