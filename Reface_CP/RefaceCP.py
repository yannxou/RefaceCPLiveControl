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
        self._device = DeviceComponent()
        self._device.name = 'Device_Component'
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
        if liveobj_valid(self._device):
            # self.log_message("New device selected")
            self.set_device_to_selected()

    def _reface_type_select_changed(self, value):
        channel = reface_type_map.get(value, 0)
        self.log_message(f"Type changed: {value} -> {channel}")
        self._setRefaceTransmitChannel(channel)
        self._update_device_control_channel(channel)

    def _reface_tremolo_switch_changed(self, value):
        self.log_message(f"Tremolo changed: {value}")
        self.set_device_to_selected()

# --- Other functions

    def set_device_to_selected(self):
        """
        Set the DeviceComponent to manage the currently selected device in Ableton Live.
        """
        selected_track = self.song().view.selected_track
        device_to_select = selected_track.view.selected_device
        if device_to_select is None and len(selected_track.devices) > 0:
            device_to_select = selected_track.devices[0]
        if device_to_select is not None:
            self.log_message(f"Select Device: {device_to_select.name}")
            # self.log_message(f"Appointed: {self.song().appointed_device.name}")
            self._device.set_device(device_to_select)
            self._device.update()            
            self.request_rebuild_midi_map()  # This tells Live to refresh the MIDI mappings and the blue hand
            # self._device.notify_device()
        else:
            self.log_message("No device to select.")

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
