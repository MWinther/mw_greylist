from mw_greylist.plugins import *
from mw_greylist.exceptions import *
import psycopg2
import rbl
import socket
import spf
import sys
from syslog import *
import string 
from random import Random

class GLCandidate(object):

	def __init__(self, conf_file="/usr/local/bin/greylist/mw_greylist.conf"):
		self.db_connection = None
		self.db_info = dict()
		self.db_params = dict()
		self.db_type = None
		self.db_write_mode = "INSERT"
		self.headers = dict()
		self.rbl_results = dict()
		self.rbl_servers = list()
		self.scores = dict()
		self.should_write_to_db = True
		self.spf_result = dict()
		self.syslog_facility = LOG_MAIL
		openlog(sys.argv[0].split('/')[-1], 0, self.syslog_facility)
		if conf_file:
			import ConfigParser
			self.config = ConfigParser.ConfigParser()
			file = self.config.read(conf_file)
			if file:
				try:
					self.session_id_length = \
						  self.config.getint('general',
									 	  	 'session_id_length')
				except ConfigParser.NoOptionError:
					self.session_id_length = 6
				try:
					self.greylist_message = self.config.get('general', 
														    'greylist_message')
				except ConfigParser.NoOptionError:
					self.greylist_message = \
						  '450 Temporarily inaccessible, try again later.'
				self.greylist_message = "%s\n\n" % self.greylist_message
				try:
					db_settings = self.config.items('db_settings')
				except ConfigParser.NoSectionError:
					self.db_params = dict()
				self._parse_db_settings(db_settings)
			else:
				syslog(self.syslog_facility, "Can't read config file %s" % conf_file)
				raise IOError, "Can't read config file %s" % conf_file
		else:
			self.session_id_length = 6
		self.session_id = self._generate_id()
		

	def _generate_id(self):
		id = ''.join(Random().sample(string.hexdigits.upper(), 
									 self.session_id_length))
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
		raise GLEndOfFunctionException, "End of non-void function reached."

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

	def do_tests(self):
		score = 0
		for plugin in self.plugins:
			p = plugin(self.headers)
			print p.do_test()
		print "Total score: %d" % score

	def _test_rbl_server(self, server_name):
		if 'client_address' in self.headers:
			res = rbl.check_rbl_like(self.headers['client_address'],
					  				 root_name=server_name)
			self.rbl_results[server_name] = res
			self._write_to_syslog("RBL check for server %s returns %s" % (server_name, res))
			return res
		else:
			self._write_to_syslog(LOG_WARN, "No client_address in headers.")
			raise GLIncompleteHeaderException, "No client address in headers."
			return None

	def test_rbl(self):
		try:
			servers = self.config.get('test_settings', 'rbl_servers')
		except NoOptionError:
			self._write_to_syslog(LOG_INFO, "No RBL servers, ignoring test")
			return None
		for server in servers.split('\n'):
			self._test_rbl_server(server)

	def rbl_score(self):
		score = 0
		for server in self.rbl_results.keys():
			if self.rbl_results[server]:
				score = score + 1
		return score

	def _conn_str(self):
		conn_str = ""
		parameters = self.db_params.keys()
		parameters.sort()
		for parameter in parameters:
			conn_str = conn_str + "%s='%s' " % (parameter, 
												self.db_params[parameter])
		return conn_str

	def db_connect(self):
		conn_str = self._conn_str()
		try:
			self.db_connection = psycopg2.connect(conn_str)
		except Exception, e:
			self._write_to_syslog(LOG_WARN, "Couldn't connect to database: %s" % e)
			print "action=DUNNO\n\n"
			return None
		self._write_to_syslog("Connected to database.")
		return 1

	def db_disconnect(self):
		self._write_to_syslog('Disconnecting from database.')
		if self.db_connection and not self.db_connection.closed:
			self.db_connection.close()

	def db_execute(self, cursor=None, cmd=""):
		if isinstance(self.db_connection, psycopg2._psycopg.connection) \
			  and isinstance(cursor, psycopg2._psycopg.cursor) \
			  and self.db_connection and not self.db_connection.closed:
			self._write_to_syslog("Executing query '%s'" % cmd)
			try:
				cursor.execute(cmd)
			except Exception, e:
				self._write_to_syslog("Couldn't execute '%s': %s" % \
										(cmd, e))
				raise GLNoDBConnectionException, e
				return None
		else:
			self._write_to_syslog(LOG_WARN, "Invalid cursor or connection.")
			raise GLNoDBConnectionException, \
				"Invalid cursor or connection."

	def _write_to_syslog(self, level=LOG_DEBUG, str=""):
		if not str:
			str = level
			level = LOG_DEBUG
		syslog(level, "%s: %s" % (self.session_id, str))

	def _parse_db_settings(self, db_settings):
		for pair in db_settings:
			if pair[0] == 'db':
				self.db_type = pair[1]
			else:
				self.db_params[pair[0]] = pair[1]

	def _gl_sig(self, format='SQL'):
		sender = self.headers['sender'].split('@')[-1]
		if format == 'SQL':
			sig_str = "client='%s' AND helo='%s' AND sender='%s'" \
						% (self.headers['client_address'],
						   self.headers['helo_name'],
						   sender)
		else:
			sig_str = "client='%s', helo='%s', sender='%s'" \
						% (self.headers['client_address'],
						   self.headers['helo_name'],
						   sender)

		return sig_str

	def get_action(self, cur=None):
		if not self.db_connection:
			if not self.db_connect():
				return None
		if self.db_connection:
			query_str = "SELECT status, action, count FROM active_greylist WHERE %s" % self._gl_sig()
			self._write_to_syslog("Querying database: \"%s\"" % query_str)
			if not cur:
				cur = self.db_connection.cursor()
			self.db_execute(cursor=cur, cmd=query_str)
			if cur.rowcount:
				self.db_write_mode = "UPDATE"
				row = cur.fetchone()
				self._write_to_syslog(LOG_INFO, "Action for signature %s: %s" \
					  % (self._gl_sig(format='LOG'), row[1]))
				self.db_info['status'] = row[0]
				self.db_info['action'] = row[1]
				self.db_info['count'] = row[2]
				return row[1]
		return None

	def get_interval(self, status='G', score=0, cur=None):

		def score2interval(option, score):
			interval_str = self.config.get('general', option)
			intervals = interval_str.split(',')
			if score >= len(intervals):
				interval = intervals[-1]
			else:
				interval = intervals[score]
			if interval[-1] == 'm':
				unit = "minutes"
			elif interval[-1] == 'h':
				unit = "hours"
			elif interval[-1] == 'd':
				unit = "days"
			elif interval[-1] == 'M':
				unit = "months"
			elif interval[-1] == 'y':
				unit = "years"
			return "%s %s" % (interval[:-1], unit)

		interval = ""
		if not self.db_connection:
			self.db_connect()
		query_str = "SELECT interval FROM greylist_senders WHERE sender='%s'" % self.headers['sender_domain']
		if not cur:
			cur = self.db_connection.cursor()
		self.db_execute(cursor=cur, cmd=query_str)
		if cur.rowcount:
			interval = cur.fetchone()[0]
			self.db_info['expiry_date'] = "current_timestamp + '%s'" % interval
			return interval
		if status == 'W':
			interval = score2interval('whitelist_intervals', score)
		else:
			interval = score2interval('greylist_intervals', score)
		self._write_to_syslog(LOG_INFO, 'Interval for signature %s: %s' % (self._gl_sig(format=', '), interval))
		self.db_info['expiry_date'] = "current_timestamp + '%s'" % interval

	def _handle_score(self, score, cur=None):
		self.db_info['score'] = score
		if score:
			self.db_info['status'] = "G"
			self.db_info['action'] = "DENY"
		else:
			self.db_info['status'] = "W"
			self.db_info['action'] = "ALLOW"
		self.get_interval(score=score)

	def write_to_db(self):

		def create_insert_str(info):
			info['client'] = self.headers['client_address']
			info['helo'] = self.headers['helo_name']
			info['sender'] = self.headers['sender_domain']
			info['count'] = 0
			order = info.keys()
			order_str = ','.join(order)
			values = list()
			for column in order:
				if column in ('last_activated', 'expiry_date'):
					values.append("%s" % db_info[column])
				else:
					values.append("'%s'" % db_info[column])
			value_str = ','.join(values)
			query_str = "INSERT INTO greylist (%s) VALUES(%s)" % (order_str, 
																  value_str)
			return query_str

		def create_update_str(info, sig):
			values = list()
			info['count'] += 1
			for column in info:
				if column in ('last_activated', 'expiry_date'):
					values.append("%s=%s" % (column, db_info[column]))
				else:
					values.append("%s='%s'" % (column, db_info[column]))
			value_str = ','.join(values)
			query_str = "UPDATE greylist SET %s where %s" % (value_str, sig)
			return query_str

		query_str = ""
		db_info = self.db_info
		score = 0
		if 'score' in db_info:
			score = db_info['score']
		action = db_info.pop('action')
		status = db_info['status']
		db_info['last_activated'] = 'current_timestamp'
		if action == 'ALLOW':
			if db_info['status'] == 'W':
				pass
			elif db_info['status'] == 'G':
				db_info['status'] = 'W'
				db_info['count'] = 0
				self.get_interval(status=db_info['status'], score=score)
		elif action == 'DENY':
			pass
		elif action == 'EXPIRED':
			self.get_interval(status=db_info['status'], score=score)
			db_info['count'] = 0
		if self.db_write_mode == 'INSERT':
			query_str = create_insert_str(db_info)
		else:
			query_str = create_update_str(db_info, self._gl_sig())
		if not self.db_connection:
			self.db_connect()
		cur = self.db_connection.cursor()
		self.db_execute(cursor=cur, cmd=query_str)
		self.db_connection.commit()

if __name__ == "__main__":
	gl = GLCandidate()
	gl.read_headers()
	action = gl.get_action()
	if action == 'ALLOW':
		print "action=DUNNO\n\n"
	elif action == 'DENY':
		print "action=%s" % gl.greylist_message
	elif not action or action == 'EXPIRED':
		gl.test_rbl()
		gl.test_spf()
		score = gl.rbl_score() + gl.spf_score()
		gl.db_info['score'] = score
		gl._handle_score(score)
	gl.write_to_db()

