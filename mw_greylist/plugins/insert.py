from mw_greylist.pluginframework import ActionProvider

class Insert(ActionProvider):
	@staticmethod
	def perform(var):
		print "Insert.perform(%s)" % var

class Update(ActionProvider):
	@staticmethod
	def perform(var):
		print "Update.perform(%s)" % var
