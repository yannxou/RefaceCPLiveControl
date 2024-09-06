# Logger
# - Simple logger to pass around other classes
#
# Part of RefaceCPLiveControl
#
# Ableton Live MIDI Remote Script for the Yamaha Reface CP
#
# Author: Joan Duat
#
# Distributed under the MIT License, see LICENSE

from .Settings import *

class Logger:
	def __init__(self, c_instance):
		self._enabled = DEBUG_ENABLED
		self._c_instance = c_instance

	def log(self, message):
		if self._enabled:
			self._c_instance.log_message(message)

	def show_message(self, message):
		self._c_instance.show_message(message)
		if self._enabled:
			self._c_instance.log_message(message)