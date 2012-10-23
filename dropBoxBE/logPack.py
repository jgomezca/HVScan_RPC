'''dropBoxBE's log packing/unpacking.
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = ['Giacomo Govi', 'Salvatore Di Guida', 'Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


import uu
import gzip
import cStringIO


def pack(log):
    '''Packs a string into the .gz.uu format (i.e. compressing it with gzip
    and encoding with uu for easy transfer as ASCII).
    '''

    # Compress with gzip
    gzFile = cStringIO.StringIO()
    f = gzip.GzipFile(fileobj = gzFile, mode = 'w')
    f.write(log)
    f.close()
    gzFile.seek(0)

    # Encode with uu
    uuFile = cStringIO.StringIO()
    uu.encode(gzFile, uuFile)
    uuFile.seek(0)
    log = uuFile.read()

    return log


def unpack(log):
    '''Unpacks a string from the .gz.uu format.
    '''

    # Decode with uu
    uuFile = cStringIO.StringIO()
    uuFile.write(log)
    uuFile.seek(0)
    gzFile = cStringIO.StringIO()
    uu.decode(uuFile, gzFile)
    gzFile.seek(0)

    # Decompress with gzip
    f = gzip.GzipFile(fileobj = gzFile)
    log = f.read()
    f.close()

    return log

