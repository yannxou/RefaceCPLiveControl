---
title: "Scale Mode"
permalink: /docs/scale-mode/
excerpt: "How to fix the Yamaha Reface CP note keys to a specific scale."
toc: true
---

This mode allows fixing the Yamaha Reface CP note keys to a specific scale.
There are two sub-modes (Play/Edit) which can be toggled by turning the **Reverb Depth** knob left/right.

Turn *on* the Chorus switch (up position) to enable the Scale Mode.

**Tip:** This mode can be used simultaneously with another mode. Once the Scale Mode is turned on, enabling another mode allows using the knob controls of the new mode while keeping the note keys locked to the scale.
{: .notice--info}

## Scale Play Mode

The Scale Play Mode is always enabled by default when turning on the Chorus switch.

<p align="center">
    <a href="{{ '/assets/images/scale_play_mode.jpg' | relative_url }}"> 
      <img src="{{ '/assets/images/scale_play_mode.jpg' | relative_url }}" alt="Scale Play Mode" width="70%"/>
    </a>
</p>

In this mode, only the note keys that are part of the current scale will reach Live's input and keys outside the scale are muted.

The following controls apply while in the Scale Play Mode:

| Control | Description |
| --- | --- |
| **Wave Type** | Set MIDI Transmit channel |
| **Chorus Depth** | Root note. Move the knob to select the current root note |
| **Chorus Speed** | Scale mode. Move the knob to select the current scale mode |
| **Reverb Depth** | Enter Scale Edit Mode (right) |

## Scale Edit Mode

Once the Scale Mode is enabled, turn right the Reverb Depth knob to enter the Scale Edit Mode. The Reverb Depth knob led indicator will also turn on to indicate that the Scale Edit Mode is enabled.

To exit the Scale Edit Mode, turn left the Reverb Depth Knob. The Reverb Depth knob will turn off to indicate that the Scale Play Mode is enabled.

<p align="center">
    <a href="{{ '/assets/images/scale_edit_mode.jpg' | relative_url }}"> 
      <img src="{{ '/assets/images/scale_edit_mode.jpg' | relative_url }}" alt="Scale Edit Mode" width="70%"/>
    </a>
</p>

In this mode, the first note pressed on the keyboard sets the root note. While holding down the root key, additional notes can be added to a list that defines the target scale. 

Once all keys are released, an in-memory list of all the possible scales that include all the entered notes will be populated and the first root and scale match is automatically changed in Live. Use the Chorus Depth knob to select other matching root/scales from that list.

The following controls apply while in the Scale Edit Mode:

| Control | Description |
| --- | --- |
| **Chorus Depth** | Matching scales. Move the knob to cycle between all the matching root/scales found that include all the entered notes |
| **Reverb Depth** | Exit Scale Edit Mode (left) |
