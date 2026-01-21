# taming-stan

All-in-one Claude Code Enhancement: Graphiti Memory, Intelligent Guards, und STAN.FLUX Rules.

## Features

- **Graphiti Integration** - Langzeit-Gedächtnis mit Knowledge Graph
- **Smart Guards** - Pre/Post Tool-Use Guards für Qualitätssicherung
- **STAN.FLUX Rules** - Strukturierte Verhaltensregeln
- **Unified Installer** - Ein Befehl für alles

## Quick Start

```bash
npx taming-stan install              # Interaktiv
npx taming-stan install --all        # Alle Services
npx taming-stan install graphiti stanflux git-workflow-github-flow
```

---

## Hook Workflow

Kompletter Ablauf bei jedem Claude Code Aufruf (wenn alle Services installiert):

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                SESSION START                                     │
│                          (einmalig bei Session-Beginn)                           │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   reset-session-flags.py ──────► Setzt alle Session-Flags zurück                │
│            │                     (graphiti_searched, memory_saved, etc.)         │
│            ▼                                                                     │
│   graphiti-context-loader.py ──► Prüft Graphiti-Verfügbarkeit                   │
│                                  Setzt group_id aus Projekt-Kontext              │
│                                  Output: "Graphiti verfügbar (group_id: X)"      │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              USER PROMPT SUBMIT                                  │
│                           (bei JEDER User-Nachricht)                             │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   session-reminder.py ─────────► "📁 Projekt: X"                                │
│            │                     "   group_id: Owner-projekt"                    │
│            ▼                                                                     │
│   graphiti-knowledge-reminder.py► "💡 search_nodes(group_ids=[...])"            │
│                                   Erinnert: Erst Wissen prüfen!                  │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                PRE TOOL USE                                      │
│                          (VOR jeder Tool-Ausführung)                             │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   ┌── Read/Edit/Write/Glob/Grep ───────────────────────────────────────────┐    │
│   │   file-context-tracker.py ──► Trackt Dateizugriffe für Kontext         │    │
│   └────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│   ┌── graphiti__add_memory ────────────────────────────────────────────────┐    │
│   │   graphiti-guard.py ────────► ✗ Quelle fehlt? → BLOCK                  │    │
│   │                               ✗ Credentials? → BLOCK (3-Strikes)       │    │
│   │                               ✗ group_id unklar? → BLOCK               │    │
│   │                               ⚠ Tech ohne Version? → WARNUNG           │    │
│   └────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│   ┌── WebSearch / WebFetch ────────────────────────────────────────────────┐    │
│   │   graphiti-first-guard.py ──► Graphiti durchsucht? Nein → BLOCK        │    │
│   │   firecrawl-guard.py ───────► Firecrawl versucht? Nein → BLOCK         │    │
│   └────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│   ┌── firecrawl__* ────────────────────────────────────────────────────────┐    │
│   │   firecrawl-guard.py ───────► Library-Docs? → Context7 erst!           │    │
│   └────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│   ┌── context7__* ─────────────────────────────────────────────────────────┐    │
│   │   context7-guard.py ────────► Graphiti durchsucht? Nein → BLOCK        │    │
│   └────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│   ┌── Bash (git commit) ───────────────────────────────────────────────────┐    │
│   │   git-workflow-guard.py ────► Conventional Commits? Nein → BLOCK       │    │
│   │                               Push zu main? → Bestätigung              │    │
│   │                               Force push? → Bestätigung                │    │
│   └────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│   ┌── Bash (npx playwright/puppeteer) ─────────────────────────────────────┐    │
│   │   agent-browser-guard.py ───► CLI Browser-Tools → BLOCK (nutze MCP)    │    │
│   │   playwright-guard.py ──────► CLI Browser-Tools → BLOCK (nutze MCP)    │    │
│   └────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
                               [ TOOL EXECUTION ]
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                               POST TOOL USE                                      │
│                          (NACH jeder Tool-Ausführung)                            │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   ┌── Bash / MCP Tools (bei Fehler) ───────────────────────────────────────┐    │
│   │   graphiti-retry-guard.py ──► 1. Fehler → OK                           │    │
│   │                               2. Fehler → OK                           │    │
│   │                               3. Fehler → BLOCK                        │    │
│   │                               "Erst Graphiti nach Learnings suchen!"   │    │
│   └────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Services

### Graphiti

**Langzeit-Gedächtnis mit Knowledge Graph** - Speichert Wissen persistent über Sessions hinweg.

| Komponente | Datei | Event |
|------------|-------|-------|
| Hook | `graphiti-context-loader.py` | SessionStart |
| Hook | `session-reminder.py` | UserPromptSubmit |
| Hook | `graphiti-knowledge-reminder.py` | UserPromptSubmit |
| Hook | `graphiti-guard.py` | PreToolUse |
| Hook | `graphiti-first-guard.py` | PreToolUse |
| Hook | `graphiti-retry-guard.py` | PostToolUse |
| Rule | `graphiti.md` | - |

