from mw_greylist.pluginframework import ActionProvider
from mw_greylist.plugins import *
from mw_greylist.exceptions import *
from mw_greylist.glentry import GLEntry
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.expression import and_
import psycopg2
import sys
from syslog import *
import string 
from random import Random

class GLCandidate(object):

    def __init__(self, settings, session):
        self.settings = settings
        self.session = session
        self.headers = dict()
        self.settings.session_id = self._generate_id()
        self.db_entry = None
        self.score = None

    def _generate_id(self):
        id = ''.join(Random().sample(string.hexdigits.upper(), 
                                     self.settings.session_id_length))
        syslog(LOG_DEBUG, "Created session id %s" % id)
        return id

    def _split_headers(self, line=""):
        line = line.strip()
        if not line:
            return None
        fields = line.split('=')
        if len(fields) == 1:
            raise GLHeaderException, "Invalid header line: '%s'" % line    
        if len(fields) == 2:
            name, value = fields
        if len(fields) > 2:
            name = fields[0]
            value = '='.join(fields[1:])
        self._write_to_syslog("Header line: %s=%s" % (name, value))
        return [name, value] 

    def read_headers(self, filename=""):
        if filename:
            try:
                file = open(filename, 'r')
            except IOError:
                sys.exit(1)
        else:
            file = sys.stdin

        while True:
            line = file.readline()
            line = line.strip()
            if line:
                name, value = self._split_headers(line)
                self.headers[name] = value
                if name == 'sender':
                    self.headers['sender_domain'] = value.split('@')[-1]
            else:
                break

    def _do_tests(self):
        score = 0
        for plugin in self.plugins:
            p = plugin(self.headers)
            p.do_test()
            score += p.get_score()
        self.score = score

    def _write_to_syslog(self, level=LOG_DEBUG, str=""):
        if not str:
            str = level
            level = LOG_DEBUG
        syslog(level, "%s: %s" % (self.settings.session_id, str))

    def get_action(self):
        if not self.db_entry:
            self.db_entry = self._get_or_create_db_entry()
            #self._write_to_syslog("Querying database: \"%s\"" % query_str)
        return self.db_entry.get_action()            

    def _get_or_create_db_entry(self):
        query = self.session.query(GLEntry).filter(
                and_(GLEntry.client == self.headers['client_address'],
                     GLEntry.helo == self.headers['helo_name'],
                     GLEntry.sender == self.headers['sender_domain'])
        )
        if(query.count() == 1):
            return query.first()
        else:
            entry = GLEntry(client=self.headers['client_address'],
                            helo=self.headers['helo_name'],
                            sender=self.headers['sender_domain'])
            self.session.add(entry)
            return entry

    def _handle_score(self):
        if self.score != None:
            self.db_entry.last_activated = self.settings.now
            self.db_entry.count = 1
            self.db_entry.score = self.score
            if self.score:
                self.db_entry.expiry_date =\
                    self.settings.greylist_expiry(self.score)
                self.db_entry.status = 'G'
            else:
                self.db_entry.expiry_date =\
                    self.settings.whitelist_expiry(self.score)
                self.db_entry.status = 'W'

    def _update_db_entry(self, action):
        status = self.db_entry.status
        if status == 'W' and action == 'ALLOW':
            self.db_entry.last_activated = self.settings.now
            self.db_entry.count += 1
        elif status == 'G' and action == 'ALLOW':
            self.db_entry.status = 'W'
            self.db_entry.expiry_date =\
                    self.settings.whitelist_expiry(self.db_entry.score)
            self.db_entry.last_activated = self.settings.now
            self.db_entry.count = 1
        elif status == 'G' and action == 'DENY':
            self.db_entry.last_activated = self.settings.now
            self.db_entry.count += 1

    def perform_action(self):
        action = self.get_action()
        if action == 'TEST':
            self._do_tests()
            self._handle_score()
            action = self.get_action()
        else:
            self._update_db_entry(action)
        if action == 'ALLOW':
            return 'DUNNO\n\n'
        elif action == 'DENY':
            return self.settings.greylist_message
        else:
            return 'DUNNO\n\n'
