#!/usr/bin/env bash
# pet — turn the terminal pet on or off.
# State is a marker file: presence of ~/.claude/pet-off means OFF, absence means ON.
# Usage: pet.sh [on|off|toggle|status]   (no argument = toggle)
STATE_FILE="$HOME/.claude/pet-off"

case "${1:-toggle}" in
  on)
    rm -f "$STATE_FILE"
    echo "pet is ON"
    ;;
  off)
    touch "$STATE_FILE"
    echo "pet is OFF"
    ;;
  status)
    if [ -f "$STATE_FILE" ]; then
      echo "pet is OFF"
    else
      echo "pet is ON"
    fi
    ;;
  toggle|*)
    if [ -f "$STATE_FILE" ]; then
      rm -f "$STATE_FILE"
      echo "pet is ON"
    else
      touch "$STATE_FILE"
      echo "pet is OFF"
    fi
    ;;
esac
