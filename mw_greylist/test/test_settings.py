from mw_greylist.settings import Settings
from mw_greylist.exceptions import *
import os.path
import sys
import unittest

class SPFTest(unittest.TestCase):

	def setUp(self):
		script_path = sys.argv[0]
		script_path = os.path.split(script_path)[0]
		self.script_path = script_path
		self.header_file = script_path + "/header_file.txt"

	def testSettingsWithIncorrectFilenameSupplied(self):
		filename = '%s/doesnotexist' % self.script_path
		self.failUnlessRaises(GLInvalidConfigFileException,
							  Settings, filename) 

	def testSettingsWithCorrectFilenameSupplied(self):
		filename = '%s/mw_greylist.conf' % self.script_path
		settings = Settings(filename)
		self.failUnlessEqual(66, settings.session_id_length)
		self.failUnlessEqual('foo\n\n', settings.greylist_message)
		self.failUnlessEqual('bar', settings.connection_url)

	def testSettingsWithoutFilenameSupplied(self):
		settings = Settings()
		self.failUnlessEqual(6, settings.session_id_length)
		self.failUnlessEqual('450 Temporarily inaccessible, try again later.\n\n', 
							 settings.greylist_message)
		self.failUnlessEqual('sqlite:///mw_greylist.db', settings.connection_url)

if __name__ == '__main__':
	unittest.main()
