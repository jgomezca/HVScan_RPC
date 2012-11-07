'''dropBoxBE's log packing/unpacking.
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = ['Giacomo Govi', 'Salvatore Di Guida', 'Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


def pack(log):
    '''Packs a string into the .bz2 format.
    '''

    return log.encode('bz2')


def unpack(log):
    '''Unpacks a string from the .bz2 format.
    '''

    return log.decode('bz2')

