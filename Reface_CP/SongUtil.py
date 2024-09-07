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

class SongUtil:
    @staticmethod
    def get_nearest_cue_times(song):
        # Returns the positions in beats for the previous cue and next cue to the current song position.
        prev_cue, next_cue = SongUtil.find_nearest_cue_points(song)
        left_time = prev_cue.time if prev_cue is not None else 0
        right_time = next_cue.time if next_cue is not None else song.last_event_time
        return left_time, right_time

    @staticmethod
    def find_nearest_cue_points(song):
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