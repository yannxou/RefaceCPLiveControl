# AudioTrackMonitoringListener
# - Listens for track changes and notifies when an audio track name with a matching substring is armed/unarmed or its monitoring state changes. 
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
import re
from functools import partial

def get_all_tracks(doc):
    all_tracks = []
    for track in doc.tracks:
        all_tracks.append(track)
        if hasattr(track, 'is_foldable') and track.is_foldable:
            all_tracks.extend(get_nested_tracks(track))
    return all_tracks

def get_nested_tracks(group_track):
    nested_tracks = []
    for track in group_track.canonical_parent.tracks:
        if hasattr(track, 'is_grouped') and track.is_grouped and track.group_track == group_track:
            nested_tracks.append(track)
            if hasattr(track, 'is_foldable') and track.is_foldable:
                nested_tracks.extend(get_nested_tracks(track))
    return nested_tracks

class AudioTrackMonitoringListener:
    
    def __init__(self, 
                 logger: Logger, 
                 song: Live.Song.Song,
                 track_name_pattern = "",
                 on_monitoring_changed = None
                ):
        self._logger = logger
        self._song = song
        self._track_name_pattern = track_name_pattern
        self._on_monitoring_changed = on_monitoring_changed
        self._track_name_listeners = {}
        self._track_arm_listeners = {}
        self._last_sent_value = False
        all_tracks = get_all_tracks(self._song)
        self._song.add_tracks_listener(self._on_tracks_changed)
        for track in all_tracks:
            if track.has_audio_input:
                self._add_track_name_listener(track)
                self._update_monitoring_listeners(track)
        self._check_monitoring_status()

    def _add_track_name_listener(self, track):
        if track._live_ptr not in self._track_name_listeners:
            self._logger.log(f"Adding name listener to track: {track.name}")
            listener = partial(self._on_track_name_changed, track)
            self._track_name_listeners[track._live_ptr] = listener
            track.add_name_listener(listener)

    def _remove_track_name_listener(self, live_ptr):
        if live_ptr in self._track_name_listeners:
            # self._logger.log("_remove_track_name_listener")
            listener = self._track_name_listeners[live_ptr]
            try:
                # Find the track object using the _live_ptr
                track = next((t for t in self._song.tracks if t._live_ptr == live_ptr), None)
                if track and track.name_has_listener(listener):
                    track.remove_name_listener(listener)
            except:
                pass
            finally:
                del self._track_name_listeners[live_ptr]

    def _add_track_arm_listener(self, track):
        if track._live_ptr not in self._track_arm_listeners:
            # self._logger.log(f"Adding arm listener to track: {track.name}")
            listener = partial(self._on_track_arm_changed, track)
            self._track_arm_listeners[track._live_ptr] = listener
            track.add_arm_listener(listener)

    def _remove_track_arm_listener(self, live_ptr):
        if live_ptr in self._track_arm_listeners:
            # self._logger.log(f"Removing arm listener from track: {live_ptr}")
            listener = self._track_arm_listeners[live_ptr]
            try:
                # Find the track object using the _live_ptr
                track = next((t for t in self._song.tracks if t._live_ptr == live_ptr), None)
                if track and track.arm_has_listener(listener):
                    track.remove_arm_listener(listener)
            except:
                pass
            finally:
                del self._track_arm_listeners[live_ptr]

    def _on_tracks_changed(self):
        """Listener function called when a track is added or deleted"""
        current_tracks = {track._live_ptr: track for track in self._song.tracks}
        previous_tracks = set(self._track_name_listeners.keys())

        # Tracks that have been removed
        removed_tracks = previous_tracks - current_tracks.keys()
        for live_ptr in removed_tracks:
            self._remove_track_name_listener(live_ptr)
            self._remove_track_arm_listener(live_ptr)

        # Tracks that have been added
        added_tracks = current_tracks.keys() - previous_tracks
        for live_ptr in added_tracks:
            track = current_tracks[live_ptr]
            if track.has_audio_input:
                self._add_track_name_listener(track)
                self._update_monitoring_listeners(track)
        
        self._check_monitoring_status()

    def _on_track_arm_changed(self, track):
        # self._logger.log(f"_on_arm_changed: {track.name}, {track.arm}")
        bypass = True if track.arm else False
        if self._on_monitoring_changed and bypass != self._last_sent_value:
            self._on_monitoring_changed(bypass)
            self._last_sent_value = bypass

    def _on_track_name_changed(self, track):
        # self._logger.log(f"_on_track_name_changed: {track.name}")
        self._update_monitoring_listeners(track)

    def _update_monitoring_listeners(self, track):
        if track.has_audio_input:
            if re.search(self._track_name_pattern, track.name, re.IGNORECASE):
                self._logger.log(f"Track match: {track.name}")
                self._add_track_arm_listener(track)
            else:
                self._remove_track_arm_listener(track)
    
    def _check_monitoring_status(self):
        bypass = self._last_sent_value
        enabled_track = next((t for t in self._song.tracks if t.has_audio_input and re.search(self._track_name_pattern, t.name, re.IGNORECASE) and t.arm), None)
        if enabled_track:
            if self._last_sent_value == False:
                bypass = True
        else:
            if self._last_sent_value == True:
                bypass = False
        if self._on_monitoring_changed and bypass != self._last_sent_value:
            self._on_monitoring_changed(bypass)
            self._last_sent_value = bypass


    def disconnect(self):
        for live_ptr in list(self._track_name_listeners.keys()):
            self._remove_track_name_listener(live_ptr)
        for live_ptr in list(self._track_arm_listeners.keys()):
            self._remove_track_arm_listener(live_ptr)
        self._song.remove_tracks_listener(self._on_tracks_changed)