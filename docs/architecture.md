# Architecture

## Overview

taming-stan enhances Claude Code through three main components:

1. **Hooks** - Python scripts that intercept Claude's tool calls
2. **Rules** - Markdown files that configure Claude's behavior
3. **Installer** - Node.js CLI that manages installation

## Hook Flow

```
User Prompt
    │
    ▼
SessionStart Hooks
    │ graphiti-context-loader.py
    │ reset-session-flags.py
    ▼
UserPromptSubmit Hooks
    │ session-reminder.py
    │ graphiti-knowledge-reminder.py
    ▼
Claude Processing
    │
    ▼
PreToolUse Hooks (before tool execution)
    │ graphiti-guard.py
    │ graphiti-first-guard.py
    │ firecrawl-guard.py
    │ context7-guard.py
    │ git-workflow-guard.py
    │ file-context-tracker.py
    ▼
Tool Execution
    │
    ▼
PostToolUse Hooks (after tool execution)
    │ graphiti-retry-guard.py
    ▼
Response
```

## Installation Hierarchy

Claude Code supports hierarchical hook installation:

```
~/.claude/settings.json          <- HOME installation (global)
    │
    └── /project/.claude/settings.json  <- Project installation (local)
```

**Rules:**
- HOME hooks apply to all projects
- Project-specific rules can be installed without duplicating hooks
- When HOME has hooks, project installations only add rules

## Session State

Hooks communicate via `/tmp/claude-session-state-{hash}.json`:

```json
{
  "graphiti_searched": true,
  "firecrawl_attempted": true,
  "context7_attempted_for": ["react", "next.js"],
  "error_counts": {"Bash": {"Permission denied": 3}},
  "hooks_active": {"graphiti-guard": true}
}
```

State is per-working-directory (hash of CWD).

## Guard Pattern

Guards enforce best practices by intercepting tool calls:

```python
# PreToolUse guard pattern
def main():
    input_data = json.load(sys.stdin)

    # Check conditions
    if should_block(input_data):
        print(json.dumps({
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "denyMessage": "Reason for blocking"
        }))
    else:
        print(json.dumps({
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow"
        }))
```

## Matchers

PreToolUse hooks use matchers to filter which tools trigger them:

```json
{
  "PreToolUse": [{
    "matcher": "Bash",
    "hooks": [{"type": "command", "command": "/path/to/hook.py"}]
  }, {
    "matcher": "mcp__graphiti.*",
    "hooks": [{"type": "command", "command": "/path/to/guard.py"}]
  }]
}
```

Matchers support:
- Exact names: `Bash`, `Read`, `Write`
- Regex patterns: `mcp__graphiti.*`
- OR patterns: `WebSearch|WebFetch`

## Directory Structure

### Installed (in ~/.claude or /project/.claude)
```
.claude/
├── settings.json           # Hook configuration
├── hooks/taming-stan/      # Hook scripts
│   ├── session-start/
│   ├── user-prompt-submit/
│   ├── pre-tool-use/
│   ├── post-tool-use/
│   └── lib/
├── rules/taming-stan/      # Rule files
│   └── mcp-configurations/
└── commands/taming-stan/   # Slash commands
```

### Source Package
```
taming-stan/
├── bin/cli.js              # Installer
├── hooks/                  # Source hooks
├── rules/                  # Source rules
├── commands/               # Source commands
├── lib/                    # Library files (copied to hooks/lib)
└── tests/                  # Test suite
```

## Services Architecture

Services are defined in `bin/cli.js`:

```javascript
const SERVICES = {
  graphiti: {
    category: 'graphiti',
    name: 'Graphiti',
    hooks: {
      'session-start': ['graphiti-context-loader.py'],
      'pre-tool-use': ['graphiti-guard.py', 'graphiti-first-guard.py'],
      'post-tool-use': ['graphiti-retry-guard.py']
    },
    preToolUseMatchers: {
      'graphiti-guard.py': ['mcp__graphiti.*']
    },
    rule: 'graphiti.md',
    localLib: ['secret_patterns.py']
  }
};
```

Each service can have:
- `hook` (single) or `hooks` (multiple)
- `rule` - Rule file to install
- `commands` - Slash commands
- `localLib` - Additional library files
