#!/usr/bin/env python3
import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from session_state import register_hook, append_to_list, read_state

def allow(): return {"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow"}}
def deny(msg): return {"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":msg}}

def graphiti_check_required():
    """Check if Graphiti search is required before external research."""
    state = read_state()
    if not state.get("graphiti_available"): return False
    return not state.get("graphiti_searched", False)

def main():
    try: hi = json.load(sys.stdin)
    except: print(json.dumps(allow())); return
    register_hook("context7")
    tn, ti = hi.get("tool_name",""), hi.get("tool_input",{})
    if tn == "mcp__mcp-funnel__bridge_tool_request":
        bt = ti.get("tool","")
        if "context7" in bt.lower():
            # Check Graphiti first (Context7 is also external research)
            if graphiti_check_required():
                print(json.dumps(deny("💡 Was weißt du schon dank Graphiti?\n→search_nodes(query)")))
                return
            # Track library lookups
            if "resolve" in bt.lower() or "library" in bt.lower():
                ln = ti.get("arguments",{}).get("libraryName","")
                if ln: append_to_list("context7_attempted_for", ln.lower())
    print(json.dumps(allow()))

if __name__ == "__main__": main()
