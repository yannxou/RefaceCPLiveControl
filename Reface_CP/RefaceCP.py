# RefaceCP
# - Includes MIDI constants and basic interfacing with the Reface CP
#
# Part of RefaceCPLiveControl
#
# Ableton Live MIDI Remote Script for the Yamaha Reface CP
#
# Author: Joan Duat
#
# Distributed under the MIT License, see LICENSE

from .Logger import Logger

# Reface constants
# https://usa.yamaha.com/files/download/other_assets/7/794817/reface_en_dl_b0.pdf

# Reface Sysex
SYSEX_START = 0xF0
SYSEX_END = 0xF7
DEVICE_ID = 0x43 # Yamaha ID
GROUP_HIGH = 0x7F # Group number high
GROUP_LOW = 0x1C # Group number low
MODEL_ID = 0x04 # Model ID

# Reface CP MIDI CCs:
TYPE_SELECT_KNOB = 80
DRIVE_KNOB = 81
TREMOLO_DEPTH_KNOB = 18
TREMOLO_RATE_KNOB = 19
CHORUS_DEPTH_KNOB = 86
CHORUS_SPEED_KNOB = 87
DELAY_DEPTH_KNOB = 89
DELAY_TIME_KNOB = 90
REVERB_DEPTH_KNOB = 91
ENCODER_MSG_IDS = (DRIVE_KNOB, TREMOLO_DEPTH_KNOB, TREMOLO_RATE_KNOB, CHORUS_DEPTH_KNOB, CHORUS_SPEED_KNOB, DELAY_DEPTH_KNOB, DELAY_TIME_KNOB, REVERB_DEPTH_KNOB) # Reface CP knobs from Drive to Reverb Depth
TREMOLO_WAH_TOGGLE = 17
CHORUS_PHASER_TOGGLE = 85
DELAY_TOGGLE = 88

# Reface CP Parameter IDs:
REFACE_PARAM_TYPE = 0x02
REFACE_PARAM_TREMOLO_TOGGLE = 0x04
REFACE_PARAM_CHORUS_TOGGLE = 0x07
REFACE_PARAM_DELAY_TOGGLE = 0x0A

# Reface toggle constants
REFACE_TOGGLE_OFF = 0
REFACE_TOGGLE_UP = 1
REFACE_TOGGLE_DOWN = 2

# Reface type knob CC value to MIDI channel map
reface_type_map = {
    0: 0,
    25: 1,
    51: 2,
    76: 3,
    102: 4,
    127: 5
}

# Reface toggle CC value to parameter value
reface_toggle_map = {
    0: REFACE_TOGGLE_OFF,
    64: REFACE_TOGGLE_UP,
    127: REFACE_TOGGLE_DOWN
}

class RefaceCP:
    def __init__(self, logger: Logger, send_midi, 
                 receive_type_value = None,
                 receive_tremolo_toggle_value = None,
                 receive_chorus_toggle_value = None,
                 receive_delay_toggle_value = None):
        self._logger = logger
        self._send_midi = send_midi
        self._receive_type_value = receive_type_value
        self._receive_tremolo_toggle_value = receive_tremolo_toggle_value
        self._receive_chorus_toggle_value = receive_chorus_toggle_value
        self._receive_delay_toggle_value = receive_delay_toggle_value

    def request_current_values(self):
        self.request_parameter(REFACE_PARAM_TYPE)
        self.request_parameter(REFACE_PARAM_TREMOLO_TOGGLE)
        self.request_parameter(REFACE_PARAM_CHORUS_TOGGLE)
        self.request_parameter(REFACE_PARAM_DELAY_TOGGLE)

# --- Reface Sysex commands

    def _reface_sysex_header(self, device_number):
        # Returns the sysex prefix up to the address field
        return (SYSEX_START, DEVICE_ID, device_number, GROUP_HIGH, GROUP_LOW, MODEL_ID)

    def set_transmit_channel(self, channel):
        sys_ex_message = self._reface_sysex_header(0x10) + (0x00, 0x00, 0x00, channel, SYSEX_END)
        self._send_midi(sys_ex_message)

    def request_parameter(self, parameter):
        sys_ex_message = self._reface_sysex_header(0x30) + (0x30, 0x00, parameter, SYSEX_END)
        self._send_midi(sys_ex_message)

    def handle_sysex(self, midi_bytes):
        param_change_header = self._reface_sysex_header(0x10)
        self._logger.log(f"handle_sysex: {midi_bytes}. param_change_header: {param_change_header}")
        if midi_bytes[:len(param_change_header)] == param_change_header:
            param_id = midi_bytes[-3]
            param_value = midi_bytes[-2]
            self._logger.log(f"parameter sysex response. id: {param_id}, value: {param_value}")
            if param_id == REFACE_PARAM_TYPE:
                if self._receive_type_value is not None:
                    self._receive_type_value(param_value)
            elif param_id == REFACE_PARAM_TREMOLO_TOGGLE:
                if self._receive_tremolo_toggle_value is not None:
                    self._receive_tremolo_toggle_value(param_value)
            elif param_id == REFACE_PARAM_CHORUS_TOGGLE:
                if self._receive_chorus_toggle_value is not None:
                    self._receive_chorus_toggle_value(param_value)
            elif param_id == REFACE_PARAM_DELAY_TOGGLE:
                if self._receive_delay_toggle_value is not None:
                    self._receive_delay_toggle_value(param_value)

# ---

    def disconnect(self):
        self._logger = None
        self._send_midi = None
        self._receive_type_value = None
        self._receive_tremolo_toggle_value = None
        self._receive_chorus_toggle_value = None
        self._receive_delay_toggle_value = None