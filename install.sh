#!/usr/bin/env bash
# install.sh — wire the terminal pet into Claude Code.
# Idempotent: safe to run repeatedly. The repo is the single source of truth
# (git-tracked); this script only recreates the user-level symlink + settings entry.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_LINK="$HOME/.claude/skills/pet"
SETTINGS="$HOME/.claude/settings.json"

# 1. Skill — make /pet available at the user level via a symlink into the repo,
#    so the real file stays git-tracked.
if [ ! -e "$SKILL_LINK" ]; then
  mkdir -p "$HOME/.claude/skills"
  ln -s "$REPO_DIR/.claude/skills/pet" "$SKILL_LINK"
  echo "Linked skill: $SKILL_LINK -> $REPO_DIR/.claude/skills/pet"
else
  echo "Skill link already present: $SKILL_LINK"
fi

# 2. Settings — add the statusLine entry if it's missing.
python3 - "$REPO_DIR" "$SETTINGS" <<'PY'
import json, sys
repo, path = sys.argv[1], sys.argv[2]
with open(path) as f:
    data = json.load(f)
if "statusLine" not in data:
    data["statusLine"] = {"type": "command", "command": f"{repo}/statusline.sh"}
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    print("Added statusLine to", path)
else:
    print("statusLine already present in", path)
PY

echo "Done. Restart Claude (or run /reload-skills) to pick up the /pet command."
