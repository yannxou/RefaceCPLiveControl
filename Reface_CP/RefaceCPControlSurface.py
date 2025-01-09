# RefaceCPControlSurface
# - Main class adding behaviour for the Reface CP Live control surface
#
# Part of RefaceCPLiveControl
#
# Ableton Live MIDI Remote Script for the Yamaha Reface CP
#
# Author: Joan Duat
#
# Distributed under the MIT License, see LICENSE

from __future__ import absolute_import, print_function, unicode_literals
import re
import Live
import Live.Track
from .RefaceCP import *
from .Logger import Logger
from _Framework.ControlSurface import ControlSurface
from _Framework.MixerComponent import MixerComponent
from _Framework.TransportComponent import TransportComponent
from _Framework.SessionComponent import SessionComponent
from _Framework.EncoderElement import *
from _Framework.ButtonElement import ButtonElement
from _Framework.SliderElement import SliderElement
from _Framework.InputControlElement import MIDI_NOTE_TYPE, MIDI_NOTE_ON_STATUS, MIDI_NOTE_OFF_STATUS, MIDI_CC_STATUS, MIDI_CC_TYPE
from ableton.v2.base import listens, liveobj_valid, liveobj_changed
from .RotaryToggleElement import RotaryToggleElement
from .DeviceController import DeviceController
from .TrackController import TrackController
from .TransportController import TransportController
from .NavigationController import NavigationController
from .NoteRepeatController import NoteRepeatController
from .ScaleModeController import ScaleModeController
from .ClipLauncherController import ClipLauncherController
from .AudioTrackMonitoringListener import AudioTrackMonitoringListener

# Live Routing Category values
ROUTING_CATEGORY_NONE = 6
ROUTING_CATEGORY_EXTERNAL = 0
ROUTING_CATEGORY_RESAMPLING = 2
ROUTING_CATEGORY_PARENT_GROUP_TRACK = 4 # Audio from another track?
ROUTING_CATEGORY_MASTER = 3 # Audio from Main?
ROUTING_CATEGORY_MIDI = 7 # Not sure which value is but corresponds to MIDI tracks

class RefaceCPControlSurface(ControlSurface):
    def __init__(self, c_instance):
        ControlSurface.__init__(self, c_instance)
        self._logger = Logger(c_instance)
        with self.component_guard():
            self._logger.log("RefaceCPControlSurface Init Started")
            self._refaceCP = RefaceCP(
                self._logger, self._send_midi,
                on_device_identified = self._on_device_identified,
                receive_tone_parameter = self._receive_tone_parameter
            )

            self._suppress_send_midi = True
            self._all_controls = []
            self._channel = 0
            self._rx_channel = 0x0F # Reface MIDI receive channel (used for manual feedback like updating leds)
            self._tremolo_toggle_value = -1
            self._chorus_toggle_value = -1
            self._delay_toggle_value = -1

            self._suggested_input_port = MODEL_NAME
            self._suggested_output_port = MODEL_NAME

            self._audioTrackMonitoringListener = AudioTrackMonitoringListener(
                self._logger,
                song=self.song(),
                track_name_pattern=r"(" + "|".join(["Reface CP", "RefaceCP", "Reface_CP"]) + r")",
                on_monitoring_changed=self._on_reface_track_monitoring_changed
            )

            self._waiting_for_first_response = True
            self.schedule_message(10, self._continue_init) # delay call otherwise it silently fails during init stage

            self._logger.log("RefaceCP Init.")


