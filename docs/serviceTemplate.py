'''CMS DB Web service template.

Use this code as a base for your service.
Please read the related documentation as well.
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = ['Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


import cherrypy

import service


class ServiceTemplate:
	'''My service description.
	'''

	@cherrypy.expose
	def index(self):
		'''My method description.
		'''

		return 'I am ' + service.settings['name'] + ', I am listening on ' + str(service.settings['listeningPort']) + ', with production level "' + service.settings['productionLevel'] + '", my root directory is ' + service.settings['rootDirectory'] + ' and I have ' + str(len(service.secrets)) + ' secrets hidden!'


def main():
	service.start(ServiceTemplate())


if __name__ == '__main__':
	main()

