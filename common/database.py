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


class Connection(object):

    def __init__(self, connectionDictionary):
        self.connectionDictionary = connectionDictionary
        self.reconnect()


    def __str__(self):
        return 'Connection %s@%s' % (self.connectionDictionary['user'], self.connectionDictionary['db_name'])


    def reconnect(self):
        logging.info('%s: Connecting to database...', self)
        self.connection = cx_Oracle.connect(service.getCxOracleConnectionString(self.connectionDictionary), threaded = True)


    def execute(self, cursor, query, parameters = ()):
        logging.debug('%s: Database Query: %s Params: %s', self, query, parameters)
        cursor.execute(query, parameters)


    def transaction(f):
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
                        cursor.close()
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


    # Trivial transactions
    @transaction
    def fetch(self, cursor, query, parameters = ()):
        self.execute(cursor, query, parameters)

        result = []

        while True:
            row = cursor.fetchone()

            if row == None:
                break

            result.append(convertFromOracle(row))

        return result


    @transaction
    def commit(self, cursor, query = None, parameters = ()):
        if query is not None:
            self.execute(cursor, query, parameters)

        self.connection.commit()


    def close(self):
        logging.info('%s: Closing connection...', self)
        self.connection.close()

