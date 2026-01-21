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
npx taming-stan install graphiti firecrawl stanflux git-workflow-github-flow
```

## Hook Workflow

Wenn alle Services installiert sind, läuft folgender Workflow bei jedem Claude Code Aufruf:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              SESSION START                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│  1. reset-session-flags.py     → Setzt Session-Flags zurück                 │
│  2. graphiti-context-loader.py → Lädt Projekt-Kontext, setzt group_id       │
│                                                                              │
│  Output: "Graphiti verfügbar für Projekt X (group_id: Owner-projekt)"       │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           USER PROMPT SUBMIT                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│  1. session-reminder.py           → Zeigt: "📁 Projekt: X, group_id: Y"     │
│  2. graphiti-knowledge-reminder.py → Zeigt: "💡 Erst Graphiti durchsuchen!" │
│                                                                              │
│  Zweck: Claude erinnern, ERST existierendes Wissen zu prüfen                │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                             PRE TOOL USE                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─ Read/Edit/Write/Glob/Grep ──────────────────────────────────────────┐   │
│  │  file-context-tracker.py → Trackt Dateizugriffe für Kontext          │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─ graphiti__add_memory ───────────────────────────────────────────────┐   │
│  │  graphiti-guard.py → Prüft:                                          │   │
│  │    ✗ Quelle fehlt? → BLOCK                                           │   │
│  │    ✗ Credentials erkannt? → BLOCK (3-Strikes)                        │   │
│  │    ✗ group_id nicht entschieden? → BLOCK                             │   │
│  │    ⚠ Technisches Learning ohne Version? → WARNUNG                    │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─ WebSearch / WebFetch ───────────────────────────────────────────────┐   │
│  │  graphiti-first-guard.py → Graphiti ERST durchsucht? Nein → BLOCK    │   │
│  │  firecrawl-guard.py      → Firecrawl ERST versucht? Nein → BLOCK     │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─ firecrawl__search ──────────────────────────────────────────────────┐   │
│  │  firecrawl-guard.py → Graphiti ERST durchsucht? Nein → BLOCK         │   │
│  │                     → Library-Docs? Context7 ERST → BLOCK            │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─ context7__* ────────────────────────────────────────────────────────┐   │
│  │  context7-guard.py → Graphiti ERST durchsucht? Nein → BLOCK          │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─ playwright__* (mit headless:false) ─────────────────────────────────┐   │
│  │  playwright-guard.py → User hat headless:false bestätigt? Nein→BLOCK │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─ Bash (npx playwright/puppeteer/cypress) ────────────────────────────┐   │
│  │  playwright-guard.py   → CLI Browser-Tools → BLOCK (nutze MCP)       │   │
│  │  agent-browser-guard.py → CLI Browser-Tools → BLOCK (nutze MCP)      │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─ Bash (git commit) ──────────────────────────────────────────────────┐   │
│  │  git-workflow-guard.py → Conventional Commits Format? Nein → BLOCK   │   │
│  │                        → Push zu main/develop? → BLOCK (confirm)     │   │
│  │                        → Force push? → BLOCK (confirm)               │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
                              [ TOOL EXECUTION ]
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            POST TOOL USE                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─ Bash / MCP Tools (bei Fehler) ──────────────────────────────────────┐   │
│  │  graphiti-retry-guard.py → 3-Strikes Regel:                          │   │
│  │    1. Fehler → erlaubt                                               │   │
│  │    2. Fehler → erlaubt                                               │   │
│  │    3. Fehler → BLOCK: "Erst Graphiti nach Learnings durchsuchen!"    │   │
│  │    Nach Graphiti-Suche → Retry erlaubt                               │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Services

### Graphiti (Memory)

| Service | Hooks | Beschreibung |
|---------|-------|--------------|
| `graphiti` | 6 Hooks | **Langzeit-Gedächtnis mit Knowledge Graph.** Speichert Wissen persistent über Sessions hinweg. Erzwingt Quellenangaben, blockiert Credentials, validiert Zitate. |

**Hooks:**
- `graphiti-context-loader.py` - Lädt Kontext bei Session-Start
- `session-reminder.py` - Zeigt Projekt + group_id
- `graphiti-knowledge-reminder.py` - Erinnert an Graphiti-Suche
- `graphiti-guard.py` - Validiert add_memory Aufrufe
- `graphiti-first-guard.py` - Erzwingt Graphiti-Suche vor Web-Recherche
- `graphiti-retry-guard.py` - 3-Strikes bei Fehlern

### General Rules (keine Hooks)

| Service | Beschreibung |
|---------|--------------|
| `stanflux` | **Verhaltensregeln für Claude.** Definiert wie Claude recherchiert, validiert, mit Fehlern umgeht, und Entscheidungen trifft. Kernregeln für professionelles Arbeiten. |
| `pith` | **Kompaktes Notationsformat.** Referenz für die PITH-Syntax die in Rules verwendet wird. Symbole: `→` then, `\|` or, `!` wichtig, `!!` kritisch. |
| `1password` | **SSH-Keys & Secrets via 1Password.** Anleitung zur Nutzung des 1Password SSH Agents. Keine manuellen Keys in ~/.ssh/. |

### Git Workflow (wähle einen)

| Service | Hook | Beschreibung |
|---------|------|--------------|
| `git-workflow-github-flow` | git-workflow-guard.py | **main + feature branches.** Einfachster Workflow. Feature-Branch → PR → Merge. Empfohlen für die meisten Projekte. |
| `git-workflow-trunk-based` | git-workflow-guard.py | **Trunk-based Development.** Sehr kurze Branches, Feature Flags. Für große Teams mit Continuous Deployment. |
| `git-workflow-git-flow` | git-workflow-guard.py | **Vollständiger Git Flow.** main + develop + feature + release + hotfix. Für scheduled Releases. |

**Hook erzwingt:**
- Conventional Commits Format (`feat:`, `fix:`, `docs:`, etc.)
- Kein direkter Push zu main/develop (ohne Bestätigung)
- Kein Force Push (ohne Bestätigung)

### Browser Automation (wähle einen)

| Service | Hook | Beschreibung |
|---------|------|--------------|
| `agent-browser` | agent-browser-guard.py | **CLI-basierte Browser-Automation.** Nutzt vercel-labs/agent-browser. Blockiert Playwright/Puppeteer CLI. Empfohlen. |
| `playwright` | playwright-guard.py | **MCP Server Browser-Automation.** Erzwingt headless:true als Default. Blockiert Browser CLI-Tools. |

### MCP Server Rules

| Service | Hook | Beschreibung |
|---------|------|--------------|
| `firecrawl` | firecrawl-guard.py | **Web-Suche & Scraping.** Erzwingt Firecrawl VOR WebSearch/WebFetch. Spart API-Credits. Empfiehlt Context7 für Library-Docs. |
| `context7` | context7-guard.py | **Library/Framework Dokumentation.** 61.000+ Libraries indexiert. Erzwingt Graphiti-Suche zuerst. |
| `github` | - | **GitHub API Referenz.** Issues, PRs, Repos. Keine Guards, nur Dokumentation. |
| `bible` | - | **Bibelverse via BibleGateway.** 13 Übersetzungen. Keine Guards. |
| `businessmap` | - | **Portfolio & Strategy Platform.** Keine Guards. |
| `macos-automator` | - | **macOS Shortcuts & Automation.** Keine Guards. |
| `morgen` | - | **Kalender & Scheduling.** Keine Guards. |
| `unifi` | - | **UniFi Network Management.** Keine Guards. |
| `vscode` | - | **VS Code Integration.** Keine Guards. |
| `whoop` | - | **Fitness & Recovery Tracking.** Keine Guards. |
| `xert` | - | **Cycling Training Analytics.** Keine Guards. |

## group_id Logik

Die `group_id` bestimmt, wo Wissen in Graphiti gespeichert wird:

| Priorität | Quelle | Ergebnis |
|-----------|--------|----------|
| 1 | `.graphiti-group` Datei im Projekt | Wert wie angegeben |
| 2 | `CLAUDE.md` mit `graphiti_group_id: X` | Wert wie angegeben |
| 3 | GitHub Remote | `Owner-Repo` (z.B. `Milofax-taming-stan`) |
| 4 | Git Repo + `~/.graphiti-owner` | `Owner-projektname` |
| 5 | Git Repo ohne Owner | `project-name` + ⚠️ Warnung |
| 6 | Kein Git Repo | `main` |

**Wichtig:** Der Owner-Präfix ist erforderlich um Namenskonflikte zu vermeiden!

```bash
# Default Owner konfigurieren (einmalig)
echo "DeinGitHubUsername" > ~/.graphiti-owner
```

## Installation

### Global (HOME)
```bash
cd ~
npx taming-stan install
```
Hooks gelten für alle Projekte. Rules werden global installiert.

### Projekt-spezifisch
```bash
cd /your/project
npx taming-stan install
```
Wenn HOME bereits Hooks hat, werden nur Rules lokal installiert (Hooks werden vererbt).

## Commands

```bash
npx taming-stan install                     # Interaktive Auswahl
npx taming-stan install --all               # Alle Services
npx taming-stan install <service,...>       # Bestimmte Services
npx taming-stan uninstall                   # Alles entfernen
npx taming-stan status                      # Status anzeigen
```

## Core Hooks (immer installiert)

Diese Hooks werden automatisch installiert wenn ANY Service mit Hooks gewählt wird:

| Hook | Event | Beschreibung |
|------|-------|--------------|
| `reset-session-flags.py` | SessionStart | Setzt Session-Flags zurück bei neuer Session |
| `file-context-tracker.py` | PreToolUse | Trackt Dateizugriffe für besseren Kontext |

## Development

### Tests
```bash
# Alle Tests
cd taming-stan && python3 -m venv .venv && source .venv/bin/activate
pip install pytest && pytest tests/ -v

# Einzelne Test-Datei
pytest tests/test_graphiti_guard.py -v
```

### Projekt-Struktur
```
taming-stan/
├── bin/cli.js              # Installer
├── hooks/
│   ├── session-start/      # SessionStart Hooks
│   ├── user-prompt-submit/ # UserPromptSubmit Hooks
│   ├── pre-tool-use/       # PreToolUse Hooks
│   ├── post-tool-use/      # PostToolUse Hooks
│   └── lib/                # Shared Python modules
├── rules/                  # All rules (.md)
│   └── mcp-configurations/ # MCP-specific rules
├── commands/               # Slash commands
├── tests/                  # Python tests
└── test/                   # Bash tests
```

## Migration

Falls du vorher separate Pakete genutzt hast:

```bash
# Alte Pakete deinstallieren
cd ~ && npx graphiti-claude-integration uninstall 2>/dev/null
cd ~ && npx shared-claude-rules uninstall 2>/dev/null

# taming-stan installieren
cd ~ && npx taming-stan install --all
```

## License

MIT
