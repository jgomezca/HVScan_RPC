import service
import sys

class GetLumiTest(service.TestCase):

    def testIsServerAnswering(self):
        self.assertEqual(type(self.queryJson('/up')), list)

    def testValidRunNumber(self):
        res = self.queryJson('?Runs=167098')
        self.assertEqual(res, [{u'Run': 167098, u'DeliveredLumi': 9959896.620545816}])

    def testValidNewRunNumber(self):
        res = self.queryJson('?Runs=190595,211623') # a couple of new runs not in old tables. Just to check
        self.assertEqual(res, [{u'Run': 190595, u'DeliveredLumi': 5635549.359196878},
                               {u'Run': 211623, u'DeliveredLumi': 376.61880984533275},
                              ])

    def testValidRunList(self):
        res = self.queryJson('?Runs=[167098,161224,160915]') # the result is sorted by runNumber
        self.assertEqual(res, [{u'Run': 167098, u'DeliveredLumi': 9959896.620545816},
                               {u'Run': 161224, u'DeliveredLumi': 53746.74506315869},
                               {u'Run': 160915, u'DeliveredLumi': 467114.10981474567},
                       ])

    def testValidRunMix(self):
        res = self.queryJson('?Runs=167098,161222-161224,160915') # the result is sorted by runNumber
        self.assertEqual(res, [{u'Run': 167098, u'DeliveredLumi': 9959896.620545816},
                               {u'Run': 161222, u'DeliveredLumi': 571112.0599251935},
                               {u'Run': 161223, u'DeliveredLumi': 1589993.0320118787},
                               {u'Run': 161224, u'DeliveredLumi': 53746.74506315869},
                               {u'Run': 160915, u'DeliveredLumi': 467114.10981474567},
                       ])

    def testValidTimeRange(self):
        #-ap: ??? no qualified runs in this interval:
        #-ap:  res = self.queryJson('?startTime=16-Jun-11-14:00&endTime=16-Jun-11-16:00')
        res = self.queryJson('?startTime=16-Jun-12-14:00&endTime=17-Jun-12-14:00')
        # the result is sorted by runNumber
        self.assertEqual(res, [{u'Run': 196452, u'DeliveredLumi': 118421072.06045863},
                               {u'Run': 196453, u'DeliveredLumi': 116237971.39496592},
                               {u'Run': 196458, u'DeliveredLumi': 332634.18678372639},
                       ])

    def testInvalidRunNumber(self):
        self.assertRaisesHTTPError(405, '?Runs=AA167098')


def main():
    sys.exit(service.test(GetLumiTest))


if __name__ == "__main__":
    main()

