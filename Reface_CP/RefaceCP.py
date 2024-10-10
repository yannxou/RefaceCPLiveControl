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

VENDOR_ID = 5667
PRODUCT_ID = 1177
MODEL_NAME = "reface CP"

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

class ToneParameter:
    # Reface CP Parameter IDs:
    REFACE_PARAM_TYPE = 0x02
    REFACE_PARAM_TREMOLO_TOGGLE = 0x04
    REFACE_PARAM_CHORUS_TOGGLE = 0x07
    REFACE_PARAM_DELAY_TOGGLE = 0x0A

class RefaceCP:
    IDENTITY_REPLY = (0xF0, 0x7E, 0x7F, 0x06, 0x02, 0x43, 0x00, 0x41, 0x52, 0x06, 0x00, 0x00, 0x00, 0x7F, 0xF7)

    def __init__(self, logger: Logger, send_midi,
                 on_device_identified = None,
                 receive_type_value = None,
                 receive_tremolo_toggle_value = None,
                 receive_chorus_toggle_value = None,
                 receive_delay_toggle_value = None):
        self._logger = logger
        self._send_midi = send_midi
        self._on_device_identified = on_device_identified
        self._receive_type_value = receive_type_value
        self._receive_tremolo_toggle_value = receive_tremolo_toggle_value
        self._receive_chorus_toggle_value = receive_chorus_toggle_value
        self._receive_delay_toggle_value = receive_delay_toggle_value
        self._device_number = 0x00
        self._is_identified = False

    def request_current_values(self):
        self.request_tone_parameter(ToneParameter.REFACE_PARAM_TYPE)
        self.request_tone_parameter(ToneParameter.REFACE_PARAM_TREMOLO_TOGGLE)
        self.request_tone_parameter(ToneParameter.REFACE_PARAM_CHORUS_TOGGLE)
        self.request_tone_parameter(ToneParameter.REFACE_PARAM_DELAY_TOGGLE)

    def request_identity(self):
        # F0H 7EH 0nH 06H 01H F7H
        # (“n” = Device No. However, this instrument receives under “omni.”)
        self._send_midi((SYSEX_START, 0x7E, 0x00 | self._device_number, 0x06, 0x01, SYSEX_END))

# --- Reface Sysex commands

    def _reface_sysex_header(self, prefix):
        # Returns the sysex prefix up to the address field
        return (SYSEX_START, DEVICE_ID, prefix | self._device_number, GROUP_HIGH, GROUP_LOW, MODEL_ID)

    def set_transmit_channel(self, channel):
        if not self._is_identified:
            return
        sys_ex_message = self._reface_sysex_header(0x10) + (0x00, 0x00, 0x00, channel, SYSEX_END)
        self._send_midi(sys_ex_message)

    def set_local_control(self, enabled: bool):
        if not self._is_identified:
            return
        sys_ex_message = self._reface_sysex_header(0x10) + (0x00, 0x00, 0x06, 0x01 if enabled else 0x00, SYSEX_END)
        self._send_midi(sys_ex_message)

    def set_midi_control(self, enabled: bool):
        if not self._is_identified:
            return
        sys_ex_message = self._reface_sysex_header(0x10) + (0x00, 0x00, 0x0E, 0x01 if enabled else 0x00, SYSEX_END)
        self._send_midi(sys_ex_message)

    def set_speaker_output(self, enabled: bool):
        if not self._is_identified:
            return
        sys_ex_message = self._reface_sysex_header(0x10) + (0x00, 0x00, 0x0D, 0x01 if enabled else 0x00, SYSEX_END)
        self._send_midi(sys_ex_message)

    # See: MIDI PARAMETER CHANGE TABLE (Tone Generator)
    def request_tone_parameter(self, parameter: ToneParameter):
        if not self._is_identified:
            return
        sys_ex_message = self._reface_sysex_header(0x30) + (0x30, 0x00, parameter, SYSEX_END)
        self._send_midi(sys_ex_message)

    def set_tone_parameter(self, parameter: ToneParameter, value):
        if not self._is_identified:
            return
        sys_ex_message = self._reface_sysex_header(0x10) + (0x30, 0x00, parameter, value, SYSEX_END)
        self._send_midi(sys_ex_message)

    def handle_sysex(self, midi_bytes):
        # self._logger.log(f"handle_sysex: {midi_bytes}.")
        if len(midi_bytes) > 2:
            if midi_bytes[1] == 0x7E:
                if midi_bytes[:len(RefaceCP.IDENTITY_REPLY)] == RefaceCP.IDENTITY_REPLY:
                    self._is_identified = True
                    if self._on_device_identified is not None:
                        self._on_device_identified()
            else:
                param_change_header = self._reface_sysex_header(0x10)
                self._logger.log(f"handle_sysex: {midi_bytes}. param_change_header: {param_change_header}")
                if midi_bytes[:len(param_change_header)] == param_change_header:
                    param_id = midi_bytes[-3]
                    param_value = midi_bytes[-2]
                    self._logger.log(f"parameter sysex response. id: {param_id}, value: {param_value}")
                    if param_id == ToneParameter.REFACE_PARAM_TYPE:
                        if self._receive_type_value is not None:
                            self._receive_type_value(param_value)
                    elif param_id == ToneParameter.REFACE_PARAM_TREMOLO_TOGGLE:
                        if self._receive_tremolo_toggle_value is not None:
                            self._receive_tremolo_toggle_value(param_value)
                    elif param_id == ToneParameter.REFACE_PARAM_CHORUS_TOGGLE:
                        if self._receive_chorus_toggle_value is not None:
                            self._receive_chorus_toggle_value(param_value)
                    elif param_id == ToneParameter.REFACE_PARAM_DELAY_TOGGLE:
                        if self._receive_delay_toggle_value is not None:
                            self._receive_delay_toggle_value(param_value)

# ---

    def disconnect(self):
        self._logger = None
        self._send_midi = None
        self._on_device_identified = None
        self._receive_type_value = None
        self._receive_tremolo_toggle_value = None
        self._receive_chorus_toggle_value = None
        self._receive_delay_toggle_value = None
        self._is_identified = False