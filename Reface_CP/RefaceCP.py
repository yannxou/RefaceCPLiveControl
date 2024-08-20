from __future__ import absolute_import, print_function, unicode_literals
import Live
from _Framework.ControlSurface import ControlSurface
from _Framework.MixerComponent import MixerComponent
from _Framework.TransportComponent import TransportComponent
from _Framework.SessionComponent import SessionComponent
from _Framework.EncoderElement import *
from _Framework.ButtonElement import ButtonElement
from _Framework.SliderElement import SliderElement
from _Framework.InputControlElement import MIDI_NOTE_TYPE, MIDI_NOTE_ON_STATUS, MIDI_NOTE_OFF_STATUS, MIDI_CC_TYPE
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
ENCODER_MSG_IDS = (81, 18, 19, 86, 87, 89, 90, 91) # Reface CP knobs from Drive to Reverb Depth
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
            # self._suppress_send_midi = True
            self._locked_device = None
            self._selected_parameter = None
            self._channel = 0
            self._tremolo_toggle_value = REFACE_TOGGLE_OFF
            self._type_select_buttons = []
            self._tremolo_toggle_buttons = []
            self._custom_knob_controls = []

            # FIXME: not working? try manually setting those?
            self._suggested_input_port = "reface CP"
            self._suggested_output_port = "reface CP"

            self._setup_initial_values()
            self._setup_buttons()
            self._setup_device_control()
            self._setup_song_listeners()

            self.log_message("RefaceCP Init Succeeded.")

# --- Setup

    def _setup_initial_values(self):
        self._waiting_for_first_response = True
        self.schedule_message(25, self._request_initial_values) # delay call otherwise it silently fails during init stage

    def _request_initial_values(self):
        self.request_reface_parameter(REFACE_PARAM_TYPE)
        self.request_reface_parameter(REFACE_PARAM_TREMOLO)

    def _setup_buttons(self):
        # Add listeners for each channel (so they keep working as channel changes)
        for index in range(len(reface_type_map)):
            # Type select knob
            button = ButtonElement(1, MIDI_CC_TYPE, index, TYPE_SELECT_KNOB)
            button.add_value_listener(self._reface_type_select_changed)
            self._type_select_buttons.append(button)
            # Tremolo toggle button
            toggle = ButtonElement(1, MIDI_CC_TYPE, index, TREMOLO_WAH_TOGGLE)
            toggle.add_value_listener(self._reface_tremolo_toggle_changed)
            self._tremolo_toggle_buttons.append(toggle)

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
        if self._tremolo_toggle_value == REFACE_TOGGLE_DOWN:
            self.enable_custom_knob_controls(channel)
        else:
            self._update_device_control_channel(channel)

    def set_tremolo_toggle(self, value):
        self.log_message(f"set_tremolo_toggle: {value}")
        self._tremolo_toggle_value = value

        if value == REFACE_TOGGLE_UP:
            self.disable_custom_knob_controls()
            selected_device = self.get_selected_device()
            self.log_message(f"Device locked: {selected_device.name}")
            self._update_device_control_channel(self._channel)
            self.set_device_component(self._device)
            self._lock_to_device(selected_device)
        elif value == REFACE_TOGGLE_DOWN:
            self._unlock_from_device()
            self._device.set_parameter_controls(None)
            self.set_device_component(None)
            self.enable_custom_knob_controls(self._channel)
        else:
            self.log_message("Device lock off. Following selected device.")
            self.disable_custom_knob_controls()
            self._update_device_control_channel(self._channel)
            self._unlock_from_device()
            self.set_device_component(self._device)
            self.set_device_to_selected()
        self.request_rebuild_midi_map()

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

    def _reface_type_select_changed(self, value):
        channel = reface_type_map.get(value, 0)
        self.log_message(f"Type changed: {value} -> {channel}")
        self.set_channel(channel)

    def _reface_tremolo_toggle_changed(self, value):
        toggle_value = reface_toggle_map.get(value, REFACE_TOGGLE_OFF)
        self.set_tremolo_toggle(toggle_value)

    def _reface_knob_changed(self, value, sender):
        index = int(sender.name.split('_')[-1])
        self.log_message(f"_reface_knob_changed. sender: {index}, value: {value}")
        if index == 0 and self._selected_parameter:
            self._selected_parameter.value = value

# --- Other functions

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

    def disable_custom_knob_controls(self):
        for button in self._custom_knob_controls:
            button.remove_value_listener(self._reface_knob_changed)
        self._custom_knob_controls = []

    def enable_custom_knob_controls(self, channel):
        self.log_message(f"enable_custom_knob_controls. channel: {channel}")
        self.disable_custom_knob_controls()

        for index in range(8):
            control = EncoderElement(MIDI_CC_TYPE, channel, ENCODER_MSG_IDS[index], Live.MidiMap.MapMode.absolute)
            control.name = 'Knob_' + str(index)
            control.add_value_listener(self._reface_knob_changed, identify_sender=True)
            self._custom_knob_controls.append(control)


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

# --- MIDI sysex handling

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

        self.disable_custom_knob_controls()

        for button in self._type_select_buttons:
            button.remove_value_listener(self._reface_type_select_changed)
        self._type_select_buttons = []

        for button in self._tremolo_toggle_buttons:
            button.remove_value_listener(self._reface_tremolo_toggle_changed)
        self._tremolo_toggles = []

        # TODO: Restore previous reface midi transmit channel ?

        # Calling disconnect on parent sends some MIDI that messes up or resets the reface. Why?
        # super(RefaceCP, self).disconnect()
