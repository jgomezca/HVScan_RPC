'''Offline new dropBox's database-based log for the status of files and runs.

In this file, only the functionality related to logging the status
for the dropBox should be implemented.
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = ['Giacomo Govi', 'Salvatore Di Guida', 'Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


import database
import service


if service.settings['productionLevel'] == 'private':
    connection = database.Connection(service.getConnectionDictionaryFromNetrc('dropBoxDatabase'))
else:
    connection = database.Connection(service.secrets['connections']['dev'])


def insertFileLog(fileHash, statusCode, username):
    connection.commit('''
        insert into fileLog
        (fileHash, statusCode, username)
        values (:s, :s, :s)
    ''', (fileHash, statusCode, username))


def updateFileLogStatus(fileHash, statusCode):
    connection.commit('''
        update fileLog
        set statusCode = :s
        where fileHash = :s
    ''', (statusCode, fileHash))


def updateFileLogLog(fileHash, log, runLogCreationTimestamp):
    connection.commit('''
        update fileLog
        set log = :s, runLogCreationTimestamp = to_timestamp(:s, 'YYYY-MM-DD HH24:MI:SS,FF3')
        where fileHash = :s
    ''', (log, runLogCreationTimestamp, fileHash))


def insertOrUpdateRunLog(creationTimestamp, statusCode):
    connection.commit('''
        merge into runLog
        using dual
        on (creationTimestamp = to_timestamp(:s, 'YYYY-MM-DD HH24:MI:SS,FF3'))
        when matched then
            update
            set statusCode = :s
            where creationTimestamp = to_timestamp(:s, 'YYYY-MM-DD HH24:MI:SS,FF3')
        when not matched then
            insert
            (creationTimestamp, statusCode)
            values (to_timestamp(:s, 'YYYY-MM-DD HH24:MI:SS,FF3'), :s)
    ''', (creationTimestamp, statusCode, creationTimestamp, creationTimestamp, statusCode))


def updateRunLogRuns(creationTimestamp, firstConditionSafeRun, hltRun):
    connection.commit('''
        update runLog
        set firstConditionSafeRun = :s, hltRun = :s
        where creationTimestamp = to_timestamp(:s, 'YYYY-MM-DD HH24:MI:SS,FF3')
    ''', (firstConditionSafeRun, hltRun, creationTimestamp))


def updateRunLogInfo(creationTimestamp, downloadLog, globalLog):
    connection.commit('''
        update runLog
        set downloadLog = :s, globalLog = :s
        where creationTimestamp = to_timestamp(:s, 'YYYY-MM-DD HH24:MI:SS,FF3')
    ''', (downloadLog, globalLog, creationTimestamp))


# For testing (test.py)

def getLatestRunLogStatusCode():
    result = connection.fetch('''
        select *
        from (
            select statusCode
            from runLog
            order by creationTimestamp desc
        )
        where rownum = 1
    ''')

    # Usually test.py will be so fast uploading that the dropBox was sleeping
    # all the time, so it did not even have time to call insertOrUpdateRunLog()
    # at least once, so there are no row in the table since cleanUp() deleted
    # them all
    if result == []:
        return None

    return result[0][0]


def getLatestRunLogInfo():
    return connection.fetch('''
        select *
        from (
            select creationTimestamp, downloadLog, globalLog
            from runLog
            order by creationTimestamp desc
        )
        where rownum = 1
    ''')[0]


def getFileLogInfo(fileHash):
    return connection.fetch('''
        select statusCode, log, runLogCreationTimestamp
        from fileLog
        where fileHash = :s
    ''', (fileHash, ))[0]


# For debugging

def dumpDatabase():
    return (
        connection.fetch('''
            select *
            from runLog
        '''),
        connection.fetch('''
            select *
            from fileLog
        '''),
    )


def close():
    connection.close()


def cleanUp():
    connection.commit('''
        delete from fileLog
    ''')
    connection.commit('''
        delete from runLog
    ''')

