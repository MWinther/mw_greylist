from mw_greylist.settings import Settings
from mw_greylist.exceptions import *
import os.path
import sys
import unittest
from datetime import timedelta

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
        self.failUnlessEqual('foo', settings.greylist_message)
        self.failUnlessEqual('bar', settings.connection_url)
        self.failUnlessEqual('10d', settings.greylist_intervals)
        self.failUnlessEqual('77m', settings.whitelist_intervals)

    def testSettingsWithoutFilenameSupplied(self):
        settings = Settings()
        self.failUnlessEqual(6, settings.session_id_length)
        self.failUnlessEqual('450 Temporarily inaccessible, try again later.', 
                             settings.greylist_message)
        #self.failUnlessEqual('sqlite:///mw_greylist.db', settings.connection_url)

    def testTimeDeltaWithIncorrectValues(self):
        settings = Settings()
        self.failUnlessRaises(ValueError, settings.mk_timedelta, 'foo')
        self.failUnlessRaises(TypeError, settings.mk_timedelta, 9)
        self.failUnlessRaises(ValueError, settings.mk_timedelta, 'g9m')

    def testTimeDeltaWithCorrectValues(self):
        settings = Settings()
        self.failUnlessEqual(timedelta(seconds=4), settings.mk_timedelta('4s'))
        self.failUnlessEqual(timedelta(minutes=6), settings.mk_timedelta('6m'))
        self.failUnlessEqual(timedelta(hours=8), settings.mk_timedelta('8h'))
        self.failUnlessEqual(timedelta(days=10), settings.mk_timedelta('10d'))
        self.failUnlessEqual(timedelta(weeks=12), settings.mk_timedelta('12w'))
        self.failUnlessEqual(timedelta(days=14*30), settings.mk_timedelta('14M'))
        self.failUnlessEqual(timedelta(days=16*365), settings.mk_timedelta('16y'))

    def testWhiteListExpiryWithCorrectValues(self):
        settings = Settings()
        settings.whitelist_intervals = '1M,3w'
        self.failUnlessEqual(settings.whitelist_expiry(0),
                             settings.now + timedelta(days=30))
        self.failUnlessEqual(settings.whitelist_expiry(1),
                             settings.now + timedelta(weeks=3))
        self.failUnlessEqual(settings.whitelist_expiry(2),
                             settings.now + timedelta(weeks=3))

    def testGreyListExpiryWithCorrectValues(self):
        settings = Settings()
        settings.greylist_intervals = '2m,5m,10m'
        self.failUnlessEqual(settings.greylist_expiry(1),
                             settings.now + timedelta(minutes=2))
        self.failUnlessEqual(settings.greylist_expiry(2),
                             settings.now + timedelta(minutes=5))
        self.failUnlessEqual(settings.greylist_expiry(3),
                             settings.now + timedelta(minutes=10))
        self.failUnlessEqual(settings.greylist_expiry(4),
                             settings.now + timedelta(minutes=10))

if __name__ == '__main__':
    unittest.main()
