# DeviceController
# - Handles device control (follow selection/locked)
#
# Part of RefaceCPLiveControl
#
# Ableton Live MIDI Remote Script for the Yamaha Reface CP
#
# Author: Joan Duat
#
# Distributed under the MIT License, see LICENSE

from .Logger import Logger
import Live.Song
from _Framework.InputControlElement import MIDI_CC_TYPE
from ableton.v2.base import listens, liveobj_valid, liveobj_changed
from _Framework.ButtonElement import ButtonElement
from _Framework.DeviceComponent import DeviceComponent

class DeviceController:
    
    def __init__(self,
                 logger: Logger,
                 song: Live.Song.Song,
                 controls
                ):
        self._logger = logger
        self._song = song
        self._enabled = False
        self._locked_device = None
        self._setup_device_control(controls)

    def set_enabled(self, enabled):
        """Enables/Disables the device control functionality."""
        self._enabled = enabled
        self._device.set_enabled(enabled)

    def set_device(self, device):
        """
        Set the DeviceComponent to manage the given device.
        """
        self._device.set_device(device)
        self._song.appointed_device = device
        self._device.update()

    def lock_to_device(self, device):
        if device is not None:
            self._locked_device = device
            self._song.appointed_device = device
            self._device_lock_button.receive_value(127)
            self._device.set_lock_to_device(True, device)
            self._device.update()

    def unlock_from_device(self):
        device = self._locked_device
        if device is not None and liveobj_valid(device):
            self._logger.log(f"Unlocking from device {device.name}")
            self._device.set_lock_to_device(False, device)

            # workaround to update device correctly when locked on another track. Probably doing something wrong here but this works.
            current_selection = self._song.view.selected_track.view.selected_device
            # self._logger.log(f"appointed device: {self.song().appointed_device.name}. current: {current_selection.name}")
            self._song.view.select_device(device)
            self._device_lock_button.receive_value(127)
            self._device_lock_button.receive_value(0)
            self._device.update()
            if current_selection is not None:
                self._song.view.select_device(current_selection)

        self._locked_device = None

    def _setup_device_control(self, controls):
        self._device_lock_button = ButtonElement(1, MIDI_CC_TYPE, 15, 100, name="DeviceLock")
        self._device = DeviceComponent(device_selection_follows_track_selection=True)
        self._device.name = 'Device_Component'
        self._device.set_lock_button(self._device_lock_button)
        self._device.set_parameter_controls(controls)

    def disconnect(self):
        self.set_enabled(False)
        self._logger = None
        self._song = None
        self._device = None
