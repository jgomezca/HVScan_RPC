#!/usr/bin/env python2.6
'''Script that prints some statistics on DropBox's usage and draws some plots.
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = ['Giacomo Govi', 'Salvatore Di Guida', 'Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


import sys
import logging

import jinja2
import subprocess

import database
import service


class DropBoxStatistics():
    '''Class to get some statistics on usage from a DropBox database.
    '''

    def __init__(self, level = 'pro', fromDaysAgo = 2 * 7):
        self.connection = database.Connection(service.secrets['connections'][level])
        self.fromDaysAgo = fromDaysAgo


    def getFiles(self):
        return self.connection.fetch('''
            select count(*)
            from files
            where creationTimestamp > sysdate - :s
        ''', (self.fromDaysAgo, ))[0][0]


    def getTier0Files(self):
        return self.connection.fetch('''
            select count(*)
            from files
            where creationTimestamp > sysdate - :s
                and backend = 'tier0'
        ''', (self.fromDaysAgo, ))[0][0]


    def getBadFiles(self):
        return self.connection.fetch('''
            select count(*)
            from files
            where creationTimestamp > sysdate - :s
                and state = 'Bad'
        ''', (self.fromDaysAgo, ))[0][0]


    def getTier0BadFiles(self):
        return self.connection.fetch('''
            select count(*)
            from files
            where creationTimestamp > sysdate - :s
                and backend = 'tier0'
                and state = 'Bad'
        ''', (self.fromDaysAgo, ))[0][0]


    def getNonTier0BadFiles(self):
        return self.connection.fetch('''
            select count(*)
            from files
            where creationTimestamp > sysdate - :s
                and backend <> 'tier0'
                and state = 'Bad'
        ''', (self.fromDaysAgo, ))[0][0]


    def getUsers(self):
        return self.connection.fetch('''
            select count(*)
            from (
                select distinct username
                from files
                where creationTimestamp > sysdate - :s
            )
        ''', (self.fromDaysAgo, ))[0][0]


    def getFailedAcknowledgedFiles(self):
        return self.connection.fetch('''
            select count(*)
            from fileLog
            where creationTimestamp > sysdate - :s
                and statusCode <> 4999
        ''', (self.fromDaysAgo, ))[0][0]


    def getNonTier0FailedAcknowledgedFiles(self):
        return self.connection.fetch('''
            select count(*)
            from fileLog
            where creationTimestamp > sysdate - :s
                and statusCode <> 4999
                and fileHash not in (
                    select fileHash
                    from files
                    where creationTimestamp > sysdate - :s
                        and backend = 'tier0'
                )
        ''', (self.fromDaysAgo, self.fromDaysAgo))[0][0]


    def getFileTimestamps(self):
        return zip(*self.connection.fetch('''
            select creationTimestamp
            from files
            where creationTimestamp > sysdate - :s
            order by creationTimestamp
        ''', (self.fromDaysAgo, )))[0]


    def getFilesPerDay(self):
        return self.connection.fetch('''
            select coalesce(bad.creationDate, total.creationDate) creationDate, coalesce(bad.bad, 0) bad, coalesce(total.total, total) total
            from (
                select creationDate, count(fileHash) bad
                from (
                    select trunc(creationTimestamp) creationDate, fileHash
                    from files
                    where creationTimestamp > sysdate - :s
                        and state = 'Bad'
                )
                group by creationDate
            ) bad full outer join (
                select creationDate, count(fileHash) total
                from (
                    select trunc(creationTimestamp) creationDate, fileHash
                    from files
                    where creationTimestamp > sysdate - :s
                )
                group by creationDate
            ) total
            on bad.creationDate = total.creationDate
            order by creationDate
        ''', (self.fromDaysAgo, self.fromDaysAgo))


    def getTier0FilesPerDay(self):
        return self.connection.fetch('''
            select coalesce(bad.creationDate, total.creationDate) creationDate, coalesce(bad.bad, 0) bad, coalesce(total.total, total) total
            from (
                select creationDate, count(fileHash) bad
                from (
                    select trunc(creationTimestamp) creationDate, fileHash
                    from files
                    where creationTimestamp > sysdate - :s
                        and state = 'Bad'
                        and backend = 'tier0'
                )
                group by creationDate
            ) bad full outer join (
                select creationDate, count(fileHash) total
                from (
                    select trunc(creationTimestamp) creationDate, fileHash
                    from files
                    where creationTimestamp > sysdate - :s
                        and backend = 'tier0'
                )
                group by creationDate
            ) total
            on bad.creationDate = total.creationDate
            order by creationDate
        ''', (self.fromDaysAgo, self.fromDaysAgo))


    def getNonTier0FilesPerDay(self):
        return self.connection.fetch('''
            select coalesce(bad.creationDate, total.creationDate) creationDate, coalesce(bad.bad, 0) bad, coalesce(total.total, total) total
            from (
                select creationDate, count(fileHash) bad
                from (
                    select trunc(creationTimestamp) creationDate, fileHash
                    from files
                    where creationTimestamp > sysdate - :s
                        and state = 'Bad'
                        and backend <> 'tier0'
                )
                group by creationDate
            ) bad full outer join (
                select creationDate, count(fileHash) total
                from (
                    select trunc(creationTimestamp) creationDate, fileHash
                    from files
                    where creationTimestamp > sysdate - :s
                        and backend <> 'tier0'
                )
                group by creationDate
            ) total
            on bad.creationDate = total.creationDate
            order by creationDate
        ''', (self.fromDaysAgo, self.fromDaysAgo))


template = jinja2.Template('''
  * Total users:      {{users}}

  * Total files:      {{files}}
      + OK (Ack'd):   {{files - badFiles}} ({{'%0.2f' % (100 * (files - badFiles) / files)}} %)
          - OK:       {{files - badFiles - failedAcknowledgedFiles}} ({{'%0.2f' % (100 * (files - badFiles - failedAcknowledgedFiles) / (files - badFiles))}} %)
          - Failed:   {{failedAcknowledgedFiles}} ({{'%0.2f' % (100 * failedAcknowledgedFiles / (files - badFiles))}} %)
              - Tier0:      {{failedAcknowledgedFiles - nonTier0FailedAcknowledgedFiles}} ({{'%0.2f' % (100 * (failedAcknowledgedFiles - nonTier0FailedAcknowledgedFiles) / failedAcknowledgedFiles)}} %)
              - Non-Tier0:  {{nonTier0FailedAcknowledgedFiles}} ({{'%0.2f' % (100 * nonTier0FailedAcknowledgedFiles / failedAcknowledgedFiles)}} %)

      + Failed:       {{badFiles}} ({{'%0.2f' % (100 * badFiles / files)}} %)

      + Non-Tier0:    {{files - tier0Files}} ({{'%0.2f' % (100 * (files - tier0Files) / files)}} %)
          - OK:       {{files - tier0Files - nonTier0BadFiles}} ({{'%0.2f' % (100 * (files - tier0Files - nonTier0BadFiles) / (files - tier0Files))}} %)
          - Failed:   {{nonTier0BadFiles}} ({{'%0.2f' % (100 * nonTier0BadFiles / (files - tier0Files))}} %)

      + Tier0:        {{tier0Files}} ({{'%0.2f' % (100 * tier0Files / files)}} %)
          - OK:       {{tier0Files - tier0BadFiles}} ({{'%0.2f' % (100 * (tier0Files - tier0BadFiles) / tier0Files)}} %)
          - Failed:   {{tier0BadFiles}} ({{'%0.2f' % (100 * tier0BadFiles / tier0Files)}} %)


   * Uploads / day: {{'%0.2f' % (files / 14)}}
      + Tier0:      {{'%0.2f' % (tier0Files / 14)}}
      + Non-Tier0:  {{'%0.2f' % ((files - tier0Files) / 14)}}


  * Files (failed, total) per day:

    {% for (date, bad, total) in filesPerDay %}
        {{date}} {{bad}} {{total}}
    {% endfor %}

''')


filesPerDayGnuplotFile = 'filesPerDay.gnuplot'
filesPerDayDataFile = 'filesPerDay.dat'

filesPerDayGnuplot = '''
# Data looks like:
# 
# 2013-01-21 14 23

set xdata time
set timefmt "%%Y-%%m-%%d"
set xtics rotate
set terminal png
set output "%s"
set style fill solid 0.5
set key left top
set boxwidth 86400 absolute # maximum width: 86400 seconds = 1 day

plot "%s" using 1:3 title 'Good files' with boxes lc rgb "green", \
     "%s" using 1:2 title 'Bad files' with boxes lc rgb "red"
     
'''


def doGnuplot(data, outputFile):
    with open(filesPerDayGnuplotFile, 'wb') as f:
        f.write(filesPerDayGnuplot % (outputFile, filesPerDayDataFile, filesPerDayDataFile))

    with open(filesPerDayDataFile, 'wb') as f:
        for (creationTimestamp, bad, total) in data:
            f.write('%s %s %s\n' % (creationTimestamp.strftime("%Y-%m-%d"), bad, total))

    subprocess.check_call('gnuplot %s' % filesPerDayGnuplotFile, shell = True)


def main():
    stats = DropBoxStatistics()

    filesPerDay = stats.getFilesPerDay()
    tier0FilesPerDay = stats.getTier0FilesPerDay()
    nonTier0FilesPerDay = stats.getNonTier0FilesPerDay()

    doGnuplot(filesPerDay, 'filesPerDay.png')
    doGnuplot(tier0FilesPerDay, 'tier0FilesPerDay.png')
    doGnuplot(nonTier0FilesPerDay, 'nonTier0FilesPerDay.png')

    print template.render(
        users = stats.getUsers(),
        files = stats.getFiles(),
        tier0Files = stats.getTier0Files(),
        badFiles = stats.getBadFiles(),
        tier0BadFiles = stats.getTier0BadFiles(),
        nonTier0BadFiles = stats.getNonTier0BadFiles(),
        failedAcknowledgedFiles = stats.getFailedAcknowledgedFiles(),
        nonTier0FailedAcknowledgedFiles = stats.getNonTier0FailedAcknowledgedFiles(),
        filesPerDay = filesPerDay,
    )

if __name__ == '__main__':
    logging.basicConfig(
        format = '[%(asctime)s] %(levelname)s: %(message)s',
        level = logging.INFO,
    )

    sys.exit(main())

