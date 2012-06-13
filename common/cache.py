'''Caching code for all CMS DB Web services.
'''

__author__ = 'Miguel Ojeda'
__copyright__ = 'Copyright 2012, CERN CMS'
__credits__ = ['Salvatore Di Guida', 'Miguel Ojeda', 'Andreas Pfeiffer']
__license__ = 'Unknown'
__maintainer__ = 'Miguel Ojeda'
__email__ = 'mojedasa@cern.ch'


import os
import errno
import hashlib
import datetime
import cPickle

import logging
logging.basicConfig(
	format = '[%(asctime)s] %(levelname)s: %(message)s',
	level = logging.INFO
)
logger = logging.getLogger(__name__)

cacheDirectory = 'cache'


def __getHash(key):
	return hashlib.md5(key).hexdigest()


def __getFilename(key):
	return os.path.join(cacheDirectory, __getHash(key))


def get(key, maxAge = 3600):
	try:
		filename = __getFilename(key)
		fileAge = datetime.datetime.now() - datetime.datetime.fromtimestamp(os.stat(filename).st_mtime)
		if fileAge > datetime.timedelta(seconds = maxAge):
			return
		with open(filename, 'rb') as f:
			return cPickle.load(f)
	except OSError as e:
		if e.errno != errno.ENOENT:
			logger.warning(e)
	except Exception as e:
		logger.warning(e)


def put(key, value):
	try:
		with open(__getFilename(key), 'wb') as f:
			cPickle.dump(value, f, protocol = cPickle.HIGHEST_PROTOCOL)
	except Exception as e:
		logger.warning(e)

