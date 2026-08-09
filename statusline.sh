#!/usr/bin/env bash
# Terminal pet — static blob in the Claude Code status line.
# Reads art from art/blob.txt so the creature is swappable without touching code.
# Honors the off-state: presence of ~/.claude/pet-off means the pet is hidden.
PET_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -f "$HOME/.claude/pet-off" ]; then
  exit 0
fi

echo "blobby is watching you"
cat "${PET_DIR}/art/blob.txt"