# --- Setup

    def _continue_init(self):
        self._refaceCP.request_identity()

    def _on_device_identified(self):
        self._logger.log("RefaceCP Identification Succeeded.")
        self._enable_reface_script_mode()
        self._setup_buttons()
        self._device_controller = DeviceController(
            self._logger,
            song=self.song(),
            controls=[self._drive_knob, self._tremolo_depth_knob, self._tremolo_rate_knob, self._chorus_depth_knob, self._chorus_speed_knob, self._delay_depth_knob, self._delay_time_knob, self._reverb_depth_knob]
        )
        self.set_device_component(self._device_controller._device)
        self._setup_navigation_controller()
        self._setup_track_controller()
        self._transport_controller = TransportController(
            self._logger,
            self.song(),
            channel=self._channel
        )
        self._setup_note_repeat()
        self._setup_scale_controller()
        self._setup_clip_launcher()
        self._refaceCP.request_current_values()

    def _receive_tone_parameter(self, parameter: ToneParameter, value):
        if parameter == ToneParameter.REFACE_PARAM_TYPE:
            self.set_channel(value)
        elif parameter == ToneParameter.REFACE_PARAM_TREMOLO_TOGGLE:
            self._tremolo_toggle_value = value
        elif parameter == ToneParameter.REFACE_PARAM_CHORUS_TOGGLE:
            self._chorus_toggle_value = value
        elif parameter == ToneParameter.REFACE_PARAM_DELAY_TOGGLE:
            self._delay_toggle_value = value

        if self._is_initialized:
            if self._waiting_for_first_response:
                self._waiting_for_first_response = False
                self._suppress_send_midi = False
            self._check_current_mode()

    def _setup_buttons(self):
        self._type_select_button = ButtonElement(1, MIDI_CC_TYPE, self._channel, TYPE_SELECT_KNOB)
        self._type_select_button.add_value_listener(self._reface_type_select_changed)
        self._all_controls.append(self._type_select_button)

        self._drive_knob = EncoderElement(MIDI_CC_TYPE, self._channel, DRIVE_KNOB, Live.MidiMap.MapMode.absolute)
        self._all_controls.append(self._drive_knob)
        self._tremolo_depth_knob = EncoderElement(MIDI_CC_TYPE, self._channel, TREMOLO_DEPTH_KNOB, Live.MidiMap.MapMode.absolute)
        self._all_controls.append(self._tremolo_depth_knob)
        self._tremolo_rate_knob = EncoderElement(MIDI_CC_TYPE, self._channel, TREMOLO_RATE_KNOB, Live.MidiMap.MapMode.absolute)
        self._all_controls.append(self._tremolo_rate_knob)
        self._chorus_depth_knob = EncoderElement(MIDI_CC_TYPE, self._channel, CHORUS_DEPTH_KNOB, Live.MidiMap.MapMode.absolute)
        self._all_controls.append(self._chorus_depth_knob)
        self._chorus_speed_knob = EncoderElement(MIDI_CC_TYPE, self._channel, CHORUS_SPEED_KNOB, Live.MidiMap.MapMode.absolute)
        self._all_controls.append(self._chorus_speed_knob)
        self._delay_depth_knob = EncoderElement(MIDI_CC_TYPE, self._channel, DELAY_DEPTH_KNOB, Live.MidiMap.MapMode.absolute)
        self._all_controls.append(self._delay_depth_knob)
        self._delay_time_knob = EncoderElement(MIDI_CC_TYPE, self._channel, DELAY_TIME_KNOB, Live.MidiMap.MapMode.absolute)
        self._all_controls.append(self._delay_time_knob)
        self._reverb_depth_knob = EncoderElement(MIDI_CC_TYPE, self._channel, REVERB_DEPTH_KNOB, Live.MidiMap.MapMode.absolute)
        self._all_controls.append(self._reverb_depth_knob)

        self._tremolo_toggle_button = ButtonElement(1, MIDI_CC_TYPE, self._channel, TREMOLO_WAH_TOGGLE)
        self._tremolo_toggle_button.add_value_listener(self._reface_tremolo_toggle_changed)
        self._all_controls.append(self._tremolo_toggle_button)

        self._chorus_toggle_button = ButtonElement(1, MIDI_CC_TYPE, self._channel, CHORUS_PHASER_TOGGLE)
        self._chorus_toggle_button.add_value_listener(self._reface_chorus_toggle_changed)
        self._all_controls.append(self._chorus_toggle_button)

        self._delay_toggle_button = ButtonElement(1, MIDI_CC_TYPE, self._channel, DELAY_TOGGLE)
        self._delay_toggle_button.add_value_listener(self._reface_delay_toggle_changed)
        self._all_controls.append(self._delay_toggle_button)

    def _setup_navigation_controller(self):
        self._navigation_controller = NavigationController(
            self._logger,
            self.song(),
            track_navigation_button=self._drive_knob,
            clip_navigation_button=self._tremolo_depth_knob,
            device_navigation_button=self._tremolo_rate_knob
        )

    def _setup_track_controller(self):
        mute_button = RotaryToggleElement(0, MIDI_CC_TYPE, self._channel, DELAY_DEPTH_KNOB)
        self._all_controls.append(mute_button)
        solo_button = RotaryToggleElement(0, MIDI_CC_TYPE, self._channel, DELAY_TIME_KNOB)
        self._all_controls.append(solo_button)
        arm_button = RotaryToggleElement(0, MIDI_CC_TYPE, self._channel, REVERB_DEPTH_KNOB)
        self._all_controls.append(arm_button)
        self._track_controller = TrackController(
            self._logger,
            song=self.song(),
            selected_parameter_control=self._drive_knob,
            volume_control=self._tremolo_depth_knob,
            pan_control=self._tremolo_rate_knob,
            send_controls=[self._chorus_depth_knob, self._chorus_speed_knob],
            mute_control=mute_button,
            solo_control=solo_button,
            arm_control=arm_button,
            on_track_arm_changed=self._on_track_arm_changed
        )

    def _setup_note_repeat(self):
        self._note_repeat_controller = NoteRepeatController(
            self._logger, 
            self._c_instance.note_repeat,
            repeat_rate_button=self._delay_time_knob,
            notes_per_bar_button=self._delay_depth_knob
        )

    def _setup_scale_controller(self):
        scale_edit_mode_button = RotaryToggleElement(0, MIDI_CC_TYPE, self._channel, REVERB_DEPTH_KNOB)
        self._all_controls.append(scale_edit_mode_button)
        self._scale_controller = ScaleModeController(
            self._logger,
            song=self.song(),
            root_note_button=self._chorus_depth_knob,
            scale_mode_button=self._chorus_speed_knob,
            edit_mode_button=scale_edit_mode_button,
            on_edit_mode_changed=self._on_scale_edit_mode_changed,
            on_note_event = self._play_note
        )

    def _setup_clip_launcher(self):
        clip_scene_target_button = RotaryToggleElement(0, MIDI_CC_TYPE, self._channel, CHORUS_SPEED_KNOB)
        self._all_controls.append(clip_scene_target_button)
        self._clip_launcher_controller = ClipLauncherController(
            logger=self._logger, 
            parent=self, 
            channel=self._channel,
            trigger_quantization_button=self._drive_knob,
            horizontal_offset_button=self._tremolo_depth_knob,
            vertical_offset_button=self._tremolo_rate_knob,
            note_layout_button=self._chorus_depth_knob,
            clip_scene_target_button=clip_scene_target_button
        )

    @property
    def _is_initialized(self):
        return self._tremolo_toggle_value >= 0 and self._chorus_toggle_value >= 0 and self._delay_toggle_value >= 0
    
