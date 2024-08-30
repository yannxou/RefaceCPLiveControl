# RefaceCPLiveControl

RefaceCPLiveControl is an Ableton Live Control Surface script for the Yamaha Reface CP keyboard.

## Installation

1. Manually create a folder called `Remote Scripts` within your User Library if it does not already exist. The default User Library locations are:

   - **Windows:** `\Users\[username]\Documents\Ableton\User Library`
   - **Mac:** `Macintosh HD/Users/[username]/Music/Ableton/User Library`
   
2. Place the remote script folder called `RefaceCP` (the folder you found this README.md in) into the `Remote Scripts` from previous step.

You can also do this automatically with the `make install` command after setting the correct Live installation path in the `Makefile`.

## Controls

### Wave type knob:

Changes the MIDI transmit channel from 0 (Rdl type) to 5 (CP type). This is useful to quickly change and play instruments from tracks on to specific MIDI channels. 

This also provides a lot more of flexibility to the custom MIDI mappings since each control can be mapped to any Live parameter across all 6 MIDI channels, effectively bringing up to 48 knobs, 18 toggles and 504 note keys for MIDI mapping in a Live Set.

*Note*: When mapping a control or key from the Reface using the custom user mapping in Live it overrides any special behaviour added by the script but its functionality can still be reached by changing to any of the remaining unmapped MIDI channels for that control.

### Tremolo/Wah switch:

* **Off**: When the switch is in the middle position (off), the 8 right-most knobs follow and control the selected device.

<p align="center">
	<img src="Images/device_mode.jpg" alt="Device Mode" width="75%" />
</p>


* **Tremolo On**: When the switch is enabled, the 8 right-most knobs are locked to control a specific device.

<p align="center">
	<img src="Images/locked_device_mode.jpg" alt="Locked Device Mode" width="75%" />
</p>

* **Wah On**: Enables the track mode. This allows changing the selected track's volume, panning, sends A and B as well as the Mute, Solo and Arm buttons. In this mode the `Drive` knob is connected to the currently selected parameter in Live which can be very handy for quick automations.

<p align="center">
	<img src="Images/track_mode.jpg" alt="Track Mode" width="75%" />
</p>

## Constraints

Sadly, the Reface CP does not send any MIDI CC for the Volume and Octave faders. It's also a pity that the Type knob is not an endless encoder. This limits the possibilities of what could be achieved when used as a controller but I hope this still brings a new dimension to your great Reface CP. 

