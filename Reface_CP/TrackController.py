# TrackController
# - Handles the track mode controls
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
from _Framework.ChannelStripComponent import ChannelStripComponent

class TrackController:
    
    def __init__(self,
                 logger: Logger,
                 song: Live.Song.Song,
                 selected_parameter_control = None,
                 volume_control = None,
                 pan_control = None,
                 send_controls = [],
                 mute_control = None,
                 solo_control = None,
                 arm_control = None,
                 on_track_arm_changed = None
                ):
        self._logger = logger
        self._song = song
        self._enabled = False
        self._selected_parameter = None
        self._selected_parameter_control = selected_parameter_control
        self._volume_control = volume_control
        self._pan_control = pan_control
        self._send_controls = send_controls
        self._mute_control = mute_control
        self._solo_control = solo_control
        self._arm_control = arm_control
        self._on_track_arm_changed = on_track_arm_changed
        self._channel_strip = ChannelStripComponent()
        self._channel_strip.set_enabled(False)
        self._channel_strip.set_invert_mute_feedback(True)

    @property
    def track(self):
        return self._channel_strip.track

    def set_enabled(self, enabled):
        """Enables/Disables the track mode control."""
        self._enabled = enabled
        if enabled:
            self._selected_parameter_control.connect_to(self._selected_parameter)
            if not self._song.view.selected_parameter_has_listener(self._on_selected_parameter_changed):
                self._song.view.add_selected_parameter_listener(self._on_selected_parameter_changed)
            self._channel_strip.set_volume_control(self._volume_control)
            self._channel_strip.set_pan_control(self._pan_control)
            self._channel_strip.set_send_controls(self._send_controls)
            self._channel_strip.set_mute_button(self._mute_control)
            self._channel_strip.set_solo_button(self._solo_control)
            self._channel_strip.set_arm_button(self._arm_control)
            self.set_track(self._song.view.selected_track)
        else:
            self._channel_strip.set_volume_control(None)
            self._channel_strip.set_pan_control(None)
            self._channel_strip.set_send_controls(None)
            self._channel_strip.set_mute_button(None)
            self._channel_strip.set_solo_button(None)
            self._channel_strip.set_arm_button(None)
            if self._song.view.selected_parameter_has_listener(self._on_selected_parameter_changed):
                self._song.view.remove_selected_parameter_listener(self._on_selected_parameter_changed)
            self._selected_parameter_control.connect_to(None)
            self._remove_track_listeners(self._channel_strip.track)
        self._channel_strip.set_enabled(enabled)

    def set_track(self, track):
        if self._enabled:
            self._remove_track_listeners(self._channel_strip.track)        
            self._channel_strip.set_track(track)
            self._add_track_listeners(track)
            self._on_arm_changed()

    def _add_track_listeners(self, track):
        try:
            if track is not None and self._on_track_arm_changed is not None:
                if not track.arm_has_listener(self._on_arm_changed):
                    track.add_arm_listener(self._on_arm_changed)
        except:
            pass

    def _remove_track_listeners(self, track):
        try:
            if track is not None and self._on_track_arm_changed is not None:
                if track.arm_has_listener(self._on_arm_changed):
                    track.remove_arm_listener(self._on_arm_changed)
        except:
            pass
        
    def _on_selected_parameter_changed(self):
        self._selected_parameter = self._song.view.selected_parameter
        if self._enabled:
            self._selected_parameter_control.connect_to(self._selected_parameter)        

    def _on_arm_changed(self):
        if not self._enabled or not self._on_track_arm_changed:
            return
        if self._channel_strip.track.can_be_armed:
            self._on_track_arm_changed(self._channel_strip.track.arm)
        else:
            self._on_track_arm_changed(False)


    def disconnect(self):
        self._remove_track_listeners(self._channel_strip.track)
        self.set_enabled(False)
        
        self._logger = None
        self._song = None
        self._channel_strip = None
        self._selected_parameter_control = None
        self._volume_control = None
        self._pan_control = None
        self._send_controls = None
        self._mute_control = None
        self._solo_control = None
        self._arm_control = None
        self._on_track_arm_changed = None
        