# --- Reface

    def _enable_reface_script_mode(self):
        self._refaceCP.set_midi_control(True)
        self._refaceCP.set_receive_channel(0x0F)
        self._refaceCP.set_local_control(False)
        self._refaceCP.set_speaker_output(False)
        self._refaceCP.set_transmit_channel(self._channel)

    def _restore_reface_state(self, speaker_on=True):
        self._refaceCP.set_local_control(True)
        self._refaceCP.set_transmit_channel(0)
        self._refaceCP.set_receive_channel(0x10)
        self._refaceCP.set_speaker_output(speaker_on)

# --- 

    def _arm_tracks_for_channel(self, channel, select=False):
        # Arms all MIDI tracks from reface input and the given channel, disabling arm on the other reface input tracks.
        channel_tracks, other_channel_tracks = self._input_midi_tracks(channel)
        for track in other_channel_tracks:
            track.arm = False
        for track in channel_tracks:
            track.arm = True
        if select and len(channel_tracks) > 0:
            self.song().view.selected_track = channel_tracks[0]

    def _input_midi_tracks(self, channel):
        # Return two lists of MIDI tracks that have an input routing matching the reface input, one with tracks matching the given channel and another with non-matching.
        # Note: Track routing info is not available right away when the script starts. We need some delay before this is available.
        channel_tracks = []
        other_channel_tracks = []
        channel_prefix = "Ch. "
        for track in self.song().visible_tracks:
            input_routing_type = track.input_routing_type       # same as 'current_input_routing' which is now deprecated
            input_routing_channel = track.input_routing_channel # same as 'current_input_sub_routing' which is now deprecated
            if (input_routing_channel.layout == Live.Track.RoutingChannelLayout.midi 
                and input_routing_type.category == ROUTING_CATEGORY_MIDI
                and MODEL_NAME in input_routing_type.display_name):
                if input_routing_channel.display_name == f"{channel_prefix}{channel+1}":
                    channel_tracks.append(track)
                else:
                    other_channel_tracks.append(track)
        return channel_tracks, other_channel_tracks

    def set_channel(self, channel):
        self._channel = channel
        self._refaceCP.set_transmit_channel(channel)
        for control in self._all_controls:
            control.set_channel(channel)
        self._transport_controller.set_channel(channel)
        self._scale_controller.set_channel(channel)
        self._clip_launcher_controller.set_channel(channel)

