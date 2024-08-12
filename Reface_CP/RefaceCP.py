from __future__ import absolute_import, print_function, unicode_literals
import Live
from _Framework.SessionComponent import SessionComponent
from _Framework.ControlSurface import ControlSurface
from _Framework.InputControlElement import * # MIDI_CC_TYPE
#from _Framework.InputControlElement import MIDI_NOTE_TYPE
from _Framework.SliderElement import SliderElement
from _Framework.EncoderElement import EncoderElement
from _Framework.ChannelStripComponent import ChannelStripComponent
#from _Framework.ButtonElement import ButtonElement

class RefaceCP(ControlSurface):
    def __init__(self, c_instance):
        ControlSurface.__init__(self, c_instance)
        self.log_message("RefaceCP Init Started")
        # self._suppress_send_midi = True

        # FIXME: not working? try manually setting those?
        self._suggested_input_port = "reface CP"
        self._suggested_output_port = "reface CP"

        channel = 0
        #self.type_select_knob = SliderElement(MIDI_CC_TYPE, channel, 80, name='TypeKnob', send_midi=send_midi)
        self.type_select_knob = EncoderElement(MIDI_CC_TYPE, channel, 80, Live.MidiMap.MapMode.absolute)
        self.type_select_knob.add_value_listener(self._type_select_changed)

        self.log_message("RefaceCP Init Succeeded.")

    def _type_select_changed(self, value):
        self.log_message("Type: {value}")

    def disconnect(self):
        self.type_select_knob.remove_value_listener(self.type_select_changed)

        self.log_message("RefaceCP Disconnected")
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