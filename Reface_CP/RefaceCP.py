from __future__ import absolute_import, print_function, unicode_literals
import Live
from _Framework.ControlSurface import ControlSurface
from _Framework.MixerComponent import MixerComponent
from _Framework.TransportComponent import TransportComponent
from _Framework.SessionComponent import SessionComponent
from _Framework.EncoderElement import *
from _Framework.ButtonElement import ButtonElement
from _Framework.SliderElement import SliderElement
from _Framework.InputControlElement import MIDI_NOTE_TYPE, MIDI_NOTE_ON_STATUS, MIDI_NOTE_OFF_STATUS, MIDI_CC_STATUS, MIDI_CC_TYPE
from _Framework.DeviceComponent import DeviceComponent
from ableton.v2.base import listens, liveobj_valid, liveobj_changed
#from _Framework.ChannelStripComponent import ChannelStripComponent

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
REFACE_PARAM_TREMOLO = 0x04

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

class RefaceCP(ControlSurface):
    def __init__(self, c_instance):
        ControlSurface.__init__(self, c_instance)
        with self.component_guard():
            self.log_message("RefaceCP Init Started")
            self._c_instance = c_instance

            # self._suppress_send_midi = True
            self._locked_device = None
            self._selected_parameter = None
            self._channel = 0
            self._tremolo_toggle_value = REFACE_TOGGLE_OFF
            self._chorus_toggle_value = REFACE_TOGGLE_OFF
            self._delay_toggle_value = REFACE_TOGGLE_OFF
            self._note_key_buttons = []

            # FIXME: not working? try manually setting those?
            self._suggested_input_port = "reface CP"
            self._suggested_output_port = "reface CP"

            self._setup_initial_values()
            self._setup_buttons()
            self._setup_device_control()
            self._setup_song_listeners()

            #self._enable_note_key_buttons()

            self.log_message("RefaceCP Init Succeeded.")

# --- Setup

    def _setup_initial_values(self):
        self._waiting_for_first_response = True
        self.schedule_message(25, self._request_initial_values) # delay call otherwise it silently fails during init stage

    def _request_initial_values(self):
        self.request_reface_parameter(REFACE_PARAM_TYPE)
        self.request_reface_parameter(REFACE_PARAM_TREMOLO)

    def _setup_buttons(self):
        self._type_select_button = ButtonElement(1, MIDI_CC_TYPE, self._channel, TYPE_SELECT_KNOB)
        self._type_select_button.add_value_listener(self._reface_type_select_changed)

        self._drive_knob = EncoderElement(MIDI_CC_TYPE, self._channel, DRIVE_KNOB, Live.MidiMap.MapMode.absolute)

        self._tremolo_toggle_button = ButtonElement(1, MIDI_CC_TYPE, self._channel, TREMOLO_WAH_TOGGLE)
        self._tremolo_toggle_button.add_value_listener(self._reface_tremolo_toggle_changed)

        self._chorus_toggle_button = ButtonElement(1, MIDI_CC_TYPE, self._channel, CHORUS_PHASER_TOGGLE)
        self._chorus_toggle_button.add_value_listener(self._reface_chorus_toggle_changed)

        self._delay_toggle_button = ButtonElement(1, MIDI_CC_TYPE, self._channel, DELAY_TOGGLE)
        self._delay_toggle_button.add_value_listener(self._reface_delay_toggle_changed)

    def _setup_device_control(self):
        self._device_lock_button = ButtonElement(1, MIDI_CC_TYPE, 15, 100, name="DeviceLock")
        self._device = DeviceComponent()
        self._device.name = 'Device_Component'
        self._device.set_lock_button(self._device_lock_button)
        self._on_device_changed.subject = self._device
        self.set_device_component(self._device)

    def _setup_song_listeners(self):
        self.song().view.add_selected_parameter_listener(self._on_selected_parameter_changed)

    def _update_device_control_channel(self, channel):
        device_controls = []
        for index in range(8):
            control = EncoderElement(MIDI_CC_TYPE, channel, ENCODER_MSG_IDS[index], Live.MidiMap.MapMode.absolute)
            control.name = 'Ctrl_' + str(index)
            device_controls.append(control)
        self._device.set_parameter_controls(device_controls)

    def set_channel(self, channel):
        self._channel = channel
        self._setRefaceTransmitChannel(channel)
        self._type_select_button.set_channel(channel)
        self._tremolo_toggle_button.set_channel(channel)
        self._chorus_toggle_button.set_channel(channel)
        self._delay_toggle_button.set_channel(channel)

        if self._tremolo_toggle_value == REFACE_TOGGLE_DOWN:
            self.enable_track_mode(channel)
        else:
            self._update_device_control_channel(channel)

    def set_tremolo_toggle(self, value):
        self.log_message(f"set_tremolo_toggle: {value}")
        self._tremolo_toggle_value = value

        if value == REFACE_TOGGLE_UP:
            self.disable_track_mode()
            selected_device = self.get_selected_device()
            self.log_message(f"Device locked: {selected_device.name}")
            self._update_device_control_channel(self._channel)
            self.set_device_component(self._device)
            self._lock_to_device(selected_device)
        elif value == REFACE_TOGGLE_DOWN:
            self._unlock_from_device()
            self._device.set_parameter_controls(None)
            self.set_device_component(None)
            self.enable_track_mode(self._channel)
            self._c_instance.show_message("Track mode enabled.")
        else:
            self.disable_track_mode()
            self._update_device_control_channel(self._channel)
            self._unlock_from_device()
            self.set_device_component(self._device)
            self.set_device_to_selected()
            self._c_instance.show_message("Device lock off. Following device selection.")
        self.request_rebuild_midi_map()

    def _update_chorus_toggle(self, value):
        self.log_message(f"_update_chorus_toggle: {value}")
        self._chorus_toggle_value = value

    def _update_delay_toggle(self, value):
        self.log_message(f"_update_delay_toggle: {value}")
        self._delay_toggle_value = value

