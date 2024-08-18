# RefaceCPLiveControl

RefaceCPLiveControl is a control surface script for Ableton Live for the Yamaha Reface CP keyboard.

## Set Up

1. Manually create a folder called `Remote Scripts` within your User Library if it does not already exist. The default User Library locations are:

   - **Windows:** `\Users\[username]\Documents\Ableton\User Library`
   - **Mac:** `Macintosh HD/Users/[username]/Music/Ableton/User Library`
   
2. Place the remote script folder called `RefaceCP` (the folder you found this README.md in) into the `Remote Scripts` from previous step.

## Controls

### Tremolo/Wah switch:

* Tremolo On: When the switch is enabled, the 8 right-most knobs are locked to control the selected device in Live.
* Off: When the switch is in the middle position (off), the 8 right-most knobs follow and control the selected device in Live.
* Wah On: The 8 right-most knobs control the last selected element in Live automatically. This allows performing quick automations by just selecting an element in Live. The last selected element is 'pushed' to the first knob (Drive) and the older selections are pushed to the right.


## Constraints

Sadly, the reface does not send any MIDI CC for the Volume and Octave faders. This limits the possibilities of what could be achieved when used as a controller.

## known Issues:

* With device lock mode enabled from the script (Tremolo switch on), the blue hand still changes when a new device is selected even though the locked device still works. The 'Lock to control surface' option also appears disabled in Live.