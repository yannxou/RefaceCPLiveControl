---
title: "MIDI Transmit Channel"
permalink: /docs/midi-transmit-channel/
excerpt: "How to change the MIDI transmit channel in the Yamaha Reface CP using the RefaceCPLiveControl script"
---

In most of the available modes, the **Wave type knob** can be used to change the MIDI transmit channel from 1 (Rdl type) to 6 (CP type). 

This provides a lot more of flexibility to the custom MIDI mappings since each control can be mapped to any Live parameter across all 6 MIDI channels, effectively bringing up to 48 knobs, 18 toggles and 510 note keys for MIDI mapping in a Live Set.

**Note**: When mapping a control or key from the Reface using the custom user mapping Live overrides any special behaviour added by the script. In this case, its functionality can still be reached by changing to any of the remaining unmapped MIDI channels for that control. Just prevent MIDI mapping the Wave Type knob so the channel can be changed.
{: .notice--info}

## Auto-selecting Live tracks with MIDI channel

When changing the MIDI transmit channel, if there's a MIDI track in Live with an input routing from the `reface CP` source and the selected MIDI channel it will be automatically selected and armed. 

This is useful, for instance, to quickly change and play instruments from tracks on specific MIDI channels. 
