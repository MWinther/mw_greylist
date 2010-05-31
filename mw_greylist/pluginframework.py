class PluginMount(type):
	def __init__(cls, name, bases, attrs):
		if not hasattr(cls, 'plugins'):
			cls.plugins = []
		else:
			cls.plugins.append(cls)

class ActionProvider:
	__metaclass__ = PluginMount

#from mw_greylist.plugins import *

#for action in ActionProvider.plugins:
#	action.perform('foo')
