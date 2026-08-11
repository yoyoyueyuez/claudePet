#!/usr/bin/env python3
"""blobby.py — the /blobby command.

On-demand counterpart to the watcher (blobby_watch.py): lists every live
Claude Code session, shows which ones need you (idle) with the project and
Claude's last words from the transcript, and lets you switch to a session.

Usage:
  blobby.py                 full report of all sessions
  blobby.py list            list every session that needs your input
  blobby.py <session-id>    switch to that session (accepts id or name):
                              live -> focus its window
                              not running -> open `claude --resume <id>`
"""
import os
import subprocess
import sys

from blobby_watch import get_sessions, last_words, project_name, session_label

ART_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "art")


def print_alert_art():
    try:
        with open(os.path.join(ART_DIR, "blob-alert.txt")) as f:
            print(f.read().rstrip("\n"))
    except OSError:
        pass


def tty_of(pid):
    """The tty a process is attached to, e.g. 'ttys006'."""
    try:
        out = subprocess.check_output(["ps", "-o", "tty=", "-p", str(pid)],
                                      text=True, stderr=subprocess.DEVNULL)
        return out.strip() or None
    except Exception:
        return None


def host_app(pid):
    """Trace up from the claude process to the app hosting it: 'vscode',
    'terminal', or None if it can't be determined."""
    cur, seen = pid, set()
    for _ in range(12):
        if cur in seen or cur <= 1:
            break
        seen.add(cur)
        try:
            comm = subprocess.check_output(["ps", "-o", "comm=", "-p", str(cur)],
                                           text=True, stderr=subprocess.DEVNULL).strip()
            ppid = int(subprocess.check_output(["ps", "-o", "ppid=", "-p", str(cur)],
                                               text=True, stderr=subprocess.DEVNULL).strip())
        except Exception:
            break
        if "Visual Studio Code" in comm or comm.endswith("/Code"):
            return "vscode"
        if "Terminal" in comm:
            return "terminal"
        cur = ppid
    return None


def focus_terminal_by_tty(tty):
    """Focus the Terminal.app window whose pty matches the session's tty."""
    if not tty:
        return None
    if not tty.startswith("/dev/"):
        tty = "/dev/" + tty if tty.startswith("tty") else tty
    try:
        out = subprocess.run(
            ["osascript", "-e", 'tell application "Terminal" to get tty of every window'],
            capture_output=True, text=True, timeout=10)
        ttys = [t.strip() for t in (out.stdout or "").split(",") if t.strip()]
        for i, t in enumerate(ttys, start=1):
            if t == tty:
                script = (
                    'tell application "Terminal" to activate\n'
                    f'tell application "System Events" to tell process "Terminal" '
                    f'to set frontmost of window {i} to true'
                )
                subprocess.run(["osascript", "-e", script], capture_output=True, timeout=10)
                return f"Focused Terminal window {i} (tty {tty})"
    except Exception:
        pass
    return None


def focus_window_by_title(name, cwd):
    """Fallback: raise the Terminal window whose title matches name/project."""
    targets = [t for t in (name, project_name(cwd)) if t]
    try:
        out = subprocess.run(
            ["osascript", "-e", 'tell application "Terminal" to get name of every window'],
            capture_output=True, text=True, timeout=10)
        windows = [w.strip() for w in (out.stdout or "").split(",") if w.strip()]
        for i, title in enumerate(windows, start=1):
            if any(t and t in title for t in targets):
                script = (
                    'tell application "Terminal" to activate\n'
                    f'tell application "System Events" to tell process "Terminal" '
                    f'to set frontmost of window {i} to true'
                )
                subprocess.run(["osascript", "-e", script], capture_output=True, timeout=10)
                return f"Focused Terminal window: “{title}”"
    except Exception:
        pass
    return None


