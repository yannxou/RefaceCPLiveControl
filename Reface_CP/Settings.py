DEBUG_ENABLED = False

# Create a local file MySettings.py file to override with local configuration without pushing to repository.
try:
    from .MySettings import *
except ImportError:
    pass