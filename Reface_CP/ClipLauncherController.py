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

import re
from .Logger import Logger
from Live.Song import Song, Quantization
from Live import ClipSlot, Scene, Track
from _Framework.ButtonElement import ButtonElement
from _Framework.InputControlElement import MIDI_NOTE_TYPE
from .Note import Note
from .Settings import CLIP_TRIGGER_NAME_PREFIXES_ENABLED, CLIP_TRIGGER_DEFAULT_LEGATO_ENABLED
import _Framework.Task as Task

class ClipLauncherController:
    
    quantization_all = [
        Quantization.q_no_q,
        Quantization.q_8_bars,
        Quantization.q_4_bars,
        Quantization.q_2_bars,
        Quantization.q_bar,
        Quantization.q_half,
        Quantization.q_half_triplet,
        Quantization.q_quarter,
        Quantization.q_quarter_triplet,
        Quantization.q_eight,
        Quantization.q_eight_triplet,
        Quantization.q_sixtenth,
        Quantization.q_sixtenth_triplet,
        Quantization.q_thirtytwoth
    ]

    # note keys used for triggering clips per octave (C-B except C#,D#)
    notes_per_octave = 10

    def __init__(self,
                 logger: Logger,
                 parent,
                 channel = 0,
                 trigger_quantization_button = None,
                 horizontal_offset_button = None,
                 vertical_offset_button = None,
                 note_layout_button = None,
                 clip_scene_target_button = None
                 ):
        self._logger = logger
        self._enabled = False
        self._parent = parent
        self._channel = channel
        self._trigger_quantization_button = trigger_quantization_button
        self._horizontal_offset_button = horizontal_offset_button
        self._vertical_offset_button = vertical_offset_button
        self._note_layout_button = note_layout_button
        self._clip_scene_target_button = clip_scene_target_button
        self._width = 7
        self._height = self.notes_per_octave
        self._horizontal_offset = 0
        self._vertical_offset = 0
        self._tracks_per_octave = 1
        self._current_layout = 0
        self._is_legato_enabled = CLIP_TRIGGER_DEFAULT_LEGATO_ENABLED
        self._note_key_buttons = []
        self._pressed_keys = []
        self._is_scene_focused = False
        self._ongoing_keys = False  # Used to group actions until all keys are released
        self._clip_prefix_pattern = r"^.*?\│"
        self._lowest_key = 24 # Lowest key in the device
        self._max_keys = 85 # Total number of keys in the device (in the refaceCP: 7 octaves + highest C)
        for index in range(128):
            button = ButtonElement(1, MIDI_NOTE_TYPE, self._channel, index)
            self._note_key_buttons.append(button)
        self._clip_rename_task = self._parent._tasks.add(Task.sequence(Task.delay(1), self._update_clip_names)).kill()
       
    def set_enabled(self, enabled):
        """Enables/Disables the clip launcher functionality."""
        if self._enabled == enabled:
            return
        self._enabled = enabled
        self.set_controls_enabled(enabled)
        if enabled:
            self._add_song_listeners()
            self._add_note_key_listeners()
            self._update_highlight(delayed=False)
        else:
            self._remove_song_listeners()
            self._remove_note_key_listeners()
            self._hide_highlight()
            self._pressed_keys = []

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
        return self._parent.song()

    def _add_song_listeners(self):
        if not self.song().visible_tracks_has_listener(self._on_tracks_changed):
            self.song().add_visible_tracks_listener(self._on_tracks_changed)
        if not self.song().scenes_has_listener(self._on_scenes_changed):
            self.song().add_scenes_listener(self._on_scenes_changed)

    def _remove_song_listeners(self):
        if self.song().visible_tracks_has_listener(self._on_tracks_changed):
            self.song().remove_visible_tracks_listener(self._on_tracks_changed)
        if self.song().scenes_has_listener(self._on_scenes_changed):
            self.song().remove_scenes_listener(self._on_scenes_changed)

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
        if self._trigger_quantization_button and not self._trigger_quantization_button.value_has_listener(self._on_trigger_quantization_button_changed):
            self._trigger_quantization_button.add_value_listener(self._on_trigger_quantization_button_changed)
        if self._horizontal_offset_button and not self._horizontal_offset_button.value_has_listener(self._on_horizontal_offset_button_changed):
            self._horizontal_offset_button.add_value_listener(self._on_horizontal_offset_button_changed)
        if self._vertical_offset_button and not self._vertical_offset_button.value_has_listener(self._on_vertical_offset_button_changed):
            self._vertical_offset_button.add_value_listener(self._on_vertical_offset_button_changed)
        if self._note_layout_button and not self._note_layout_button.value_has_listener(self._on_note_layout_button_changed):
            self._note_layout_button.add_value_listener(self._on_note_layout_button_changed)
        if self._clip_scene_target_button and not self._clip_scene_target_button.value_has_listener(self._on_clip_scene_target_button_changed):
            self._clip_scene_target_button.add_value_listener(self._on_clip_scene_target_button_changed)

    def _remove_button_listeners(self):
        if self._trigger_quantization_button and self._trigger_quantization_button.value_has_listener(self._on_trigger_quantization_button_changed):
            self._trigger_quantization_button.remove_value_listener(self._on_trigger_quantization_button_changed)
        if self._horizontal_offset_button and self._horizontal_offset_button.value_has_listener(self._on_horizontal_offset_button_changed):
            self._horizontal_offset_button.remove_value_listener(self._on_horizontal_offset_button_changed)
        if self._vertical_offset_button and self._vertical_offset_button.value_has_listener(self._on_vertical_offset_button_changed):
            self._vertical_offset_button.remove_value_listener(self._on_vertical_offset_button_changed)
        if self._note_layout_button and self._note_layout_button.value_has_listener(self._on_note_layout_button_changed):
            self._note_layout_button.remove_value_listener(self._on_note_layout_button_changed)
        if self._clip_scene_target_button and self._clip_scene_target_button.value_has_listener(self._on_clip_scene_target_button_changed):
            self._clip_scene_target_button.remove_value_listener(self._on_clip_scene_target_button_changed)

    def _update_highlight(self, delayed=True):
        if self._is_scene_focused:
            total_tracks = len(self.song().visible_tracks)
            self._parent._c_instance.set_session_highlight(track_offset=total_tracks, scene_offset=self._vertical_offset, width=self._width, height=self._height, include_return_tracks=False)
        else:
            self._parent._c_instance.set_session_highlight(track_offset=self._horizontal_offset, scene_offset=self._vertical_offset, width=self._width, height=self._height, include_return_tracks=False)

        if CLIP_TRIGGER_NAME_PREFIXES_ENABLED:
            if delayed:
                self._clip_rename_task.kill()
                self._clip_rename_task.restart()
            else:
                self._update_clip_names()

    def _hide_highlight(self):
        if CLIP_TRIGGER_NAME_PREFIXES_ENABLED:
            self._clip_rename_task.kill()
            self._remove_name_prefixes()
        try:
            self._parent._c_instance.set_session_highlight(track_offset=0, scene_offset=0, width=0, height=0, include_return_tracks=False)
        except:
            pass

    def _update_clip_names(self, args=None):
        if self._enabled:
            self._remove_name_prefixes()
            self._add_name_prefixes()

    def _on_tracks_changed(self):
        total_tracks = len(self.song().visible_tracks)
        if self._horizontal_offset >= total_tracks:
            self._horizontal_offset = total_tracks - 1
        self._update_highlight()

    def _on_scenes_changed(self):
        total_scenes = len(self.song().scenes)
        if self._vertical_offset >= total_scenes:
            self._vertical_offset = total_scenes - 1
        self._update_highlight()

    def _on_trigger_quantization_button_changed(self, value):
        quantization = int((value / 127.0) * (len(self.quantization_all) - 1))
        self.song().clip_trigger_quantization = quantization

    def _on_horizontal_offset_button_changed(self, value):
        if self._is_scene_focused:
            return
        total_tracks = len(self.song().visible_tracks)
        max_offset = total_tracks - self._width if total_tracks > self._width else 0
        new_offset = int((value / 127.0) * max_offset)
        # compare to prevent adding multiple undo steps (each 'update_highlight' call creates one)
        if new_offset != self._horizontal_offset:
            self._horizontal_offset = new_offset
            self._update_highlight()

    def _on_vertical_offset_button_changed(self, value):
        total_scenes = len(self.song().scenes)
        max_offset = total_scenes - self._height if total_scenes > self._height else 0
        new_offset = int((value / 127.0) * max_offset)
        # compare to prevent adding multiple undo steps (each 'update_highlight' call creates one)
        if new_offset != self._vertical_offset:
            self._vertical_offset = new_offset
            self._update_highlight()

    def _on_note_layout_button_changed(self, value):
        if len(self._pressed_keys) > 0: # Prevent changing layout while notes are pressed
            return
        if self._is_scene_focused:
            return
        layout = int((value / 127.0) * (8 - 1))
        if self._current_layout == layout:
            return
        self._set_layout(layout)
        self._update_highlight()
    
    def _set_layout(self, layout):
        if layout == 0:
            self._width = 7
            self._height = self.notes_per_octave
            self._logger.show_message("Clip trigger layout: 1 octave/track")
        elif layout == 1:
            self._width = 3
            self._height = 2 * self.notes_per_octave
            self._logger.show_message("Clip trigger layout: 2 octaves/track")
        elif layout == 2:
            self._width = 2
            self._height = 3 * self.notes_per_octave
            self._logger.show_message("Clip trigger layout: 3 octaves/track")
        elif layout == 3:
            self._width = 1
            self._height = self._max_keys
            self._logger.show_message("Clip trigger layout: single track")
        elif layout == 4:
            self._width = self._max_keys
            self._height = 1
            self._logger.show_message("Clip trigger layout: single scene")
        elif layout == 5:
            self._width = 3 * self.notes_per_octave
            self._height = 2
            self._logger.show_message("Clip trigger layout: 3 octaves/scene")
        elif layout == 6:
            self._width = 2 * self.notes_per_octave
            self._height = 3
            self._logger.show_message("Clip trigger layout: 2 octaves/scene")
        elif layout == 7:
            self._width = self.notes_per_octave
            self._height = 7
            self._logger.show_message("Clip trigger layout: 1 octave/scene")
        else:
            pass
        self._current_layout = layout
        # self._logger.log(f"width: {self._width} height: {self._height}")

    def _on_clip_scene_target_button_changed(self, value):
        if len(self._pressed_keys) > 0: # Prevent changing layout while notes are pressed
            return
        is_scene_focused = value > 0
        if self._is_scene_focused == is_scene_focused:
            return
        self._is_scene_focused = is_scene_focused
        if is_scene_focused:
            self._width = 1
            self._height = min(self._max_keys, len(self.song().scenes)) # max all note keys in the reface: 7 octaves + highest C
            self._logger.show_message("Scene trigger layout")
        else:
            self._set_layout(self._current_layout)
            self._logger.show_message("Clip trigger layout")
        self._update_highlight(delayed=False)

    def _on_note_key(self, velocity, sender):
        key = sender._msg_identifier
        if velocity > 0:
            pitch_class = key % 12            

            if self._is_legato_enabled and len(self._pressed_keys) > 0:
                current_key = self._pressed_keys[0]
                current_action = current_key % 12
                if not self._ongoing_keys and current_action == Note.c_sharp:
                    if pitch_class == Note.c_sharp:
                        self._stop_all_clips() # stop all playing or triggered clips
                    elif pitch_class == Note.d_sharp:
                        pass # Ignore C# + D# for now
                    else: # C# + clip/scene
                        self._stop_from_note(key)

                elif not self._ongoing_keys and current_action == Note.d_sharp:
                    if pitch_class == Note.c_sharp:
                        self._stop_all_clips() # stop all playing or triggered clips
                    elif pitch_class == Note.d_sharp:
                        pass # Ignore Higher/Lower D# for now 
                    else:
                        if self._is_scene_focused:
                            self._fire_scene_from_note(key)
                        else:
                            self._play_scene_from_clip_note(key)

                else:
                    self._ongoing_keys = True
                    if pitch_class == Note.c_sharp:
                        # self._stop_all_track_clips_from_notes(self._pressed_keys)
                        self._stop_from_note(current_key)
                    elif pitch_class == Note.d_sharp:
                        pass # Ignore note + D# while clip/scene are being played
                    else:
                        if self._is_scene_focused:
                            self._fire_scene_from_note(key, force_legato=True)
                        else:
                            # Play new clip in legato mode if there's another one playing from the same track already.
                            clip_slot = self._get_clip_slot(key)
                            if clip_slot:
                                if clip_slot.has_clip:
                                    if self._track_has_playing_clip(clip_slot.canonical_parent):
                                        clip_slot.fire(force_legato=True)
                                    else:
                                        clip_slot.fire()
                                elif clip_slot.has_stop_button:
                                    clip_slot.fire()

            else: # No other keys are being pressed
                if pitch_class == Note.c_sharp:
                    if self._is_scene_focused:
                        self._logger.show_message("│◼︎│ Hold+note to stop the clip's scene. │◼︎◼︎◼︎│ Hold+upper/lower C# to stop all clips.")
                    else:
                        self._logger.show_message("│◼︎│ Hold+note to stop the clip's track. │◼︎◼︎◼︎│ Hold+upper/lower C# to stop all clips.")
                elif pitch_class == Note.d_sharp:
                    self._logger.show_message("[▶…] Hold+note note to play the clip's scene.")
                else:
                    if self._is_scene_focused:
                        self._fire_scene_from_note(key)
                    else:
                        clip_slot = self._get_clip_slot(key)
                        if clip_slot:
                            clip_slot.fire()

            self._pressed_keys.append(key)

        else: # note is released (velocity == 0)   
            if self._is_legato_enabled and len(self._pressed_keys) > 1:
                previous_note = self._pressed_keys[len(self._pressed_keys) - 2]
                if key % 12 == Note.c_sharp:
                    previous_clip_slot = self._get_clip_slot(previous_note)
                    if previous_clip_slot and previous_clip_slot.has_clip:
                        previous_clip_slot.fire(force_legato=True)
                elif previous_note % 12 == Note.c_sharp and key not in [Note.c_sharp, Note.d_sharp]:
                    self._stop_from_note(key)
                elif previous_note % 12 == Note.d_sharp:
                    pass
                elif self._is_scene_focused:
                    self._fire_scene_from_note(previous_note, force_legato=True)
                elif self._is_most_recent_key_from_track(key): # The released key corresponds to the most recent key press for a track
                    # Since legato only applies to clips within the same track we find here the previous pressed clip on a track basis.
                    released_clip_slot = self._get_clip_slot(key)
                    if released_clip_slot:
                        previous_sibling_clip_slot = self._get_previous_clip_slot_from_track(key, released_clip_slot.canonical_parent)
                        if previous_sibling_clip_slot:
                            if previous_sibling_clip_slot.has_clip:
                                # Play previous clip in legato mode only if released clip belongs to same track or there's another key corresponding to its track with a playing clip
                                previous_sibling_clip_slot.fire(force_legato=True)
                            else:
                                if previous_sibling_clip_slot.has_stop_button:
                                    self._stop_track_clips_from_note(previous_note)

            try:
                self._pressed_keys.remove(key)
                if len(self._pressed_keys) == 0:
                    self._ongoing_keys = False
            except:
                pass

    def _get_index_from_note(self, note):
        """
        Maps MIDI notes to item indices, skipping C# and D#.

        Args:
            note (int): MIDI note number (e.g., C1 = 24, D1 = 26, etc.).

        Returns:
            int: Item index corresponding to the note, or None if the note is invalid.
        """
        # Notes per octave, skipping C# and D# (C, D, E, F, F#, G, G#, A, A#, B)
        valid_notes = [0, 2, 4, 5, 6, 7, 8, 9, 10, 11]  # Relative to C in the octave
        
        # Calculate the pitch class (0-11, relative to C) and octave
        pitch_class = note % 12
        octave = (note // 12) - 2  # MIDI note 0 corresponds to C-1

        if pitch_class in valid_notes:
            # Find position of pitch class in valid notes
            index_in_octave = valid_notes.index(pitch_class)
            # Add to the octave's base index
            index = index_in_octave + len(valid_notes) * octave
            return index
        else:
            # Note is skipped (C# or D#)
            return None

    def _get_clip_slot(self, note: int) -> ClipSlot.ClipSlot:
        index = self._get_index_from_note(note)
        if index is None:
            return
        # Map octave to track
        track_index = self._horizontal_offset + (index // self._height if self._height > self._width else index % self._width)
        if track_index < 0 or track_index >= len(self.song().visible_tracks) or track_index > (self._horizontal_offset + self._width - 1):
            return None
        track = self.song().visible_tracks[track_index]
        if track in self.song().return_tracks:
            return None
        # Map note to clip slot
        clip_slot_index = self._vertical_offset + (index % self._height if self._height > self._width else index // self._width)
        if clip_slot_index < len(track.clip_slots) and clip_slot_index < (self._vertical_offset + self._height):
            clip_slot = track.clip_slots[clip_slot_index]
            if clip_slot.has_clip or clip_slot.has_stop_button:
                return clip_slot
            else:
                return None
        else:
            return None
        
    def _get_scene(self, note: int) -> Scene.Scene:
        index = self._get_index_from_note(note)
        if index is None or index < 0:
            return
        scene_index = self._vertical_offset + index
        if scene_index < len(self.song().scenes):
            return self.song().scenes[scene_index]
        else:
            return None

    def _add_name_prefixes(self):
        if self._is_scene_focused:
            for note in range(self._lowest_key, self._lowest_key + min(self._max_keys, len(self.song().scenes))):
                scene = self._get_scene(note)
                if scene:
                    # Add additional spaces before separator if is white key so prefixes are aligned in Live
                    prefix = Note.midi_note_to_string(note) + ("  " if Note.is_white_key(note) else "") + "│"
                    if scene.name.startswith(prefix):
                        break
                    # Remove previous prefix if it exists
                    if re.match(self._clip_prefix_pattern, scene.name):
                        scene.name = prefix + re.sub(self._clip_prefix_pattern, "", scene.name)
                    else:
                        scene.name = prefix + scene.name

        else:
            for note in range(self._lowest_key, 128):
                clip_slot = self._get_clip_slot(note)
                if clip_slot and clip_slot.has_clip:
                    clip = clip_slot.clip
                    # Add additional spaces before separator if is white key so prefixes are aligned in Live
                    prefix = Note.midi_note_to_string(note) + ("  " if Note.is_white_key(note) else "") + "│"
                    if clip.name.startswith(prefix):
                        break
                    # Remove previous prefix if it exists
                    if re.match(self._clip_prefix_pattern, clip.name):
                        clip.name = prefix + re.sub(self._clip_prefix_pattern, "", clip.name)
                    else:
                        clip.name = prefix + clip.name

    def _remove_name_prefixes(self):
        # Remove prefixes from scene names
        for scene in self.song().scenes:
            if re.match(self._clip_prefix_pattern, scene.name):
                scene.name = re.sub(self._clip_prefix_pattern, "", scene.name)

        # Remove prefixes from clip names:
        for track in self.song().tracks:
            slots = track.clip_slots
            for index in range(0, len(slots)):
                clip_slot = slots[index]
                if clip_slot.has_clip:
                    clip = clip_slot.clip
                    if re.match(self._clip_prefix_pattern, clip.name):
                        clip.name = re.sub(self._clip_prefix_pattern, "", clip.name)

    def _stop_all_clips(self, quantized=True):
        """Stop all playing or triggered clips."""
        self.song().stop_all_clips(Quantized=quantized)

    def _stop_from_note(self, note, quantized=True):
        """Stops running and triggered clip and slots from the scene or track (according current scene/clips mode) corresponding to the given note"""
        if self._is_scene_focused:
            self._stop_scene_clips_from_note(note)
        else:
            self._stop_track_clips_from_note(note)

    def _stop_track_clips_from_note(self, note, quantized=True):
        """Stop running and triggered clip and slots on the track from the clip of the corresponding given note"""
        clip_slot = self._get_clip_slot(note)
        if clip_slot and clip_slot.has_clip:
            track = clip_slot.canonical_parent
            if isinstance(track, Track.Track):
                track.stop_all_clips(Quantized=quantized)

    def _stop_scene_clips_from_note(self, note, quantized=True):
        """Stop all playing or triggered clips from the scene of the corresponding given note"""
        scene = self._get_scene(note)
        if scene:
            for clip_slot in scene.clip_slots:
                if clip_slot and clip_slot.has_clip:
                    track = clip_slot.canonical_parent
                    if isinstance(track, Track.Track):
                        track.stop_all_clips(Quantized=quantized)

    def _stop_all_track_clips_from_notes(self, notes, quantized=True):
        """Stop all the tracks form clips corresponding to the given notes"""
        unique_tracks = set()
        for note in [index for index in notes if index not in [Note.c_sharp, Note.d_sharp]]:
            clip_slot = self._get_clip_slot(note)
            if clip_slot and clip_slot.has_clip:
                track = clip_slot.canonical_parent
                if isinstance(track, Track.Track):
                    unique_tracks.add(track)
        for track in unique_tracks:
            track.stop_all_clips(Quantized=quantized)

    def _play_scene_from_clip_note(self, note, quantized=True):
        """Plays the scene from the clip corresponding to the given note key"""
        index = self._get_index_from_note(note)
        if index is None:
            return
        scene_index = self._vertical_offset + (index % self._height if self._height > self._width else index // self._width)
        if scene_index < len(self.song().scenes):
            scene: Scene.Scene = self.song().scenes[scene_index]
            scene.fire(force_legato=False, can_select_scene_on_launch=True)

    def _fire_scene_from_note(self, note, force_legato: bool = False):
        scene = self._get_scene(note)
        if scene:
            scene.fire(force_legato=force_legato)

    def _track_has_playing_clip(self, track: Track.Track) -> bool:
        return any(clip_slot.has_clip and clip_slot.clip.is_playing for clip_slot in track.clip_slots)
    
    def _is_any_pressed_key_from_track(self, track: Track.Track) -> bool:
        """Return True if any of the pressed keys corresponds to a clip in the given track"""
        for note in self._pressed_keys:
            clip_slot = self._get_clip_slot(note)
            if clip_slot and clip_slot.has_clip:
                if clip_slot.canonical_parent == track:
                    return True

    def _get_previous_clip_slot_from_track(self, released_key, track: Track.Track) -> ClipSlot.ClipSlot | None:
        """Returns the previous to the most recent clip slot from the same given track whose key is currently being pressed"""
        for index in range(len(self._pressed_keys) - 1, -1, -1):
            key = self._pressed_keys[index]
            clip_slot = self._get_clip_slot(key)
            if clip_slot and clip_slot.canonical_parent == track and key != released_key:
                return clip_slot
        return None

    def _is_most_recent_key_from_track(self, note) -> bool:
        """Returns True if the given key corresponds to the most recent key of a track's clip still being pressed."""
        clip_slot = self._get_clip_slot(note)
        if clip_slot is None:
            return False
        most_recent_keys = {}
        for index in range(len(self._pressed_keys) - 1, -1, -1):
            key = self._pressed_keys[index]
            slot = self._get_clip_slot(key)
            if slot and slot.canonical_parent._live_ptr not in most_recent_keys:
                most_recent_keys[slot.canonical_parent._live_ptr] = key
        recent_note = most_recent_keys.get(clip_slot.canonical_parent._live_ptr)
        return recent_note == note


    def disconnect(self):
        self._remove_song_listeners()
        self._remove_button_listeners()
        self._remove_note_key_listeners()
        self._note_key_buttons = []