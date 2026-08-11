#!/usr/bin/env python3
"""blobby_watch.py — the switchboard watcher for Blobby.

Runs as the Claude Code status-line script (via statusline.sh). Each poll:

  * reads this session's identity from the session JSON on stdin (or env),
  * lists every live session via `claude agents --json`,
  * spots sessions that flipped busy -> idle (now waiting on the user),
  * fires ONE macOS notification per session (deduped; quiet until the next wait),
  * prints the status line: a live caption + blob art when calm, or an
    alert block — who, session id, where, and Claude's last message — when
    a session needs you.

State lives in ~/.claude/pet-watcher/ (seen/ + notified/). Pre-existing idle
sessions show in the caption but do NOT ping — only observed transitions do,
so the first run doesn't ping-storm.
"""
import json
import os
import select
import subprocess
import sys

HOME = os.path.expanduser("~")
WATCH_DIR = os.path.join(HOME, ".claude", "pet-watcher")
SEEN_DIR = os.path.join(WATCH_DIR, "seen")          # <sid> -> last status
NOTIFIED_DIR = os.path.join(WATCH_DIR, "notified")  # <sid> -> marker (ping once)
PROJECTS_DIR = os.path.join(HOME, ".claude", "projects")
PET_DIR = os.path.dirname(os.path.abspath(__file__))
ART_CALM = os.path.join(PET_DIR, "art", "blob.txt")
ART_ALERT = os.path.join(PET_DIR, "art", "blob-alert.txt")


def own_session_id():
    """This session's id: from the status-line JSON on stdin, else env.

    Reads stdin only if data is actually ready — never blocks, so the script
    is safe to run by hand where stdin is a tty or an open pipe.
    """
    try:
        if not sys.stdin.isatty():
            ready, _, _ = select.select([sys.stdin], [], [], 0.5)
            if ready:
                data = json.load(sys.stdin)
                if data.get("session_id"):
                    return data["session_id"]
    except Exception:
        pass
    return os.environ.get("CLAUDE_CODE_SESSION_ID")


def get_sessions():
    try:
        out = subprocess.run(["claude", "agents", "--json"],
                             capture_output=True, text=True, timeout=10)
        parsed = json.loads(out.stdout) if out.stdout.strip() else []
        return parsed if isinstance(parsed, list) else []
    except Exception:
        return []


def project_name(cwd):
    return os.path.basename(cwd.rstrip("/")) if cwd else "?"


def session_label(sess):
    return sess.get("name") or project_name(sess.get("cwd"))


def encode_cwd(cwd):
    """~/.claude/projects dir encoding: leading '-', '/' -> '-'."""
    return "-" + cwd.strip("/").replace("/", "-")


def transcript_path(cwd, sid):
    return os.path.join(PROJECTS_DIR, encode_cwd(cwd), f"{sid}.jsonl")


def last_words(cwd, sid, limit=220, single_line=False):
    """Claude's last assistant text from the session transcript (best effort).

    Reads only the tail of the file so it stays cheap on every poll.
    """
    path = transcript_path(cwd, sid)
    try:
        with open(path, "rb") as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            f.seek(max(0, size - 65536))
            tail = f.read().decode("utf-8", errors="replace")
    except OSError:
        return None
    lines = tail.splitlines()
    if size > 65536 and lines:
        lines = lines[1:]  # drop the partial line we landed mid-way through
    for line in reversed(lines):
        if not line.strip():
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if ev.get("type") != "assistant":
            continue
        content = ev.get("message", {}).get("content")
        texts = []
        if isinstance(content, list):
            texts = [c.get("text", "") for c in content
                     if isinstance(c, dict) and c.get("type") == "text"]
        elif isinstance(content, str):
            texts = [content]
        text = next((t.strip() for t in texts if t and t.strip()), None)
        if text:
            if single_line:
                text = " ".join(text.split())
            return text[:limit] + ("…" if len(text) > limit else "")
    return None


def notify(label, cwd):
    proj = project_name(cwd)
    msg = f"{label} is waiting for you"
    sub = f"in {proj}" if proj and proj != label else "needs your attention"
    try:
        subprocess.run(
            ["osascript", "-e",
             f'display notification "{msg}" with title "Blobby" subtitle "{sub}"'],
            capture_output=True, text=True, timeout=10)
    except Exception:
        pass


def poll(sessions, self_id):
    """Record transitions, fire once-per-wait pings, return waiting sessions."""
    os.makedirs(SEEN_DIR, exist_ok=True)
    os.makedirs(NOTIFIED_DIR, exist_ok=True)
    waiting = []
    for sess in sessions:
        sid = sess.get("sessionId")
        if not sid:
            continue
        status = sess.get("status", "")
        label = session_label(sess)
        if status == "idle" and sid != self_id:
            waiting.append(sess)

        seen_file = os.path.join(SEEN_DIR, sid)
        prev = ""
        try:
            with open(seen_file) as f:
                prev = f.read().strip()
        except OSError:
            pass

        if status == "idle" and prev and prev != "idle" and sid != self_id:
            marker = os.path.join(NOTIFIED_DIR, sid)
            if not os.path.exists(marker):
                notify(label, sess.get("cwd"))
                try:
                    open(marker, "w").close()
                except OSError:
                    pass
        elif status != "idle" and prev == "idle":
            # session went back to work — re-arm it for the next wait
            try:
                os.remove(os.path.join(NOTIFIED_DIR, sid))
            except OSError:
                pass

        try:
            with open(seen_file, "w") as f:
                f.write(status)
        except OSError:
            pass
    return waiting


def render_caption(total):
    return f"👀 watching {total} session{'s' if total != 1 else ''}"


def render_alert(waiting):
    """Alert caption: who's waiting, with the short id for /blobby <id>."""
    head = waiting[0]
    label = session_label(head)
    short_id = (head.get("sessionId") or "")[:8]
    caption = f"⚠ {label} [{short_id}] needs you"
    if len(waiting) > 1:
        caption += f" · +{len(waiting) - 1} more (run /blobby list)"
    return caption


def print_art(path):
    try:
        with open(path) as f:
            sys.stdout.write(f.read())
    except OSError:
        pass


def main():
    self_id = own_session_id()
    sessions = get_sessions()
    waiting = poll(sessions, self_id) if sessions else []
    if waiting:
        print(render_alert(waiting))
        print_art(ART_ALERT)
    else:
        print(render_caption(len(sessions)))
        print_art(ART_CALM)
    return 0


if __name__ == "__main__":
    sys.exit(main())
