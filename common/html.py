'''Common code related to HTML for all CMS DB Web services.
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = ['Giacomo Govi', 'Salvatore Di Guida', 'Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


import re
import xml.sax.saxutils


class HTMLError(Exception):
    '''A common HTML exception.
    '''


def urlize(text, target = r'<a href="\1">\1</a>'):
    '''Replaces http://... and https://... URLs (without whitespace)
    with HTML links.
    '''

    return re.sub(
        r'\b(http(|s)://\S+)\b',
        target,
        text
    )


def escape(data):
    '''Escapes strings in Python objects for (X)HTML.

    e.g. escape([0, '<li>']) returns [0, '&lt;li&gt;']

    Typically you call this with the data you pass to your template generator,
    thus having all the problematic strings escaped, no matter whether
    they are inside your dictionary, set or table.
    '''

    if isinstance(data, str) or isinstance(data, unicode):
        return xml.sax.saxutils.escape(data)

    elif data is None or isinstance(data, bool) or isinstance(data, int) or isinstance(data, long):
        return data

    elif isinstance(data, list) or isinstance(data, tuple):
        return [escape(x) for x in data]

    elif isinstance(data, set) or isinstance(data, frozenset):
        ret = set([])
        for x in data:
            ret.add(escape(x))
        return ret

    elif isinstance(data, dict):
        for x in data.items():
            data[escape(x[0])] = escape(x[1])
        return data

    raise HTMLError('Impossible to escape type %s' % str(type(data)))

