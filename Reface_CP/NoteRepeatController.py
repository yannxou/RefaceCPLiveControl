# NoteRepeatController
# - Handles note repeat functionality
#
# Part of RefaceCPLiveControl
#
# Ableton Live MIDI Remote Script for the Yamaha Reface CP
#
# Author: Joan Duat
#
# Distributed under the MIT License, see LICENSE

import math
import threading
import time
import Live
import Live.Application
import Live.Song
from .Logger import Logger
from _Framework.ButtonElement import ButtonElement
from _Framework.InputControlElement import MIDI_CC_TYPE

def _frequency_to_repeat_rate(frequency):
    return 1.0 / frequency * 4.0

NOTE_REPEAT_RATES = list(map(_frequency_to_repeat_rate, [32*1.5, 32, 16*1.5, 16, 8*1.5, 8, 4*1.5, 4]))
DEFAULT_INDEX = 5
DEFAULT_RATE = NOTE_REPEAT_RATES[DEFAULT_INDEX]

class NoteRepeatController:
    
    def __init__(self,
                 logger: Logger, 
                 note_repeat, 
                 repeat_rate_button = None
                 ):
        self._logger = logger
        self._note_repeat = note_repeat
        self._enabled = False
        self._repeat_rate_button = repeat_rate_button

    def set_enabled(self, enabled):
        if self._enabled == enabled:
            return
        if enabled:
            self._setup_button_listeners()
        else:
            self._disable_button_listeners()
        self._note_repeat.enabled = enabled
        self._enabled = enabled

    def _setup_button_listeners(self):
        if self._repeat_rate_button:
            self._repeat_rate_button.add_value_listener(self._on_repeat_rate_button_changed)

    def _disable_button_listeners(self):
        if self._repeat_rate_button:
            self._repeat_rate_button.remove_value_listener(self._on_repeat_rate_button_changed)

    def _on_repeat_rate_button_changed(self, value):
        total_rates = len(NOTE_REPEAT_RATES)
        rate_index = int((value / 127.0) * (total_rates - 1))
        self._logger.log(f"Repeat rate {rate_index}. value: {NOTE_REPEAT_RATES[rate_index]}")
        self._note_repeat.repeat_rate = NOTE_REPEAT_RATES[rate_index]

    def disconnect(self):
        self._disable_button_listeners()