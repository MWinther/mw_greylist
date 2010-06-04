from mw_greylist.pluginframework import ActionProvider
from mw_greylist.exceptions import *
from syslog import *
import socket
import spf

class SPF(ActionProvider):

    def __init__(self, headers={}):
        self.headers = headers
        self.result = {'action': None}
        self.msg_prio = None
        self.message = ""

    def do_test(self):
        if 'client_address' and 'helo_name' and 'sender' in self.headers:
            results = spf.check(i=self.headers['client_address'], 
                                h=self.headers['helo_name'], 
                                s=self.headers['sender'], 
                                receiver=socket.gethostname())
            self.result['action'] = results[0]
            self.result['code'] = results[1]
            self.result['message'] = results[2]
            self.message = "SPF check returns action='%s', code='%s', message='%s'" % (results[0], results[1], results[2])
            self.msg_prio = LOG_INFO
            return results
        else:
            self.message = "Client address, helo name or sender missing from headers."
            self.msg_prio = LOG_WARNING
            raise GLIncompleteHeaderException, "Incomplete headers."

    def get_score(self):
        action = self.result['action']
        if action == None:
            return None
        if action == 'pass':
            return 0
        if action == 'none':
            return 1
        if action == 'softfail':
            return 2
        if action == 'fail':
            return 3
        raise GLPluginException, "Unexpected SPF result: got '%s'" % action
