import database
import service


connection = database.Connection(service.secrets['connections']['pro'])


def GetRunResults(runID):
    return connection.fetch('''
        SELECT ID, R_RELEASE, R_ARCH
        FROM RUN_RESULT
        WHERE RID = :runID
        ORDER BY R_RELEASE
    ''', (runID, ))


def GetResultsList(runID):
    return connection.fetch('''
        SELECT ID, STATUS, STEP_LABEL
        FROM RUN_STEP_RESULT
        WHERE ID = :runID and STEP_LABEL IS NOT NULL
    ''', (runID, ))


def GetLabels():
    return zip(*connection.fetch('''
        SELECT DISTINCT LABEL
        FROM RUN_HEADER
    '''))[0]
    

def GetReleasesHeaders(label, release = '', arch = '', count = 2):
    if release and arch:
        return connection.fetch('''
            SELECT *
            FROM (
                SELECT RID, TO_CHAR(RDATE, 'DD.MM.YYYY HH24:MI:SS'), LABEL, T_RELEASE, T_ARCH
                FROM RUN_HEADER
                WHERE T_RELEASE = :rel AND T_ARCH = :arc AND LABEL = :labl
                ORDER BY RID DESC
            )
            WHERE ROWNUM <= :count
        ''', (release, arch, label, count))

    if release:
        return connection.fetch('''
            SELECT *
            FROM (
                SELECT RID, TO_CHAR(RDATE, 'DD.MM.YYYY HH24:MI:SS'), LABEL, T_RELEASE, T_ARCH
                FROM RUN_HEADER
                WHERE T_RELEASE = :rel AND LABEL = :labl
                ORDER BY RID DESC
            )
            WHERE ROWNUM <= :count
        ''', (release, label, count))

    if arch:
        return connection.fetch('''
            SELECT *
            FROM (
                SELECT RID, TO_CHAR(RDATE, 'DD.MM.YYYY HH24:MI:SS'), LABEL, T_RELEASE, T_ARCH
                FROM RUN_HEADER
                WHERE T_ARCH = :arc AND LABEL = :labl
                ORDER BY RID DESC
            )
            WHERE ROWNUM <= :count
        ''', (arch, label, count))

    return connection.fetch('''
        SELECT *
        FROM (
            SELECT RID, TO_CHAR(RDATE, 'DD.MM.YYYY HH24:MI:SS'), LABEL, T_RELEASE, T_ARCH
            FROM RUN_HEADER WHERE LABEL = :labl ORDER BY RID DESC
        )
        WHERE ROWNUM <= :count
    ''', (label, count))


def GetReadLogStatus(runId):
    return connection.fetch('''
        SELECT LOG
        FROM RUN_HEADER
        WHERE RID = :rid
    ''', (runId, ))[0][0]

