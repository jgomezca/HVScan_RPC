'''Common code related to shells for all CMS DB Web services.
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2013, CERN CMS'
__credits__ = ['Giacomo Govi', 'Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


import re


_find_unsafe = re.compile(r'[^\w@%+=:,./-]').search


def escape(s):
    '''Return a shell-escaped version of the string *s*.

    Back-ported from Python 3.3's shlex.quote() where it is officially
    supported. Previously this was in pipes.quote() in Python 2.6; however,
    in early 2.6 versions there were two bugs (one was the empty string,
    another one the unsafe ! character not listed as such). Unluckily,
    our version of Python 2.6 contains this bug :(
    '''

    if not s:
        return "''"
    if _find_unsafe(s) is None:
        return s

    # use single quotes, and put single quotes into double quotes
    # the string $'b is then quoted as '$'"'"'b'
    return "'" + s.replace("'", "'\"'\"'") + "'"

