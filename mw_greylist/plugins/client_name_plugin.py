from mw_greylist.pluginframework import ActionProvider
from mw_greylist.exceptions import *
from mw_greylist.log import Log
from syslog import *
import socket

class ClientName(ActionProvider):

    def __init__(self, headers={}, settings=None):
        self.headers = headers
        self.settings = settings
        self.msg_prio = None
        self.message = ""
	self.score = 0

    def __repr__(self):
        return "Client Name plugin v1.0b for mw_greylist"

    def do_test(self):
	score = 0
	if 'client_name' and 'reverse_client_name' in self.headers:
	    name = self.headers['client_name'];
	    reverse = self.headers['reverse_client_name'];
	else:
	    log.write("Client name or reverse client name missing.", 
	              LOG_WARNING) 
	    raise GLPluginException, "Incomplete headers."

	if name == 'unknown':
	    score += 1
	if reverse == 'unknown':
	    score += 1
	if name != reverse:
	    score += 1
	self.score = score

    def get_score(self):
        log.write("Client name score: %d" % self.score, LOG_DEBUG)
        return self.score

log = Log()