# --- Listeners

    @subject_slot('device')
    def _on_device_changed(self):
        # self.log_message("on_device_changed")
        if liveobj_valid(self._device):
            self.set_device_to_selected()

    def _on_selected_parameter_changed(self):
        self._selected_parameter = self.song().view.selected_parameter
        if self._selected_parameter:
            self.log_message(f"_on_selected_parameter_changed: {self._selected_parameter.name}")
        else:
            self.log_message("No parameter selected.")

    def _on_note_key(self, value, sender):
        key = sender._msg_identifier
        self.log_message(f"_on_note_on: {key}, {value}")

    def _reface_type_select_changed(self, value):
        channel = reface_type_map.get(value, 0)
        self.log_message(f"Type changed: {value} -> {channel}")
        self.set_channel(channel)

    def _reface_tremolo_toggle_changed(self, value):
        toggle_value = reface_toggle_map.get(value, REFACE_TOGGLE_OFF)
        self.set_tremolo_toggle(toggle_value)

    def _reface_chorus_toggle_changed(self, value):
        toggle_value = reface_toggle_map.get(value, REFACE_TOGGLE_OFF)
        self._update_chorus_toggle(toggle_value)

    def _reface_delay_toggle_changed(self, value):
        toggle_value = reface_toggle_map.get(value, REFACE_TOGGLE_OFF)
        self._update_delay_toggle(toggle_value)

# --- Other functions

    def map_midi_to_parameter_value(self, midi_value, parameter):
        midi_value = max(0, min(127, midi_value))
        param_min = parameter.min
        param_max = parameter.max
        return param_min + ((midi_value / 127.0) * (param_max - param_min))

    def get_selected_device(self):
        selected_track = self.song().view.selected_track
        device_to_select = selected_track.view.selected_device
        if device_to_select is None and len(selected_track.devices) > 0:
            device_to_select = selected_track.devices[0]
        return device_to_select

    def set_device_to_selected(self):
        """
        Set the DeviceComponent to manage the currently selected device in Ableton Live.
        """
        device_to_select = self.get_selected_device()
        if device_to_select is not None:
            self.log_message(f"Select Device: {device_to_select.name}")
            self._device.set_device(device_to_select)
            self.song().appointed_device = device_to_select
            self._device.update()
        else:
            self.log_message("No device to select.")

    def _lock_to_device(self, device):
        if device is not None:
            self.log_message(f"Locking to device {device.name}")
            self._locked_device = device
            self.song().appointed_device = device
            self._device_lock_button.receive_value(127)
            self._device.set_lock_to_device(True, device)
            self._device.update()

    def _unlock_from_device(self):
        device = self._locked_device
        if device is not None:
            self.log_message(f"Unlocking from device {device.name}")
            self._device.set_lock_to_device(False, device)

            # workaround to update device correctly when locked on another track. Probably doing something wrong here but this works.
            current_selection = self.song().view.selected_track.view.selected_device
            # self.log_message(f"appointed device: {self.song().appointed_device.name}. current: {current_selection.name}")
            self.song().view.select_device(device)
            self._device_lock_button.receive_value(127)
            self._device_lock_button.receive_value(0)
            self._device.update()
            if current_selection is not None:
                self.song().view.select_device(current_selection)

        self._locked_device = None

