---
title: "Clip Trigger Mode"
permalink: /docs/clip-trigger-mode/
excerpt: "How to use the Yamaha Reface CP note keys to play clips/scenes in Ableton Live."
---

This mode allows using the Yamaha Reface CP note keys to play clips and scenes in Ableton Live.

Turn *on* the Phaser switch (down position) to enable the Clip Trigger Mode.

When enabled, all MIDI note keys (except keys C# and D# which are reserved for special functions) can be used for clip/scene triggering.

* Press and hold C# + clip note key to stop the clip.
* Press and hold C# + upper/lower C# to stop all clips.
* Press and hold D# + clip note key to play the clip's scene.

**Tip:** Pressing a new key while another one is being held down allows playing the different clips from the same track in **legato** mode. This also works with the stop key (C#) so it can be used as some sort of temporal mute when triggering clips. This feature can be enabled/disabled in the [user settings]({{ "/docs/user-settings/" | relative_url }}).
{: .notice--info}

## Layouts

There are multiple keyboard layouts available for triggering clips:

* 1 octave per track (allow triggering up to 10 clips per track)
* 2 octaves per track (allow triggering up to 20 clips per track)
* 3 octaves per track (allow triggering up to 30 clips per track)
* 7 octaves per track (use all note keys to target clips across a single track)
* 7 octaves per scene (use all note keys to target clips across a single scene)
* 3 octaves per scene (allow triggering clips from same scene across 30 tracks)
* 2 octaves per scene (allow triggering clips from same scene across 20 tracks)
* 1 octave per scene (allow triggering clips from same scene across 10 tracks)

## Controls

The following controls apply in this mode:

| Control | Description |
| --- | --- |
| **Wave Type** | Set MIDI Transmit channel |
| **Drive** | Global clip trigger quantization |
| **Tremolo Depth** | Horizontal grid offset. Use this knob to move the clip grid highlight horizontally |
| **Tremolo Rate** | Vertical grid offset. Use this knob to move the clip grid highlight vertically |
| **Chorus Depth** | Note Key Layout. Move this knob to switch between the different layouts |
| **Chorus Speed** | Clip/Scene triggering. Move this knob to the left to target clips for triggering. Move it to the right to target scenes |

By default, when enabling the Clip trigger mode, the clip names are renamed to show the MIDI key that can be used to fire each clip. This behaviour can be disabled by changing the `CLIP_TRIGGER_NAME_PREFIXES_ENABLED` setting to `False`.

<p align="center">
    <img src="{{ '/assets/images/clip_trigger_mode.jpg' | relative_url }}" alt="Clip Trigger Mode" width="70%">
</p>