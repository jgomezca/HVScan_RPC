#!/usr/bin/python2.6
'''Builds all tables for payloadInspector.
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = ['Miguel Ojeda']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


if __name__ == '__main__':
	import sys
	if '--productionLevel' not in sys.argv:		
		sys.path.insert(0, '/data/services/keeper')
		import keeper
		keeper.run('payloadInspector', sys.argv[0], replaceProcess = True)


import logging
logger = logging.getLogger(__name__)


import service


from lastIOVSince import LastIOVSince
from EcalCondDB import EcalCondDB


def main():
	lastIOVSince = LastIOVSince(authPath = '')
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

			loggerPrefix = '[%s/%s %s %s/%s] %s: ' % (i, len(connections), level, j, len(connectionStrings), connectionString.rsplit('/', 1)[1])

			try:
				logger.info(loggerPrefix + 'Building HTML...')
				table = LastIOVSince(dbName = connectionString).writeTable(dbName = shortConnectionString)
			except Exception as e:
				logger.error(loggerPrefix + 'Exception while building HTML: %s.' % str(e))

			try:
				logger.info(loggerPrefix + 'Building JSON...')
				condDB = EcalCondDB(dbName = connectionString)
				condDB.listContainers_json_writer(content = condDB.listContainers(), dbName = shortConnectionString)
			except Exception as e:
				logger.error(loggerPrefix + 'Exception while building JSON: %s.' % str(e))


if __name__ == '__main__':
	main()

