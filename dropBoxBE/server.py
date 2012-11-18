'''dropBox backend.
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = ['Giacomo Govi', 'Salvatore Di Guida', 'Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


import logging
import socket
import time

# Initialize logging
import service

import config
import Dropbox


# helper functions -- todo: this should probably go into a more common place ?? (used also in replay)
import datetime

def getNextDropBoxRunTimestamp( timestamp ) :
    '''Given a timestamp, give the timestamp of the next dropBox run.
    i.e. the closest in the future.
    '''

    closeDropBoxRuns = [
        timestamp.replace( minute=0, second=0, microsecond=0 ),
        timestamp.replace( minute=10, second=0, microsecond=0 ),
        timestamp.replace( minute=20, second=0, microsecond=0 ),
        timestamp.replace( minute=30, second=0, microsecond=0 ),
        timestamp.replace( minute=40, second=0, microsecond=0 ),
        timestamp.replace( minute=50, second=0, microsecond=0 ),
        timestamp.replace( minute=0, second=0, microsecond=0 )
        + datetime.timedelta( hours=1 ),
    ]

    for run in closeDropBoxRuns :
        if timestamp < run :
            return run

    raise Exception( 'This should not happen.' )


def secUntilNext10Min() :
    timestamp = datetime.datetime.fromtimestamp( time.time( ) )
    next = getNextDropBoxRunTimestamp( timestamp )
    # Add 3 more seconds to avoid races (i.e. .seconds does
    # not contain the microseconds part and even them we would
    # be asking for trouble, so just add 3 full seconds since
    # we do not need precise runs at :10 minute marks (even
    # 1 or 2 seconds should be enough).
    return ( next - timestamp ).seconds + 3

def main():
    '''Runs the dropBox forever.
    '''

    logging.info('Starting...')

    fqdn = socket.getfqdn()

    if fqdn.endswith('.cms'):
        logging.info('Using online configuration.')
        dropBoxConfig = config.online()
    elif fqdn == 'vocms226.cern.ch':
        # FIXME: This will be in the online soon.
        logging.info('Using tier0Test configuration.')
        dropBoxConfig = config.tier0Test()
    elif fqdn.endswith('.cern.ch'):
        logging.info('Using test configuration.')
        dropBoxConfig = config.test()
    else:
        raise Exception('Not running at CERN.')

    logging.info('Configuring object...')

    dropBox = Dropbox.Dropbox(dropBoxConfig)

    logging.info('Running forever...')

    while True:
        logging.info('Processing all files...')
        dropBox.processAllFiles()

        if dropBoxConfig.delay:
            logging.info('Processing all files done; waiting %s seconds for the next run.', dropBoxConfig.delay)
            time.sleep( dropBoxConfig.delay )
        else:  # if delay is not set, it means we're Tier-0 and need to run at next 10 min interval:
            sleepTime = secUntilNext10Min()
            logging.info('Processing all files done; waiting %s seconds for the next run.', sleepTime)
            time.sleep( sleepTime )


if __name__ == '__main__':
    main()

