# taming-stan

All-in-one Claude Code enhancement: Graphiti memory, intelligent guards, and STAN.FLUX rules.

## Features

- **Graphiti Integration** - Long-term memory with knowledge graph, credential protection, citation validation
- **Smart Guards** - Pre/Post tool-use guards for Firecrawl, Context7, Git, and more
- **STAN.FLUX Rules** - Structured behavior rules for research, validation, and error handling
- **Unified Installer** - Single command to configure everything

## Quick Start

```bash
# Interactive installation
npx taming-stan install

# Install all services
npx taming-stan install --all

# Install specific services
npx taming-stan install graphiti firecrawl stanflux
```

## Installation

### Global (HOME)
```bash
cd ~
npx taming-stan install
```
Hooks apply to all projects. Rules are installed globally.

### Project-specific
```bash
cd /your/project
npx taming-stan install
```
If HOME already has hooks, only rules are installed locally (hooks inherited).

## Services

### Graphiti (Memory)
| Service | Description |
|---------|-------------|
| `graphiti` | Long-term memory with knowledge graph (Recommended) |

### General Rules
| Service | Description |
|---------|-------------|
| `stanflux` | Behavior rules for Claude (research, validation, errors) |
| `pith` | Compact notation format reference |
| `1password` | SSH keys & secrets via 1Password Agent |

### Git Workflow (choose one)
| Service | Description |
|---------|-------------|
| `git-workflow-github-flow` | main + feature branches (Recommended) |
| `git-workflow-trunk-based` | Short branches + feature flags |
| `git-workflow-git-flow` | main + develop + feature + release + hotfix |

### Browser Automation (choose one)
| Service | Description |
|---------|-------------|
| `agent-browser` | CLI-based automation (Recommended) |
| `playwright` | MCP Server-based automation |

### MCP Server Rules
| Service | Description |
|---------|-------------|
| `firecrawl` | Web search & scraping |
| `context7` | GitHub libraries research |
| `github` | GitHub API (Issues, PRs) |
| `bible` | Bible passages (13 translations) |
| `morgen` | Calendar & scheduling |
| And more... | |

## Commands

```bash
npx taming-stan install                     # Interactive selection
npx taming-stan install --all               # All services
npx taming-stan install <service,...>       # Specific services
npx taming-stan uninstall                   # Remove all
npx taming-stan status                      # Show status
```

## Hooks Overview

| Event | Hook | Purpose |
|-------|------|---------|
| SessionStart | graphiti-context-loader.py | Load project context |
| SessionStart | reset-session-flags.py | Reset session state |
| UserPromptSubmit | session-reminder.py | Project context reminder |
| UserPromptSubmit | graphiti-knowledge-reminder.py | Memory search reminder |
| PreToolUse | graphiti-guard.py | Validate add_memory calls |
| PreToolUse | graphiti-first-guard.py | Enforce search-first |
| PreToolUse | firecrawl-guard.py | Enforce Firecrawl before WebSearch |
| PreToolUse | context7-guard.py | Enforce Context7 for libraries |
| PreToolUse | git-workflow-guard.py | Validate git commits |
| PreToolUse | file-context-tracker.py | Track file operations |
| PostToolUse | graphiti-retry-guard.py | 3-strikes error pattern |

## Documentation

- [Architecture](docs/architecture.md) - System design and hook flow
- [Hooks Reference](docs/hooks.md) - Detailed hook documentation
- [Rules Reference](docs/rules.md) - All available rules

## Development

### Tests
```bash
# Run all tests
npm test

# Python tests only
pytest tests/ -v

# Installer tests only
bash test/installer.test.sh
```

### Project Structure
```
taming-stan/
├── bin/cli.js          # Unified installer
├── hooks/              # All hooks by event type
│   ├── session-start/
│   ├── user-prompt-submit/
│   ├── pre-tool-use/
│   ├── post-tool-use/
│   └── lib/            # Shared Python modules
├── rules/              # All rules
│   └── mcp-configurations/
├── commands/           # Slash commands
├── lib/                # Source library files
├── tests/              # Python tests
└── test/               # Bash tests
```

## Migration from Previous Packages

If you were using the separate packages:
- `graphiti-claude-integration` -> `taming-stan`
- `shared-claude-rules` -> `taming-stan`
- `claude-hooks-core` -> (bundled in taming-stan)

```bash
# Uninstall old packages first
cd ~ && npx graphiti-claude-integration uninstall
cd ~ && npx shared-claude-rules uninstall

# Install taming-stan
cd ~ && npx taming-stan install --all
```

## License

MIT