# --- Listeners

    def _on_reface_track_monitoring_changed(self, track: Live.Track.Track, bypass: bool):
        if not self._is_initialized:
            return
        self._logger.log(f"_on_reface_track_monitoring_changed: bypass {bypass}")
        # Find all prpoerty/values with the format "property1:value1 property2:value2"
        matches = re.findall(r"(\w+):(\w+)", track.name)
        properties = {key: value for key, value in matches}
        self.set_enabled(not bypass, properties)

    def _reface_type_select_changed(self, value):
        index = reface_type_map.get(value, 0)
        self._logger.log(f"Type changed: {value} -> {index}")

        if self._scale_controller._enabled and self._scale_controller._edit_mode_enabled:
            return # disable control while in scale edit mode
        
        if self.is_device_lock_mode_enabled:
            new_index = self._device_controller.set_bank_index(index)
            self._send_midi((0xB0 | self._rx_channel, TYPE_SELECT_KNOB, next(key for key, value in reface_type_map.items() if value == new_index)))
            return

        self.set_channel(index)
        self._arm_tracks_for_channel(index, select=True)
        self._send_midi((0xB0 | self._rx_channel, TYPE_SELECT_KNOB, value))  # Update led in device since we disabled local control

    def _reface_tremolo_toggle_changed(self, value):
        self._set_tremolo_toggle(reface_toggle_map.get(value, REFACE_TOGGLE_OFF))

    def _reface_chorus_toggle_changed(self, value):
        self._set_chorus_toggle(reface_toggle_map.get(value, REFACE_TOGGLE_OFF))

    def _reface_delay_toggle_changed(self, value):
        self._set_delay_toggle(reface_toggle_map.get(value, REFACE_TOGGLE_OFF))

    def _on_track_arm_changed(self, arm):
        self._send_midi((0xB0 | self._rx_channel, REVERB_DEPTH_KNOB, 127 if arm else 0))
    
# --- Other functions

    def map_midi_to_parameter_value(self, midi_value, parameter):
        midi_value = max(0, min(127, midi_value))
        param_min = parameter.min
        param_max = parameter.max
        return param_min + ((midi_value / 127.0) * (param_max - param_min))

    def get_selected_device(self):
        selected_track = self.song().view.selected_track
        device_to_select = selected_track.view.selected_device
        if device_to_select is None and len(selected_track.devices) > 0:
            device_to_select = selected_track.devices[0]
        return device_to_select

    def set_device_to_selected(self):
        """
        Set the DeviceComponent to manage the currently selected device in Ableton Live.
        """
        device_to_select = self.get_selected_device()
        if device_to_select is not None:
            self._logger.log(f"Select Device: {device_to_select.name}")
            self._device_controller.set_device(device_to_select)
            self._transport_controller.set_locked_device(device_to_select)
        else:
            self._logger.log("No device to select.")

    def _lock_to_device(self, device):
        if device is not None and self._is_initialized:
            self._logger.log(f"Locking to device {device.name}")
            self._device_controller.lock_to_device(device)
            self._device_controller.set_bank_index(0)
            self._send_midi((0xB0 | self._rx_channel, TYPE_SELECT_KNOB, next(key for key, value in reface_type_map.items() if value == 0)))
            self._transport_controller.set_locked_device(device)

    def _unlock_from_device(self):
        if self._is_initialized:
            self._device_controller.unlock_from_device()
            self._device_controller.set_bank_index(0)
            self._send_midi((0xB0 | self._rx_channel, TYPE_SELECT_KNOB, next(key for key, value in reface_type_map.items() if value == self._channel)))
            self._transport_controller.set_locked_device(None)

