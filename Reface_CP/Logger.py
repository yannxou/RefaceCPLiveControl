class Logger:
	def __init__(self, c_instance):
		self._enabled = True
		self._c_instance = c_instance

	def log(self, message):
		if self._enabled:
			self._c_instance.log_message(message)

	def show_message(self, message):
		self._c_instance.show_message(message)
		if self._enabled:
			self._c_instance.log_message(message)