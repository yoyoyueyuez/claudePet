---
description: Show which Claude Code sessions need your input, switch to a live one (focus its window), or resume a closed session in a new window.
argument-hint: [session-id]
disable-model-invocation: true
---

Run `/Users/yili/Documents/yoyo/claudePet/blobby.py $ARGUMENTS` with the Bash tool and share its output with the user. If they gave a session id, run it with that id — that switches to and resumes the session (live sessions get their window focused; closed sessions open a new Terminal window running `claude --resume <id>`). When no session needs attention, say so plainly and report what Blobby sees across sessions. Report what the switch/resume attempt did.
