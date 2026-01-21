#!/usr/bin/env python3
"""
Graphiti Retry Guard (PostToolUse Hook)

Tracks consecutive tool failures. After 3 failures on same tool,
blocks until Graphiti is searched for relevant learnings.

Principle: Zettelkasten - Knowledge AND Access = Value.
If you keep failing, check if you already learned something about this.
"""
import json
import sys
import os
import time
import hashlib

HOOK_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HOOK_DIR, '..', 'lib'))
from session_state import register_hook, read_state, write_state

FAILURE_THRESHOLD = 3
TIME_WINDOW = 300  # 5 minutes


def allow():
    return {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "permissionDecision": "allow"
        }
    }


def deny(msg):
    return {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": msg
        }
    }


def get_error_key(tool_name, error):
    """Create key from tool + error pattern (first 50 chars)."""
    error_prefix = (error or "")[:50].strip()
    return hashlib.md5(f"{tool_name}:{error_prefix}".encode()).hexdigest()[:12]


def main():
    try:
        hook_input = json.load(sys.stdin)
    except Exception:
        print(json.dumps(allow()))
        return

    register_hook("graphiti-retry")

    tool_name = hook_input.get("tool_name", "")
    tool_error = hook_input.get("tool_error")

    # Success = reset counter for this tool
    if not tool_error:
        state = read_state()
        failures = state.get("tool_failures", {})
        if tool_name in failures:
            del failures[tool_name]
            write_state("tool_failures", failures)
        print(json.dumps(allow()))
        return

    # Failure = increment counter
    state = read_state()
    failures = state.get("tool_failures", {})
    now = time.time()

    tool_data = failures.get(tool_name, {"count": 0, "last_time": 0, "error_key": ""})
    error_key = get_error_key(tool_name, tool_error)

    # Reset if outside time window or different error
    if now - tool_data["last_time"] > TIME_WINDOW or tool_data["error_key"] != error_key:
        tool_data = {"count": 0, "last_time": now, "error_key": error_key}

    tool_data["count"] += 1
    tool_data["last_time"] = now
    failures[tool_name] = tool_data
    write_state("tool_failures", failures)

    # Check threshold
    if tool_data["count"] >= FAILURE_THRESHOLD:
        # Check if Graphiti was already searched
        if state.get("graphiti_searched"):
            # Already searched, allow retry (but keep counting)
            print(json.dumps(allow()))
            return

        # Block until Graphiti search
        group_ids = state.get("active_group_ids", [])
        gids = ["main"] + [g for g in group_ids if g != "main"]
        gids_str = '", "'.join(gids)

        # Truncate error for display
        error_display = (tool_error or "")[:40]
        if len(tool_error or "") > 40:
            error_display += "..."

        print(json.dumps(deny(
            f"🛑 3-Strikes: {tool_name} failed {tool_data['count']}x with same error.\n"
            f"→ search_nodes(query=\"{error_display}\", group_ids=[\"{gids_str}\"])\n"
            f"Zettelkasten: Check existing knowledge BEFORE retry."
        )))
        return

    print(json.dumps(allow()))


if __name__ == "__main__":
    main()
