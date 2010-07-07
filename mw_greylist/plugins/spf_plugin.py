from mw_greylist.pluginframework import ActionProvider
from mw_greylist.exceptions import *
from mw_greylist.log import Log
from syslog import *
import socket
import spf

class SPF(ActionProvider):

    def __init__(self, headers={}, settings=None):
        self.headers = headers
        self.settings = settings
        self.result = {'action': None}
        self.msg_prio = None
        self.message = ""

    def __repr__(self):
        return "SPF plugin v1.0b for mw_greylist"

    def do_test(self):
        if 'client_address' and 'helo_name' and 'sender' in self.headers:
            results = spf.check(i=self.headers['client_address'], 
                                h=self.headers['helo_name'], 
                                s=self.headers['sender'], 
                                receiver=socket.gethostname())
            self.result['action'] = results[0]
            self.result['code'] = results[1]
            self.result['message'] = results[2]
            log.write("SPF check returns action='%s', code='%s', message='%s'"\
                        % (results[0], results[1], results[2]), LOG_DEBUG)
            return results
        else:
            log.write("Client address, helo name or sender missing from headers.",
                      LOG_WARNING)
            raise GLPluginException, "Incomplete headers."

    def get_score(self):
        action = self.result['action']
        score = None
        if action == None:
            score = None
        elif action == 'pass':
            score = 0
        elif action == 'none':
            score = 1
        elif action == 'neutral':
            score = 1
        elif action == 'softfail':
            score = 2
        elif action == 'fail':
            score = 3
        elif action == 'unknown':
            score = 1
        elif action == 'temperror':
            score = 1
        else:
            raise GLPluginException, "Unexpected SPF result: got '%s'" % action
        if score == None:
            log.write("SPF score: None", LOG_DEBUG)
        else:
            log.write("SPF score: %d" % score, LOG_DEBUG)
        return score

log = Log()
