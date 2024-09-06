import math
import threading
import time
import Live
from .Logger import Logger
from .Note import Note
from _Framework.ButtonElement import ButtonElement
from _Framework.InputControlElement import MIDI_NOTE_TYPE

class TransportController:
    
    def __init__(self, logger, song, channel = 0):
        self._logger = logger
        self._song = song
        self._enabled = False
        self._channel = channel
        self._note_key_buttons = []
        self._pressed_keys = []
        self._current_action_key = None
        self._current_action_skips_ending = False
        self._action_timer = None

    def set_enabled(self, enabled):
        if self._enabled == enabled:
            return
        if enabled:
            self._setup_transport_keys()
        else:
            self._disable_transport_keys()
        self._enabled = enabled

    def set_channel(self, channel):
        self._channel = channel
        for note_key in self._note_key_buttons:
            note_key.set_channel(channel)

# - Private

    def _setup_transport_keys(self):
        self._logger.log("Transport keys mode enabled.")
        self._disable_transport_keys(debug=False)
        # Enable note key listeners
        for index in range(127):
            button = ButtonElement(1, MIDI_NOTE_TYPE, self._channel, index)
            button.add_value_listener(self._on_note_key, identify_sender=True)
            self._note_key_buttons.append(button)

    def _disable_transport_keys(self, debug=True):
        if debug:
            self._logger.log("Transport keys mode disabled.")
        for button in self._note_key_buttons:
            button.remove_value_listener(self._on_note_key)
        self._note_key_buttons = []
        self._pressed_keys = []

    def _on_note_key(self, value, sender):
        key = sender._msg_identifier

        if value > 0:
            self._pressed_keys.append(key)
            if len(self._pressed_keys) == 1:
                self._current_action_key = key
                self._current_action_skips_ending = False
                self._begin_action(key)
                self._start_action_timeout()
                return

        # self._logger.log(f"_on_note_on: {key}, {value}. current_action: {self._current_action}. pressed: {self._pressed_keys}")

        if self._current_action_key is not None and self._current_action_key != key and value > 0:
            self._handle_subaction(self._current_action_key, key)
            self._cancel_action_timeout()

        if value == 0:
            self._pressed_keys.remove(key)
            if len(self._pressed_keys) == 0:
                if self._current_action_key == key and not self._current_action_skips_ending:
                    self._end_action(key)
                self._cancel_action_timeout()
                self._current_action_key = None  # Reset after all keys are released

    def _begin_action(self, action_key):
        action = action_key % 12
        if action == Note.c:
            self._logger.show_message("◼︎ Release to stop playing. │◼︎│ Hold+D: Stop track clips. │◼︎◼︎◼︎│ Hold+E: Stop all clips.")
        elif action == Note.c_sharp:
            self._logger.show_message("● Release to toggle record. ▶= Hold+C: Back to Arranger. ✚ Hold+D: Arrangement overdub. ○ Hold+D#: Session record •-• Hold+E: Automation arm. ◀︎- Hold+F: Reenable automation.")
        elif action == Note.d:
            self._logger.show_message("▶ Release to start playing. ◀︎┼▶︎ Hold+white keys to jump. │▶ Hold+F#: Continue playback.")
        elif action == Note.e:
            self._logger.show_message("[○ ●] Release to toggle metronome. [TAP] Hold+D")
        elif action == Note.g:
            self._logger.show_message("[←] Release to toggle loop. [←→] Hold+F#/G#: Dec/Inc loop length. ←[ ] Hold+white keys to move loop start. [◀︎] Hold+C#: Jump to loop start.")

    def _end_action(self, action_key):
        action = action_key % 12
        self._logger.log(f"handle_action: {action}")

        if action == Note.c:
            self._logger.show_message("Stop playing.")
            self._song.stop_playing()

        elif action == Note.c_sharp:
            self._logger.show_message("Toggle arrangement record.")
            self._song.record_mode = not self._song.record_mode

        elif action == Note.d:
            self._logger.show_message("Play.")
            self._song.start_playing()

        elif action == Note.e:
            self._logger.show_message("Toggle metronome.")
            self._song.metronome = not self._song.metronome

        elif action == Note.g:
            self._logger.show_message("Toggle loop.")
            self._song.loop = not self._song.loop

    def _handle_subaction(self, action_key, subaction_key):
        action = action_key % 12
        subaction = subaction_key % 12
        # self._logger.log(f"handle_subaction: {action}, {subaction}")

        if action == Note.c:
            if subaction == Note.d:
                self._logger.show_message("Stop current track clip.")
                self._song.view.selected_track.stop_all_clips()
            elif subaction == Note.e:
                self._logger.show_message("Stop all clips.")
                self._song.stop_all_clips()
            else:
                self._logger.show_message("")
            self._current_action_key = None  # Consume action (force to press again first note to redo action)


        elif action == Note.c_sharp:
            if subaction == Note.c:
                self._logger.show_message("Back to arrangement.")
                self._song.back_to_arranger = False
            elif subaction == Note.d:
                self._logger.show_message("Toggle MIDI arrangement overdub.")
                self._song.arrangement_overdub = not self._song.arrangement_overdub
            elif subaction == Note.d_sharp:
                self._logger.show_message("Toggle Session record.")
                self._song.session_record = not self._song.session_record
            elif subaction == Note.e:
                self._logger.show_message("Toggle automation arm.")
                self._song.session_automation_record = not self._song.session_automation_record
            elif subaction == Note.f:
                self._logger.show_message("Re-enable automation.")
                self._song.re_enable_automation() 
            else:
                self._logger.show_message("")
            self._current_action_key = None  # Consume action (force to press again first note to redo action)


        elif action == Note.d:
            if Note.is_white_key(subaction):
                # Jump playhead using white keys and distance to root.
                distance = Note.white_key_distance(action_key, subaction_key)
                jump_value = (2 ** abs(distance) / 4) * math.copysign(1, distance)
                # self._logger.log(f"distance: {distance}. jump: {jump_value}")
                # self._song.scrub_by(distance) 
                self._song.jump_by(jump_value) # compred to scrub_by, this one keeps playback in sync
                self._current_action_skips_ending = True  # Avoid sending main action on note off but allow sending more subactions.
            else:
                if subaction == Note.f_sharp:
                    self._logger.show_message("Play from selection.")
                    self._song.continue_playing()   # Continue playing the song from the current position
                    self._current_action_key = None # Consume action (force to press again first note to redo action)
                
        
        elif action == Note.e:
            if subaction == Note.d:
                if not self._current_action_skips_ending:
                    self._logger.show_message("Tap Tempo.")
                self._song.tap_tempo()
                self._current_action_skips_ending = True  # Avoid sending main action on note off but allow sending more subactions.
            else:
                self._current_action_key = None # Consume action (force to press again first note to redo action)


        elif action == Note.g:
            if Note.is_white_key(subaction):
                # Move loop start using white keys and distance to root.
                distance = Note.white_key_distance(action_key, subaction_key)
                jump_value = (2 ** abs(distance) / 4) * math.copysign(1, distance)
                try:
                    self._song.loop_start = max(0, self._song.loop_start + jump_value)
                except:
                    self._logger.log("Cannot set loop start behind song length.")
            else:
                if subaction == Note.d_sharp:
                    try:
                        if self._song.is_playing:
                            self._song.jump_by(round(self._song.loop_start - self._song.current_song_time))
                        else:
                            self._song.current_song_time = self._song.loop_start
                    except:
                        self._logger.log("Cannot set time behind song length")
                elif subaction == Note.f_sharp:
                    loop_length = self._song.loop_length  # Loop length in beats
                    self._song.loop_length = max(1, loop_length / 2)
                elif subaction == Note.g_sharp:
                    loop_length = self._song.loop_length  # Loop length in beats
                    try:
                        self._song.loop_length = loop_length * 2
                    except:
                        self._logger.log("Cannot set loop length longer that song length.")
            self._current_action_skips_ending = True  # Avoid sending main action on note off but allow sending more subactions.


            # song.jump_to_next_cue()   # Jump to the next cue (marker) if possible.
            # song.jump_to_prev_cue()   # Jump to the prior cue (marker) if possible.
            # song.can_jump_to_next_cue
            # song.can_jump_to_prev_cue

    def _start_action_timeout(self):
        self._cancel_action_timeout()
        self._action_timer = threading.Timer(3.0, self._on_action_timeout)
        self._action_timer.start()

    def _cancel_action_timeout(self):
        if self._action_timer is not None:
            self._action_timer.cancel()
            self._action_timer = None

    def _on_action_timeout(self):
        self._logger.log("action timeout")
        self._current_action_key = None # Consume action (force to press again first note to redo action)
            
    def disconnect(self):
        self._cancel_action_timeout()
        self.set_enabled(False)
        self._logger = None
        self._song = None
        self._note_key_buttons = []