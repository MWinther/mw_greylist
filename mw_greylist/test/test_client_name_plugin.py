from mw_greylist.plugins.client_name_plugin import ClientName
from mw_greylist.exceptions import *
import os.path
import sys
import unittest

class SPFTest(unittest.TestCase):

    def setUp(self):
        script_path = sys.argv[0]
        script_path = os.path.split(script_path)[0]
        self.header_file = script_path + "/header_file.txt"

    def testClientNameWithEmptyHeaders(self):
	cn = ClientName()
        self.failUnlessRaises(GLPluginException, cn.do_test)

    def testClientNameScoreBeforeDoingTest(self):
        cn = ClientName()
        self.assertEqual(0, cn.get_score())

    def testClientNameCheckWithValidHeaders(self):
        headers = {}
	headers['client_name'] = 'another.domain.tld'
	headers['reverse_client_name'] = 'another.domain.tld'
        cn = ClientName(headers)
        cn.do_test()
        self.assertEqual(0, cn.get_score())

    def testClientNameCheckWithClientAndReverseSameUnknown(self):
	headers = {}
	headers['client_name'] = 'unknown'
	headers['reverse_client_name'] = 'unknown'
	cn = ClientName(headers)
	cn.do_test()
	self.assertEqual(2, cn.get_score())

    def testClientNameCheckWithClientAndReverseSameNotUnkonwn(self):
    	headers = {}
	headers['client_name'] = 'another.domain.tld'
	headers['reverse_client_name'] = 'another.domain.tld'
	cn = ClientName(headers)
	cn.do_test()
	self.assertEqual(0, cn.get_score())

    def testClientNameCheckWithClientAndReverseDifferent(self):
    	headers = {}
	headers['client_name'] = 'unknown'
	headers['reverse_client_name'] = 'another.domain.tld'
	cn = ClientName(headers)
	cn.do_test()
	self.assertEqual(2, cn.get_score())

if __name__ == '__main__':
    unittest.main()
