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
from .Note import Note

class ScaleModeController:
    
    def __init__(self,
                 logger: Logger,
                 song: Live.Song.Song,
                 channel = 0,
                 root_note_button = None,
                 scale_mode_button = None,
                 edit_mode_button = None,
                 on_edit_mode_changed = None,
                 on_note_event = None
                 ):
        self._logger = logger
        self._enabled = False
        self._edit_mode_enabled = False
        self._song = song
        self._channel = channel
        self._root_note_button = root_note_button
        self._scale_mode_button = scale_mode_button
        self._edit_mode_button = edit_mode_button
        self._on_edit_mode_changed = on_edit_mode_changed
        self._on_note_event = on_note_event
        self._note_key_buttons = []
        self._pressed_keys = []
        self._captured_notes = set()  # Set of pitches (0..11) captured during scale edit
        self._custom_matching_scales = []
        self._current_root_note = -1
        self._current_scale_intervals = None
        self._all_scales = Live.Song.get_all_scales_ordered()
        self._setup_song_listeners()
        for index in range(128):
            button = ButtonElement(1, MIDI_NOTE_TYPE, self._channel, index)
            self._note_key_buttons.append(button)

    def set_enabled(self, enabled, enable_controls: bool = True):
        """Enables/Disables the scale play mode."""
        self._enabled = enabled
        if enabled:
            if self._edit_mode_enabled:
                self.enable_edit_mode()
            else:
                self.enable_play_mode(enable_controls)
        else:
            self._remove_button_listeners()
            self._remove_note_key_listeners()
            self.disable_edit_mode()

    def enable_play_mode(self, enable_controls: bool = True):
        """Enables/Disables the scale play mode functionality."""
        self.disable_edit_mode()
        if self._enabled:
            # self._logger.log("Scale play mode enabled.")
            self._update_play_mode_key_listeners()
            self.set_controls_enabled(enable_controls)

    def set_controls_enabled(self, enabled):
        if enabled and self._enabled:
            self._setup_button_listeners()
        else:
            self._remove_button_listeners()

    def enable_edit_mode(self):
        self._edit_mode_enabled = True
        if self._enabled:
            self._update_edit_mode_key_listeners()
            self._on_edit_mode_changed(True)

    def disable_edit_mode(self):
        if self._edit_mode_enabled:
            self._edit_mode_enabled = False
            self._on_edit_mode_changed(False)
            if self._enabled:
                self._update_play_mode_key_listeners()

    def set_channel(self, channel):
        self._channel = channel
        if self._edit_mode_button is not None:
            self._edit_mode_button.set_channel(channel)
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
        # self._logger.log(f"intervals: {list(scale_intervals)}")
        for midi_note in range(128):
            button = self._note_key_buttons[midi_note]
            is_matching = (12 + midi_note - root_note) % 12 in scale_intervals
            # self._logger.log(f"midi_note: {midi_note}, isMatching: {is_matching}")
            if is_matching:
                if button.value_has_listener(self._on_note_key):
                    button.remove_value_listener(self._on_note_key)
            else:
                if not button.value_has_listener(self._on_note_key):
                    button.add_value_listener(self._on_note_key, identify_sender=True)

    def _update_edit_mode_key_listeners(self):
        """Updates the note key listeners so all notes are captured"""
        for midi_note in range(128):
            button = self._note_key_buttons[midi_note]
            if not button.value_has_listener(self._on_note_key):
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
        if self._edit_mode_button and not self._edit_mode_button.value_has_listener(self._on_edit_mode_button_changed):
            self._edit_mode_button.add_value_listener(self._on_edit_mode_button_changed)

    def _remove_button_listeners(self):
        if self._root_note_button and self._root_note_button.value_has_listener(self._on_root_note_button_changed):
            self._root_note_button.remove_value_listener(self._on_root_note_button_changed)
        if self._scale_mode_button and self._scale_mode_button.value_has_listener(self._on_scale_mode_button_changed):
            self._scale_mode_button.remove_value_listener(self._on_scale_mode_button_changed)
        if self._edit_mode_button and self._edit_mode_button.value_has_listener(self._on_edit_mode_button_changed):
            self._edit_mode_button.remove_value_listener(self._on_edit_mode_button_changed)

    def _on_root_note_button_changed(self, value):
        if self._edit_mode_enabled:
            total_scales = len(self._custom_matching_scales)
            if total_scales > 0:
                scale_index = int((value / 127.0) * (total_scales - 1))
                self._song.root_note = self._custom_matching_scales[scale_index][0]
                self._song.scale_name = self._custom_matching_scales[scale_index][1]
        else:
            total_notes = 12
            note = int((value / 127.0) * (total_notes - 1))
            if note != self._song.root_note:
                self._song.root_note = note

    def _on_scale_mode_button_changed(self, value):
        if self._edit_mode_enabled:
            return
        total_scales = len(self._all_scales)
        scale_index = int((value / 127.0) * (total_scales - 1))
        self._song.scale_name = self._all_scales[scale_index][0]

    def _on_edit_mode_button_changed(self, value):
        if value > 0:
            self.enable_edit_mode()
        else:
            self.disable_edit_mode()

    def _on_root_note_changed(self):
        if self._enabled:
            if self._current_root_note == self._song.root_note and self._current_scale_intervals == self._song.scale_intervals:
                return
            if not self._edit_mode_enabled:
                self._update_play_mode_key_listeners()
        self._current_root_note = self._song.root_note
        
    def _on_scale_intervals_changed(self):
        if self._enabled:
            if self._current_root_note == self._song.root_note and self._current_scale_intervals == self._song.scale_intervals:
                return
            if not self._edit_mode_enabled:
                self._update_play_mode_key_listeners()
        self._current_scale_intervals = self._song.scale_intervals

    def _on_note_key(self, value, sender):
        if not self._edit_mode_enabled:
            return
        key = sender._msg_identifier
        if value > 0:
            self._pressed_keys.append(key)
            if len(self._pressed_keys) == 1:
                self._song.root_note = key % 12
                self._captured_notes = set()
                # self._logger.log(f"Set root {key % 12}")
            self._captured_notes.add(key % 12)
        else:
            self._pressed_keys.remove(key)
            if len(self._pressed_keys) == 0:
                self._custom_matching_scales = self._find_scales(self._captured_notes, starting_root=self._current_root_note)
                if len(self._custom_matching_scales) > 0:
                    self._song.root_note = self._custom_matching_scales[0][0]
                    self._song.scale_name = self._custom_matching_scales[0][1]
                    note_names = [Note.NOTE_NAMES[note] for note in sorted(self._captured_notes)]
                    self._logger.show_message(f"Found {len(self._custom_matching_scales)} scales including notes {note_names}")
                else:
                    self._logger.show_message(f"No scales found including notes {note_names}")
        # self._logger.log(f"Note: {key}, velocity: {value}")
        self._on_note_event(key, value)

    def _find_scales(self, notes: set, starting_root = 0):
        """Returns a list of tuples of (root, scale) with scales that include all the given notes. List is sorted from the starting_root and upwards"""
        matching_scales = []
        for root_index in range(12):
            root = (starting_root + root_index) % 12
            for scale in self._all_scales:
                scale_name = scale[0]
                original_intervals = scale[1]
                transposed_intervals = {(root + interval) % 12 for interval in original_intervals}
                # Check if all notes in the note_pitch_classes are in the transposed_intervals
                if notes.issubset(transposed_intervals):
                    # self._logger.log(f"Match: {scale_name} in {root}")
                    matching_scales.append((root, scale_name))
        return matching_scales

    def disconnect(self):
        self._remove_button_listeners()
        self._remove_note_key_listeners()
        self._song.remove_root_note_listener(self._on_root_note_changed)
        self._song.remove_scale_intervals_listener(self._on_scale_intervals_changed)
        self._note_key_buttons = []
        self._root_note_button = None
        self._scale_mode_button = None
        self._edit_mode_button = None
        self._on_edit_mode_changed = None
        self._on_note_event = None