---
title: "Device Randomization Mode"
permalink: /docs/device-randomization-mode/
excerpt: "How to use the Yamaha Reface CP to randomize and morph presets on a specific Ableton Live device."
---

To enable this mode, first lock the controls to a device by turning *on* the Tremolo switch (up position) and then select the last **Wave Type** 6 (CP). 

<p align="center">
    <img src="{{ '/assets/images/device_randomization_mode.jpg' | relative_url }}" alt="Device Randomization Mode" width="70%">
</p>

This mode can be used to create new presets for the device by morphing between the current preset and a target preset.

When entering this mode, the current values of all the device's parameters are stored and a new random variation is created. 

Using the **Drive** knob it applies a morphing amount between the original and the target preset and thus allows transitioning between all intermediate values.

Everytime the **Tremolo Rate** knob is turned left or right a new set of random values are created and used as a target preset.

The number of parameters that are affected can be changed with the **Tremolo Depth** knob.

Any parameter can be excluded from the randomization by selecting the desired value in the device. When a parameter is manually changed in the device it will become a fixed value in the target preset.
This can be used to load another preset and then morph between both.
This list of excluded parameters is cleared out when the Device Randomization Mode is disabled.

**Note:** With more complex devices like instruments or those with toggle controls are more difficult to morph smoothly and it works better with linear parameters. Excluding some of those parameters might help when finding a new preset to morph to.
{: .notice--info}

The following controls apply in this mode:

| Control | Description |
| --- | --- |
| **Wave Type** | Select device parameter bank (1-5) or enable the Device Randomization Mode (6) |
| **Drive** | Morphing Amount. How close to the target values each parameters changes. 0% - Original. 100% - Target |
| **Tremolo Depth** | Morphing Length. How many parameters change. 0..number of device parameters |
| **Tremolo Rate** | Randomize target values. Create a new target set of random parameters and values on each knob turn. |
