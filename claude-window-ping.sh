#!/usr/bin/env bash
# Start a minimal Claude Code session to anchor a 5-hour usage window.
# Intended to be triggered by cron at strategic times.

LOG="$HOME/.claude_window_ping.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M %Z')

echo "$TIMESTAMP - starting window ping" >> "$LOG"

# Run a minimal prompt that uses negligible tokens
if "$HOME/.local/bin/claude" -p "reply with 'ok'" --model haiku > /dev/null 2>&1; then
    echo "$TIMESTAMP - window ping OK" >> "$LOG"
else
    echo "$TIMESTAMP - window ping FAILED (exit $?)" >> "$LOG"
fi