**Highlights:**
- Erzwingt Quellenangaben bei `add_memory`
- Blockiert Credentials (Passwörter, API-Keys, Tokens)
- Validiert group_id vor dem Speichern
- Warnt bei technischem Wissen ohne Versionsangabe
- 3-Strikes Regel: Nach 3 Fehlern erst Graphiti durchsuchen

**Nutzen:** Wissen überlebt Sessions. Keine doppelte Recherche. Learnings gehen nicht verloren.

---

### STAN.FLUX

**Verhaltensregeln für Claude** - Definiert wie Claude arbeitet, recherchiert und Entscheidungen trifft.

| Komponente | Datei |
|------------|-------|
| Rule | `stanflux.md` |

**Highlights:**
- **Wissen erst:** Recherchieren vor Raten
- **Kein Druck:** "schnell" ist Warnsignal, nicht Auftrag
- **Bei Fehler:** Transparenz → Stufen → Handeln
- **3-Strikes:** Nach 3 gleichen Fehlern → Perspektivwechsel
- **Irreversibel:** Push, Delete, Drop → immer fragen
- **Empathie:** User frustriert? Erst anerkennen, dann weiter

**Nutzen:** Konsistentes, professionelles Verhalten. Weniger Fehler durch Eile.

---

### Git Workflow (wähle einen)

**Erzwingt Conventional Commits und Branch-Schutz.**

#### git-workflow-github-flow (empfohlen)

| Komponente | Datei | Event |
|------------|-------|-------|
| Hook | `git-workflow-guard.py` | PreToolUse (Bash) |
| Rule | `git-workflow-github-flow.md` | - |

**Strategie:** `main` + Feature-Branches → PR → Merge

#### git-workflow-trunk-based

| Komponente | Datei | Event |
|------------|-------|-------|
| Hook | `git-workflow-guard.py` | PreToolUse (Bash) |
| Rule | `git-workflow-trunk-based.md` | - |

**Strategie:** Sehr kurze Branches, Feature Flags, Continuous Deployment

#### git-workflow-git-flow

| Komponente | Datei | Event |
|------------|-------|-------|
| Hook | `git-workflow-guard.py` | PreToolUse (Bash) |
| Rule | `git-workflow-git-flow.md` | - |

**Strategie:** main + develop + feature + release + hotfix

**Hook erzwingt:**
- `feat:`, `fix:`, `docs:`, `refactor:`, etc. Format
- Kein direkter Push zu main/develop ohne Bestätigung
- Kein Force Push ohne Bestätigung

**Nutzen:** Saubere Git-History. Automatische Changelog-Generierung möglich.

---

### Firecrawl

**Web-Suche und Scraping** - Ersetzt WebSearch/WebFetch mit besserer Kontrolle.

| Komponente | Datei | Event |
|------------|-------|-------|
| Hook | `firecrawl-guard.py` | PreToolUse |
| Rule | `firecrawl.md` | - |

**Highlights:**
- Blockiert WebSearch/WebFetch → nutze Firecrawl stattdessen
- Empfiehlt Context7 für Library-Dokumentation
- Dokumentiert alle Firecrawl-Tools und Parameter

**Nutzen:** Spart API-Credits ($19/Mo für 3000 Credits). Bessere Kontrolle über Web-Recherche.

---

### Context7

**Library/Framework Dokumentation** - 61.000+ Libraries indexiert.

| Komponente | Datei | Event |
|------------|-------|-------|
| Hook | `context7-guard.py` | PreToolUse |
| Rule | `context7.md` | - |

**Highlights:**
- Erzwingt Graphiti-Suche vor Context7
- Dokumentiert `resolve-library-id` und `query-docs`
- Häufige IDs: `/vercel/next.js`, `/prisma/docs`, etc.

**Nutzen:** Aktuelle Dokumentation direkt aus der Quelle. Kein veraltetes Training-Wissen.

---

### Agent Browser

**CLI-basierte Browser-Automation** - Nutzt vercel-labs/agent-browser.

| Komponente | Datei | Event |
|------------|-------|-------|
| Hook | `agent-browser-guard.py` | PreToolUse (Bash) |
| Rule | `agent-browser.md` | - |

**Highlights:**
- Blockiert `npx playwright`, `npx puppeteer`, `npx cypress`
- Erzwingt Nutzung von agent-browser CLI stattdessen
- Dokumentiert Snapshot-First Workflow mit Refs (@e1, @e2)

**Nutzen:** Deterministische Browser-Automation. Stabilere Selektoren durch Refs.

---

### Playwright

**MCP Server Browser-Automation** - Alternative zu Agent Browser.

| Komponente | Datei | Event |
|------------|-------|-------|
| Hook | `playwright-guard.py` | PreToolUse |
| Rule | `playwright.md` | - |

**Highlights:**
- Blockiert CLI Browser-Tools (nutze MCP stattdessen)
- Erzwingt `headless: true` als Default
- Fragt bei `headless: false` nach Bestätigung

**Nutzen:** Kontrollierte Browser-Automation ohne unerwartete Fenster.

---

### PITH