# -- Modes

    def _check_current_mode(self):
        if self.is_navigation_mode_enabled:
            self._enable_navigation_mode()
        else:
            if self.is_note_repeat_enabled:
                self._note_repeat_controller.set_enabled(True)
                self._note_repeat_controller.set_controls_enabled(False)
            if self.is_scale_mode_enabled:
                self._scale_controller.set_enabled(True, enable_controls=False)
            if self.is_clip_mode_enabled:
                self._clip_launcher_controller.set_enabled(True)
            self._check_device_track_modes()
            
    def _check_device_track_modes(self):
        if self.is_navigation_mode_enabled:
            return
        if self.is_track_mode_enabled:
            self._enable_track_mode()
        else:
            self._device_controller.set_enabled(True)
            if self.is_device_follow_mode_enabled:
                self._enable_device_follow_mode()
            elif self.is_device_lock_mode_enabled:
                current_bank = self._device_controller._device._bank_index
                self._send_midi((0xB0 | self._rx_channel, TYPE_SELECT_KNOB, next(key for key, value in reface_type_map.items() if value == current_bank)))

        self._send_midi((0xB0 | self._rx_channel, TREMOLO_WAH_TOGGLE, 64))
        self._send_midi((0xB0 | self._rx_channel, CHORUS_PHASER_TOGGLE, 0))
        self._send_midi((0xB0 | self._rx_channel, DELAY_TOGGLE, 0))
        self._send_midi((0xB0 | self._rx_channel, REVERB_DEPTH_KNOB, 0))

# -- Track mode

    def _set_tremolo_toggle(self, value):        
        # self._logger.log(f"_set_tremolo_toggle: {value}")
        if self._tremolo_toggle_value == value:
            return
        self._tremolo_toggle_value = value

        if self.is_navigation_mode_enabled: # Navigation mode prevails over other modes
            return
        
        if value == REFACE_TOGGLE_UP:
            self._track_controller.set_enabled(False)
            self._enable_device_lock_mode()
        elif value == REFACE_TOGGLE_DOWN:
            self._unlock_from_device()
            self._device_controller.set_enabled(False)
            self._enable_track_mode()
        else:
            self._enable_device_follow_mode()

        self.request_rebuild_midi_map()

    @property
    def is_track_mode_enabled(self):
        return self._tremolo_toggle_value == REFACE_TOGGLE_DOWN and not self.is_navigation_mode_enabled

    @property
    def is_device_follow_mode_enabled(self):
        return self._tremolo_toggle_value == REFACE_TOGGLE_OFF and not self.is_navigation_mode_enabled

    @property
    def is_device_lock_mode_enabled(self):
        return self._tremolo_toggle_value == REFACE_TOGGLE_UP and not self.is_navigation_mode_enabled

    def _enable_device_follow_mode(self):
        self._note_repeat_controller.set_controls_enabled(False)
        self._scale_controller.disable_edit_mode()
        self._scale_controller.set_controls_enabled(False)
        self._clip_launcher_controller.set_controls_enabled(False)

        self._track_controller.set_enabled(False)
        self._unlock_from_device()
        self._device_controller.set_enabled(True)
        self.set_device_to_selected()
        self._logger.show_message("Following device selection.")
        # Update leds in device since we disabled local control
        self._send_midi((0xB0 | self._rx_channel, TREMOLO_WAH_TOGGLE, 64))
        self._send_midi((0xB0 | self._rx_channel, CHORUS_PHASER_TOGGLE, 0))
        self._send_midi((0xB0 | self._rx_channel, DELAY_TOGGLE, 0))
        self._send_midi((0xB0 | self._rx_channel, REVERB_DEPTH_KNOB, 0))

    def _enable_device_lock_mode(self):
        selected_device = self.get_selected_device()
        self._logger.log(f"Device locked: {selected_device.name}")

        self._note_repeat_controller.set_controls_enabled(False)
        self._scale_controller.disable_edit_mode()
        self._scale_controller.set_controls_enabled(False)
        self._clip_launcher_controller.set_controls_enabled(False)
        self._track_controller.set_enabled(False)
        self._device_controller.set_enabled(True)
        self._lock_to_device(selected_device)
        self._send_midi((0xB0 | self._rx_channel, TREMOLO_WAH_TOGGLE, 64))  # Update led in device since we disabled local control
        self._send_midi((0xB0 | self._rx_channel, CHORUS_PHASER_TOGGLE, 0))
        self._send_midi((0xB0 | self._rx_channel, DELAY_TOGGLE, 0))

    def _enable_track_mode(self):
        self._note_repeat_controller.set_controls_enabled(False)
        self._scale_controller.disable_edit_mode()
        self._scale_controller.set_controls_enabled(False)
        self._clip_launcher_controller.set_controls_enabled(False)
        self._device_controller.set_enabled(False)
        self._track_controller.set_enabled(True)
        self._logger.show_message("Track mode enabled.")

        # Update leds in device since we disabled local control
        self._send_midi((0xB0 | self._rx_channel, TREMOLO_WAH_TOGGLE, 127))
        self._send_midi((0xB0 | self._rx_channel, CHORUS_PHASER_TOGGLE, 0))
        self._send_midi((0xB0 | self._rx_channel, DELAY_TOGGLE, 0))

