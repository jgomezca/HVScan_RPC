import service
import sys

class GetLumiTest(service.TestCase):

    def testIsServerAnswering(self):
        self.assertEqual(type(self.queryJson('')), list)

    def testValidRunNumber(self):
        res = self.queryJson('?Runs=167098')
        self.assertEqual(res, [{u'Run': 167098, u'DeliveredLumi': 9699885.6811485887}])

    def testValidRunList(self):
        res = self.queryJson('?Runs=[167098,161224,160915]') # the result will be sorted by runNumber
        self.assertEqual(res, [{u'Run': 160915, u'DeliveredLumi': 467125.02761090151},
                       {u'Run': 161224, u'DeliveredLumi': 50094.586426071066},
                       {u'Run': 167098, u'DeliveredLumi': 9699885.6811485887},
                       ])

    def testValidRunMix(self):
        res = self.queryJson('?Runs=167098,161222-161224,160915') # the result will be sorted by runNumber
        self.assertEqual(res, [{u'Run': 160915, u'DeliveredLumi': 467125.02761090151},
                       {u'Run': 161222, u'DeliveredLumi': 571125.40845842543},
                       {u'Run': 161223, u'DeliveredLumi': 1590030.1947217495},
                       {u'Run': 161224, u'DeliveredLumi': 50094.586426071066},
                       {u'Run': 167098, u'DeliveredLumi': 9699885.6811485887},
                       ])

    def testValidTimeRange(self):
        res = self.queryJson('?startTime=16-Jun-11-14:00&endTime=16-Jun-11-16:00') # the result will be sorted by runNumber
        self.assertEqual(res, [{u'Run': 167052, u'DeliveredLumi': u'n/a'},
                       {u'Run': 167053, u'DeliveredLumi': u'n/a'},
                       {u'Run': 167056, u'DeliveredLumi': u'n/a'},
                       {u'Run': 167057, u'DeliveredLumi': u'n/a'},
                       ])

    def testInvalidRunNumber(self):
        self.assertRaisesHTTPError(405, '?Runs=AA167098')


def main():
    sys.exit(service.test(GetLumiTest))


if __name__ == "__main__":
    main()

