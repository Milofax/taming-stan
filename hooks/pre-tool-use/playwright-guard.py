#!/usr/bin/env python3
"""
Playwright Guard - Enforces MCP over CLI and headless default.

Rules:
- !!erst: Block CLI tools (playwright, puppeteer, cypress, selenium) → Use MCP instead
- !!headless: headless:false requires explicit USER confirmation (not Claude auto-confirm)
  Standard ist IMMER headless:true. Browser sichtbar nur wenn User explizit bestätigt.
"""
import json, sys, os, re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from session_state import register_hook, read_state, write_state

BLOCKED = [r"(?:npx|npm run|yarn|pnpm)\s+(?:exec\s+)?playwright\b",r"(?:npx|npm run|yarn|pnpm)\s+(?:exec\s+)?puppeteer\b",r"(?:npx|npm run|yarn|pnpm)\s+(?:exec\s+)?cypress\b",r"\bplaywright\s+(?:test|install|codegen|show-report)\b",r"\bpuppeteer\s+",r"\bcypress\s+(?:run|open|install)\b",r"\bselenium-webdriver\b",r"\bwebdriver-manager\b",r"\bagent-browser\s+"]

def allow(): return {"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow"}}
def deny(msg): return {"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":msg}}

def main():
    try: hi = json.load(sys.stdin)
    except: print(json.dumps(allow())); return
    register_hook("playwright")
    tn, ti = hi.get("tool_name",""), hi.get("tool_input",{})
    if tn == "Bash":
        cmd = ti.get("command","")
        for p in BLOCKED:
            m = re.search(p, cmd, re.I)
            if m:
                print(json.dumps(deny(f"💡 Playwright MCP > '{m.group()}' CLI\n→discover_tools_by_words('playwright',enable=true)")))
                return
    if tn == "mcp__mcp-funnel__bridge_tool_request":
        bt = ti.get("tool","")
        args = ti.get("arguments",{})
        # !!headless: Standard ist headless:true
        # headless:false nur wenn User es explizit will (Confirm-by-Retry)
        if "playwright" in bt.lower():
            headless_val = args.get("headless")
            if headless_val is False:
                state = read_state()
                if state.get("headless_confirmed"):
                    write_state("headless_confirmed", False)  # Reset für nächstes Mal
                    print(json.dumps(allow()))
                    return
                write_state("headless_confirmed", True)
                print(json.dumps(deny("💡 headless:true ist Standard.\n→User will Browser sehen? JA=wiederholen|NEIN=headless:true setzen")))
                return
    print(json.dumps(allow()))

if __name__ == "__main__": main()
