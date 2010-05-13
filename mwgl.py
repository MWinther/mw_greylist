from syslog import *
import sys
import psycopg2
import time
from rbl import check_rbl_like
import spf
import socket

def check_rbls(server):
	syslog(LOG_DEBUG|LOG_MAIL, "Starting RBL checks")
	rbls = ['problems.dnsbl.sorbs.net',
			'dul.dnsbl.sorbs.net',
			'rhsbl.sorbs.net',
			'bl.csma.biz',
			'sbl.csma.biz',
			'0spam.fusionzero.com',
			'0spam-killlist.fusionzero.com',
			'dnsbl-1.uceprotect.net',
			'ips.backscatterer.org']
	score = 0
	for rbl in rbls:
		result = check_rbl_like(server, root_name=rbl, yes_addr=None)
		if(not result):
			score = score + 1

#	fh = open('/tmp/mwgl.out', 'a')
#	fh.write('RBL score for %s: %d\n' % (server, score))
#	fh.close()
	syslog(LOG_MAIL|LOG_DEBUG, "RBL score for %s: %d" % (server, score))
	return score

def check_spf(client="", helo="", sender=""):
	results = spf.check(i=client, h=helo, s=sender, receiver=socket.gethostname())
	if results[0] == 'pass':
		syslog(LOG_MAIL|LOG_DEBUG, 'SPF check for signature client=%s, helo=%s, sender=%s passed.' % client, helo, sender)
		return 0
	else:
		if results[2]:
			log_str = "SPF check for signature client=%s, helo=%s, sender=%s returned '%s: %s'" % (client, helo, sender, results[0], results[2])
		else:
			log_str = "SPF check for signature client=%s, helo=%s, sender=%s returned '%s'" % (client, helo, sender, results[0])
		syslog(LOG_MAIL|LOG_DEBUG, log_str)
		return 1

def connect(dbname="postfix", dbuser="postfix",
			password=""):
	conn_str = "dbname='%s' user='%s' password='%s'" % (dbname, dbuser, password)
	try:
		conn = psycopg2.connect(conn_str);
	except Exception, e:
		syslog(LOG_MAIL|LOG_ERR, "Failed to connect to database: %s" % e)
		return None
	syslog(LOG_MAIL|LOG_DEBUG, "Connected to database.")
	return conn

def set_greylist(conn=None, client="", helo="", sender="", status="G", interval="2 minutes"):
	if (conn == None):
		return False
	else:
		count, dbstatus = get_count(conn, client=client, helo=helo, sender=sender)
		if count != None:
			count = count + 1
		if dbstatus == 'G':
			syslog(LOG_MAIL|LOG_DEBUG, "Updating database for signature client=%s, helo=%s, sender=%s to status=%s (%s), count=%d, interval=%s" % (client, helo, sender, status, dbstatus, count, interval))
			insert_str = "UPDATE greylist SET status='%s', last_activated=current_timestamp, expiry_date=current_timestamp + interval '%s', count='%s' WHERE client='%s' AND helo='%s' AND sender='%s'" % (status, interval, count, client, helo, sender)
		if dbstatus == 'W':
			syslog(LOG_MAIL|LOG_DEBUG, "Signature client=%s, helo=%s, sender=%s already whitelisted, incrementing hit count to %d" % (client, helo, sender, count))
			insert_str = "UPDATE greylist SET last_activated=current_timestamp, count=%d WHERE client='%s' AND helo='%s' AND sender='%s'" % (count, client, helo, sender)
		if dbstatus == None:
			syslog(LOG_MAIL|LOG_DEBUG, "Adding signature client=%s, helo=%s, sender=%s to database with status=%s, interval=%s" % (client, helo, sender, status, interval))
			insert_str = "INSERT INTO greylist (client, helo, sender, status, last_activated, expiry_date, count) VALUES ('%s', '%s', '%s', '%s', current_timestamp, current_timestamp + interval '%s', 0)" % (client, helo, sender, status, interval)
		cur = conn.cursor()
		cur.execute(insert_str)
		conn.commit()
	return True

