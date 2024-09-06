# RotaryToggleElement
#
# Part of RefaceCPLiveControl
#
# Ableton Live MIDI Remote Script for the Yamaha Reface CP
#
# Author: Joan Duat
#
# Distributed under the MIT License, see LICENSE

import Live
from _Framework.ButtonElement import *

class RotaryToggleElement(ButtonElement):
    """
    Rotary element that acts as a toggle button. Turning to each direction toggles on/off regardless of the value.
    """
    def __init__(self, is_momentary, msg_type, channel, identifier, reverse=False):
        ButtonElement.__init__(self, is_momentary, msg_type, channel, identifier)
        self._value = 0
        self._last_sent = 0
        self._reverse = reverse

    def _compare(self, value):
        if self._reverse:
            return (value - self._value) > 0
        else:
            return (value - self._value) < 0

    def receive_value(self, value):
        if value != self._value:
            if self._compare(value) and self._last_sent == 1:
                self._last_sent = 0
                super().receive_value(0)
            elif not self._compare(value) and self._last_sent == 0:
                self._last_sent = 1
                super().receive_value(1)
            self._value = value

    def turn_on(self):
        self._last_sent = 1

    def turn_off(self):
        self._last_sent = 0
