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

from Live.Song import Song, Quantization

class SongUtil:

    # - Cue helpers

    @staticmethod
    def get_nearest_cue_times(song: Song):
        # Returns the positions in beats for the previous cue and next cue to the current song position.
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
            if cue_time < current_position:
                if prev_cue is None or cue_time > prev_cue.time:
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