import ConfigParser
from os import getenv, path
from mw_greylist.exceptions import *

class Settings(object):

	def __init__(self, conf_file=None):
		self.session_id_length = 6
		self.greylist_message = '450 Temporarily inaccessible, try again later.\n\n'
		self.connection_url = 'sqlite:///mw_greylist.db'
		if conf_file != None:
			if path.isfile(conf_file):
				self.conf_file = conf_file
			else:
				# If supplying a config file, default value should be to exit if
				# that file doesn't exist.
				raise GLInvalidConfigFileException, "%s doesn't exist."
		else:
			self.conf_file = self.get_config_file()
		if self.conf_file:
			self.file_settings = ConfigParser.ConfigParser()
			file_content = self.file_settings.read(conf_file)
			if file_content:
				if self.file_settings.has_option('general', 'session_id_length'):
					self.session_id_length = \
						  self.file_settings.getint('general',
											 'session_id_length')
				if self.file_settings.has_option('general', 'greylist_message'):
					self.greylist_message = self.file_settings.get('general', 
															'greylist_message')
					self.greylist_message = "%s\n\n" % self.greylist_message
				if self.file_settings.has_option('general', 'connection_url'):
					self.connection_url = self.file_settings.get('general',
																 'connection_url')
		else:
			# FIXME: Write message to syslog about using defaults.
			pass

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

