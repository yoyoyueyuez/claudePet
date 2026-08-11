#!/usr/bin/env bash
# Terminal pet — Blobby the switchboard watcher in the Claude Code status line.
# Polls live sessions, pings when one needs you, and renders a dynamic caption.
# Honors the off-state: presence of ~/.claude/pet-off means the pet is hidden.
PET_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -f "$HOME/.claude/pet-off" ]; then
  exit 0
fi

exec python3 "$PET_DIR/blobby_watch.py"
