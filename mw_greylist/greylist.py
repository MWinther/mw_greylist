from mw_greylist.glcandidate import GLCandidate
from mw_greylist.glentry import GLEntry
from mw_greylist.pluginframework import ActionProvider
from sqlalchemy import create_engine
from sys import stdout

engine = create_engine('sqlite:////tmp/alch_test.db', echo=True)

#settings = Settings()
#connection = Connection()
#candidate = GLCandidate(connection, settings)
#candidate.plugins = ActionProvider.plugins
#candidate.read_headers('mw_greylist/test/header_file.txt')
#print candidate.perform_action()

gl = GLCandidate()
gl.plugins = ActionProvider.plugins
gl.read_headers("mw_greylist/test/header_file.txt")
#for action in gl.tests:
#	action.perform('bar')
action = gl.get_action()
if action == 'ALLOW':
	print "action=DUNNO\n\n"
#if action == 'DENY':
#	print "action=%s" % gl.greylist_message
if not action or action == 'EXPIRED':
	gl.do_tests()
#	gl.test_rbl()
#	gl.test_spf()
#	print gl.rbl_results
#	print gl.spf_result
#	score = gl.rbl_score() + gl.spf_score()
#	gl.db_info['score'] = score
#	gl._handle_score(score)

#session = sessionmaker(bind=engine)