def focus_session(sess):
    """Bring the window/tab actually hosting this session's claude to front."""
    pid = sess.get("pid")
    label = session_label(sess)
    proj = project_name(sess.get("cwd", ""))
    tty = tty_of(pid) if pid else None
    app = host_app(pid) if pid else None
    if app == "terminal":
        res = focus_terminal_by_tty(tty)
        if res:
            return res
    if app == "vscode":
        try:
            subprocess.run(["osascript", "-e", 'tell application "Visual Studio Code" to activate'],
                           capture_output=True, timeout=10)
            where = f"the “{proj}” integrated terminal" if proj else "an integrated terminal"
            return (f"Activated Visual Studio Code — {label} is running in {where} "
                    f"(tty {tty}). Click that terminal tab to resume it.")
        except Exception:
            return None
    # host unknown: best-effort Terminal title match
    return focus_window_by_title(label, sess.get("cwd", ""))


def show_session(sess):
    label = session_label(sess)
    print(f"{label} — {sess.get('status')} — {project_name(sess.get('cwd', ''))}")
    print(f"  session: {sess.get('sessionId')}")
    words = last_words(sess.get("cwd", ""), sess.get("sessionId"))
    print(f"  last from Claude: {words}" if words else "  (no transcript text found)")


def open_resume(session_id):
    """Open a new Terminal window that resumes the session from disk."""
    try:
        script = f'tell application "Terminal" to do script "claude --resume {session_id}"'
        subprocess.run(["osascript", "-e", script], capture_output=True, timeout=10)
        return f"Opened a new Terminal window resuming {session_id}"
    except Exception:
        return None


def report(sessions):
    print(f"{len(sessions)} live session{'s' if len(sessions) != 1 else ''}:")
    for s in sessions:
        mark = "⚠" if s.get("status") == "idle" else "·"
        print(f"  {mark} {session_label(s)}  [{s.get('status')}]  {project_name(s.get('cwd', ''))}")
    waiting = [s for s in sessions if s.get("status") == "idle"]
    if not waiting:
        print("\nNothing waiting on you — Blobby is calm. 😌")
        return
    print()
    print_alert_art()
    for s in waiting:
        print(f"=== {session_label(s)} needs you ===")
        show_session(s)
    if len(waiting) == 1:
        res = focus_session(waiting[0])
        print("\n" + res if res else "\nCouldn't auto-focus a window — switch to it manually.")


def list_waiting(sessions):
    """Compact list of every session that needs input (idle), no side effects."""
    waiting = [s for s in sessions if s.get("status") == "idle"]
    if not waiting:
        print("Nothing needs your input right now — Blobby is calm. 😌")
        return
    verb = "needs" if len(waiting) == 1 else "need"
    print(f"{len(waiting)} session{'s' if len(waiting) != 1 else ''} {verb} your input:")
    for s in waiting:
        label = session_label(s)
        short_id = (s.get("sessionId") or "")[:8]
        proj = project_name(s.get("cwd", ""))
        print(f"⚠ {label}  [{short_id}]  {proj}")
        words = last_words(s.get("cwd", ""), s.get("sessionId"), limit=110, single_line=True)
        if words:
            print(f'   waiting: "{words}"')
    print("\nRun /blobby <id> to switch to one of them.")


def main():
    args = sys.argv[1:]
    sessions = get_sessions()
    if not sessions:
        print("No live Claude Code sessions right now.")
        return 0
    if args:
        key = args[0]
        if key in ("list", "ls", "-l", "--list"):
            list_waiting(sessions)
            return 0
        target = next((s for s in sessions
                       if s.get("sessionId", "").startswith(key) or key in session_label(s)), None)
        if target:
            label = session_label(target)
            show_session(target)
            res = focus_session(target)
            print("  " + res if res else "  Couldn't auto-focus — switch to it manually.")
        else:
            print(f"“{key}” isn't running right now — opening a resume window…")
            res = open_resume(key)
            print("  " + res if res else "  Couldn't open a resume window.")
        return 0
    report(sessions)
    return 0


if __name__ == "__main__":
    sys.exit(main())
