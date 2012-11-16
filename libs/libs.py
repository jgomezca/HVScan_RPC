'''CMS DB Web docs server.
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = ['Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


import service


class Libs(object):
	'''Libs server.
	'''


def main():
	service.start(Libs())


if __name__ == '__main__':
	main()

