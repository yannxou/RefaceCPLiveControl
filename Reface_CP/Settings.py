DEBUG_ENABLED = False
# Add prefixes to clip names to indicate the corresponding note key under Clip Trigger mode.
CLIP_TRIGGER_NAME_PREFIXES_ENABLED = True

# Create a local file MySettings.py file to override with local configuration without pushing to repository.
try:
    from .MySettings import *
except ImportError:
    pass