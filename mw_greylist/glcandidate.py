from mw_greylist.pluginframework import ActionProvider
from mw_greylist.plugins import *
from mw_greylist.exceptions import *
from mw_greylist.glentry import GLEntry
from mw_greylist.log import Log
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
        self.db_entry = None
        self.score = None
        self.oldstatus = None
        self.plugins = ActionProvider.plugins

    def __repr__(self):
        if 'client_name' in self.headers:
            client_name = self.headers['client_name']
        else:
            client_name = 'unknown'
        if 'client_address' and 'helo_name' and 'sender_domain' in self.headers:
            return 'client=%s[%s] helo=<%s> sender_domain=%s'\
                      % (client_name,
                         self.headers['client_address'],
                         self.headers['helo_name'],
                         self.headers['sender_domain'])
        else:
            return '<GLCandidate; incomplete headers>'

    def _split_headers(self, line=""):
        line = line.strip()
        if not line:
            return None
        fields = line.split('=')
        if len(fields) == 1:
            log.write("Invalid header line: '%s'" % line, LOG_DEBUG)
            raise GLHeaderException, "Invalid header line: '%s'" % line    
        if len(fields) == 2:
            name, value = fields
        if len(fields) > 2:
            name = fields[0]
            value = '='.join(fields[1:])
        log.write("Header line: %s=%s" % (name, value), LOG_DEBUG)
        return [name, value] 

    def read_headers(self, filename=""):
        if filename:
            try:
                file = open(filename, 'r')
            except IOError, e:
                log.write("Can't open file %s: %s" % (filename, e), LOG_ERR)
                sys.exit(1)
        else:
            log.write("No file name given. Reading from stdin.", LOG_DEBUG)
            file = sys.stdin

        while True:
            line = file.readline()
            line = line.strip()
            if line:
                name, value = self._split_headers(line)
                self.headers[name] = value
                if name == 'sender':
                    self.headers['sender_domain'] = value.split('@')[-1]
                if name == 'queue_id':
                    log.session_id = value
            else:
                log.write("Done reading headers.", LOG_DEBUG)
                break

    def _do_tests(self):
        score = 0
        for plugin in self.plugins:
            p = plugin(self.headers, self.settings)
            log.write("Using plugin '%s'" % p, LOG_DEBUG)
            try:
                p.do_test()
                test_score = p.get_score()
            except GLPluginException, e:
                log.write("Plugin '%s' raised exception '%s'" % (p, e),
                          LOG_ERR)
                test_score = 0
            if test_score:
                score += test_score
        log.write("Settings GLCandidate score to %d" % score, LOG_DEBUG)
        self.score = score

    def get_action(self):
        if not self.db_entry:
            self.db_entry = self._get_or_create_db_entry()
        action = self.db_entry.get_action()            
        log.write("Got action '%s' from db entry." % action, LOG_DEBUG)
        return action

    def _get_or_create_db_entry(self):
        client = self.headers['client_address']
        helo = self.headers['helo_name']
        sender = self.headers['sender_domain']
        query = self.session.query(GLEntry).filter(
                and_(GLEntry.client == client,
                     GLEntry.helo == helo,
                     GLEntry.sender == sender)
        )
        entry = None
        if(query.count() == 1):
            log.write("Entry client='%s', helo='%s', sender='%s' found in database."\
                        % (client, helo, sender), LOG_DEBUG)
            entry = query.first()
            self.oldstatus = entry.status
        else:
            log.write("Created new entry client='%s', helo='%s', sender='%s'.",
                      LOG_DEBUG)
            entry = GLEntry(client=client, helo=helo, sender=sender)
            self.session.add(entry)
            self.oldstatus = '-'
        return entry

    def _handle_score(self):
        if self.score != None:
            log.write('Updating db entry: last activated=%s' % self.settings.now,
                      LOG_DEBUG)
            self.db_entry.last_activated = self.settings.now
            log.write('Updating db entry: count=%d' % 1, LOG_DEBUG)
            self.db_entry.count = 1
            log.write('Updating db entry: score=%d' % self.score, LOG_DEBUG) 
            self.db_entry.score = self.score
            if self.score:
                self.db_entry.status = 'G'
                self.db_entry.expiry_date =\
                    self.settings.greylist_expiry(self.score)
            else:
                self.db_entry.status = 'W'
                self.db_entry.expiry_date =\
                    self.settings.whitelist_expiry(self.score)
            log.write("Entry will expire on=%s" % self.db_entry.expiry_date,
                      LOG_DEBUG)


    def _update_db_entry(self, action):
        status = self.db_entry.status
        if status == 'W' and action == 'ALLOW':
            self.oldstatus = 'W'
            self.db_entry.last_activated = self.settings.now
            self.db_entry.count += 1
        elif status == 'G' and action == 'ALLOW':
            self.oldstatus = 'G'
            self.db_entry.status = 'W'
            self.db_entry.expiry_date =\
                    self.settings.whitelist_expiry(self.db_entry.score)
            log.write("New expiry date: %s" % self.db_entry.expiry_date, LOG_DEBUG)
            self.db_entry.last_activated = self.settings.now
            self.db_entry.count = 1
        elif status == 'G' and action == 'DENY':
            self.oldstatus = 'G'
            self.db_entry.last_activated = self.settings.now
            self.db_entry.count += 1

    def perform_action(self):
        action = self.get_action()
        response = ""
        if action == 'TEST':
            log.write("Got action '%s', performing tests." % action, LOG_DEBUG)
            self._do_tests()
            self._handle_score()
            action = self.get_action()
            log.write("Rechecked action after tests, new action is '%s'" % action,
                      LOG_DEBUG)
        else:
            log.write("Won't perform tests, updating db entry.", LOG_DEBUG)
            self._update_db_entry(action)
        if action == 'ALLOW':
            response = 'DUNNO'
        elif action == 'DENY':
            response = self.settings.greylist_message
            log.write('reject: %s; %s' % (response, self))
        else:
            response = 'DUNNO'
        log.write("Got action '%s', returning '%s'" % (action, response), LOG_DEBUG)
        log.write("%s, status=%s/%s score=%d count=%d expiry=%s"\
                  % (self,
                     self.oldstatus,
                     self.db_entry.status,
                     self.db_entry.score,
                     self.db_entry.count,
                     self.db_entry.expiry_date))
        return "action=%s\n\n" % response

log = Log()

