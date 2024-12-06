# RefaceCPLiveControl

RefaceCPLiveControl is an Ableton Live Control Surface script for the Yamaha Reface CP keyboard.

## Table of Contents

1. [Installation](#installation)
2. [Controls](#controls)
	1. [Wave type knob (MIDI Channel Change)](#wave-type-knob)
	2. [Tremolo/Wah toggle (Device control)](#tremolowah-toggle)
	3. [Chorus toggle (Scale mode)](#chorus-toggle)
		1. [Scale Play Mode](#scale-play-mode)
		2. [Scale Edit Mode](#scale-edit-mode)
	4. [Phaser toggle (Clip trigger mode)](#phaser-toggle)
	5. [D.Delay toggle (Note repeat)](#ddelay-toggle)
	6. [A.Delay toggle (Navigation/Transport mode)](#adelay-toggle)
		1. [C  (*Stop actions*)](#c--stop-actions)
		2. [C# (*Recording actions*)](#c--recording-actions)
		3. [D  (*Play actions*)](#d--play-actions)
		4. [E  (*Tempo actions*)](#e--tempo-actions)
		5. [F  (*Track actions*)](#f--track-actions)
		6. [F# (*Quick-recording actions*)](#f--quick-recording-actions)
		7. [G  (*Clip actions*)](#g--clip-actions)
		8. [A  (*Device actions*)](#a--device-actions)
		9. [A# (*Edit actions*)](#a--edit-actions)
		10. [B  (*Loop actions*)](#b--loop-actions)
4. [Tips & Tricks](#tips--tricks)
5. [Constraints](#constraints)
6. [Troubleshooting](#troubleshooting)
7. [Support](#support)
8. [Links](#links)

## Installation

1. Manually create a folder called `Remote Scripts` within your User Library if it does not already exist. The default User Library locations are:

   - **Windows:** `\Users\[username]\Documents\Ableton\User Library`
   - **Mac:** `Macintosh HD/Users/[username]/Music/Ableton/User Library`
   
2. Place the remote script folder called `RefaceCP` (the folder you found this README.md in) into the `Remote Scripts` from previous step. 

This can also be done automatically with the provided `make install` command.

3. Select the `Reface CP` control surface script in Live's `Link, Tempo & MIDI` settings.

For more help, see [Installing third-party remote scripts](https://help.ableton.com/hc/en-us/articles/209072009-Installing-third-party-remote-scripts) from Ableton.

## Controls

### Wave type knob:

Changes the MIDI transmit channel from 1 (Rdl type) to 6 (CP type). MIDI tracks with an input routing from the `reface CP` source and the selected MIDI channel are automatically selected and armed. This is useful to quickly change and play instruments from tracks on specific MIDI channels. 

This also provides a lot more of flexibility to the custom MIDI mappings since each control can be mapped to any Live parameter across all 6 MIDI channels, effectively bringing up to 48 knobs, 18 toggles and 510 note keys for MIDI mapping in a Live Set.

*Note*: When mapping a control or key from the Reface using the custom user mapping Live overrides any special behaviour added by the script but in this case its functionality can still be reached by changing to any of the remaining unmapped MIDI channels for that control. Just prevent MIDI mapping the `type` knob so the channel can be changed.

### Tremolo/Wah toggle:

* **Off**: When the switch is in the middle position (off), the 8 right-most knobs follow and control the selected device.

<p align="center">
	<img src="Images/device_mode.jpg" alt="Device Mode" width="50%" />
</p>


* **Tremolo On**: When the switch is enabled, the 8 right-most knobs are locked to control a specific device.

<p align="center">
	<img src="Images/locked_device_mode.jpg" alt="Locked Device Mode" width="50%" />
</p>

* **Wah On**: Enables the **Track mode**. This allows changing the selected track's volume, panning, sends A and B as well as the Mute, Solo and Arm buttons. In this mode the `Drive` knob is connected to the currently selected parameter in Live which can be very handy for quick automations.

<p align="center">
	<img src="Images/track_mode.jpg" alt="Track Mode" width="50%" />
</p>

### Chorus toggle:

Enables the **Scale mode**. This includes two sub-modes (Play/Edit) which can be toggled by turning the **Reverb Depth** knob left/right.

#### Scale Play Mode:

In this mode, only the note keys that are part of the current scale will reach Live's input and keys outside the scale are muted.

By default, when enabling the scale mode it always starts with the Scale Play mode.

The following controls apply while in the Scale Play Mode:

* **Chorus Depth**: Root note. Move the knob to select the current root note.

* **Chorus Speed**: Scale mode. Move the knob to select the current scale mode.

<p align="center">
	<img src="Images/scale_play_mode.jpg" alt="Scale Play Mode" width="50%" />
</p>

#### Scale Edit Mode:

In this mode, the first note pressed on the keyboard sets the root note. While holding down the root key, additional notes can be added to a list that defines the target scale. 

Once all keys are released a list of all the possible scales that include all the entered notes will be populated and the first root and scale match is automatically changed in Live.

* **Chorus Depth**: Matching scales. Move the knob to cycle between all the matching root/scales found that include all the entered notes.

<p align="center">
	<img src="Images/scale_edit_mode.jpg" alt="Scale Edit Mode" width="50%" />
</p>

### Phaser toggle:

Enables the **Clip trigger mode**. This allows clip/scene triggering using the MIDI note keys. The following controls apply in this mode:

* **Drive**: Global clip trigger quantization.

* **Tremolo Depth**: Horizontal grid offset. Use this knob to move the clip grid highlight horizontally.

* **Tremolo Rate**: Vertical grid offset. Use this knob to move the clip grid highlight vertically.

* **Chorus Depth**: Note Key Layout. There are multiple keyboard layouts available for triggering clips. Move this knob to switch between these:
	* 1 octave per track (allow triggering up to 12 clips per track)
	* 2 octaves per track (allow triggering up to 24 clips per track)
	* 3 octaves per track (allow triggering up to 36 clips per track)
	* 7 octaves per track (use all note keys to target clips across a single track)
	* 7 octaves per scene (use all note keys to target clips across a single scene)
	* 3 octaves per scene (allow triggering clips from same scene across 36 tracks)
	* 2 octaves per scene (allow triggering clips from same scene across 24 tracks)
	* 1 octave per scene (allow triggering clips from same scene across 12 tracks)

* **Chorus Speed**: Clip/Scene triggering. Move this knob to the left to target clips for triggering. Move it to the right to target scenes.

<p align="center">
	<img src="Images/clip_trigger_mode.jpg" alt="Clip Trigger Mode" width="50%" />
</p>

### D.Delay toggle:

Enables the **Note repeat mode**. In this mode, the MIDI notes from the keyboard are repeated automatically while they're pressed. Once enabled, the knobs control some settings for the note repeat:

* **Delay Time**: Sets the note repeat rate using fixed values from 1/32T to 1 bar.

* **Delay Depth**: Sets the note repeat rate by specifying the number of notes per bar.

<p align="center">
	<img src="Images/note_repeat.jpg" alt="Note Repeat Mode" width="50%" />
</p>

Selecting the track/device mode after enabling the note repeat allows using the knobs for automation and the note repeat functionality at the same time. To change the note repeat settings again using the knobs it needs to be disabled and enabled again.

### A.Delay toggle:

Enables the **Navigation/Transport mode**. In this mode the knobs are used for navigation and the note keys for transport actions and more.

* **Drive**: Track navigation. Move the knob to change the track selection including sends and the master track. Since the knobs in the Reface CP are not endless the navigation will only work well for up to 127 tracks. If you have more than 127 tracks in your Live Set then some of the tracks won't be accessible using this knob but usually this doesn't happen unless you're Jacob Collier. In any case, the track can still be selected manually or using some of the actions from the list below.

* **Tremolo Depth**: Clip navigation. Move the knob to change the clip selection in the current track. Again, since the knobs in the Reface CP are not endless the clip selection works fine for up to 127 scenes. Still, some simple navigation can be performed using some of the actions from the list below.

* **Tremolo Rate**: Device navigation. Move the knob to change the device selection in the current track. This also has the 127 device limit.

<p align="center">
	<img src="Images/navigation_transport_mode.jpg" alt="Navigation/Transport Mode" width="50%" />
</p>

In this mode each note key has a special function and can be recalled from any octave in the keyboard for easiness of use. In most cases, a secondary note can also be pressed to perform subactions. 

When pressing down the first key, a hint message is displayed in Live's bottom status bar. If the first note key is pressed and held for more than 3 seconds without pressing any other key the ongoing action is automatically cancelled to prevent triggering unwanted actions. This timeout corresponds to the duration that Live displays messages from the script in the status bar. 

Here are all the actions that can be triggered from the MIDI keyboard:

*Note*: Unless specified, all secondary action notes from the list correspond to the note within the same octave as the main action note. Higher or lower octaves are represented with a <sup>+n</sup> or <sup>-n</sup> text next to it.

#### C ⏐ *Stop actions*

* Press and release the key to stop playing.
* Press and hold + C# to stop all recording clips.
* Press and hold + E to stop all clips from all tracks. 
* Press and hold + F to stop the current track clip (if any).
* Press and hold + F# to stop playing clips from all armed tracks.

#### C# ⏐ *Recording actions*

* Press and release the key to toggle the Arrangement record.
* Press and hold + C to go back to Arrangement.
* Press and hold + D# to toggle the Session record.
* Press and hold + D to toggle MIDI Arrangement overdub.
* Press and hold + E to toggle automation arm.
* Press and hold + F to re-enable automation for any parameters that are currently overriden in the Arrangement or Session clips.

#### D ⏐ *Play actions*

* Press and release the key to start playing.
* Press and hold + use the white keys to change the song position (jump) according to the distance between the first key (D) and the second. This means the position can jump forwards by pressing a second higher white note or backwards by pressing a second lower white note.
* Press and hold + C# to jump to the previous cue marker.
* Press and hold + D# to jump to the next cue marker.
* Press and hold + F# to continue playback from the current position.
* Press and hold + G# to play all recording clips.

#### E ⏐ *Tempo actions*

* Press and release the key to toggle the Metronome.
* Press and hold + F to decrease the clip trigger quantization.
* Press and hold + F# to reset the clip trigger quantization to 1 bar.
* Press and hold + G to increase the clip trigger quantization.
* Press and hold + A to Tap Tempo.

#### F ⏐ *Track actions*

* Press and release the key to toggle the Clip/Device view.
* Press and hold + C to mute the selected track.
* Press and hold + C# to arm the selected track.
* Press and hold + D to solo the selected track.
* Press and hold + E to select to the previous track.
* Press and hold + G to select to the next track.
* Press and hold + A to select the current track's instrument.

#### F# ⏐ *Quick-recording actions*

* Press and release the key to start a quick clip recording on all selected tracks. This starts recording on the next free scene of all selected tracks, creating a new scene if necessary. If a track is not armed it will be armed automatically if possible.
* Press and hold + C# to start a quick recording on all armed tracks. This starts recording clips on the next free scene of all armed tracks, creating a new scene if necessary.
* Press and hold + F to start an Audio track resampling. This starts recording a new Audio clip into a track that takes the audio signal from the selected track's output, creating a new track if none is found.
* Press and hold + G to start a MIDI track resampling. This starts recording a new MIDI clip into a track that takes the MIDI signal from the selected track's output, creating a new track if none is found.
* Press and hold + G# to start a quick resampling. This starts recording a new clip in the next free scene of a track with a resampling input. If no resampling track is found a new one is created.

#### G ⏐ *Clip actions*

* Press and release the key to show the Clip view.
* Press and hold + C to stop the selected clip.
* Press and hold + C# to delete the selected clip.
* Press and hold + D to fire the selected clip.
* Press and hold + E to fire the selected scene.
* Press and hold + F to select the previous clip slot.
* Press and hold + A to select the next clip slot.

#### A ⏐ *Device actions*

* Press and release to select the currently assigned (or locked) device.
* Press and hold + C to toggle the device on/off.
* Press and hold + G to select the previous device.
* Press and hold + B to select the next device.

#### A# ⏐ *Edit actions*

* Press and hold + A to undo last action.
* Press and hold + B to redo last action.

#### B ⏐ *Loop actions*

* Press and release the key to toggle loop.
* Press and hold + D# to jump song position to the loop start position.
* Press and hold + F# to decrease the loop length.
* Press and hold + G# to increase the loop length.
* Press and hold + A# to set the loop between the nearest cue points.
* Press and hold + use the white keys to change the loop start position according to the distance between the first key (B) and the second. This means the position can jump forwards by pressing a second higher white note or backwards by pressing a second lower white note.

## Tips & Tricks

### Enabling/Disabling Reface CP audio output

While using this script the Reface CP output signal is disabled. In case you want to record or hear the Reface CP while Ableton Live is still running you can either disable the `Reface CP` control surface script manually from Live's `Link, Tempo & MIDI` settings or more conveniently, create an audio track named `Reface CP`. When a track including the `Reface CP` in its name is armed or its monitoring changes so the signal goes through, the script will be automatically disabled and the output of the Reface CP will be enabled so it can be played or recorded. When the track is unarmed the script is enabled again automatically.

Additional properties can be added to the track name that will be effective when the RefaceCP track becomes active:
* speaker:[on/off] - Allows specifying whether the internal speaker is enabled or not when the script is disabled.

## Constraints

Sadly, the Reface CP does not send any MIDI CC for the Volume and Octave faders. It's also a pity that the Type knob is not an endless encoder. This limits the possibilities of what could be achieved when used as a controller but I hope this still brings a new dimension to your great Reface CP. 

Control surface scripting in Ableton Live can be very powerful but I found some limitations that I wish are added in the future. For instance:

* Being able to define a mapping of MIDI notes so a particular MIDI note key is processed in Live's input as another MIDI note. That'd be a better way to implement a scale mode for a keyboard where notes outside a given scale would be mapped to another note in that scale. Muting those notes (by capturing their events in the script) is the only way I've been able to do this.

* Integrated MIDI effect chain. Similarly to how the `note_repeat` works, it would be awesome to have access to standard MIDI effects like velocity, note repeat, arpeggiator, etc so they could be configured from the script and the chain's output sent to Live to record the notes directly. This feature actually would solve the need for the previous point by just having access to a scale device.

## Troubleshooting

In case your Reface CP does not produce any sound after using the script you can restore it to factory defaults by holding down the right-most C-key on the keyboard while pressing the Power (Standby/On) switch. This could happen in case of application crash or if the device is disconnected before closing Live. To avoid this, make sure Live application is closed before turning off the Reface. The script will restore the settings (like the speaker output) automatically when closing.

## Support

If you'd like to receive support, please send your feedback in the form of suggestions or bug reporting using the github issues.

If you’d like to send support for this project or other hundreds of ideas you can bring the drinks using the button below.
I will happily implement something similar for other synths if I receive enough feedback or someone gifts me a unit.

<a href="https://www.buymeacoffee.com/yannxou" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-yellow.png" alt="Buy Me A Coffee" height="41" width="174"></a>

## Links

This is a collection of resources that I found useful while researching on this project. I'm collecting them here both as a documentation source and acknowledgement.

* [LOM - The Live Object Model](https://docs.cycling74.com/max8/vignettes/live_object_model): Official Live Object Model Documentation
* [Live API version 11.0.0](https://structure-void.com/PythonLiveAPI_documentation/Live11.0.xml): Unofficial Live API documentation generated by the "API_MakeDoc" MIDI Remote Script. https://structure-void.com
* [Live API version 12.1.0](https://ableton-live-docs.vercel.app/Live%2012.1.0.xml): Unofficial Live API documentation updated to version 12.1.0.
* [ableton-control-surface-toolkit](https://github.com/oslo1989/ableton-control-surface-toolkit): Repository for decompiled Ableton Python APIs and Control Surface definitions
* [AbletonLive12_MIDIRemoteScripts](https://github.com/gluon/AbletonLive12_MIDIRemoteScripts): Unofficial repository for Ableton Live 12.0.1 MIDI Remote Scripts Python Sources by Julien Bayle / Structure Void
* [_Framework](https://remotescripts.blogspot.com/2010/03/introduction-to-framework-classes.html): An Introduction to the Ableton Framework Classes by Hanz Petrov
* [Ableton Script Documentation](https://github.com/xot/ElectraOne/blob/main/DOCUMENTATION.md): Technical Documentation of the Ableton Live Remote Script for the Electra One (Jaap-Henk Hoepman)
