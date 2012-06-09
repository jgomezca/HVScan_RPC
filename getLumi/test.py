import service
import unittest
import sys

from urllib2 import HTTPError

class GetLumiTest(unittest.TestCase):

	def testIsServerAnswering(self):
		self.assertEqual(type(service.queryJson('')), list)

	def testValidRunNumber(self):
		res = service.queryJson('/?Runs=167098')
		self.assertEqual(res, [{u'Run': 167098, u'DeliveredLumi': 9699885.6811485887}])

	def testValidRunList(self):
		res = service.queryJson('/?Runs=[167098,161224,160915]') # the result will be sorted by runNumber
		self.assertEqual(res, [{u'Run': 160915, u'DeliveredLumi': 467125.02761090151},
				       {u'Run': 161224, u'DeliveredLumi': 50094.586426071066},
				       {u'Run': 167098, u'DeliveredLumi': 9699885.6811485887},
				       ])

	def testValidRunMix(self):
		res = service.queryJson('/?Runs=167098,161222-161224,160915') # the result will be sorted by runNumber
		self.assertEqual(res, [{u'Run': 160915, u'DeliveredLumi': 467125.02761090151},
				       {u'Run': 161222, u'DeliveredLumi': 571125.40845842543},
				       {u'Run': 161223, u'DeliveredLumi': 1590030.1947217495},
				       {u'Run': 161224, u'DeliveredLumi': 50094.586426071066},
				       {u'Run': 167098, u'DeliveredLumi': 9699885.6811485887},
				       ])

	def testValidTimeRange(self):
		res = service.queryJson('/?startTime=16-Jun-11-14:00&endTime=16-Jun-11-16:00') # the result will be sorted by runNumber
		self.assertEqual(res, [{u'Run': 167052, u'DeliveredLumi': u'n/a'},
				       {u'Run': 167053, u'DeliveredLumi': u'n/a'},
				       {u'Run': 167056, u'DeliveredLumi': u'n/a'},
				       {u'Run': 167057, u'DeliveredLumi': u'n/a'},
				       ])

	def testInvalidRunNumber(self):
		try:
			service.queryJson('/?Runs=AA167098')
		except HTTPError, e: #  HTTP Error 405: Method Not Allowed:
			if 'HTTP Error 405' in str(e):
				pass
			else:
				print "Got unknown HTTPError: ", str(e)
				raise
		except:
			print "unknown exception raised:", str(e)
			raise

		

def main():
	sys.exit(service.test(GetLumiTest))


if __name__ == "__main__":
	main()

