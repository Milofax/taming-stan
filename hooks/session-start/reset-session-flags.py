#!/usr/bin/env python3
"""
Session Flag Reset Hook (SessionStart)

Checks if this is a new Claude session and resets session-specific flags.
This ensures flags like firecrawl_attempted don't persist across sessions.

Uses the session_id from Claude's hook input JSON to detect new sessions.
"""

import json
import os
import sys

HOOK_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HOOK_DIR, '..', 'lib'))
from session_state import check_and_update_session, run_once

def main():
    # Deduplicate: Skip if already ran (global + local installation)
    if not run_once("reset-session-flags"):
        return

    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        return

    # Check for new session and reset flags if needed
    session_id = hook_input.get("session_id", "")
    if session_id:
        check_and_update_session(session_id)

if __name__ == "__main__":
    main()
