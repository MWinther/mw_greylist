from mw_greylist.glentry import GLEntry
from mw_greylist.exceptions import *
from sqlalchemy import create_engine
from sqlalchemy.exceptions import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import unittest

class SPFTest(unittest.TestCase):

	def setUp(self):
		engine = create_engine('sqlite:///:memory:')
		GLEntry.metadata.create_all(engine)
		GLEntry.metadata.bind = engine
		self.Session = sessionmaker()

	def testAddingValidEntryToDatabase(self):
		session = self.Session()
		entry = GLEntry(client='client',
						helo='helo',
						sender='sender')
		session.add(entry)
		session.commit()
		self.failUnlessEqual(1, session.query(GLEntry).count())

	def testAddingInvalidEntryToDatabase(self):
		session = self.Session()
		self.failUnlessRaises(TypeError, GLEntry)

	def testAddingDuplicateEntryToDatabase(self):
		session = self.Session()
		entry = GLEntry(client='client', helo='helo', sender='sender')
		entry2 = GLEntry(client='client', helo='helo', sender='sender')
		session.add(entry)
		session.add(entry2)
		self.failUnlessRaises(IntegrityError, session.commit)

	def testActionShouldBeTestForNoStatus(self):
		session = self.Session()
		entry = GLEntry(client='client', helo='helo', sender='sender')
		self.failUnlessEqual('TEST', entry.get_action())

	def testActionShouldBeAllowForCurrentWL(self):
		session = self.Session()
		entry = GLEntry(client='client', helo='helo', sender='sender')
		entry.status = 'W'
		entry.expiry_date = datetime.now() + timedelta(hours=1)
		session.add(entry)
		session.commit()
		self.failUnlessEqual('ALLOW', entry.get_action())

	def testActionShouldBeTestForExpiredWL(self):
		session = self.Session()
		entry = GLEntry(client='client', helo='helo', sender='sender')
		entry.status = 'W'
		entry.expiry_date = datetime.now() - timedelta(hours=1)
		session.add(entry)
		session.commit()
		self.failUnlessEqual('TEST', entry.get_action())

	def testActionShouldBeAllowForNewlyExpiredGL(self):
		session = self.Session()
		entry = GLEntry(client='client', helo='helo', sender='sender')
		entry.status = 'G'
		entry.expiry_date = datetime.now() - timedelta(hours=1)
		session.add(entry)
		session.commit()
		self.failUnlessEqual('ALLOW', entry.get_action())

	def testActionShouldBeDenyForCurrentGL(self):
		session = self.Session()
		entry = GLEntry(client='client', helo='helo', sender='sender')
		entry.status = 'G'
		entry.expiry_date = datetime.now() + timedelta(hours=1)
		session.add(entry)
		session.commit()
		self.failUnlessEqual('DENY', entry.get_action())

	def testActionShouldBeTestForNotNewlyExpiredGL(self):
		session = self.Session()
		entry = GLEntry(client='client', helo='helo', sender='sender')
		entry.status = 'G'
		entry.expiry_date = datetime.now() - timedelta(weeks=1)
		session.add(entry)
		session.commit()
		self.failUnlessEqual('TEST', entry.get_action())

if __name__ == '__main__':
		unittest.main()
