import ConfigParser
from syslog import LOG_DEBUG, LOG_INFO, LOG_ERR
from os import getenv, path
from mw_greylist.exceptions import *
from mw_greylist.log import Log
from datetime import datetime, timedelta

class Settings(object):

    def __init__(self, conf_file=None):
        self.conf_file = conf_file
        self.file_settings = ConfigParser.ConfigParser()
        log.open()
        if conf_file != None:
            log.write('Config file %s supplied as argument.' % conf_file, LOG_DEBUG)
            if path.isfile(conf_file):
                self.conf_file = conf_file
            else:
                # If supplying a config file, default value should be to exit if
                # that file doesn't exist.
                log.write("Supplied config file %s doesn't exist." % conf_file,
                              LOG_ERR)
                raise GLInvalidConfigFileException, "%s doesn't exist."
        else:
            self.conf_file = self.get_config_file()
        if self.conf_file:
            log.write("Found config file %s." % self.conf_file, LOG_DEBUG)
            self.file_settings.read(self.conf_file)
        else:
            log.write("No config file found. Using defaults.", LOG_DEBUG)
        self.session_id_length = int(self.get_setting(6, 'session_id_length'))
        default_message = '450 Temporarily inaccessible, try again later.'
        self.greylist_message =\
                self.get_setting(default_message, 'greylist_message')
        self.connection_url = self.get_setting('sqlite:///mw_greylist.db',
                                               'connection_url')
        self.greylist_intervals = self.get_setting('2m', 'greylist_intervals')
        self.whitelist_intervals = self.get_setting('1M', 'whitelist_intervals')
        self.log_dest = self.get_setting('syslog', 'log_dest')
        self.log_debug_messages = self.get_setting('yes', 'log_debug_messages')
        self.now = datetime.now()
        self.session_id = None

    def get_config_file(self):
        filename = 'mw_greylist'
        # Special case for home directory, where file should be a dotfile.
        locations = ["%s/.%s" % (getenv('HOME'), filename)]
        std_locations = ['/etc/postfix',
                         '/etc/mail',
                         '/etc']
        for location in std_locations:
            locations.append("%s/%s" % (location, filename))

        for location in locations:
            if path.isfile(location):
                return location
        return None

    def get_setting(self, default, option, section='general'):
        # If settings are available in the ConfigParser, return
        # those. If not, return the default value.
        if self.file_settings.has_option(section, option):
            value = self.file_settings.get(section, option)
            log.write("Option %s found in section %s of config file, setting to %s"\
                        % (option, section, value), LOG_DEBUG)
            return value 
        else:
            log.write("Option %s not found in config file, using default value %s"\
                        % (option, default), LOG_DEBUG)
            return default

    def whitelist_expiry(self, score):
        intervals = self.whitelist_intervals.split(',')
        if score < len(intervals):
            interval = intervals[score]
        else:
            interval = intervals[-1]
        return self.now + self.mk_timedelta(interval)

    def greylist_expiry(self, score):
        intervals = self.greylist_intervals.split(',')
        if score < len(intervals):
            interval = intervals[score-1]
        else:
            interval = intervals[-1]
        return self.now + self.mk_timedelta(interval)

    def mk_timedelta(self, interval):
        # Takes an interval string and returns a timedelta object.
        unit = interval[-1]
        if unit not in ['s', 'm', 'h', 'd', 'w', 'M', 'y']:
            raise ValueError, "Incorrect interval '%s'" % interval
        value = int(interval[0:-1])
        if unit == 's': return timedelta(seconds=value)
        if unit == 'm': return timedelta(minutes=value)
        if unit == 'h': return timedelta(hours=value)
        if unit == 'd': return timedelta(days=value)
        if unit == 'w': return timedelta(weeks=value)
        if unit == 'M': return timedelta(days=value*30)
        if unit == 'y': return timedelta(days=value*365)
            
log = Log()

