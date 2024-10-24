# ScaleModeController
# - Handles the scale play/edit modes
#
# Part of RefaceCPLiveControl
#
# Ableton Live MIDI Remote Script for the Yamaha Reface CP
#
# Author: Joan Duat
#
# Distributed under the MIT License, see LICENSE

import Live
import Live.Application
import Live.Song
from _Framework.ButtonElement import ButtonElement
from _Framework.InputControlElement import MIDI_NOTE_TYPE
from .Logger import Logger

class ScaleModeController:
    
    def __init__(self,
                 logger: Logger,
                 song: Live.Song.Song,
                 channel = 0,
                 root_note_button = None,
                 scale_mode_button = None
                 ):
        self._logger = logger
        self._enabled = False
        self._song = song
        self._channel = channel
        self._root_note_button = root_note_button
        self._scale_mode_button = scale_mode_button
        self._note_key_buttons = []
        self._pressed_keys = []
        self._current_root_note = -1
        self._current_scale_intervals = None
        self._all_scales = Live.Song.get_all_scales_ordered()
        self._setup_song_listeners()
        for index in range(128):
            button = ButtonElement(1, MIDI_NOTE_TYPE, self._channel, index)
            self._note_key_buttons.append(button)

    def set_enabled(self, enabled):
        """Enables/Disables the scale play mode."""
        if enabled:
            self.set_play_mode_enabled(True)
        else:
            self._remove_button_listeners()
            self._remove_note_key_listeners()

    def set_play_mode_enabled(self, enabled, enable_controls: bool = True):
        """Enables/Disables the scale play mode functionality."""
        self._enabled = enabled
        if enabled:
            # self._logger.log("Scale play mode enabled.")
            self._update_play_mode_key_listeners()
            self.set_controls_enabled(enable_controls)

    def set_controls_enabled(self, enabled):
        if enabled:
            self._setup_button_listeners()
        else:
            self._remove_button_listeners()

    def set_channel(self, channel):
        self._channel = channel
        for button in self._note_key_buttons:
            button.set_channel(channel)

    # Private
    
    def _setup_song_listeners(self):
        self._song.add_root_note_listener(self._on_root_note_changed)
        self._song.add_scale_intervals_listener(self._on_scale_intervals_changed)

    def _update_play_mode_key_listeners(self):
        """Updates the note key listeners so notes not corresponding to the current scale mode are captured by the script (thus silenced)"""
        root_note = self._song.root_note
        scale_intervals = self._song.scale_intervals
        if self._current_root_note == root_note and self._current_scale_intervals == scale_intervals:
            return

        self._logger.log(f"intervals: {list(scale_intervals)}")
        for midi_note in range(128):
            button = self._note_key_buttons[midi_note]
            is_matching = (12 + midi_note - root_note) % 12 in scale_intervals
            # self._logger.log(f"midi_note: {midi_note}, isMatching: {is_matching}")
            if is_matching:
                if button.value_has_listener(self._on_note_key):
                    button.remove_value_listener(self._on_note_key)
            else:
                button.add_value_listener(self._on_note_key, identify_sender=True)

    def _remove_note_key_listeners(self):
        for button in self._note_key_buttons:
            if button.value_has_listener(self._on_note_key):
                button.remove_value_listener(self._on_note_key)
        self._pressed_keys = []

    def _setup_button_listeners(self):
        if self._root_note_button and not self._root_note_button.value_has_listener(self._on_root_note_button_changed):
            self._root_note_button.add_value_listener(self._on_root_note_button_changed)
        if self._scale_mode_button and not self._scale_mode_button.value_has_listener(self._on_scale_mode_button_changed):
            self._scale_mode_button.add_value_listener(self._on_scale_mode_button_changed)

    def _remove_button_listeners(self):
        if self._root_note_button and self._root_note_button.value_has_listener(self._on_root_note_button_changed):
            self._root_note_button.remove_value_listener(self._on_root_note_button_changed)
        if self._scale_mode_button and self._scale_mode_button.value_has_listener(self._on_scale_mode_button_changed):
            self._scale_mode_button.remove_value_listener(self._on_scale_mode_button_changed)

    def _on_root_note_button_changed(self, value):
        total_notes = 12
        note = int((value / 127.0) * (total_notes - 1))
        if note != self._song.root_note:
            self._song.root_note = note

    def _on_scale_mode_button_changed(self, value):
        total_scales = len(self._all_scales)
        scale_index = int((value / 127.0) * (total_scales - 1))
        self._song.scale_name = self._all_scales[scale_index][0]

    def _on_root_note_changed(self):
        if self._enabled:
            self._update_play_mode_key_listeners()
        self._current_root_note = self._song.root_note
        
    def _on_scale_intervals_changed(self):
        if self._enabled:
            self._update_play_mode_key_listeners()
        self._current_scale_intervals = self._song.scale_intervals

    def _on_note_key(self, value, sender):
        return
        key = sender._msg_identifier
        if value > 0:
            self._pressed_keys.append(key)
        else:
            self._pressed_keys.remove(key)
        # self._logger.log(f"Note: {key}")

    def disconnect(self):
        self._remove_button_listeners()
        self._remove_note_key_listeners()
        self._song.remove_root_note_listener(self._on_root_note_changed)
        self._song.remove_scale_intervals_listener(self._on_scale_intervals_changed)
        self._note_key_buttons = []