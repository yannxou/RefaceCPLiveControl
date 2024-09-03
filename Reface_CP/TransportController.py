import Live
from _Framework.ButtonElement import ButtonElement
from _Framework.InputControlElement import MIDI_NOTE_TYPE

class Note:
    c = 0
    c_sharp = 1
    d = 2
    d_sharp = 3
    e = 4
    f = 5
    f_sharp = 6
    g = 7
    g_sharp = 8
    a = 9
    a_sharp = 10
    b = 11

ACTION_STOP = Note.c

class TransportController:
    
    def __init__(self, logger, song, channel = 0):
        self._logger = logger
        self._song = song
        self._enabled = False
        self._channel = channel
        self._note_key_buttons = []
        self._pressed_keys = []
        self._current_action_key = None

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
            if len(self._pressed_keys) == 0:
                self._current_action_key = key
            self._pressed_keys.append(key)

        # self._logger.log(f"_on_note_on: {key}, {value}. current_action: {self._current_action}. pressed: {self._pressed_keys}")

        if self._current_action_key != key and value > 0:
            self.handle_subaction(self._current_action_key, key)

        if value == 0:
            self._pressed_keys.remove(key)
            if len(self._pressed_keys) == 0:
                if self._current_action_key == key:
                    self.handle_action(key)
                self._current_action_key = None  # Reset after all keys are released
                self._logger.log("_on_note_on. reset action.")

    def handle_action(self, action_key):
        action = action_key % 12
        self._logger.log(f"handle_action: {action}")
        if action == ACTION_STOP:
            self._logger.log("Stop playing")
            self._song.stop_playing()

    def handle_subaction(self, action_key, subaction_key):
        action = action_key % 12
        subaction = subaction_key % 12
        # self._logger.log(f"handle_subaction: {action}, {subaction}")
        if action == ACTION_STOP:
            if subaction == Note.d:
                self._logger.log("Stop current track clip")
                self._song.view.selected_track.stop_all_clips()
            elif subaction == Note.e:
                self._logger.log("Stop all clips")
                self._song.stop_all_clips()
            self._current_action_key = None  # Consume action (force to press again first note to redo action)
            
    def disconnect(self):
        self.set_enabled(False)
        self._logger = None
        self._song = None
        self._note_key_buttons = []