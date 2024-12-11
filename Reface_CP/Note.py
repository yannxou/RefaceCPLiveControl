# Note
# - Includes Note constants and helper functions for MIDI notes
#
# Part of RefaceCPLiveControl
#
# Ableton Live MIDI Remote Script for the Yamaha Reface CP
#
# Author: Joan Duat
#
# Distributed under the MIT License, see LICENSE

class Note:
    c = 0
    c_sharp = 1
    d = 2
    d_sharp = 3
    e = 4
    f = 5
    f_sharp = 6
    g = 7
    g_sharp = 8
    a = 9
    a_sharp = 10
    b = 11

    # White key positions in an octave mapped to their index (0 to 6)
    white_key_mapping = {
        0: 0,  # C
        2: 1,  # D
        4: 2,  # E
        5: 3,  # F
        7: 4,  # G
        9: 5,  # A
        11: 6  # B
    }

    NOTE_NAMES = {0: "C", 1: "C#", 2: "D", 3: "D#", 4: "E", 5: "F", 6: "F#", 7: "G", 8: "G#", 9: "A", 10: "A#", 11: "B"}
    NOTE_ARRAY = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

    def midi_note_to_string(midi_note) -> str:
        if not (0 <= midi_note <= 127):
            raise ValueError("MIDI note number must be between 0 and 127.")
        
        note_name = Note.NOTE_ARRAY[midi_note % 12]
        octave = (midi_note // 12) - 1
        return f"{note_name}{octave + 1}"

    @staticmethod
    def is_black_key(note) -> bool:
        # Notes corresponding to black keys in an octave
        return note % 12 not in Note.white_key_mapping
    
    @staticmethod
    def is_white_key(note) -> bool:
        # Notes corresponding to white keys in an octave
        return note % 12 in Note.white_key_mapping

    @staticmethod
    def white_key_index(note):
        # Get the index of the white key in the white key sequence (0 to 6)
        if Note.is_white_key(note):
            return Note.white_key_mapping[note % 12]
        return None

    @staticmethod
    def white_key_distance(note1, note2):
        # Calculate the distance between two white keys without counting black keys
        if not (Note.is_white_key(note1) and Note.is_white_key(note2)):
            raise ValueError("Both notes must be white keys.")

        # Calculate the octave difference
        octave1, octave2 = note1 // 12, note2 // 12
        
        # Get the indices of the white keys within their respective octaves
        index1 = Note.white_key_index(note1)
        index2 = Note.white_key_index(note2)
        
        # Calculate the total distance
        distance = (octave2 - octave1) * 7 + (index2 - index1)

        return distance