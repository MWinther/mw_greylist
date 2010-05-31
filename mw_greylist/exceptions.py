class GLException(Exception):
	"Used to indicate Greylist Candidate errors."
	pass

class GLEndOfFunctionException(GLException):
	"Used to indicate end of function without catching circumstances."
	pass

class GLHeaderException(GLException):
	"Used to indicate incorrectly formatted header line."
	pass

class GLNoDBConnectionException(GLException):
	"Used to indicate inability to communicate with database."
	pass

class GLIncompleteHeaderException(GLException):
	"Used to indicate incomplete information in headers."
	pass

class GLPluginException(GLException):
	"Used to indicate something went wrong with one of the plugin checks."
	pass
