#!/usr/bin/env python2.6
'''Makes the Redis configuration file for the backends.
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = ['Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


import sys
import optparse
import logging

import config


redisTemplate = '''
daemonize yes
pidfile /var/run/redis/redis.pid

port 6379
bind 127.0.0.1

timeout 0

loglevel notice
logfile /var/log/redis/redis.log

databases {databases}

save 900 1
save 300 10
save 60 10000

rdbcompression yes
dbfilename dump.rdb
dir /var/lib/redis/

slave-serve-stale-data yes

maxmemory {maxmemory}
maxmemory-policy volatile-lru
maxmemory-samples 3

appendonly no
appendfsync everysec
no-appendfsync-on-rewrite no
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb

slowlog-log-slower-than 10000
slowlog-max-len 1024

vm-enabled no
vm-swap-file /tmp/redis.swap
vm-max-memory 0
vm-page-size 32
vm-pages 134217728
vm-max-threads 4

hash-max-zipmap-entries 512
hash-max-zipmap-value 64

list-max-ziplist-entries 512
list-max-ziplist-value 64

set-max-intset-entries 512
zset-max-ziplist-entries 128
zset-max-ziplist-value 64

activerehashing yes
'''


def makeRedisConfiguration():
    '''Returns the Redis configuration file (redis.conf).
    '''

    return redisTemplate.format(
        databases = config.maxCaches,
        maxmemory = config.cacheSize,
    )


def main():
    '''Entry point.
    '''

    parser = optparse.OptionParser(usage =
        'Usage: %prog [options]'
    )

    parser.add_option('-o', '--outputFile',
        dest = 'outputFile',
        default = '/etc/redis.conf',
        help = 'The output file. Default: %default'
    )

    options = parser.parse_args()[0]

    output = makeRedisConfiguration()
    with open(options.outputFile, 'w') as f:
        logging.info('Generating: %s', options.outputFile)
        f.write(output)


if __name__ == '__main__':
    logging.basicConfig(
        format = '[%(asctime)s] %(levelname)s: %(message)s',
        level = logging.INFO,
    )

    sys.exit(main())

