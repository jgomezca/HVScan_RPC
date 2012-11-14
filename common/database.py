'''Common database code for all CMS DB Web services.
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = ['Giacomo Govi', 'Salvatore Di Guida', 'Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


import logging

import cx_Oracle

import service


# From CMS TagCollector
oracleReconnectCodes = frozenset([
    # From PhEDEx
     3113,  # End-of-file on communication channel
     3114,  # not connected to Oracle
     3135,  # Connection lost contact
     1031,  # insufficient privileges
     1012,  # not logged on
     1003,  # no statement parsed
    12545,  # target host or object does not exist
    17008,  # closed connection
    25408,  # can not safely replay call

    # Some more from Jacek
     2396,  # exceeded maximum idle time, please connect again.
    25401,  # can not continue fetches
    25402,  # transaction must roll back
    25403,  # could not reconnect
    25404,  # lost instance
    25405,  # transaction status unknown
    25406,  # could not generate a connect address
    25407,  # connection terminated
    25409,  # failover happened during the network operation,cannot continue
])


def isReconnectException(e):
    return isinstance(e, cx_Oracle.InterfaceError) or e.args[0].code in oracleReconnectCodes


def convertFromOracle(data):
    if isinstance(data, list) or isinstance(data, tuple):
        return [convertFromOracle(value) for value in data]

    if isinstance(data, set) or isinstance(data, frozenset):
        ret = set([])
        for key in data:
            ret.add(convertFromOracle(key))
        return ret

    if isinstance(data, dict):
        for (key, value) in data.items():
            data[key] = convertFromOracle(value)
        return data

    if isinstance(data, cx_Oracle.LOB):
        return data.read()

    return data


class BLOB(str):
    '''A BLOB: any string that needs to be stored in a BLOB column
    must be wrapped with this class.
    '''

    def __new__(cls, *args, **kwargs):
        return str.__new__(cls, *args, **kwargs)


def transaction(f):
    '''Decorator for functions with signature f(connection, cursor, ...).

    The decorator will take care of creating a cursor for the transaction
    and destroying it as needed. The decorator also takes care of connection
    issues that require a reconnection and retries the *full* transaction again
    with a new cursor after reconnecting (i.e. it will call f() again).
    It also rolls-back in case of other exceptions (Oracle-related exceptions
    that do not require a reconnection, like a failed constraint check
    or user exceptions).

    Since this decorator retries the full transaction again, you need to
    be careful when using it for cases where you need to execute actions
    on external services that may be unreliable (e.g. sending an email)
    since, if not done properly, you may repeat the action several times
    on the external service.

    The returned function by the decorator must be called with a Connection
    object as the first argument, e.g. df(connection, ...). This means
    this decorator can be used for methods in inherited classes
    from Connections, like:

        class MyConnection(database.Connection):

            @database.transaction
            def f(self, cursor):
                ...

        ...

        myConnection.f()

    or in stand-alone functions like:

        @database.transaction
        def f(connection, cursor):
            ...

        ...

        f(connection)
    '''

    def newf(self, *args, **kwargs):
        tries = 2
        while True:
            try:
                logging.debug('%s: Creating cursor...', self)
                cursor = self.connection.cursor()
                try:
                    logging.debug('%s: Calling transaction function...', self)
                    return f(self, cursor, *args, **kwargs)
                finally:
                    logging.debug('%s: Closing cursor...', self)
                    try:
                        cursor.close()
                    except cx_Oracle.Error as e:
                        # Ignore reconnection exceptions when closing the cursor
                        # since the user probably does not want to rerun
                        # the full transaction (since it successfully finished)
                        logging.error('%s: Exception while closing cursor: %s', self, e)
                        if not isReconnectException(e):
                            raise e
            except cx_Oracle.Error as e:
                logging.error('%s: Database Exception: %s', self, e)

                if isReconnectException(e):
                    logging.error('%s: Database Exception: This exception requires a reconnection.', self)

                    logging.error('%s: Database Exception: Reconnection tries: %s', self, tries)
                    if tries == 0:
                        logging.critical('%s: Database Exception: Impossible to reconnect.', self)
                        raise e
                    tries -= 1

                    try:
                        self.reconnect()
                    except Exception as e:
                        logging.error('%s: Exception while reconnecting: %s', self, e)
                else:
                    logging.error('%s: Database Exception: This exception does not require a reconnection.', self)
                    self.connection.rollback()
                    raise e
            except Exception as e:
                logging.error('%s: Exception (not database related): %s', self, e)
                self.connection.rollback()
                raise e

    return newf


class Connection(object):

    def __init__(self, connectionDictionary):
        '''Connects automatically to the database.
        '''

        self.connectionDictionary = connectionDictionary
        self.reconnect()


    def __str__(self):
        return 'Connection %s@%s' % (self.connectionDictionary['user'], self.connectionDictionary['db_name'])


    def reconnect(self):
        '''Note that this invalidates all cursors as well.
        '''

        logging.info('%s: Connecting to database...', self)
        self.connection = cx_Oracle.connect(service.getCxOracleConnectionString(self.connectionDictionary), threaded = True)


    def close(self):
        '''Normally only used for debugging (i.e. testing closing connections
        in-between a running transaction which can simulate network problems
        and session timeouts).
        '''

        logging.info('%s: Closing connection...', self)
        self.connection.close()


    def execute(self, cursor, query, parameters = ()):
        '''Executes a query taking care of BLOBs in the parameters
        (which need to be wrapped with the BLOB() class).

        It also logs the query and parameters if in DEBUG level (but avoiding
        the load of doing so if not).
        '''

        if logging.getLogger().isEnabledFor(logging.DEBUG):
            printParameters = []
            for parameter in parameters:
                if isinstance(parameter, BLOB):
                    printParameters.append('BLOB %s [len]' % len(parameter))
                else:
                    printParameters.append(parameter)
            logging.debug('%s: Executing: %s Params: %s', self, query, printParameters)

        inputSizes = []
        for parameter in parameters:
            if isinstance(parameter, BLOB):
                inputSizes.append(cx_Oracle.BLOB)
            else:
                inputSizes.append(None)

        if cx_Oracle.BLOB in inputSizes:
            cursor.setinputsizes(*inputSizes)

        cursor.execute(query, parameters)


    # These are not transactions, intended to be used within
    # complex user transactions
    def _commit(self):
        '''Commits in the database.
        '''

        logging.debug('%s: Committing...', self)
        self.connection.commit()


    def _fetch(self, cursor, query, parameters = ()):
        '''Fetches the results from a query, automatically taking care of
        reading all returned BLOBs into memory.

        Therefore, it has to loop through fetchone() and it is not a good
        choice if the BLOBs are really big (e.g. if they hold extremely
        large files that need to be handled one by one and even chunk by chunk
        since they do not fit in memory).
        '''

        self.execute(cursor, query, parameters)

        result = []

        while True:
            row = cursor.fetchone()

            if row == None:
                break

            result.append(convertFromOracle(row))

        logging.debug('%s: Fetched: %s', self, result)

        return result


    # Trivial transactions
    @transaction
    def fetch(self, cursor, query, parameters = ()):
        '''Trivial transaction that fetches the results from a single query.
        '''

        return self._fetch(cursor, query, parameters)


    @transaction
    def commit(self, cursor, query = None, parameters = ()):
        '''Trivial transaction that commits a single query.
        '''

        if query is not None:
            self.execute(cursor, query, parameters)

        self._commit()

