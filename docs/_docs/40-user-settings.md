---
title: "User Settings"
permalink: /docs/user-settings/
excerpt: "How to customize the RefaceCPLiveControl script with user settings."
---

There are some script settings that can be user-defined. 

To modify a default setting, first create a `MySettings.py` file in the script folder. This file is not included in the project to prevent overwriting it when updating. Edit that file to include any of the following settings:

```python
# Add prefixes to clip names to indicate the corresponding MIDI note key in the Clip Trigger mode.
CLIP_TRIGGER_NAME_PREFIXES_ENABLED = True
```

```python
# Enable/Disable legato clip launching by default.
CLIP_TRIGGER_DEFAULT_LEGATO_ENABLED = True
```
