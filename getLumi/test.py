import service
import unittest
import sys


class GetLumiTest(unittest.TestCase):

	def testIsServerAnswering(self):
		self.assertEqual(type(service.queryJson('')), list)


def main():
	sys.exit(service.test(GetLumiTest))


if __name__ == "__main__":
	main()

