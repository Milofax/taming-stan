# Hooks Reference

## SessionStart Hooks

### graphiti-context-loader.py
Loads project context at session start.

**Triggers:** Once per session

**Function:**
- Detects project from working directory
- Outputs group_id for Graphiti
- Shows context reminder

### reset-session-flags.py
Resets session-specific state flags.

**Triggers:** Once per session

**Function:**
- Clears `firecrawl_attempted`
- Clears `graphiti_searched`
- Clears `context7_attempted_for`

---

## UserPromptSubmit Hooks

### session-reminder.py
Shows project context reminder on each prompt.

**Triggers:** Every user prompt

**Output:**
```
📁 Project: my-project
   group_id: Milofax-my-project
```

### graphiti-knowledge-reminder.py
Reminds to search Graphiti before answering.

**Triggers:** Every user prompt

**Output:**
```
❌ !!graphiti_first:REQUIRED before answering
   →search_nodes(group_ids=["project-xyz", "main"])
```

---

## PreToolUse Hooks

### graphiti-guard.py
Validates Graphiti add_memory calls.

**Matcher:** `mcp__graphiti.*`, `mcp__mcp-funnel__bridge_tool_request`

**Validates:**
- `source_description` is present
- No credentials in content (903 patterns)
- Technical learnings include version
- Citations are complete

**Block reasons:**
- Missing source_description
- Credentials detected
- Missing version for technical content

### graphiti-first-guard.py
Enforces search-first pattern for web tools.

**Matcher:** `WebSearch|WebFetch`, `mcp__mcp-funnel__bridge_tool_request`

**Function:**
- Checks if `graphiti_searched` flag is set
- Blocks WebSearch/WebFetch if Graphiti not searched first

**Block message:**
```
STOP! Search Graphiti BEFORE web search.
→search_nodes(group_ids=["project-xyz", "main"])
```

### firecrawl-guard.py
Enforces Firecrawl before WebSearch/WebFetch.

**Matcher:** `mcp__firecrawl.*`, `mcp__mcp-funnel__bridge_tool_request`, `WebSearch|WebFetch`

**Function:**
- Tracks `firecrawl_attempted` flag
- Blocks WebSearch/WebFetch if Firecrawl not tried first

### context7-guard.py
Enforces Context7 for library documentation.

**Matcher:** `mcp__context7.*`, `mcp__mcp-funnel__bridge_tool_request`

**Function:**
- Tracks which libraries have been checked
- Reminds to use Context7 for known libraries

### git-workflow-guard.py
Validates git commits against workflow rules.

**Matcher:** `Bash`

**Validates:**
- Conventional commit format
- No direct push to main
- No force push without confirmation

### file-context-tracker.py
Tracks file operations for context.

**Matcher:** `Read|Edit|Write|Glob|Grep`

**Function:**
- Records which files have been accessed
- Helps with project context

### playwright-guard.py
Enforces Playwright MCP best practices.

**Matcher:** `mcp__playwright.*`, `mcp__mcp-funnel__bridge_tool_request`, `Bash`

### agent-browser-guard.py
Enforces agent-browser CLI best practices.

**Matcher:** `Bash`, `mcp__mcp-funnel__bridge_tool_request`

**Validates:**
- Snapshot before interaction
- Use refs instead of selectors

---

## PostToolUse Hooks

### graphiti-retry-guard.py
Implements 3-strikes pattern for repeated errors.

**Matcher:** `Bash`, `mcp__.*`

**Function:**
- Tracks consecutive errors per tool
- After 3 identical errors, blocks further attempts
- Suggests searching Graphiti for solutions

**Output on 3rd strike:**
```
{
  "permissionDecision": "deny",
  "denyMessage": "3 identical errors. Search Graphiti for existing solutions."
}
```

---

## Shared Library

### session_state.py
Provides atomic state management for hooks.

**Functions:**
- `read_state()` - Read current state
- `write_state(key, value)` - Write single value
- `run_once(hook_name, ttl)` - Deduplicate hook execution
- `reset_session_flags()` - Clear session-specific flags

### secret_patterns.py
Contains 903 regex patterns for credential detection.

**Categories:**
- API keys (AWS, GCP, Azure, etc.)
- Tokens (JWT, OAuth, etc.)
- Passwords and secrets
- Private keys (SSH, PGP, etc.)
- Database connection strings
