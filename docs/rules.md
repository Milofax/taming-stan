# Rules Reference

## Graphiti (Memory)

### graphiti.md
Complete Graphiti MCP configuration.

**Entity Types:** Person, Organization, Location, Event, Project, Requirement, Procedure, Concept, Learning, Document, Topic, Object, Preference, Decision, Goal, Task, Work, Revision

**Key Rules:**
- Search before answering (graphiti_first)
- Always provide source_description
- Never store credentials
- Use correct group_id (main vs project-specific)

---

## General Rules

### stanflux.md
STAN.FLUX behavior rules for Claude.

**Principles:**
- Knowledge first: Research before acting
- Gründlichkeit: Thorough, not fast
- Transparency: Admit errors immediately
- Empathy: Acknowledge frustration

**Error Handling:**
- Trivial: Fix + continue
- Logic: STOP + verify affected artifacts
- Pattern (3+): 3-strikes rule

### pith.md
PITH notation format reference.

**Symbols:**
- `→` then/leads to
- `|` or
- `!!` critical/MUST
- `!` important

### 1password.md
1Password SSH Agent configuration.

**Key Points:**
- Use SSH Agent (not manual key copying)
- Never use `op read` for SSH keys
- Configure Host entries in ~/.ssh/config

---

## Git Workflows

### git-workflow-github-flow.md
Simple branching strategy.

**Branches:** main + feature branches

**Rules:**
- main is always deployable
- Feature branches are short-lived
- Squash merge for clean history

### git-workflow-trunk-based.md
Trunk-based development.

**Branches:** main + very short-lived branches

**Rules:**
- Branches live < 1 day
- Feature flags for incomplete work
- Continuous integration

### git-workflow-git-flow.md
Full Git Flow strategy.

**Branches:** main, develop, feature/*, release/*, hotfix/*

**Rules:**
- develop for integration
- release branches for stabilization
- hotfix branches for production fixes

---

## Browser Automation

### mcp-configurations/playwright.md
Playwright MCP Server configuration.

**Best Practices:**
- Wait for elements before interaction
- Use data-testid selectors
- Screenshot on failure

### mcp-configurations/agent-browser.md
agent-browser CLI configuration.

**Best Practices:**
- Always snapshot before interaction
- Use refs (@e1, @e2) not selectors
- New snapshot after navigation

---

## MCP Server Rules

### mcp-configurations/firecrawl.md
Firecrawl web scraping MCP.

**Tools:** scrape, search, map, crawl, extract

**Key Rules:**
- Use before WebSearch/WebFetch
- Set maxAge for caching
- Use onlyMainContent: true

### mcp-configurations/context7.md
Context7 library documentation MCP.

**Tools:** resolve-library-id, query-docs

**Workflow:**
1. resolve-library-id(name) -> get ID
2. query-docs(id, topic) -> get docs

### mcp-configurations/github.md
GitHub MCP Server configuration.

### mcp-configurations/bible.md
Bible passages MCP (13 translations).

### mcp-configurations/morgen.md
Morgen calendar MCP.

### mcp-configurations/businessmap.md
BusinessMap portfolio MCP.

### mcp-configurations/macos-automator.md
macOS shortcuts MCP.

### mcp-configurations/unifi.md
UniFi network management MCP.

### mcp-configurations/vscode.md
VS Code integration MCP.

### mcp-configurations/whoop.md
Whoop fitness tracking MCP.

### mcp-configurations/xert.md
Xert cycling analytics MCP.

---

## Rule Format (PITH)

Rules use PITH notation:

```markdown
#PITH:1.2
#MCP:service-name|stand:2026-01

!!critical_rule:MUST do X
  |verstoß:Consequence of violation
  |trigger:When to apply

!important:SHOULD do Y

## section
description:text
```

**Markers:**
- `!!` - Critical (MUST)
- `!` - Important (SHOULD)
- `|` - Sub-rule or condition
