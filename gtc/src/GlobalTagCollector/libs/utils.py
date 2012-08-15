# coding=utf-8
import datetime
from django.conf import  settings
from django.core.exceptions import MultipleObjectsReturned
import re
from GlobalTagCollector.models import GTType, Tag, Record
from GlobalTagCollector.libs.exceptions import TagNotDetectedException, RecordNotDetectedException, UnknownSoftwareReleaseNamePattern


def software_release_name_to_version(software_release_name):
    #if some version would achive 999 - we would have some problems. But it is almouts improbable

    maching = re.match(settings.SOFTWARE_RELEASE_NAME_PATTERN, software_release_name)
    if maching:
        g = maching.groups()
        version = int(g[0]) * 1000000000  + int(g[1]) * 1000000 + int(g[2])* 1000
        version += int(g[3]) if (g[3] is not None) else 999
        return version
    else:
        raise UnknownSoftwareReleaseNamePattern(software_release_name)



def get_new_queue_entry_status(status, was_found_in_gt):

    found_statuses = {
        'O': 'O',
        'P': 'P',
        'A': 'O',
        'R': 'R',
        'I': 'I',
    }

    not_found_statuses = {
        'O': 'R',
        'P': 'P',
        'A': 'P',
        'R': 'R',
        'I': 'I',
    }

    if was_found_in_gt:
        return found_statuses[status]
    else:
        return not_found_statuses[status]
