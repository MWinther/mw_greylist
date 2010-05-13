import mwgl2
from syslog import *

gl = mwgl2.GLCandidate()
gl.read_headers("test/header_file.txt")
action = gl.get_action()
if action == 'ALLOW':
	print "action=DUNNO\n\n"
if action == 'DENY':
	print "action=%s" % gl.greylist_message
if not action or action == 'EXPIRED':
	gl.test_rbl()
	gl.test_spf()
	print gl.rbl_results
	print gl.spf_result
	score = gl.rbl_score() + gl.spf_score()
	gl.db_info['score'] = score
	gl._handle_score(score)
gl.write_to_db()
