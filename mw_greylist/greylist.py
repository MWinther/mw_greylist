from mw_greylist.settings import Settings
from mw_greylist.glcandidate import GLCandidate
from mw_greylist.glentry import GLEntry
#from mw_greylist.pluginframework import ActionProvider
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sys import stdout

settings = Settings()
engine = create_engine(settings.connection_url)
Session = sessionmaker(bind=engine)
session = Session()
candidate = GLCandidate(settings, session)
#candidate.plugins = ActionProvider.plugins
candidate.read_headers('mw_greylist/test/header_file.txt')
print candidate.perform_action()
session.commit()

#gl = GLCandidate()
#gl.plugins = ActionProvider.plugins
#gl.read_headers("mw_greylist/test/header_file.txt")
#for action in gl.tests:
#    action.perform('bar')
#action = gl.get_action()
#if action == 'ALLOW':
#    print "action=DUNNO\n\n"
#if action == 'DENY':
#    print "action=%s" % gl.greylist_message
#if not action or action == 'EXPIRED':
#    gl.do_tests()
#    gl.test_rbl()
#    gl.test_spf()
#    print gl.rbl_results
#    print gl.spf_result
#    score = gl.rbl_score() + gl.spf_score()
#    gl.db_info['score'] = score
#    gl._handle_score(score)

#session = sessionmaker(bind=engine)
