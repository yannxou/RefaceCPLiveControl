.EXPORT_ALL_VARIABLES:
.NOTPARALLEL:

ABLETON_PREFS_DIR          := $(HOME)/Library/Preferences/Ableton/Live 12.1.5
SOURCE_SCRIPT_DIR          := ./Reface_CP
TARGET_SCRIPT_DIR          := $(HOME)/Music/Ableton/User Library/Remote Scripts


define HELP_BODY
\033[1mall\033[0m
    Cleans log and updates the script.

\033[1minstall\033[0m
    Copy required files to Ableton's directory.

\033[1mclean\033[0m
    Removes Log.txt file from Ableton's Preferences directory.

\033[1mopen-log\033[0m
	Opens a Terminal window with a content stream of Ableton's Live Log.txt file.
endef

help:
	@echo "$$HELP_BODY"

all:
	$(MAKE) clean
	$(MAKE) install

clean:
	#rm "$(ABLETON_PREFS_DIR)/Log.txt"
	cat /dev/null > "$(ABLETON_PREFS_DIR)/Log.txt"

install:
	rsync -av --exclude=".*" "$(SOURCE_SCRIPT_DIR)" "$(TARGET_SCRIPT_DIR)"

open-log:
	osascript -e 'tell app "Terminal" to do script "cd \"$(ABLETON_PREFS_DIR)\" && tail -f -n 20 Log.txt"'
