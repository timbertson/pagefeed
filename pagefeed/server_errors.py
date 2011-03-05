class HttpError(Exception):
	def __init__(self, code, content=''):
		self.code = code
		self.content = content
		super(HttpError, self).__init__(code, content)

class RedirectError(Exception):
	def __init__(self, target):
		self.target = target
		super(HttpError, self).__init__(target)

