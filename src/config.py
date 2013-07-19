import ConfigParser
import os.path

class Config(ConfigParser.RawConfigParser):
	CONFIG_FILE_LOCATION = '.twicli'
	use_new_super = False
	def __init__(self):
		# Call the parent constructor.
		self.use_new_super = issubclass(ConfigParser.RawConfigParser().__class__, object)
		if self.use_new_super:
			super(Config, self).__init__(allow_no_value=True)
		else:
			ConfigParser.RawConfigParser.__init__(self, allow_no_value=True)

		# Prefix the user's home directory.
		self.CONFIG_FILE_LOCATION = os.path.expanduser('~') + '/' + self.CONFIG_FILE_LOCATION

		if not os.path.exists(self.CONFIG_FILE_LOCATION):
			# Create a default configuration file.
			self.add_section('app')
			self.set('app', 'key', '')
			self.set('app', 'secret', '')
			self.add_section('auth')
			self.set('auth', 'token', '')
			self.set('auth', 'secret', '')
		else:
			# Read the configuration file.
			self.read(self.CONFIG_FILE_LOCATION)

	def set(self, section, option, value):
		if self.use_new_super:
			super(Config, self).set(section, option, value)
		else:
			ConfigParser.RawConfigParser.set(self, section, option, value)
		self.save()

	def save(self):
		# Write out the configuration file.
		with open(self.CONFIG_FILE_LOCATION, 'wb') as configfile:
			self.write(configfile)
