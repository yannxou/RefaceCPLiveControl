# NavigationController
# - Handles navigation for tracks, clips, etc
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
import Live.Song
from .Logger import Logger
from _Framework.ButtonElement import ButtonElement
from _Framework.InputControlElement import MIDI_CC_TYPE

class NavigationController:
    
    def __init__(self, logger: Logger, 
                 song: Live.Song.Song, channel = 0,
                 track_navigation_button = None
                 ):
        self._logger = logger
        self._song = song
        self._enabled = False
        self._track_navigation_button = track_navigation_button

    def set_enabled(self, enabled):
        if self._enabled == enabled:
            return
        if enabled:
            self._setup_button_listeners()
        else:
            self._disable_button_listeners()
        self._enabled = enabled

    def _setup_button_listeners(self):
        if self._track_navigation_button:
            self._track_navigation_button.add_value_listener(self._on_track_navigation_button_change)

    def _disable_button_listeners(self):
        if self._track_navigation_button:
            self._track_navigation_button.remove_value_listener(self._on_track_navigation_button_change)

    def _on_track_navigation_button_change(self, value):
        # self._logger.log(f"_on_track_navigation_button_change: {value}")
        all_tracks = list(self._song.tracks) + list(self._song.return_tracks) + [self._song.master_track]
        total_tracks = len(all_tracks)
        track_index = int((value / 127.0) * (total_tracks - 1))
        selected_track = all_tracks[track_index]
        if self._song.view.selected_track != selected_track:
            self._song.view.selected_track = selected_track
            self._logger.log(f"Select track: {selected_track.name}")

    def disconnect(self):
        self._disable_button_listeners()