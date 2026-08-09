#!/usr/bin/env bash
# Terminal pet — static blob in the Claude Code status line.
# Reads art from art/blob.txt so the creature is swappable without touching code.
PET_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "blobby is watching you"
cat "${PET_DIR}/art/blob.txt"
