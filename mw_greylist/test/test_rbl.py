from mw_greylist.plugins.rbl_plugin import RBL
from mw_greylist.plugins import rbl
from mw_greylist.exceptions import *
from mw_greylist.settings import Settings
import os.path
import sys
import unittest
import socket

class RBLTest(unittest.TestCase):

    def setUp(self):
        script_path = sys.argv[0]
        script_path = os.path.split(script_path)[0]
        self.header_file = script_path + "/header_file.txt"
        self.servers = ['dul.dnsbl.sorbs.net']

    def testRBLCheckWithEmptyHeaders(self):
        rbl = RBL(settings=Settings())
        rbl.servers = self.servers
        self.failUnlessRaises(GLIncompleteHeaderException, rbl.do_test)

    def testRBLScoreBeforeDoingTest(self):
        rbl = RBL(settings=Settings())
        self.assertEqual(None, rbl.get_score())

    def testRBLCheckWithoutConfigSection(self):
        headers = {}
        headers['client_address'] = 'foo'
        rbl = RBL(headers, Settings())
        self.assertEqual(None, rbl.get_score())

    def testRBLCheckWithInvalidHeaderValues(self):
        headers = {}
        headers['client_address'] = 'foo'
        settings = Settings()
        rbl = RBL(headers, settings)
        rbl.servers = self.servers
        self.failUnlessRaises(socket.gaierror, rbl.do_test)

    def testRBLCheckWithValidHeaders(self):
        headers = {}
        headers['client_address'] = '67.207.130.103'
        result_dict = {'dul.dnsbl.sorbs.net': None}
        rbl = RBL(headers, Settings())
        rbl.servers = self.servers
        rbl.do_test()
        self.assertEqual(result_dict, rbl.results)

    def testRBLActionCheckScoreWithValidResult(self):
        rbl = RBL()
        rbl.results['dul.dnsbl.sorbs.net'] = '127.0.0.2'
        self.assertEqual(1, rbl.get_score())

if __name__ == '__main__':
    unittest.main()
