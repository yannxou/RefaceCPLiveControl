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

# Reface CP elements:
TYPE_SELECT_KNOB = 80
ENCODER_MSG_IDS = (81, 18, 19, 86, 87, 89, 90, 91) # Reface CP knobs from Drive to Reverb Depth

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

    def _setup_buttons(self):
        self.type_select_button = ButtonElement(1, MIDI_CC_TYPE, 0, TYPE_SELECT_KNOB)
        self.type_select_button.add_value_listener(self._type_select_changed)

    def _setup_device_control(self):
        self._device = DeviceComponent()
        self._device.name = 'Device_Component'
        device_controls = []
        for index in range(8):
            control = EncoderElement(MIDI_CC_TYPE, 0, ENCODER_MSG_IDS[index], Live.MidiMap.MapMode.absolute)
            control.name = 'Ctrl_' + str(index)
            device_controls.append(control)
        self._device.set_parameter_controls(device_controls)
        self._on_device_changed.subject = self._device
        self.set_device_component(self._device)

    @subject_slot('device')
    def _on_device_changed(self):
        if liveobj_valid(self._device):
            self.log_message("New device selected")
        else:
            # no device
            self.log_message("No device selected")

    def _type_select_changed(self, value):
        self.log_message(f"Type changed: {value}")

    def disconnect(self):
        self.log_message("RefaceCP Disconnected")
        self.type_select_button.remove_value_listener(self._type_select_changed)

        super(RefaceCP, self).disconnect()

"""
        # Initialize a simple button
        is_momentary = True
        channel = 0
        note = 60  # Middle C

        self.my_button = ButtonElement(is_momentary, MIDI_NOTE_TYPE, channel, note)
        self.my_button.add_value_listener(self.button_pressed)

    def button_pressed(self, value):
        if value > 0:  # Button pressed
            self.log_message("Button Pressed")
            self.show_message("Hello from MyController")
"""