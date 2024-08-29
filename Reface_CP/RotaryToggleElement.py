import Live
from _Framework.ButtonElement import *

class RotaryToggleElement(ButtonElement):
    """
    Rotary element that acts as a toggle button. Turning to each direction toggles on/off regardless of the value.
    """
    def __init__(self, is_momentary, msg_type, channel, identifier):
        ButtonElement.__init__(self, is_momentary, msg_type, 15, identifier)
        self._value = 0
        self._last_sent = 0
        self._source_button = ButtonElement(is_momentary, msg_type, channel, identifier)
        self._source_button.add_value_listener(self._on_source_value_changed)

    def _on_source_value_changed(self, value):
        if (value - self._value) < 0 and self._last_sent == 1:
            self._last_sent = 0
            super().receive_value(0)
        elif (value - self._value) > 0 and self._last_sent == 0:
            self._last_sent = 1
            super().receive_value(1)
        self._value = value
        
    def set_channel(self, channel):
        self._source_button.set_channel(channel)

    def receive_value(self, value):
        super().receive_value(value)

    def turn_on(self):
        self._last_sent = 1

    def turn_off(self):
        self._last_sent = 0

    def disconnect(self):
        self._source_button.remove_value_listener(self._on_source_value_changed)


