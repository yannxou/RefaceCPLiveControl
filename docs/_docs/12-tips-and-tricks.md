---
title: "Tips & Tricks"
permalink: /docs/tips-and-tricks/
excerpt: "Some tips and advanced features of the RefaceCPLiveControl script."
---

## Enabling/Disabling Reface CP audio output

While using this script the Reface CP output signal is disabled. In case you want to record or hear the Reface CP while Ableton Live is still running you can either disable the `Reface CP` control surface script manually from Live's `Link, Tempo & MIDI` settings or more conveniently, create an audio track named `Reface CP`. 

When a track including the `Reface CP` in its name is armed or its monitoring changes so the signal goes through, the script will be automatically disabled and the output of the Reface CP will be enabled so it can be played or recorded. When the track is unarmed the script is enabled again automatically.

Additional properties can be added to the track name that will be effective when the RefaceCP track becomes active:

| Parameter | Description |
| --- | --- |
| **speaker:[on/off]** | Allows specifying whether the internal speaker is enabled or not when the script is disabled. |
