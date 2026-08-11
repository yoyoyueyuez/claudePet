# Blobby

> _blobby is watching you._ 👀

A tiny terminal pet that lives in the **Claude Code status line** — and a switchboard for every Claude session on your machine.

```
 ▄▀▀▀▀▀▀▀▄
 █ ◕  ◕ █
 █   ▿  █
 ▀▄▄▄▄▄▄▀
```

When things are calm, that's all it is: a blob and a caption. But Blobby also keeps an eye on every live Claude Code session. When one finishes a turn and is waiting on **you**, it pings you once and puts on its alert face:

```
 ▄▀▀▀▀▀▀▀▄ !
 █ ◕  ◕ █
 █  !!!  █
 ▀▄▄▄▄▄▄▀
```

…and the status line tells you who's waiting.

## Requirements

- **macOS** — notifications and window focus use AppleScript (`osascript`).
- **Claude Code** (recent version) — Blobby hooks into the status line and reads `claude agents --json`.

## Install

```bash
git clone https://github.com/yoyoyueyuez/claudePet.git
cd claudePet
./install.sh
```

The installer links the `/pet` and `/blobby` skills into `~/.claude/skills/` and adds the status-line entry (with a 2-second refresh) to `~/.claude/settings.json`. Then restart Claude Code, or run `/reload-skills`.

Blobby appears in the footer of **every** session. Want it gone?

```bash
/pet off
```

## Commands

| Command | What it does |
|---|---|
| `/pet on` / `/pet off` | show / hide the pet |
| `/pet toggle` | flip it (no argument also toggles) |
| `/pet status` | is the pet on or off? |
| `/blobby` | full report of every live session |
| `/blobby list` | just the sessions that need your input, and what each is waiting on |
| `/blobby <id-or-name>` | switch to that session — focus its window if it's live, or reopen it via `claude --resume <id>` if it isn't |

## How it works

Every status-line render (roughly every 2 seconds), Blobby:

1. Lists the live sessions with `claude agents --json`.
2. Marks a session as _needs you_ when its status is `idle` — it finished its turn and is waiting for input. Your own session never flags itself: you're already looking at it.
3. When a session flips **busy → idle**, sends **one** macOS notification. It's deduped and only re-arms when that session starts working again — so it nudges you once, then goes quiet.
4. Prints a compact footer: name + short session id. The status line truncates long text, so that's on purpose; `/blobby list` gives you the full picture, with what each session is waiting on.

The short id in the footer is exactly what `/blobby` accepts, so `⚠ claudepet-3b [d45fbf4c] needs you` turns straight into `/blobby d45fbf4c`.

## Files

| Path | Role |
|---|---|
| `statusline.sh` | status-line entry point — honors the off-state, runs the watcher |
| `blobby_watch.py` | the watcher — polls sessions, pings once per wait, renders the footer |
| `blobby.py` | the `/blobby` command (report, list, switch, resume) |
| `pet.sh` | `/pet` on/off/toggle/status |
| `install.sh` | installer — links the skills, adds the status-line entry |
| `.claude/skills/pet`, `.claude/skills/blobby` | slash-command definitions |
| `art/blob.txt`, `art/blob-alert.txt` | the two faces |

## Notes

Personal project — macOS, works on my machine. The creature and captions are pure ASCII and swappable: edit `art/` and start a new session.
