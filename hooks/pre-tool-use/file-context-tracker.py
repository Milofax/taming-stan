#!/usr/bin/env python3
"""
File Context Tracker Hook (PreToolUse)

Tracks which projects/repos Claude works with during a session.
When files are read/edited in different repos, their group_ids
are added to active_group_ids in session state.

Triggers: Read|Edit|Write|Glob|Grep
Action: Always ALLOW (tracking only, no blocking)
"""
import json, sys, os
HOOK_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HOOK_DIR, '..', 'lib'))
from session_state import track_group_id_for_path, read_state

def allow():
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow"}}

def get_file_path(tool_name: str, tool_input: dict) -> str | None:
    """Extract file path from tool arguments."""
    if tool_name in ("Read", "Edit", "Write"):
        return tool_input.get("file_path")
    elif tool_name == "Glob":
        return tool_input.get("path")  # directory path
    elif tool_name == "Grep":
        return tool_input.get("path")  # directory or file path
    return None

def main():
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        print(json.dumps(allow()))
        return

    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})

    # Extract file path based on tool type
    file_path = get_file_path(tool_name, tool_input)

    if file_path:
        # Track the group_id for this path (adds to active_group_ids if not main)
        track_group_id_for_path(file_path)

    # Always allow - this hook only tracks, never blocks
    print(json.dumps(allow()))

if __name__ == "__main__":
    main()
