from mw_greylist.glcandidate import GLCandidate
from mw_greylist.pluginframework import ActionProvider

gl = GLCandidate()
gl.tests = ActionProvider.plugins
gl.read_headers("mw_greylist/test/header_file.txt")
#for action in gl.tests:
#	action.perform('bar')
#action = gl.get_action()
if action == 'ALLOW':
	print "action=DUNNO\n\n"
#if action == 'DENY':
#	print "action=%s" % gl.greylist_message
if not action or action == 'EXPIRED':
	gl.run_tests()
#	gl.test_rbl()
#	gl.test_spf()
#	print gl.rbl_results
#	print gl.spf_result
#	score = gl.rbl_score() + gl.spf_score()
#	gl.db_info['score'] = score
#	gl._handle_score(score)
