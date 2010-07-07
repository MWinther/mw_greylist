from syslog import *
import sys

class Log(object):

    def __init__(self):
        self.facility = LOG_MAIL
        self.log_debug_messages = True
        self.session_id = None
            
    def open(self):
        #openlog(sys.argv[0].split('/')[-1], 0, self.facility)
        openlog('mw_greylist', 0, self.facility)
        if self.log_debug_messages == False:
            setlogmask(LOG_UPTO(LOG_INFO))

    def write(self, message, level=LOG_INFO):
        if self.session_id:
            syslog(level, "%s: %s" % (self.session_id, message))
        else:
            syslog(level, message)

    def close(self):
        closelog()