# -- Scale Mode

    @property
    def is_scale_mode_enabled(self):
        return self._chorus_toggle_value == REFACE_TOGGLE_UP

    def _set_chorus_toggle(self, value):
        self._logger.log(f"_set_chorus_toggle: {value}")
        self._chorus_toggle_value = value

        if self.is_navigation_mode_enabled: # Navigation mode prevails over other modes
            return

        if value == REFACE_TOGGLE_UP:
            self._note_repeat_controller.set_controls_enabled(False)
            self._track_controller.set_enabled(False)
            self._device_controller.set_enabled(False)
            self._clip_launcher_controller.set_enabled(False)
            self._scale_controller.set_enabled(True)
            self._logger.show_message("Scale mode enabled.")
            # Update device leds
            self._send_midi((0xB0 | self._rx_channel, CHORUS_PHASER_TOGGLE, 64))
            self._send_midi((0xB0 | self._rx_channel, TREMOLO_WAH_TOGGLE, 0))
            self._send_midi((0xB0 | self._rx_channel, DELAY_TOGGLE, 0))
            self._send_midi((0xB0 | self._rx_channel, REVERB_DEPTH_KNOB, 0))
        elif value == REFACE_TOGGLE_DOWN:
            self._note_repeat_controller.set_controls_enabled(False)
            self._track_controller.set_enabled(False)
            self._device_controller.set_enabled(False)
            self._scale_controller.set_enabled(False)
            self._clip_launcher_controller.set_enabled(True)
            self._logger.show_message("Clip trigger mode enabled.")
             # Update device leds
            self._send_midi((0xB0 | self._rx_channel, CHORUS_PHASER_TOGGLE, 64))
            self._send_midi((0xB0 | self._rx_channel, TREMOLO_WAH_TOGGLE, 0))
            self._send_midi((0xB0 | self._rx_channel, DELAY_TOGGLE, 0))
            self._send_midi((0xB0 | self._rx_channel, REVERB_DEPTH_KNOB, 0))
        else:
            self._scale_controller.set_enabled(False)
            self._clip_launcher_controller.set_enabled(False)
            self._send_midi((0xB0 | self._rx_channel, CHORUS_PHASER_TOGGLE, 0))  # Update led in device since we disabled local control
            self._check_device_track_modes()
        
    def _on_scale_edit_mode_changed(self, enabled):
        if enabled:
            self._logger.show_message("Scale edit mode enabled.")
            self._send_midi((0xB0 | self._rx_channel, REVERB_DEPTH_KNOB, 16))
            self._refaceCP.set_speaker_output(True)
            self._refaceCP.set_preset(RefaceCP.PLAIN_PIANO_PRESET)
        else:
            self._logger.show_message("Scale play mode enabled.")
            self._send_midi((0xB0 | self._rx_channel, REVERB_DEPTH_KNOB, 0))
            self._send_midi((0xB0 | self._rx_channel, TYPE_SELECT_KNOB, next(key for key, value in reface_type_map.items() if value == self._channel)))
            self._refaceCP.set_speaker_output(False)

    def _play_note(self, note, velocity):
        self._send_midi((0x90 | self._rx_channel, note, velocity))

# -- Clip Mode

    @property
    def is_clip_mode_enabled(self):
        return self._chorus_toggle_value == REFACE_TOGGLE_DOWN

