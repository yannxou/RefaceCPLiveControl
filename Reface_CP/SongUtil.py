# SongUtil
# - Some utilities for the Live Song type
#
# Part of RefaceCPLiveControl
#
# Ableton Live MIDI Remote Script for the Yamaha Reface CP
#
# Author: Joan Duat
#
# Distributed under the MIT License, see LICENSE

from Live.Device import Device
from Live.Track import Track
from Live.Song import Song, Quantization
from Live.DeviceParameter import ParameterState

class SongUtil:

    # - Clip navigation

    @staticmethod
    def select_previous_clip_slot(song: Song):
        """Set the highlighted clip to the previous clip slot in the current track"""
        current_track = song.view.selected_track
        all_clip_slots = current_track.clip_slots
        highlighted_clip_slot = song.view.highlighted_clip_slot
        if highlighted_clip_slot is None:
            return
        
        current_clip_slot_index = list(all_clip_slots).index(highlighted_clip_slot)
        if current_clip_slot_index > 0:
            song.view.highlighted_clip_slot = current_track.clip_slots[current_clip_slot_index - 1]

    @staticmethod
    def select_next_clip_slot(song: Song):
        """Set the highlighted clip to the next clip slot in the current track"""
        current_track = song.view.selected_track
        all_clip_slots = current_track.clip_slots
        highlighted_clip_slot = song.view.highlighted_clip_slot
        if highlighted_clip_slot is None:
            return
        
        current_clip_slot_index = list(all_clip_slots).index(highlighted_clip_slot)
        if current_clip_slot_index < (len(all_clip_slots) - 1):
            song.view.highlighted_clip_slot = current_track.clip_slots[current_clip_slot_index + 1]

    @staticmethod
    def select_previous_clip(song: Song):
        """Set the highlighted clip to the previous clip slot that has a clip in the current track"""
        # Get the currently selected track and highlighted clip slot
        current_track = song.view.selected_track
        highlighted_clip_slot = song.view.highlighted_clip_slot
        if highlighted_clip_slot is None:
            return

        current_clip_slot_index = list(current_track.clip_slots).index(highlighted_clip_slot)
        for clip_slot_index in range(current_clip_slot_index - 1, -1, -1):
            previous_clip_slot = current_track.clip_slots[clip_slot_index]
            if previous_clip_slot.has_clip:
                song.view.highlighted_clip_slot = previous_clip_slot
                return

    @staticmethod
    def select_next_clip(song: Song):
        """Set the highlighted clip to the next clip slot that has a clip in the current track"""
        # Get the currently selected track and highlighted clip slot
        current_track = song.view.selected_track
        highlighted_clip_slot = song.view.highlighted_clip_slot
        if highlighted_clip_slot is None:
            return

        current_clip_slot_index = list(current_track.clip_slots).index(highlighted_clip_slot)
        for clip_slot_index in range(current_clip_slot_index + 1, len(current_track.clip_slots)):
            next_clip_slot = current_track.clip_slots[clip_slot_index]
            if next_clip_slot.has_clip:
                song.view.highlighted_clip_slot = next_clip_slot
                return


    # - Device helpers

    @staticmethod
    def get_track_from_device(device: Device):
        """Recursively find the track associated with a given device."""
        parent = device.canonical_parent

        # Traverse up the parent chain until we find a Track object
        while parent is not None:
            if isinstance(parent, Track):
                return parent  # We found the track
            parent = parent.canonical_parent
        
        # If no track is found, return None
        return None
    
    @staticmethod
    def toggle_device_on_off(device: Device):
        """Toggle the on/off state of the currently appointed device."""
        on_off_param = next((param for param in device.parameters if param.name == "Device On"), None)
        if on_off_param is not None:
            if on_off_param.state != ParameterState.disabled:
                on_off_param.value = 0.0 if on_off_param.value == 1.0 else 1.0

    # - Cue helpers

    @staticmethod
    def get_nearest_cue_times(song: Song):
        """Returns the positions in beats for the previous cue and next cue to the current song position."""
        prev_cue, next_cue = SongUtil.find_nearest_cue_points(song)
        left_time = prev_cue.time if prev_cue is not None else 0
        right_time = next_cue.time if next_cue is not None else song.last_event_time
        return left_time, right_time

    @staticmethod
    def find_nearest_cue_points(song: Song):
        current_position = song.current_song_time
        prev_cue = None
        next_cue = None

        for cue_point in song.cue_points:
            cue_time = cue_point.time
            if cue_time <= current_position:
                if prev_cue is None or cue_time >= prev_cue.time:
                    prev_cue = cue_point
            elif cue_time > current_position:
                if next_cue is None or cue_time < next_cue.time:
                    next_cue = cue_point

        return prev_cue, next_cue
    
    # - Quantization helpers
    
    quantization_all = [
        Quantization.q_no_q,
        Quantization.q_8_bars,
        Quantization.q_4_bars,
        Quantization.q_2_bars,
        Quantization.q_bar,
        Quantization.q_half,
        Quantization.q_half_triplet,
        Quantization.q_quarter,
        Quantization.q_quarter_triplet,
        Quantization.q_eight,
        Quantization.q_eight_triplet,
        Quantization.q_sixtenth,
        Quantization.q_sixtenth_triplet,
        Quantization.q_thirtytwoth
    ]

    @staticmethod
    def set_next_clip_trigger_quantization(song: Song):
        current_quantization = song.clip_trigger_quantization
        if current_quantization in SongUtil.quantization_all:
            current_index = SongUtil.quantization_all.index(current_quantization)
            if current_index < len(SongUtil.quantization_all) - 1:
                next_quantization = SongUtil.quantization_all[current_index + 1]
                song.clip_trigger_quantization = next_quantization

    def set_previous_clip_trigger_quantization(song: Song):
        current_quantization = song.clip_trigger_quantization
        if current_quantization in SongUtil.quantization_all:
            current_index = SongUtil.quantization_all.index(current_quantization)
            if current_index > 0:
                previous_quantization = SongUtil.quantization_all[current_index - 1]
                song.clip_trigger_quantization = previous_quantization