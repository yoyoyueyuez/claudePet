#!/usr/bin/env bash
# install.sh — wire the terminal pet into Claude Code.
# Idempotent: safe to run repeatedly. The repo is the single source of truth
# (git-tracked); this script only recreates the user-level skill symlinks and
# the statusLine settings entry.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_DIR="$HOME/.claude/skills"
SETTINGS="$HOME/.claude/settings.json"

# 1. Skills — make /pet and /blobby available at the user level via symlinks
#    into the repo, so the real files stay git-tracked.
mkdir -p "$SKILLS_DIR"
for skill in pet blobby; do
  link="$SKILLS_DIR/$skill"
  if [ ! -e "$link" ]; then
    ln -s "$REPO_DIR/.claude/skills/$skill" "$link"
    echo "Linked skill: $link -> $REPO_DIR/.claude/skills/$skill"
  else
    echo "Skill link already present: $link"
  fi
done

# 2. Settings — add the statusLine entry (with a 2s refresh so the watcher
#    polls live sessions) if it's missing, and backfill refreshInterval if a
#    statusLine already exists without one.
python3 - "$REPO_DIR" "$SETTINGS" <<'PY'
import json, sys
repo, path = sys.argv[1], sys.argv[2]
with open(path) as f:
    data = json.load(f)

changed = False
sl = data.get("statusLine")
if sl is None:
    data["statusLine"] = {"type": "command", "command": f"{repo}/statusline.sh", "refreshInterval": 2}
    print("Added statusLine to", path)
    changed = True
elif sl.get("refreshInterval") is None:
    sl["refreshInterval"] = 2
    print("Added refreshInterval: 2 to existing statusLine in", path)
    changed = True
else:
    print("statusLine already present with refreshInterval in", path)

if changed:
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
PY

echo "Done. Restart Claude (or run /reload-skills) to pick up the /pet and /blobby commands."
