# DeviceRandomizer
# - Handles device parameter randomization
#
# Part of RefaceCPLiveControl
#
# Ableton Live MIDI Remote Script for the Yamaha Reface CP
#
# Author: Joan Duat
#
# Distributed under the MIT License, see LICENSE

import Live.Device
from Live.DeviceParameter import ParameterState
import Live.Song
from .Logger import Logger
import random

class DeviceRandomizer:
    
    def __init__(self,
                 logger: Logger,
                 song: Live.Song.Song,
                 device: Live.Device.Device = None,
                 morphing_amount_button = None,
                 morphing_length_button = None,
                 param_randomization_button = None,
                 ):
        self._logger = logger
        self._song = song
        self._enabled = False
        self._morphing_amount_button = morphing_amount_button
        self._morphing_length_button = morphing_length_button
        self._param_randomization_button = param_randomization_button
        self._device = device
        self._initial_preset = {}
        self._target_preset = {}
        self._target_parameters = []
        self._morphing_amount = 0
        self._morphing_length = 0
        self._excluded_params = ["Device On"]

    def set_enabled(self, enabled):
        """Enables/Disables the device randomization functionality."""
        if self._enabled == enabled:
            return
        if enabled:
            self._setup_button_listeners()
            if self._device is not None:
                self._capture_initial_values()
                if len(self._target_preset) == 0:
                    self._randomize_target_values()
        else:
            self._disable_button_listeners()
            self._device = None
        self._enabled = enabled

    def set_device(self, device):
        if self._device == device:
            return
        self._device = device
        if device is None:
            return
        self._logger.log(f"Randomizing device: {device.name}")
        if self._enabled:
            self._capture_initial_values()
            self._randomize_target_values()

    def _setup_button_listeners(self):
        if self._morphing_amount_button and not self._morphing_amount_button.value_has_listener(self._on_morphing_amount_button_changed):
            self._morphing_amount_button.add_value_listener(self._on_morphing_amount_button_changed)
        if self._morphing_length_button and not self._morphing_length_button.value_has_listener(self._on_morphing_length_button_changed):
            self._morphing_length_button.add_value_listener(self._on_morphing_length_button_changed)
        if self._param_randomization_button and not self._param_randomization_button.value_has_listener(self._on_param_randomization_button_changed):
            self._param_randomization_button.add_value_listener(self._on_param_randomization_button_changed)

    def _disable_button_listeners(self):
        if self._morphing_amount_button and self._morphing_amount_button.value_has_listener(self._on_morphing_amount_button_changed):
            self._morphing_amount_button.remove_value_listener(self._on_morphing_amount_button_changed)
        if self._morphing_length_button and self._morphing_length_button.value_has_listener(self._on_morphing_length_button_changed):
            self._morphing_length_button.remove_value_listener(self._on_morphing_length_button_changed)
        if self._param_randomization_button and self._param_randomization_button.value_has_listener(self._on_param_randomization_button_changed):
            self._param_randomization_button.remove_value_listener(self._on_param_randomization_button_changed)

    def _on_morphing_amount_button_changed(self, value):
        if self._device is None:
            return
        self._morphing_amount = value / 127.0
        self._logger.log(f"Morphing amount: {self._morphing_amount}")
        self._morph_parameters()

    def _on_morphing_length_button_changed(self, value):
        if self._device is None:
            return
        self._morphing_length = int((value / 127.0) * (len(self._target_parameters) - 1))
        self._logger.log(f"Morphing length: {self._morphing_length}")
        self._morph_parameters() # Call only needed if we restore non-target params when morphing

    def _on_param_randomization_button_changed(self, value):
        if self._device is None:
            return
        self._logger.log("Randomizing preset")
        self._randomize_target_values()
        self._morph_parameters()
        # self._debug_parameter(self._song.view.selected_parameter, value)

    def _capture_initial_values(self):
        """
        Stores the device's current parameter values as the initial preset. 
        This allows returning back to this state when setting the morphing amount back to 0.
        """
        if self._device is None:
            return
        self._initial_preset = {}
        for parameter in self._device.parameters:
            self._initial_preset[parameter.name] = parameter.value

    def _randomize_target_values(self):
        self._target_preset = self._make_random_preset(self._device)
        self._target_parameters = list(self._target_preset.keys())
        random.shuffle(self._target_parameters)
        self._logger.log(f"Target params: {self._target_parameters}")

    def _make_random_preset(self, device) -> dict:
        if device is None:
            return
        preset = {}
        for parameter in device.parameters:
            if parameter.name not in self._excluded_params: #or parameter.state == ParameterState.irrelevant:
                if parameter.is_quantized:
                    preset[parameter.name] = self._map_to_value_item(random.uniform(0, 1), parameter.value_items)
                else:
                    preset[parameter.name] = random.uniform(parameter.min, parameter.max)
        return preset
        
    def _morph_parameters(self):
        """
        Morphs between an initial preset and a target preset based on a morphing percentage.
        """
        # Ensure morph_percentage is clamped between 0 and 1
        morph_percentage = max(0, min(1, self._morphing_amount))
        target_parameters = self._target_parameters[:self._morphing_length]

        for parameter in self._device.parameters:
            # Skip parameters that cannot be changed
            if parameter.is_enabled:
                if parameter.name in target_parameters:
                    # Perform linear interpolation between initial and target values
                    initial_value = self._initial_preset[parameter.name]
                    target_value = self._target_preset[parameter.name]
                    parameter.value = initial_value + (target_value - initial_value) * morph_percentage
                else:
                    # Restore initial values for non-target params?
                    value = self._initial_preset[parameter.name]
                    if value is not None:
                        parameter.value = value

    def _map_to_value_item(self, input_value, value_items):
        """
        Maps an input value evenly from the range [0, 1] to an index in the parameter value_items list.

        Args:
            input_value (float): A float value in the range [0, 1].
            value_items (list): A list of discrete items to map to.

        Returns:
            The selected item from value_items.
        """
        # Ensure input_value is clamped between 0 and 1
        input_value = max(0, min(1, input_value))

        # Determine the number of value_items
        num_items = len(value_items)

        # Map input_value to an index in value_items
        index = int(input_value * num_items)  # Compute the index
        if index == num_items:  # Handle the edge case where input_value == 1
            index = num_items - 1

        return index #value_items[index]

    def _debug_parameter(self, param, value):
        if param is None:
            return
        newvalue = value / 127.0
        self._logger.log(f"param: {param.name}, is_enabled: {param.is_enabled} is_quantized: {param.is_quantized} state: {param.state} value: {param.value}")
        if param.is_quantized:
            self._logger.log(f"param: {param.name}, value_items: {len(param.value_items)}")
            newvalue = self._map_to_value_item(newvalue, param.value_items)
        else:
            newvalue = param.min + (param.max - param.min) * newvalue
        param.value = newvalue
        self._logger.log(f"setting param: {param.name}, newvalue: {newvalue}")

    def disconnect(self):
        self.set_enabled(False)
        self._logger = None
        self._song = None
        self._morphing_amount_button = None
        self._morphing_length_button = None
        self._param_randomization_button = None
        self._device = None
        self._initial_preset = None
        self._target_preset = None
        self._target_parameters = None

