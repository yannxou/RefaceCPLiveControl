# RefaceCPLiveControl

RefaceCPLiveControl is a control surface script for Ableton Live for the Yamaha Reface CP keyboard.

## Set Up

1. Manually create a folder called `Remote Scripts` within your User Library if it does not already exist. The default User Library locations are:

   - **Windows:** `\Users\[username]\Documents\Ableton\User Library`
   - **Mac:** `Macintosh HD/Users/[username]/Music/Ableton/User Library`
   
2. Place the remote script folder called `RefaceCP` (the folder you found this README.md in) into the `Remote Scripts` from previous step.

## Controls

### Wave type knob:

Allows changing the MIDI transmit channel from 0 (Rdl type) to 5 (CP type). This is useful to quickly change and play instruments for tracks armed to specific MIDI channels. 

This also provides a lot more of flexibility to the custom MIDI mappings since each knob, toggle and note key in the device can be mapped to any Live parameter across all 6 MIDI channels.

When mapping a control or key using the custom user mapping in Live it will override any special behaviour added by the script, but its functionality will still be reachable by changing to any of the remaining unmapped MIDI channels for that control. Just make sure to avoid custom mapping the wave type knob to ensure the MIDI channel can be changed by the script.

### Tremolo/Wah switch:

* Tremolo On: When the switch is enabled, the 8 right-most knobs are locked to control the selected device in Live.
* Off: When the switch is in the middle position (off), the 8 right-most knobs follow and control the selected device in Live.
* Wah On: The 8 right-most knobs control the last selected element in Live automatically. This allows performing quick automations by just selecting an element in Live. The last selected element is 'pushed' to the first knob (Drive) and the older selections are pushed to the right.


## Constraints

Sadly, the Reface CP does not send any MIDI CC for the Volume and Octave faders. It's also a pity that the Type knob is not an endless encoder. This limits the possibilities of what could be achieved when used as a controller but I hope this still brings a new dimension to your great Reface CP. 

## known Issues:

* With device lock mode is enabled manually from Live it needs to be unlocked also manually or lock another device from the reface since going to current device won't work otherwise.