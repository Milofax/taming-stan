#!/usr/bin/env python3
"""
Graphiti Knowledge Reminder (UserPromptSubmit Hook)

Injects a systemMessage reminding Claude to check existing Graphiti knowledge
before answering. Does NOT block - just a helpful reminder.

Trigger: Every user prompt (when Graphiti is available)
"""
import json, sys, os
HOOK_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HOOK_DIR, '..', 'lib'))
from session_state import read_state

def main():
    try:
        hi = json.load(sys.stdin)
    except:
        print(json.dumps({"continue": True}))
        return

    state = read_state()

    # Only remind if Graphiti is available
    if not state.get("graphiti_available", False):
        print(json.dumps({"continue": True}))
        return

    # Don't spam if already searched in this prompt cycle
    if state.get("graphiti_searched", False):
        print(json.dumps({"continue": True}))
        return

    # Get active group_ids for context
    project_gid = state.get("project_group_id", "")
    gids = ["main"]
    if project_gid and project_gid != "main":
        gids.append(project_gid)
    gids_str = '", "'.join(gids)

    # Zettelkasten principle: Knowledge only has value if accessed
    output = {
        "continue": True,
        "systemMessage": f"💡 !!Zettelkasten=Value: search_nodes([\"{gids_str}\"])"
    }
    print(json.dumps(output))

if __name__ == "__main__":
    main()
