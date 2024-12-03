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

import Live
from Live.Device import Device
from Live.Track import Track, RoutingTypeCategory
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
            
    @staticmethod
    def find_first_free_scene_index(tracks):
        """
        Find the first free scene index in Ableton Live where all given tracks
        have empty clip slots, starting from the last scene.
        
        Args:
            tracks: The list of tracks.
        
        Returns:
            int: The index of the first free scene, or -1 if none found.
        """
        song = Live.Application.get_application().get_document()
        scenes = song.scenes
        free_scene_index = -1
        for scene_index in reversed(range(len(scenes))):
            all_slots_empty = all(
                track.clip_slots[scene_index].has_clip == False and track.clip_slots[scene_index].has_stop_button == True
                for track in tracks
            )
            if all_slots_empty:
                free_scene_index = scene_index
            else:
                return free_scene_index

        return free_scene_index

    @staticmethod
    def start_quick_recording():
        """
        Starts recording clips on the next free scene of all armed tracks, creating a new scene if necessary. 
        If no track is armed the current track will be armed automatically if possible.
        """
        song = Live.Application.get_application().get_document()
        armed_tracks = [track for track in song.tracks if track.can_be_armed and track.arm]
        if not armed_tracks:
            # Try auto-arm selected track
            track = song.view.selected_track
            if track.can_be_armed:
                track.arm = True
                if track.arm:
                    armed_tracks = [track]
            else:
                return
        scene_index = SongUtil.find_first_free_scene_index(armed_tracks)
        if scene_index < 0:
            song.create_scene(-1)
            scene_index = len(song.scenes) - 1
        for track in armed_tracks:
            clip_slot = track.clip_slots[scene_index]
            clip_slot.fire()

    @staticmethod
    def find_first_resampling_track():
        """
        Find the first track in the Ableton Live set that is set to "Resampling" as its input source.
        
        Returns:
            Live.Track.Track or None: The first track with "Resampling" input, or None if not found.
        """
        song = Live.Application.get_application().get_document()
        for track in song.tracks:
            if track.has_audio_input:
                if track.input_routing_type.category == RoutingTypeCategory.resampling:
                    return track
        return None
    
    @staticmethod
    def start_quick_resampling(select_first: bool = False):
        """
        Starts recording a clip on the next free slot of the first track with "Resampling" input, creating a new scene if necessary. 
        If no track exists with the "Resampling" input routing a new one is created.

        Args:
            select_first: When True, if a resampling clip is already being recorded and is not selected it will be selected first.
        """
        song = Live.Application.get_application().get_document()
        resampling_track = SongUtil.find_first_resampling_track()
        if resampling_track is None:
            resampling_track = song.create_audio_track(-1)
            for routing_type in resampling_track.available_input_routing_types:
                if routing_type.category == RoutingTypeCategory.resampling:
                    resampling_track.input_routing_type = routing_type
                    break
        else:
            recording_clip_slot = next((slot for slot in resampling_track.clip_slots if slot.has_clip and slot.clip.is_recording), None)
            if recording_clip_slot is not None:
                if recording_clip_slot != song.view.highlighted_clip_slot and select_first:
                    song.view.highlighted_clip_slot = recording_clip_slot
                    Live.Application.get_application().view.show_view("Detail/Clip")
                    return
        scene_index = SongUtil.find_first_free_scene_index([resampling_track])
        if scene_index < 0:
            song.create_scene(-1)
            scene_index = len(song.scenes) - 1
        if not resampling_track.arm:
            resampling_track.arm = True
        resampling_track.clip_slots[scene_index].fire()
        # Focus new clip
        song.view.highlighted_clip_slot = resampling_track.clip_slots[scene_index]
        Live.Application.get_application().view.show_view("Detail/Clip")

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