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

# Reface CP MIDI CCs:
TYPE_SELECT_KNOB = 80
ENCODER_MSG_IDS = (81, 18, 19, 86, 87, 89, 90, 91) # Reface CP knobs from Drive to Reverb Depth
TREMOLO_WAH_SWITCH = 17
TREMOLO_ON_VALUE = 64
WAH_ON_VALUE = 127
CHORUS_PHASER_SWITCH = 85
DELAY_SWITCH = 88

# Reface type knob CC value to MIDI channel map
reface_type_map = {
    0: 0,
    25: 1,
    51: 2,
    76: 3,
    102: 4,
    127: 5
}

class RefaceCP(ControlSurface):
    def __init__(self, c_instance):
        ControlSurface.__init__(self, c_instance)
        with self.component_guard():
            self.log_message("RefaceCP Init Started")
            # self._suppress_send_midi = True
            self._locked_device = None

            # FIXME: not working? try manually setting those?
            self._suggested_input_port = "reface CP"
            self._suggested_output_port = "reface CP"

            self._setup_buttons()
            self._setup_device_control()

            self.log_message("RefaceCP Init Succeeded.")

# --- Setup

    def _setup_buttons(self):
        # Add listeners for each channel (so they keep working as channel changes)
        self._type_select_buttons = []
        self._tremolo_switch_buttons = []
        for index in range(len(reface_type_map)):
            # Type select knob
            button = ButtonElement(1, MIDI_CC_TYPE, index, TYPE_SELECT_KNOB)
            button.add_value_listener(self._reface_type_select_changed)
            self._type_select_buttons.append(button)
            # Tremolo switch button
            switch = ButtonElement(1, MIDI_CC_TYPE, index, TREMOLO_WAH_SWITCH)
            switch.add_value_listener(self._reface_tremolo_switch_changed)
            self._tremolo_switch_buttons.append(switch)


    def _setup_device_control(self):
        self._device_lock_button = ButtonElement(1, MIDI_CC_TYPE, 15, 100, name="DeviceLock")
        self._device = DeviceComponent()
        self._device.name = 'Device_Component'
        self._device.set_lock_button(self._device_lock_button)
        self._update_device_control_channel(0) # TODO: Initialize with current reface channel
        self._on_device_changed.subject = self._device
        self.set_device_component(self._device)


    def _update_device_control_channel(self, channel):
        device_controls = []
        for index in range(8):
            control = EncoderElement(MIDI_CC_TYPE, channel, ENCODER_MSG_IDS[index], Live.MidiMap.MapMode.absolute)
            control.name = 'Ctrl_' + str(index)
            device_controls.append(control)
        self._device.set_parameter_controls(device_controls)

# --- Listeners

    @subject_slot('device')
    def _on_device_changed(self):
        # self.log_message("on_device_changed")
        if liveobj_valid(self._device):
            self.set_device_to_selected()

    def _reface_type_select_changed(self, value):
        channel = reface_type_map.get(value, 0)
        self.log_message(f"Type changed: {value} -> {channel}")
        self._setRefaceTransmitChannel(channel)
        self._update_device_control_channel(channel)

    def _reface_tremolo_switch_changed(self, value):
        if value == TREMOLO_ON_VALUE:
            selected_device = self.get_selected_device()
            self.log_message(f"Device locked: {selected_device.name}")
            self._update_device_control_channel(0) # use current_channel
            self.set_device_component(self._device)
            self._lock_to_device(selected_device)
        elif value == WAH_ON_VALUE:
            # self.log_message("Not implemented yet.")
            self._unlock_from_device()
            self._device.set_parameter_controls(None)
            self.set_device_component(None)
        else:
            self.log_message("Device lock off. Following selected device.")
            self._update_device_control_channel(0) # use current_channel
            self._unlock_from_device()
            self.set_device_component(self._device)
            self.set_device_to_selected()
            self.request_rebuild_midi_map()

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
            self.log_message(f"appointed device: {self.song().appointed_device.name}. current: {current_selection.name}")
            self.song().view.select_device(device)

            self._device_lock_button.receive_value(127)
            self._device_lock_button.receive_value(0)
            self._device.update()

            if current_selection is not None:
                self.song().view.select_device(current_selection)

        self._locked_device = None


# --- Reface Sysex commands
# Specs: https://usa.yamaha.com/files/download/other_assets/7/794817/reface_en_dl_b0.pdf

    def _setRefaceTransmitChannel(self, channel):
        sysex_start = 0xF0  # SysEx message start
        sysex_end = 0xF7  # SysEx message end
        device_id = 0x43 # Yamaha ID
        device_number = 0x10 # Device Number
        group_high = 0x7F # Group number high
        group_low = 0x1C # Group number low
        model_id = 0x04 # Model ID
        sys_ex_message = (sysex_start, device_id, device_number, group_high, group_low, model_id, 0x00, 0x00, 0x00, channel, sysex_end)
        self._send_midi(sys_ex_message)


    def disconnect(self):
        self.log_message("RefaceCP Disconnected")
        for button in self._type_select_buttons:
            button.remove_value_listener(self._reface_type_select_changed)
        self._type_select_buttons = []

        for button in self._tremolo_switch_buttons:
            button.remove_value_listener(self._reface_tremolo_switch_changed)
        self._tremolo_switches = []

        super(RefaceCP, self).disconnect()
