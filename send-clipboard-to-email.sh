#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Get clipboard content using AppleScript
CLIPBOARD_CONTENT=$(osascript -e '
    tell application "System Events"
        set clipboardContent to the clipboard as text
        return clipboardContent
    end tell
')

# Check if clipboard is empty
if [ -z "$CLIPBOARD_CONTENT" ]; then
    echo "Error: Clipboard is empty!"
    exit 1
fi

# Run the Python script with the clipboard content
echo "$CLIPBOARD_CONTENT" | python3 "$SCRIPT_DIR/clipmail_raycast.py" 