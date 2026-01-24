# Prompt Hook Test Experiment

## Purpose

Test whether `type: prompt` hooks (Claude Code 2.1.19+) can invoke MCP tools like Graphiti. Updated: 2026-01-24 22:32.

This is part of the "Guards to Skills" exploration documented in `plans/prompt-hooks-exploration.md`.

## Hypothesis

If prompt hooks can call MCP, we can evolve from:
- **Reactive Guards** (block after mistake)
- to **Proactive Skills** (learn and act autonomously)

## Setup

### Enable the plugin:
```bash
claude plugins enable experiments/prompt-hook-test
```

### Disable the plugin:
```bash
claude plugins disable experiments/prompt-hook-test
```

## Critical Finding (2026-01-24)

**type:prompt hooks CANNOT directly call MCP tools.**

They can only return:
- `continue`: true/false
- `systemMessage`: Text message to Claude
- `permissionDecision`: allow/deny/ask
- `updatedInput`: Modified tool parameters

### Workaround: Indirect Steering

Hooks send `systemMessage` to Claude, which then decides whether to act:
```
Hook detects learning → systemMessage: "Save this to Graphiti" → Claude calls add_memory
```

## What This Tests

### PostToolUse Hook
- Runs after every tool call
- Analyzes results for potential learnings
- Returns `systemMessage` suggesting Claude save to Graphiti
- Does NOT directly call MCP (not possible)

### Stop Hook
- Runs at session end
- Reviews session for unsaved learnings
- Can block session end if learnings detected

## Parallel Operation

**Important:** This plugin runs IN ADDITION to existing guards in `hooks/`.

| Layer | Location | Function |
|-------|----------|----------|
| New Skills | This plugin | Proactive learning detection |
| Old Guards | `hooks/` | Fallback if skills miss something |

## Expected Outcomes

### Confirmed: MCP does NOT work from prompt hooks

**Result:** Prompt hooks are limited to text/decision output only.

### Adjusted Strategy: Skills + Guards (Hybrid)

| Component | Role |
|-----------|------|
| type:prompt Skill | Detects learnings, sends systemMessage |
| Claude | Decides whether to follow suggestion |
| type:command Guard | Validates the actual Graphiti call |

### What we're now testing:
1. Does Claude follow systemMessage suggestions?
2. How reliably does the prompt hook detect learnings?
3. Is the latency acceptable (10s timeout per hook)?

## Metrics to Track

1. **Skill detections:** How often does the prompt hook detect a learning?
2. **MCP success rate:** Can it actually save to Graphiti?
3. **Guard fallback rate:** How often do old guards still trigger?