def get_action(conn=None, client="", helo="", sender="", qid=""):
	if (conn == None):
		return "?"
	else:
		query_str = "SELECT action FROM active_greylist WHERE client='%s' AND helo='%s' AND sender='%s'" % (client, helo, sender)
		cur = conn.cursor()
		cur.execute(query_str)
		results = cur.fetchall()
		if len(results):
			syslog(LOG_MAIL|LOG_NOTICE, "Action for client=%s, helo=%s, sender=%s: %s" % (client, helo, sender, results[0][0]))
			return results[0][0]
		else:
			syslog(LOG_MAIL|LOG_DEBUG, "Signature client=%s, helo=%s, sender=%s not found in database." % (client, helo, sender))
			return "?"
	return "?"

def get_count(conn=None, client="", helo="", sender=""):
	if (conn == None):
		return -1
	query_str = "SELECT count, status FROM greylist WHERE client='%s' AND helo='%s' AND sender='%s'" % (client, helo, sender)
	cur = conn.cursor()
	cur.execute(query_str)
	results = cur.fetchall()
	if len(results):
		syslog(LOG_MAIL|LOG_DEBUG, "Status for client=%s, helo=%s, sender=%s: count=%d, status=%s" % (client, helo, sender, results[0][0], results[0][1]))
		return results[0]
	else:
		syslog(LOG_MAIL|LOG_DEBUG, "Signature client=%s, helo=%s, sender=%s not found in database." % (client, helo, sender))
		return [None, None]

if __name__ == "__main__":
	openlog(sys.argv[0].split('/')[-1], LOG_MAIL)
	conn = connect(password="n(x9v0Q>JMki")
	if (conn == None):
		print "action=DUNNO\n\n"
		sys.exit(0)
	headers = {}
	line = "input"
	while line:
		line = sys.stdin.readline()
		line = line.strip()
		if line:
			components = line.split('=')
			if (len(components) == 2):
				name, value = components
			else:
				name = components[0]
				value = '='.join(components[1:])
			headers[name] = value.strip()
		else:
			break

	headers['sender_domain'] = headers['sender'].split('@')[-1]
	action = get_action(conn,
				  		client=headers['client_address'],
				  		helo=headers['helo_name'],
				  		sender=headers['sender_domain'],
				  		)
	if (action == "ALLOW"):
		print "action=DUNNO\n\n"
		set_greylist(conn=conn,
	                 client=headers['client_address'],
	                 helo=headers['helo_name'],
                     sender=headers['sender_domain'],
	                 status='W', interval='30 days')
		syslog(LOG_MAIL|LOG_DEBUG, "Signature client=%s, helo=%s, sender=%s whitelisted." % (headers['client_address'], headers['helo_name'], headers['sender_domain']))
		sys.exit(0)
	if (action == "DENY"):
		syslog(LOG_MAIL|LOG_NOTICE, "%s: Signature client=%s, helo=%s, sender=%s temporarily rejected." % (headers['queue_id'], headers['client_address'], headers['helo_name'], headers['sender_domain']))
		print "action=450 Temporarily unaccessible, try again later.\n\n"
		sys.exit(0)
	total_score = 0
	score = check_rbls(headers['client_address'])
	total_score = score
	score = check_spf(client=headers['client_address'],
					  helo=headers['helo_name'],
					  sender=headers['sender_domain'])
	total_score += score
	if total_score:
		status = "G"
		interval = "2 minutes"
		syslog(LOG_MAIL|LOG_NOTICE, "%s: Signature client=%s, helo=%s, sender=%s received a total score of %d. Greylisting for %s." % (headers['queue_id'], headers['client_address'], headers['helo_name'], headers['sender_domain'], total_score, interval))
		print "action=450 Temporarily unaccessible, try again later.\n\n"
	else:
		status = "W"
		interval = "30 days"
		syslog(LOG_MAIL|LOG_NOTICE, "Signature client=%s, helo=%s, sender=%s passed all tests. Whitelisting for %s." % (headers['client_address'], headers['helo_name'], headers['sender_domain'], interval))
		print "action=DUNNO\n\n"
	set_greylist(conn=conn,
			  	 client=headers['client_address'],
			  	 helo=headers['helo_name'],
			  	 sender=headers['sender_domain'],
				 status=status, interval=interval)
	closelog()
