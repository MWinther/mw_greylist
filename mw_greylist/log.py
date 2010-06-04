from syslog import *
import sys

class Log(object):

    def __init__(self, settings):
        self.destination = settings.log_dest
        self.session_id = settings.session_id
        self.facility = LOG_MAIL
        if self.destination != 'syslog':
            self.filehandle = None
        if settings.log_debug_messages == 'yes':
            self.log_debug_messages = True
        else:
            self.log_debug_messages = False
            
    def open(self):
        if self.destination == 'syslog':
            openlog(sys.argv[0].split('/')[-1], 0, self.facility)
        if self.log_debug_messages == False:
            setlogmask(LOG_UPTO(LOG_INFO))

    def write(self, message, level=LOG_INFO):
        if self.destination == 'syslog':
            syslog(level, "%s: %s" % (self.session_id, message))

    def close(self):
        if self.destination == 'syslog':
            closelog()