**Kompaktes Notationsformat** - Referenz für die Syntax in Rules.

| Komponente | Datei |
|------------|-------|
| Rule | `pith.md` |

**Symbole:**
| Symbol | Bedeutung |
|--------|-----------|
| `→` | then/führt zu |
| `\|` | or/oder |
| `!` | wichtig |
| `!!` | kritisch/MUSS |
| `:` | key:value |

**Nutzen:** Kompakte, maschinenlesbare Regeln. Weniger Token-Verbrauch.

---

### 1Password

**SSH-Keys und Secrets Management** - Anleitung für 1Password SSH Agent.

| Komponente | Datei |
|------------|-------|
| Rule | `1password.md` |

**Highlights:**
- SSH-Keys NIEMALS in `~/.ssh/` kopieren
- 1Password SSH Agent liefert Keys automatisch
- `ssh-add -l` zeigt verfügbare Keys

**Nutzen:** Sichere Key-Verwaltung. Keine manuellen Secrets im Dateisystem.

---

### MCP Server Rules (ohne Hooks)

Diese Services haben nur Dokumentation, keine Guards:

| Service | Rule | Beschreibung |
|---------|------|--------------|
| `github` | `github.md` | GitHub API (Issues, PRs, Repos) |
| `bible` | `bible.md` | Bibelverse via BibleGateway (13 Übersetzungen) |
| `businessmap` | `businessmap.md` | Portfolio & Strategy Platform |
| `macos-automator` | `macos-automator.md` | macOS Shortcuts & Automation |
| `morgen` | `morgen.md` | Kalender & Scheduling |
| `unifi` | `unifi.md` | UniFi Network Management |
| `vscode` | `vscode.md` | VS Code Integration |
| `whoop` | `whoop.md` | Fitness & Recovery Tracking |
| `xert` | `xert.md` | Cycling Training Analytics |

---

## group_id Logik

Die `group_id` bestimmt, wo Wissen in Graphiti gespeichert wird:

| Priorität | Quelle | Ergebnis |
|-----------|--------|----------|
| 1 | `.graphiti-group` Datei | Wert wie angegeben |
| 2 | `CLAUDE.md` mit `graphiti_group_id: X` | Wert wie angegeben |
| 3 | GitHub Remote | `Owner-Repo` (z.B. `Milofax-taming-stan`) |
| 4 | Git Repo + `~/.graphiti-owner` | `Owner-projektname` |
| 5 | Git Repo ohne Owner | `project-name` + ⚠️ Warnung |
| 6 | Kein Git Repo | `main` |

```bash
# Default Owner konfigurieren (einmalig)
echo "DeinGitHubUsername" > ~/.graphiti-owner
```

**Wichtig:** Owner-Präfix verhindert Namenskonflikte in Graphiti!

---

## Installation

### Global (HOME)
```bash
cd ~ && npx taming-stan install
```
Hooks gelten für alle Projekte. Rules werden global installiert.

### Projekt-spezifisch
```bash
cd /your/project && npx taming-stan install
```
Wenn HOME bereits Hooks hat, werden nur Rules lokal installiert.

### Commands
```bash
npx taming-stan install                     # Interaktiv
npx taming-stan install --all               # Alle Services
npx taming-stan install <service,...>       # Bestimmte Services
npx taming-stan uninstall                   # Alles entfernen
npx taming-stan status                      # Status anzeigen
```

---

## Core Hooks

Diese Hooks werden automatisch installiert wenn ANY Service mit Hooks gewählt wird:

| Hook | Event | Beschreibung |
|------|-------|--------------|
| `reset-session-flags.py` | SessionStart | Setzt Session-Flags zurück |
| `file-context-tracker.py` | PreToolUse | Trackt Dateizugriffe |

---

## Development

### Hook-Kontrakt

**WICHTIG:** Alle Hooks MÜSSEN immer gültiges JSON ausgeben!

```python
# RICHTIG
def main():
    try:
        hi = json.load(sys.stdin)
    except:
        print(json.dumps({"continue": True}))  # ← Auch bei Fehler!
        return

    if not should_show_message():
        print(json.dumps({"continue": True}))  # ← Auch ohne Message!
        return

    print(json.dumps({"continue": True, "systemMessage": "..."}))

# FALSCH - verursacht Hook Error
def main():
    if not should_show_message():
        return  # ← Kein Output = Hook Error!
```

### Tests
```bash
cd taming-stan && python3 -m venv .venv && source .venv/bin/activate
pip install pytest && pytest tests/ -v
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
├── rules/                  # Alle Rules (.md)
│   └── mcp-configurations/ # MCP-spezifische Rules
├── commands/               # Slash Commands
├── tests/                  # Python Tests
└── test/                   # Bash Tests
```

---

## Migration

Falls du vorher separate Pakete genutzt hast:

```bash
cd ~ && npx graphiti-claude-integration uninstall 2>/dev/null
cd ~ && npx shared-claude-rules uninstall 2>/dev/null
cd ~ && npx taming-stan install --all
```

## License

MIT
