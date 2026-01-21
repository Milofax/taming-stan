#!/usr/bin/env python3
import fcntl, hashlib, json, os, time
from pathlib import Path
from typing import Any, Callable

def get_session_id() -> str:
    """
    Get a unique identifier for the state file.
    Uses working directory hash to separate state between parallel projects.
    Note: The actual Claude session_id comes via stdin JSON in hooks,
    not as an environment variable.
    """
    cwd_hash = hashlib.md5(os.getcwd().encode()).hexdigest()[:8]
    return f"state-{cwd_hash}"

def get_state_path() -> Path:
    return Path(f"/tmp/claude-session-{get_session_id()}.json")

def _atomic_update(updater: Callable[[dict], dict]) -> None:
    sp, lp = get_state_path(), Path(f"{get_state_path()}.lock")
    try:
        lp.touch(exist_ok=True)
        with open(lp, 'r+') as lf:
            fcntl.flock(lf.fileno(), fcntl.LOCK_EX)
            try:
                state = json.loads(sp.read_text()) if sp.exists() else {}
            except: state = {}
            sp.write_text(json.dumps(updater(state), indent=2))
            fcntl.flock(lf.fileno(), fcntl.LOCK_UN)
    except: pass

def read_state() -> dict:
    sp, lp = get_state_path(), Path(f"{get_state_path()}.lock")
    try:
        lp.touch(exist_ok=True)
        with open(lp, 'r') as lf:
            fcntl.flock(lf.fileno(), fcntl.LOCK_SH)
            try:
                r = json.loads(sp.read_text()) if sp.exists() else {}
            except: r = {}
            fcntl.flock(lf.fileno(), fcntl.LOCK_UN)
            return r
    except: return {}

def write_state(key: str, value: Any) -> None:
    _atomic_update(lambda s: {**s, key: value})

def register_hook(hook_name: str) -> None:
    def u(s):
        h = s.get("hooks_active", {}); h[hook_name] = True; s["hooks_active"] = h; return s
    _atomic_update(u)

def run_once(hook_name: str, ttl_seconds: float = 2.0) -> bool:
    """
    Deduplicate hook execution when same hook is registered globally AND locally.
    Returns True if this is the first run, False if duplicate (should skip).
    Uses timestamp to detect if hook ran very recently (within ttl_seconds).
    """
    key = f"_run_once_{hook_name}"
    state = read_state()
    last_run = state.get(key, 0)
    now = time.time()

    if now - last_run < ttl_seconds:
        # Duplicate execution detected - skip
        return False

    # First run - mark timestamp
    write_state(key, now)
    return True

def is_hook_active(hook_name: str) -> bool:
    return read_state().get("hooks_active", {}).get(hook_name, False)

def append_to_list(key: str, value: Any) -> None:
    def u(s):
        l = s.get(key, [])
        if value not in l: l.append(value)
        s[key] = l; return s
    _atomic_update(u)

# Session-specific flags that should be reset on new session
SESSION_FLAGS = [
    "firecrawl_attempted",
    "graphiti_searched",
    "context7_attempted_for",
]

def reset_session_flags() -> None:
    """Reset session-specific flags."""
    def u(s):
        for flag in SESSION_FLAGS:
            s.pop(flag, None)
        return s
    _atomic_update(u)

def check_and_update_session(claude_session_id: str) -> bool:
    """
    Check if this is a new Claude session and reset flags if needed.

    Args:
        claude_session_id: The session_id from Claude's hook input JSON

    Returns:
        True if this is a new session (flags were reset), False otherwise
    """
    state = read_state()
    previous_session = state.get("claude_session_id")

    if previous_session != claude_session_id:
        # New session detected - reset flags and store new session ID
        def u(s):
            for flag in SESSION_FLAGS:
                s.pop(flag, None)
            s["claude_session_id"] = claude_session_id
            return s
        _atomic_update(u)
        return True

    return False
