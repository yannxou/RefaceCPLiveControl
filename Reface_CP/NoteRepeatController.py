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

NOTE_REPEAT_RATES = list(map(_frequency_to_repeat_rate, [32*1.5, 32, 16*1.5, 16, 8*1.5, 8, 4*1.5, 4, 2*1.5, 2, 1]))
NOTE_REPEAT_NAMES = ["1/32T", "1/32", "1/16T", "1/16", "1/8T", "1/8", "1/4T", "1/4", "1/2T", "1/2", "1 Bar"]
DEFAULT_INDEX = 5
DEFAULT_RATE = NOTE_REPEAT_RATES[DEFAULT_INDEX]

MIN_NOTES_PER_BEAT = 0.25
MAX_NOTES_PER_BEAT = 16

class NoteRepeatController:
    
    def __init__(self,
                 logger: Logger, 
                 note_repeat, 
                 repeat_rate_button = None,
                 notes_per_bar_button = None,
                 ):
        self._logger = logger
        self._note_repeat = note_repeat
        self._enabled = False
        self._repeat_rate_button = repeat_rate_button
        self._notes_per_bar_button = notes_per_bar_button

    def set_enabled(self, enabled):
        """Enables/Disables the note repeat functionality."""
        self._note_repeat.enabled = enabled
        self._enabled = enabled
        self.set_controls_enabled(enabled)

    def set_controls_enabled(self, enabled):
        """Enables the buttons for controlling the note repeat parameters."""
        if enabled and self._enabled:
            self._setup_button_listeners()
        else:
            self._disable_button_listeners()

    def _setup_button_listeners(self):
        if self._repeat_rate_button and not self._repeat_rate_button.value_has_listener(self._on_repeat_rate_button_changed):
            self._repeat_rate_button.add_value_listener(self._on_repeat_rate_button_changed)
        if self._notes_per_bar_button and not self._notes_per_bar_button.value_has_listener(self._on_notes_per_bar_button_changed):
            self._notes_per_bar_button.add_value_listener(self._on_notes_per_bar_button_changed)

    def _disable_button_listeners(self):
        if self._repeat_rate_button and self._repeat_rate_button.value_has_listener(self._on_repeat_rate_button_changed):
            self._repeat_rate_button.remove_value_listener(self._on_repeat_rate_button_changed)
        if self._notes_per_bar_button and self._notes_per_bar_button.value_has_listener(self._on_notes_per_bar_button_changed):
            self._notes_per_bar_button.remove_value_listener(self._on_notes_per_bar_button_changed)

    def _on_repeat_rate_button_changed(self, value):
        total_rates = len(NOTE_REPEAT_RATES)
        rate_index = int((value / 127.0) * (total_rates - 1))
        self._note_repeat.repeat_rate = NOTE_REPEAT_RATES[rate_index]
        self._logger.show_message(f"Note rate: {NOTE_REPEAT_NAMES[rate_index]}")

    def _on_notes_per_bar_button_changed(self, midi_value):
        value = int(4*MAX_NOTES_PER_BEAT + (midi_value / 127) * 4 * (MIN_NOTES_PER_BEAT - MAX_NOTES_PER_BEAT))
        rate = (1/value) * 4
        self._note_repeat.repeat_rate = rate
        self._logger.show_message(f"Note rate: {value} notes/bar")

    def disconnect(self):
        self._disable_button_listeners()