# -- Track mode

    def disable_track_mode(self):
        self._drive_knob.remove_value_listener(self._update_selected_parameter)

    def enable_track_mode(self, channel):
        self.log_message(f"enable_track_mode. channel: {channel}")
        self.disable_track_mode()
        self._drive_knob.add_value_listener(self._update_selected_parameter)

    def _update_selected_parameter(self, value):
        if self._selected_parameter:
            self.log_message(f"_update_selected_parameter. value: {value}")
            # TODO: Implement takeover or value-scaling?
            self._selected_parameter.value = self.map_midi_to_parameter_value(value, self._selected_parameter)

    def _enable_note_key_buttons(self):
        self._disable_note_key_buttons()
        for index in range(127):
            button = ButtonElement(1, MIDI_NOTE_TYPE, self._channel, index)
            button.add_value_listener(self._on_note_key, identify_sender=True)
            self._note_key_buttons.append(button)

    def _disable_note_key_buttons(self):
        for button in self._note_key_buttons:
            button.remove_value_listener(self._on_note_key)
        self._note_key_buttons = []


# --- Reface Sysex commands
# Specs: https://usa.yamaha.com/files/download/other_assets/7/794817/reface_en_dl_b0.pdf

    def _reface_sysex_header(self, device_number):
        # Returns the sysex prefix up to the address field
        return (SYSEX_START, DEVICE_ID, device_number, GROUP_HIGH, GROUP_LOW, MODEL_ID)

    def _setRefaceTransmitChannel(self, channel):
        sys_ex_message = self._reface_sysex_header(0x10) + (0x00, 0x00, 0x00, channel, SYSEX_END)
        self._send_midi(sys_ex_message)

    def request_reface_parameter(self, parameter):
        sys_ex_message = self._reface_sysex_header(0x30) + (0x30, 0x00, parameter, SYSEX_END)
        self._send_midi(sys_ex_message)

# --- Live (Inherited)

    def handle_sysex(self, midi_bytes):
        param_change_header = self._reface_sysex_header(0x10)
        self.log_message(f"handle_sysex: {midi_bytes}. param_change_header: {param_change_header}")
        if midi_bytes[:len(param_change_header)] == param_change_header:
            self._waiting_for_first_response = False
            param_id = midi_bytes[-3]
            param_value = midi_bytes[-2]
            self.log_message(f"parameter sysex response. id: {param_id}, value: {param_value}")
            if param_id == REFACE_PARAM_TYPE:
                self.set_channel(param_value)
            elif param_id == REFACE_PARAM_TREMOLO:
                self.set_tremolo_toggle(param_value)

    def disconnect(self):
        self.log_message("RefaceCP Disconnected")

        self.song().view.remove_selected_parameter_listener(self._on_selected_parameter_changed)

        self.disable_track_mode()
        self._disable_note_key_buttons()

        self._type_select_button.remove_value_listener(self._reface_type_select_changed)
        self._tremolo_toggle_button.remove_value_listener(self._reface_tremolo_toggle_changed)
        self._chorus_toggle_button.remove_value_listener(self._reface_chorus_toggle_changed)
        self._delay_toggle_button.remove_value_listener(self._reface_delay_toggle_changed)

        # TODO: Restore previous reface midi transmit channel ?

        # Calling disconnect on parent sends some MIDI that messes up or resets the reface. Why?
        # super(RefaceCP, self).disconnect()
