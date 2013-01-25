'''New dropBox's database access for the files, their logs and run logs.
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = ['Giacomo Govi', 'Salvatore Di Guida', 'Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


import json

import database

import config
import Constants


connection = database.Connection(config.connectionDictionary)


def insertFile(fileHash, state, backend, username, fileName, fileContent):
    connection.commit('''
        insert into files
        (fileHash, state, backend, username, fileName, fileContent)
        values (:s, :s, :s, :s, :s, :s)
    ''', (fileHash, state, backend, username, fileName, database.BLOB(fileContent)))


def getFileState(fileHash):
    result = connection.fetch('''
        select state
        from files
        where fileHash = :s
    ''', (fileHash, ))

    # File does not exist
    if result == []:
        return None

    return result[0][0]


def updateFileState(fileHash, state):
    connection.commit('''
        update files
        set state = :s
        where fileHash = :s
    ''', (state, fileHash))


def getPendingFiles(backend):
    result = connection.fetch('''
        select fileHash
        from files
        where state = 'Pending'
            and backend = :s
    ''', (backend, ))

    if result == []:
        return []

    return zip(*result)[0]


def getFileContent(fileHash):
    return connection.fetch('''
        select fileContent
        from files
        where fileHash = :s
    ''', (fileHash, ))[0][0]


def insertFileLog(fileHash, statusCode, metadata, userText):
    connection.commit('''
        insert into fileLog
        (fileHash, statusCode, metadata, userText)
        values (:s, :s, :s, :s)
    ''', (fileHash, statusCode, metadata, userText))


def updateFileLogStatus(fileHash, statusCode):
    connection.commit('''
        update fileLog
        set statusCode = :s
        where fileHash = :s
    ''', (statusCode, fileHash))


def updateFileLogLog(fileHash, log, runLogCreationTimestamp, runLogBackend):
    connection.commit('''
        update fileLog
        set log = :s,
            runLogCreationTimestamp = to_timestamp(:s, 'YYYY-MM-DD HH24:MI:SS,FF3'),
            runLogBackend = :s
        where fileHash = :s
    ''', (database.BLOB(log), runLogCreationTimestamp, runLogBackend, fileHash))


def acknowledgeFileIssue(fileHash, username, rationale):
    connection.commit('''
        insert into fileAcks
        (fileHash, username, rationale)
        values (:s, :s, :s)
    ''', (fileHash, username, rationale))


@database.transaction
def _insertOrUpdateRunLog(connection, cursor, creationTimestamp, backend, statusCode):
    # Keep only the latest heartbeat: If for this backend we are going
    # to update to NOTHING_TO_DO and the latest run also finished with
    # NOTHING_TO_DO, then delete the previous run row.
    if int(statusCode) == Constants.NOTHING_TO_DO:
        result = connection._fetch(cursor, '''
            select *
            from (
                select creationTimestamp, statusCode
                from runLog
                where creationTimestamp <> to_timestamp(:s, 'YYYY-MM-DD HH24:MI:SS,FF3')
                    and backend = :s
                order by creationTimestamp desc
            )
            where rownum = 1
        ''', (creationTimestamp, backend))

        if len(result) != 0:
            (previousCreationTimestamp, previousStatusCode) = result[0]

            if int(previousStatusCode) == Constants.NOTHING_TO_DO:
                connection.execute(cursor, '''
                    delete from runLog
                    where creationTimestamp = to_timestamp(:s, 'YYYY-MM-DD HH24:MI:SS,FF3')
                        and backend = :s
                ''', (previousCreationTimestamp.strftime("%Y-%m-%d %H:%M:%S,%f")[:-3], backend))

    connection.execute(cursor, '''
        merge into runLog
        using dual
        on (creationTimestamp = to_timestamp(:s, 'YYYY-MM-DD HH24:MI:SS,FF3')
            and backend = :s
        )
        when matched then
            update
            set statusCode = :s
            where creationTimestamp = to_timestamp(:s, 'YYYY-MM-DD HH24:MI:SS,FF3')
                and backend = :s
        when not matched then
            insert
            (creationTimestamp, backend, statusCode)
            values (to_timestamp(:s, 'YYYY-MM-DD HH24:MI:SS,FF3'), :s, :s)
    ''', (creationTimestamp, backend, statusCode, creationTimestamp, backend, creationTimestamp, backend, statusCode))

    connection.commit()


def insertOrUpdateRunLog(creationTimestamp, backend, statusCode):
    _insertOrUpdateRunLog(connection, creationTimestamp, backend, statusCode)


def updateRunLogRuns(creationTimestamp, backend, firstConditionSafeRun, hltRun):
    connection.commit('''
        update runLog
        set firstConditionSafeRun = :s, hltRun = :s
        where creationTimestamp = to_timestamp(:s, 'YYYY-MM-DD HH24:MI:SS,FF3')
            and backend = :s
    ''', (firstConditionSafeRun, hltRun, creationTimestamp, backend))


def updateRunLogInfo(creationTimestamp, backend, downloadLog, globalLog):
    connection.commit('''
        update runLog
        set downloadLog = :s, globalLog = :s
        where creationTimestamp = to_timestamp(:s, 'YYYY-MM-DD HH24:MI:SS,FF3')
            and backend = :s
    ''', (database.BLOB(downloadLog), database.BLOB(globalLog), creationTimestamp, backend))


def getFileInformation(fileHash):
    return connection.fetch('''
        select files.fileName, fileLog.statusCode, files.creationTimestamp, fileLog.modificationTimestamp, files.username, fileLog.userText, fileLog.metadata
        from fileLog join files using (fileHash)
        where fileHash = :s
    ''', (fileHash, ))[0]


def insertEmail(subject, body, fromAddress, toAddresses, ccAddresses = ()):
    connection.commit('''
        insert into emails
        (subject, body, fromAddress, toAddresses, ccAddresses)
        values (:s, :s, :s, :s, :s)
    ''', (subject, database.BLOB(body), fromAddress, json.dumps(toAddresses), json.dumps(ccAddresses)))


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
    connection.commit('''
        delete from files
    ''')

