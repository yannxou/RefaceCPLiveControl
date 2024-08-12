.EXPORT_ALL_VARIABLES:
.NOTPARALLEL:

ABLETON_APP_DIR            := /Applications/Ableton Live 12 Suite.app
ABLETON_PREFS_DIR          := $(HOME)/Library/Preferences/Ableton/Live 12.0.20
SOURCE_SCRIPT_DIR          := ./Reface_CP
TARGET_SCRIPT_DIR          := $(ABLETON_APP_DIR)/Contents/App-Resources/MIDI Remote Scripts


define HELP_BODY
\033[1mall\033[0m
    Cleans log and updates the script.

\033[1msetup\033[0m
    Copy required files to Ableton's directory.

\033[1mclean\033[0m
    Removes Log.txt file from Ableton's Preferences directory.
endef

help:
	@echo "$$HELP_BODY"

all:
	$(MAKE) clean
	$(MAKE) setup

clean:
	rm "$(ABLETON_PREFS_DIR)/Log.txt"

setup:
	rsync -av --exclude=".*" "$(SOURCE_SCRIPT_DIR)" "$(TARGET_SCRIPT_DIR)"