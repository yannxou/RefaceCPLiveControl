# ClipLauncherController
# - Handles clip triggering using the MIDI keyboard
#
# Part of RefaceCPLiveControl
#
# Ableton Live MIDI Remote Script for the Yamaha Reface CP
#
# Author: Joan Duat
#
# Distributed under the MIT License, see LICENSE

from .Logger import Logger
from _Framework.ButtonElement import ButtonElement
from _Framework.InputControlElement import MIDI_NOTE_TYPE

class ClipLauncherController:
    
    def __init__(self,
                 logger: Logger,
                 c_instance,
                 channel = 0,
                 horizontal_offset_button = None,
                 vertical_offset_button = None
                 ):
        self._logger = logger
        self._enabled = False
        self._c_instance = c_instance
        self._channel = channel
        self._horizontal_offset_button = horizontal_offset_button
        self._vertical_offset_button = vertical_offset_button
        self._width = 7
        self._height = 12
        self._horizontal_offset = 0
        self._vertical_offset = 0
        self._tracks_per_octave = 1
        self._note_key_buttons = []
        for index in range(128):
            button = ButtonElement(1, MIDI_NOTE_TYPE, self._channel, index)
            self._note_key_buttons.append(button)
       
    def set_enabled(self, enabled):
        """Enables/Disables the clip launcher functionality."""
        if self._enabled == enabled:
            return
        self._enabled = enabled
        self.set_controls_enabled(enabled)
        if enabled:
            self._add_note_key_listeners()
            self._update_highlight()
        else:
            self._remove_note_key_listeners()
            self._hide_highlight()

    def set_controls_enabled(self, enabled):
        """Enables the buttons for controlling the clip launch mode parameters."""
        if enabled and self._enabled:
            self._add_button_listeners()
        else:
            self._remove_button_listeners()

    def set_channel(self, channel):
        self._channel = channel
        for button in self._note_key_buttons:
            button.set_channel(channel)

    def song(self):
        return self._c_instance.song()

    def _add_note_key_listeners(self):
        """Updates the note key listeners so all notes are captured"""
        for midi_note in range(128):
            button = self._note_key_buttons[midi_note]
            if not button.value_has_listener(self._on_note_key):
                button.add_value_listener(self._on_note_key, identify_sender=True)

    def _remove_note_key_listeners(self):
        for button in self._note_key_buttons:
            if button.value_has_listener(self._on_note_key):
                button.remove_value_listener(self._on_note_key)

    def _add_button_listeners(self):
        if self._horizontal_offset_button and not self._horizontal_offset_button.value_has_listener(self._on_horizontal_offset_button_changed):
            self._horizontal_offset_button.add_value_listener(self._on_horizontal_offset_button_changed)
        if self._vertical_offset_button and not self._vertical_offset_button.value_has_listener(self._on_vertical_offset_button_changed):
            self._vertical_offset_button.add_value_listener(self._on_vertical_offset_button_changed)

    def _remove_button_listeners(self):
        if self._horizontal_offset_button and self._horizontal_offset_button.value_has_listener(self._on_horizontal_offset_button_changed):
            self._horizontal_offset_button.remove_value_listener(self._on_horizontal_offset_button_changed)
        if self._vertical_offset_button and self._vertical_offset_button.value_has_listener(self._on_vertical_offset_button_changed):
            self._vertical_offset_button.remove_value_listener(self._on_vertical_offset_button_changed)

    def _update_highlight(self):
        self._c_instance.set_session_highlight(track_offset=self._horizontal_offset, scene_offset=self._vertical_offset, width=self._width, height=self._height, include_return_tracks=False)

    def _hide_highlight(self):
        try:
            self._c_instance.set_session_highlight(track_offset=0, scene_offset=0, width=0, height=0, include_return_tracks=False)
        except:
            pass

    def _on_horizontal_offset_button_changed(self, value):
        total_tracks = len(self.song().visible_tracks)
        max_offset = total_tracks - self._width if total_tracks > self._width else 0
        self._horizontal_offset = int((value / 127.0) * max_offset)
        self._update_highlight()

    def _on_vertical_offset_button_changed(self, value):
        total_scenes = len(self.song().scenes)
        max_offset = total_scenes - self._height if total_scenes > self._height else 0
        self._vertical_offset = int((value / 127.0) * max_offset)
        self._update_highlight()

    def _on_note_key(self, velocity, sender):
        key = sender._msg_identifier
        # self._logger.log(f"Key {key}, value {velocity}")
        if velocity == 0:  # Note Off
            return
        octave = key // 12
        # Map octave to track
        track_index = self._horizontal_offset + octave - 2  # Adjust for keyboard's starting octave
        if track_index < 0 or track_index >= len(self.song().visible_tracks):
            return
        track = self.song().visible_tracks[track_index]
        if track.is_foldable or not track.can_be_armed:
            return  # Skip non-audio/MIDI tracks
        # Map note to clip slot
        clip_slot_index = self._vertical_offset + (key % 12)
        # Fire the clip in the determined track and clip slot
        if clip_slot_index < len(track.clip_slots):
            clip_slot = track.clip_slots[clip_slot_index]
            if clip_slot.has_clip or clip_slot.has_stop_button:
                clip_slot.fire()

    def disconnect(self):
        self._remove_button_listeners()
        self._remove_note_key_listeners()
        self._note_key_buttons = []