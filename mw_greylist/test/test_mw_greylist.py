from mw_greylist.glcandidate import GLCandidate
from mw_greylist.exceptions import *
import os.path
import sys
import unittest
#import mw_greylist.core.exceptions

class mw_greylistTest(unittest.TestCase):

	def setUp(self):
		self.glc = GLCandidate()
		script_path = sys.argv[0]
		script_path = os.path.split(script_path)[0]
		self.header_file = script_path + "/header_file.txt"

	def testReadConfigFromNonExistingFile(self):
		self.failUnlessRaises(IOError,
							  GLCandidate,
							  "foo")

	def testSortDbConfigIntoDict(self):
		conf = [('db', 'foo'), ('user', 'bar'), ('dbname', 'gazonk')]
		self.glc._parse_db_settings(conf)
		self.assertEqual({'user':'bar', 'dbname':'gazonk'},
						 self.glc.db_params)
		self.assertEqual('foo', self.glc.db_type)

	def testReadHeadersFromExistingFile(self):
		self.glc.read_headers(self.header_file)
		self.assertEqual('1.2.3.4',
						 self.glc.headers['client_address'])

	def testInvalidHeaderLine(self):
		self.failUnlessRaises(GLHeaderException, 
							  self.glc._split_headers, 
							  'foo')

	def testValidHeaderLine(self):
		self.assertEqual(['name', 'value'], 
						 self.glc._split_headers('name=value\n'))

	def testMultipleEqualSignHeaderLine(self):
		self.assertEqual(['name', 'value==value'],
						 self.glc._split_headers('name=value==value\n'))
						 
	def testEmptyHeaderLine(self):
		self.assertEqual(None,
						 self.glc._split_headers('\n'))

	def testHeaderFromFileLineCount(self):
		fh = open(self.header_file)
		lines = fh.readlines()
		self.glc.read_headers(self.header_file)
		self.assertEqual(len(lines),
						 len(self.glc.headers))

	def testHeaderAddedCorrectly(self):
		self.glc.read_headers(self.header_file)
		self.assertEqual(self.glc.headers['client_address'], '1.2.3.4')

	def testRBLCheckWithoutClient(self):
		self.failUnlessRaises(Exception,
							  self.glc._test_rbl_server,
							  'zen.spamhaus.org')

	def testRBLServerResponse(self):
		self.glc.headers['client_address'] = '127.0.0.2'
		self.assertNotEqual(None,
						    self.glc._test_rbl_server('zen.spamhaus.org'))

	def testRBLServerResponseStoredCorrectly(self):
		self.glc.headers['client_address'] = '127.0.0.2'
		self.glc._test_rbl_server('zen.spamhaus.org')
		self.assert_('zen.spamhaus.org' in self.glc.rbl_results)

	def testHandleEmptyConnStr(self):
		self.glc = GLCandidate(conf_file="")
		self.assertEqual("", self.glc._conn_str())

	def testConnStrCreatedCorrectly(self):
		self.glc = GLCandidate(conf_file="")
		self.glc.db_params['dbname'] = 'greylist'
		self.glc.db_params['dbuser'] = 'postfix'
		self.assertEqual("dbname='greylist' dbuser='postfix' ",
						 self.glc._conn_str())

	def testHandleInvalidConnectionOption(self):
		self.glc.db_params['foo'] = 'bar'
		self.failUnlessRaises(Exception,
							  self.glc.db_connect,
							  None)

	def testConnectWithInvalidConnectionObject(self):
		self.glc.db_connection = "foo"
		self.failUnlessRaises(Exception,
							  self.glc.db_connect,
							  None)
	
	def testExecuteInvalidCursorObject(self):
		self.glc.db_params['dbname'] = 'postfix'
		self.glc.db_params['user'] = 'postgres'
		self.glc.db_connection = self.glc.db_connect()
		self.failUnlessRaises(Exception,
							  self.glc.db_execute,
							  ('foo', ""))
		
	def testExecuteInvalidQuery(self):
		self.glc.db_params['dbname'] = 'postfix'
		self.glc.db_params['user'] = 'postgres'
		self.glc.db_connect()
		cur = self.glc.db_connection.cursor()
		kwargs = {'cursor':cur, 'cmd':"foo"}
		self.failUnlessRaises(Exception,
							  self.glc.db_execute,
							  **kwargs)

if __name__ == '__main__':
	unittest.main()
