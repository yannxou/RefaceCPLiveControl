# NavigationController
# - Handles navigation for tracks, clips, devices
#
# Part of RefaceCPLiveControl
#
# Ableton Live MIDI Remote Script for the Yamaha Reface CP
#
# Author: Joan Duat
#
# Distributed under the MIT License, see LICENSE

import math
import threading
import time
import Live
import Live.Application
import Live.Song
from .Logger import Logger
from _Framework.ButtonElement import ButtonElement
from _Framework.InputControlElement import MIDI_CC_TYPE

class NavigationController:
    
    def __init__(self, logger: Logger, 
                 song: Live.Song.Song,
                 track_navigation_button = None,
                 clip_navigation_button = None,
                 device_navigation_button = None
                 ):
        self._logger = logger
        self._song = song
        self._enabled = False
        self._track_navigation_button = track_navigation_button
        self._clip_navigation_button = clip_navigation_button
        self._device_navigation_button = device_navigation_button

    def set_enabled(self, enabled):
        if self._enabled == enabled:
            return
        if enabled:
            self._setup_button_listeners()
        else:
            self._disable_button_listeners()
        self._enabled = enabled

    def _setup_button_listeners(self):
        if self._track_navigation_button and not self._track_navigation_button.value_has_listener(self._on_track_navigation_button_changed):
            self._track_navigation_button.add_value_listener(self._on_track_navigation_button_changed)
        if self._clip_navigation_button and not self._clip_navigation_button.value_has_listener(self._on_clip_navigation_button_changed):
            self._clip_navigation_button.add_value_listener(self._on_clip_navigation_button_changed)
        if self._device_navigation_button and not self._device_navigation_button.value_has_listener(self._on_device_navigation_button_changed):
            self._device_navigation_button.add_value_listener(self._on_device_navigation_button_changed)

    def _disable_button_listeners(self):
        if self._track_navigation_button and self._track_navigation_button.value_has_listener(self._on_track_navigation_button_changed):
            self._track_navigation_button.remove_value_listener(self._on_track_navigation_button_changed)
        if self._clip_navigation_button and self._clip_navigation_button.value_has_listener(self._on_clip_navigation_button_changed):
            self._clip_navigation_button.remove_value_listener(self._on_clip_navigation_button_changed)
        if self._device_navigation_button and self._device_navigation_button.value_has_listener(self._on_device_navigation_button_changed):
            self._device_navigation_button.remove_value_listener(self._on_device_navigation_button_changed)

    def _on_track_navigation_button_changed(self, value):
        # self._logger.log(f"_on_track_navigation_button_change: {value}")
        all_tracks = list(self._song.visible_tracks) + list(self._song.return_tracks) + [self._song.master_track]
        total_tracks = len(all_tracks)
        track_index = int((value / 127.0) * (total_tracks - 1))
        selected_track = all_tracks[track_index]
        if self._song.view.selected_track != selected_track:
            self._song.view.selected_track = selected_track
            # self._logger.log(f"Select track: {selected_track.name}")

    def _on_clip_navigation_button_changed(self, value):
        selected_track = self._song.view.selected_track

        view = Live.Application.get_application().view
        if not view.is_view_visible("Detail/Clip"):
            view.show_view("Detail/Clip")

        if selected_track == self._song.master_track:
            total_scenes = len(self._song.scenes)
            scene_index = int((value / 127.0) * (total_scenes - 1))
            self._song.view.selected_scene = self._song.scenes[scene_index]
        else:
            total_clip_slots = len(selected_track.clip_slots)
            if total_clip_slots > 0:
                clip_index = int((value / 127.0) * (total_clip_slots - 1))
                self._song.view.highlighted_clip_slot = selected_track.clip_slots[clip_index]

    def _on_device_navigation_button_changed(self, value):
        view = Live.Application.get_application().view
        if not view.is_view_visible("Detail/DeviceChain"):
            view.show_view("Detail/DeviceChain")

        selected_track = self._song.view.selected_track
        devices = selected_track.devices
        # TODO: Build list with subdevices from groups?
        total_devices = len(devices)
        if total_devices > 0:
            device_index = int((value / 127.0) * (total_devices - 1))
            selected_device = devices[device_index]
            self._song.view.select_device(selected_device, True)

    def disconnect(self):
        self._disable_button_listeners()