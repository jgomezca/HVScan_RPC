#!/usr/bin/python2.6
'''Builds all tables for payloadInspector.
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = ['Miguel Ojeda']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


import logging

import service

from lastIOVSince import LastIOVSince
from EcalCondDB import EcalCondDB


def main():
	connections = service.secrets['connections']

	i = 0
	for level in connections:
		i += 1

		connectionStrings = service.getFrontierConnectionStringList(connections[level])

		j = 0
		for connectionString in connectionStrings:
			j += 1

			shortConnectionString = service.getFrontierConnectionString({
				'account': connections[level]['accounts'][j-1],
				'frontier_name': connections[level]['frontier_name']
			}, short = True)

			loggingPrefix = '[%s/%s %s %s/%s] %s: ' % (i, len(connections), level, j, len(connectionStrings), connectionString.rsplit('/', 1)[1])

			try:
				logging.info(loggingPrefix + 'Building HTML...')
				LastIOVSince(dbName = connectionString).writeTable(dbName = shortConnectionString)
			except Exception as e:
				logging.error(loggingPrefix + 'Exception while building HTML: %s.' % str(e))

			try:
				logging.info(loggingPrefix + 'Building JSON...')
				condDB = EcalCondDB(dbName = connectionString)
				condDB.listContainers_json_writer(content = condDB.listContainers(), dbName = shortConnectionString)
			except Exception as e:
				logging.error(loggingPrefix + 'Exception while building JSON: %s.' % str(e))


if __name__ == '__main__':
	main()