# -- Navigation/Transport Mode

    @property
    def is_navigation_mode_enabled(self):
        return self._delay_toggle_value == REFACE_TOGGLE_DOWN

    @property
    def is_note_repeat_enabled(self):
        return self._delay_toggle_value == REFACE_TOGGLE_UP

    def _set_delay_toggle(self, value):
        self._logger.log(f"_set_delay_toggle: {value}")
        if self._delay_toggle_value == value:
            return
        self._delay_toggle_value = value

        if value == REFACE_TOGGLE_UP:
            self._track_controller.set_enabled(False)
            self._device_controller.set_enabled(False)
            self._transport_controller.set_enabled(False)
            self._navigation_controller.set_enabled(False)
            self._scale_controller.disable_edit_mode()
            self._scale_controller.set_controls_enabled(False)
            self._clip_launcher_controller.set_enabled(False)
            self._note_repeat_controller.set_enabled(True)
            self._logger.show_message("Note repeat enabled.")
            self._send_midi((0xB0 | self._rx_channel, DELAY_TOGGLE, 64))  # Update led in device since we disabled local control
            self._send_midi((0xB0 | self._rx_channel, TREMOLO_WAH_TOGGLE, 0))
            self._send_midi((0xB0 | self._rx_channel, CHORUS_PHASER_TOGGLE, 0))

        elif value == REFACE_TOGGLE_DOWN:
            self._enable_navigation_mode()

        else:
            self._note_repeat_controller.set_enabled(False)
            self._transport_controller.set_enabled(False)
            self._navigation_controller.set_enabled(False)
            self._check_device_track_modes()
        
    def _enable_navigation_mode(self):
        self._note_repeat_controller.set_enabled(False)
        self._scale_controller.set_enabled(False)
        self._clip_launcher_controller.set_enabled(False)
        self._track_controller.set_enabled(False)
        self._device_controller.set_enabled(False)
        self._transport_controller.set_enabled(True)
        self._navigation_controller.set_enabled(True)
        self._logger.show_message("Transport/Navigation mode enabled.")
        # Update device leds:
        self._send_midi((0xB0 | self._rx_channel, DELAY_TOGGLE, 127))  
        self._send_midi((0xB0 | self._rx_channel, CHORUS_PHASER_TOGGLE, 0))
        self._send_midi((0xB0 | self._rx_channel, TREMOLO_WAH_TOGGLE, 0))
        self._send_midi((0xB0 | self._rx_channel, REVERB_DEPTH_KNOB, 0))

# --- Live (ControlSurface Inherited)

    def set_enabled(self, enable, properties: dict = {}):
        """Enables/Disables the script"""
        for control in self._all_controls:
            control.suppress_script_forwarding = not enable
        if enable:
            self._tremolo_toggle_value = -1
            self._chorus_toggle_value = -1
            self._delay_toggle_value = -1
            self._enable_reface_script_mode()
            self._refaceCP.request_current_values()
        else:
            self._note_repeat_controller.set_enabled(False)
            self._scale_controller.set_enabled(False)
            self._clip_launcher_controller.set_enabled(False)
            self._track_controller.set_enabled(False)
            self._device_controller.set_enabled(False)
            self._transport_controller.set_enabled(False)
            self._navigation_controller.set_enabled(False)
            speaker_on = properties.get('speaker', '').lower() == "on"
            self._restore_reface_state(speaker_on=speaker_on)  
        return super().set_enabled(enable)

    def _on_selected_track_changed(self):
        # self._logger.log("_on_selected_track_changed")
        super()._on_selected_track_changed()
        if self._is_initialized:
            self._track_controller.set_track(self.song().view.selected_track)

    def handle_sysex(self, midi_bytes):
        self._refaceCP.handle_sysex(midi_bytes)

    def disconnect(self):
        self._logger.log("RefaceCP Disconnected")

        self._audioTrackMonitoringListener.disconnect()
        self._track_controller.disconnect()
        self._device_controller.disconnect()
        self._transport_controller.disconnect()
        self._navigation_controller.disconnect()
        self._note_repeat_controller.disconnect()
        self._scale_controller.disconnect()
        self._clip_launcher_controller.disconnect()

        self._type_select_button.remove_value_listener(self._reface_type_select_changed)
        self._tremolo_toggle_button.remove_value_listener(self._reface_tremolo_toggle_changed)
        self._chorus_toggle_button.remove_value_listener(self._reface_chorus_toggle_changed)
        self._delay_toggle_button.remove_value_listener(self._reface_delay_toggle_changed)

        self._all_controls = []

        # Restore defaults
        self._restore_reface_state()

        self._refaceCP.disconnect()

        # Calling disconnect on parent sends some MIDI that messes up or resets the reface. Why?
        # super(RefaceCPControlSurface, self).disconnect()
