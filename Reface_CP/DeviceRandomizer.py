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
import Live.DeviceParameter
import Live.Song
from .Logger import Logger
import random
from functools import partial
from _Framework.ControlSurface import ControlSurface
import _Framework.Task as Task

class DeviceRandomizer:
    
    def __init__(self,
                 logger: Logger,
                 parent: ControlSurface,
                 device: Live.Device.Device = None,
                 morphing_amount_button = None,
                 morphing_length_button = None,
                 param_randomization_button = None,
                 ):
        self._logger = logger
        self._song: Live.Song.Song = parent.song()
        self._enabled = False
        self._morphing_amount_button = morphing_amount_button
        self._morphing_length_button = morphing_length_button
        self._param_randomization_button = param_randomization_button
        self._device = device
        self._initial_preset = {}
        self._target_preset = {}
        self._target_parameters = []
        self._morphing_amount = 0 # 0..1
        self._morphing_length = 1 # 0..1
        self._excluded_params = ["Device On", "Chain Selector", "Macro 1", "Macro 2", "Macro 3", "Macro 4", "Macro 5", "Macro 6", "Macro 7", "Macro 8", "Macro 9", "Macro 10", "Macro 11", "Macro 12", "Macro 13", "Macro 14", "Macro 15", "Macro 16"]
        self._parameter_listeners = {}
        self._user_values = {} # Dict of param_name:value used to lock (exclude from randomization) parameters to specific values set by the user
        self._control_gesture_task = parent._tasks.add(Task.sequence(Task.delay(1), self._on_control_gesture_ended)).kill()

    def set_enabled(self, enabled):
        """Enables/Disables the device randomization functionality."""
        if self._enabled == enabled:
            return
        if enabled:
            self._setup_button_listeners()
        else:
            self._disable_button_listeners()
            self._remove_parameter_listeners()
            self._device = None
            self._user_values = {}
        self._enabled = enabled

    def set_device(self, device):
        if self._device == device:
            return
        self._device = device
        if device is None:
            return
        # self._logger.log(f"Randomizing enabled for device: {device.name}")
        self._user_values = {}
        self._capture_initial_values()
        self._randomize_target_values()
        self._update_parameter_listeners()

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

    def _update_parameter_listeners(self):
        device = self._device
        if device is None:
            return
        self._remove_parameter_listeners()
        for parameter in device.parameters:
            listener = partial(self._on_parameter_value_changed, parameter)
            self._parameter_listeners[parameter] = listener
            parameter.add_value_listener(listener)
    
    def _remove_parameter_listeners(self):
        for parameter, listener in self._parameter_listeners.items():
            try:
                if parameter.value_has_listener(listener):
                    parameter.remove_value_listener(listener)
            except:
                pass
        self._parameter_listeners = {}

    def _start_control_gesture(self):
        if not self._control_gesture_task.state == Task.RUNNING:
            self._song.begin_undo_step()
        self._control_gesture_task.restart()

    def _on_control_gesture_ended(self, args=None):
        self._song.end_undo_step()

    def _on_parameter_value_changed(self, parameter: Live.DeviceParameter.DeviceParameter):
        if self._control_gesture_task.state == Task.RUNNING:
            return
        # self._logger.log(f"Parameter changed: {parameter.name}:{parameter.value}")
        self._user_values[parameter.name] = parameter.value

    def _on_morphing_amount_button_changed(self, value):
        if self._device is None:
            return
        self._start_control_gesture()
        self._morphing_amount = value / 127.0
        self._logger.show_message(f"{self._device.name} > Morphing amount: {int(self._morphing_amount*100)}%")
        self._morph_parameters()

    def _on_morphing_length_button_changed(self, value):
        if self._device is None:
            return
        self._start_control_gesture()
        self._morphing_length = value / 127.0
        self._logger.show_message(f"{self._device.name} > Morphing length: {int(self._morphing_length*100)}%")
        self._morph_parameters() # Call only needed if we restore non-target params when morphing

        #DEBUG
        #length = int(self._morphing_length * (len(self._target_parameters)))
        #target_parameters = self._target_parameters[:length] if length > 0 else []
        #self._logger.log(f"Target parameters: {target_parameters}")

    def _on_param_randomization_button_changed(self, value):
        if self._device is None:
            return
        self._start_control_gesture()   
        self._logger.show_message(f"{self._device.name} > Randomized target values.")
        self._randomize_target_values()
        self._morph_parameters()

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
        """
        Randomizes the target parameters and their values.
        """
        self._target_preset = self._make_random_preset(self._device)
        self._target_parameters = list(self._target_preset.keys())
        random.shuffle(self._target_parameters)

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
        Values changed by the user override values from the target preset.
        """
        # Ensure morph_percentage is clamped between 0 and 1
        morph_percentage = max(0, min(1, self._morphing_amount))
        length = int(self._morphing_length * (len(self._target_parameters)))
        target_parameters = self._target_parameters[:length] if length > 0 else []

        for parameter in self._device.parameters:
            # Skip parameters that cannot be changed
            if parameter.is_enabled:
                is_user_override = parameter.name in self._user_values
                if parameter.name in target_parameters or is_user_override:
                    # Perform linear interpolation between initial and target values
                    initial_value = self._initial_preset.get(parameter.name)
                    if initial_value is not None:
                        target_value = self._user_values[parameter.name] if is_user_override else self._target_preset[parameter.name]
                        parameter.value = initial_value + (target_value - initial_value) * morph_percentage
                else:
                    # Restore initial values for non-target params?
                    value = self._initial_preset.get(parameter.name)
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

    def disconnect(self):
        self.set_enabled(False)
        self._remove_parameter_listeners()
        self._logger = None
        self._song = None
        self._morphing_amount_button = None
        self._morphing_length_button = None
        self._param_randomization_button = None
        self._device = None
        self._initial_preset = None
        self._target_preset = None
        self._target_parameters = None
        self._user_values = None
        self._control_gesture_task.kill()
        self._control_gesture_task = None

