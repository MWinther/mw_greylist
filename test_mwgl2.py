import unittest
import mwgl2

class MWGL2Test(unittest.TestCase):

	def setUp(self):
		self.glc = mwgl2.GLCandidate()

	def testReadConfigFromNonExistingFile(self):
		self.failUnlessRaises(IOError,
							  mwgl2.GLCandidate,
							  "foo")

	def testSortDbConfigIntoDict(self):
		conf = [('db', 'foo'), ('user', 'bar'), ('dbname', 'gazonk')]
		self.glc._parse_db_settings(conf)
		self.assertEqual({'user':'bar', 'dbname':'gazonk'},
						 self.glc.db_params)
		self.assertEqual('foo', self.glc.db_type)

	def testReadHeadersFromExistingFile(self):
		self.glc.read_headers("test/header_file.txt")
		self.assertEqual('1.2.3.4',
						 self.glc.headers['client_address'])

	def testInvalidHeaderLine(self):
		self.failUnlessRaises(mwgl2.GLHeaderException, 
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
		filename = 'test/header_file.txt'
		fh = open(filename)
		lines = fh.readlines()
		self.glc.read_headers(filename)
		self.assertEqual(len(lines),
						 len(self.glc.headers))

	def testHeaderAddedCorrectly(self):
		self.glc.read_headers('test/header_file.txt')
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

	def testSPFCheckWithoutClient(self):
		self.failUnlessRaises(Exception, self.glc.test_spf)

	def testSPFResponse(self):
		self.glc.headers['client_address'] = '67.207.130.103'
		self.glc.headers['helo_name'] = 'urd.winthernet.se'
		self.glc.headers['sender'] = 'test@winthernet.se'
		self.assertEqual(('pass', 250, 'sender SPF authorized'),
						 self.glc.test_spf())

	def testHandleEmptyConnStr(self):
		self.glc = mwgl2.GLCandidate(conf_file="")
		self.assertEqual("", self.glc._conn_str())

	def testConnStrCreatedCorrectly(self):
		self.glc = mwgl2.GLCandidate(conf_file="")
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
