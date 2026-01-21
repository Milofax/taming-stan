#!/usr/bin/env python3
import fcntl, hashlib, json, os, re, subprocess, time
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
    "active_group_ids",
    "group_id_decision",
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

# --- Group ID Detection (shared across hooks) ---

def find_git_root(start_path: str) -> str | None:
    """Find Git root from a path."""
    path = Path(start_path)
    while path != path.parent:
        if (path / ".git").exists():
            return str(path)
        path = path.parent
    return None

def get_github_repo(git_root: str) -> str | None:
    """Extract owner/repo from GitHub remote URL."""
    try:
        result = subprocess.run(
            ["git", "-C", git_root, "remote", "get-url", "origin"],
            capture_output=True, text=True, timeout=3
        )
        if result.returncode != 0:
            return None
        remote_url = result.stdout.strip()
        if remote_url.startswith("git@github.com:"):
            return remote_url[len("git@github.com:"):].removesuffix(".git")
        if remote_url.startswith("https://github.com/"):
            return remote_url[len("https://github.com/"):].removesuffix(".git")
        return None
    except Exception:
        return None

def detect_group_id(working_dir: str) -> tuple[str, str]:
    """
    Detect group_id from path. Returns (group_id, project_name).
    Priority: .graphiti-group > CLAUDE.md > GitHub remote > "main"
    """
    if not working_dir:
        return "main", ""
    cwd_path = Path(working_dir)

    # 1. Check .graphiti-group file
    for check_path in [cwd_path] + list(cwd_path.parents):
        graphiti_file = check_path / ".graphiti-group"
        if graphiti_file.exists():
            try:
                content = graphiti_file.read_text().strip()
                if content:
                    if ":" in content:
                        group_id, name = content.split(":", 1)
                        return group_id.strip(), name.strip()
                    return content, check_path.name
            except Exception:
                pass

    # 2. Check CLAUDE.md for graphiti_group_id
    for check_path in [cwd_path] + list(cwd_path.parents):
        claude_md = check_path / "CLAUDE.md"
        if claude_md.exists():
            try:
                content = claude_md.read_text()
                match = re.search(r'graphiti_group_id:\s*(\S+)', content)
                if match:
                    return match.group(1).strip(), check_path.name
            except Exception:
                pass

    # 3. Git-based: GitHub remote only (no folder fallback)
    git_root = find_git_root(working_dir)
    if git_root:
        github_repo = get_github_repo(git_root)
        if github_repo:
            # Convert Owner/Repo to Owner-Repo (Graphiti rejects slashes)
            return github_repo.replace("/", "-"), Path(git_root).name

    return "main", ""

def track_group_id_for_path(file_path: str) -> str | None:
    """
    Detect group_id for a file path and add to active_group_ids.
    Returns the detected group_id or None.
    """
    if not file_path:
        return None
    # Get directory from file path
    path = Path(file_path)
    working_dir = str(path.parent) if path.is_file() or not path.exists() else str(path)

    group_id, _ = detect_group_id(working_dir)
    if group_id and group_id != "main":
        append_to_list("active_group_ids", group_id)
    return group_id
