from mw_greylist.plugins.spf_plugin import SPF
from mw_greylist.exceptions import *
import os.path
import sys
import unittest

class SPFTest(unittest.TestCase):

    def setUp(self):
        script_path = sys.argv[0]
        script_path = os.path.split(script_path)[0]
        self.header_file = script_path + "/header_file.txt"

    def testSPFCheckWithEmptyHeaders(self):
        spf = SPF()
        self.failUnlessRaises(GLIncompleteHeaderException, spf.do_test)

    def testSPFScoreBeforeDoingTest(self):
        spf = SPF()
        self.assertEqual(None, spf.get_score())

    def testSPFCheckWithInvalidHeaderValues(self):
        headers = {}
        headers['client_address'] = 'foo'
        headers['helo_name'] = 'bar'
        headers['sender'] = 'gazonk'
        result_dict = {'action': 'pass', 
                       'code': 250, 
                       'message': 'sender SPF authorized'}
        spf = SPF(headers)
        self.failUnlessRaises(ValueError, spf.do_test)

    def testSPFCheckWithValidHeaders(self):
        headers = {}
        headers['client_address'] = '67.207.130.103'
        headers['helo_name'] = 'urd.winthernet.se'
        headers['sender'] = 'test@winthernet.se'
        result_dict = {'action': 'pass', 
                       'code': 250, 
                       'message': 'sender SPF authorized'}
        spf = SPF(headers)
        spf.do_test()
        self.assertEqual(result_dict, spf.result)

    def testSPFActionCheckScoreWithValidResult(self):
        spf = SPF()
        spf.result['action'] = 'softfail'
        self.assertEqual(2, spf.get_score())

    def testSPFActionCheckScoreWithInvalidResult(self):
        spf = SPF()
        spf.result['action'] = 'foo'
        self.failUnlessRaises(GLPluginException, spf.get_score)

if __name__ == '__main__':
    unittest.main()
