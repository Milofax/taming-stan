# VS Code MCP Server

> **Stand:** Januar 2026

Vollständige Referenz für den VS Code MCP Server - IDE-Integration und Editor-Automatisierung.

## MCP-Funnel Aktivierung

```
discover_tools_by_words("vscode", enable=true)
```

**Hinweis:** VS Code muss laufen und der MCP Server aktiv sein, damit die Tools verfügbar sind.

## Überblick

Der VS Code MCP Server ermöglicht die Fernsteuerung von Visual Studio Code. Er verbindet sich über einen lokalen HTTP-Endpoint mit der laufenden VS Code Instanz und ermöglicht Editor-Operationen wie Datei-Navigation, Code-Editing und Terminal-Befehle.

## Voraussetzungen

- **VS Code 1.99+** mit nativer MCP-Unterstützung (seit Juli 2025 GA)
- MCP Server konfiguriert in `.vscode/mcp.json` oder User Settings
- GitHub Copilot Extension für Agent Mode

## Verfügbare Tools

| Tool | Beschreibung |
|------|-------------|
| `vscode__open_file` | Datei im Editor öffnen |
| `vscode__get_active_editor` | Aktiven Editor/Datei abrufen |
| `vscode__get_selection` | Aktuelle Textauswahl abrufen |
| `vscode__replace_selection` | Auswahl ersetzen |
| `vscode__insert_text` | Text an Position einfügen |
| `vscode__run_command` | VS Code Command ausführen |
| `vscode__get_diagnostics` | Fehler/Warnungen abrufen |
| `vscode__run_terminal_command` | Terminal-Befehl ausführen |
| `vscode__get_workspace_folders` | Workspace-Ordner auflisten |
| `vscode__search_files` | Dateien im Workspace suchen |

## Kernkonzepte

### Editor State

VS Code hat mehrere Zustände die relevant sind:
- **Active Editor** - Aktuell fokussierter Tab
- **Selection** - Markierter Text
- **Cursor Position** - Zeile/Spalte des Cursors
- **Visible Range** - Sichtbarer Bereich

### Commands

VS Code hat hunderte eingebaute Commands:
- `workbench.action.files.save` - Datei speichern
- `editor.action.formatDocument` - Dokument formatieren
- `workbench.action.terminal.new` - Neues Terminal
- `workbench.action.quickOpen` - Quick Open (Ctrl+P)

## Workflow-Beispiele

### Datei öffnen und editieren

```
1. vscode__open_file
   - path: "/project/src/app.ts"

2. vscode__get_active_editor
   → Bestätigt dass Datei geöffnet

3. vscode__insert_text
   - text: "// New code here"
   - position: {line: 10, column: 0}
```

### Fehler beheben

```
1. vscode__get_diagnostics
   - uri: "file:///project/src/app.ts"
   → Liste von Fehlern mit Zeile/Spalte

2. vscode__open_file (path zum fehlerhaften File)

3. vscode__replace_selection
   - Korrigierten Code einfügen
```

### Code formatieren und speichern

```
1. vscode__run_command
   - command: "editor.action.formatDocument"

2. vscode__run_command
   - command: "workbench.action.files.save"
```

### Terminal-Befehle ausführen

```
1. vscode__run_terminal_command
   - command: "npm run build"

2. vscode__run_terminal_command
   - command: "npm test"
```

### Dateien im Projekt finden

```
1. vscode__search_files
   - pattern: "**/*.test.ts"
   → Liste aller Test-Dateien

2. vscode__open_file (erste gefundene Test-Datei)
```

## Nützliche VS Code Commands

### Navigation

| Command | Beschreibung |
|---------|-------------|
| `workbench.action.quickOpen` | Quick Open (Ctrl+P) |
| `workbench.action.gotoLine` | Zu Zeile springen |
| `workbench.action.gotoSymbol` | Zu Symbol springen |
| `editor.action.revealDefinition` | Zur Definition |

### Editing

| Command | Beschreibung |
|---------|-------------|
| `editor.action.formatDocument` | Formatieren |
| `editor.action.commentLine` | Zeile kommentieren |
| `editor.action.addSelectionToNextFindMatch` | Multi-Cursor |
| `editor.action.rename` | Symbol umbenennen |

### Workspace

| Command | Beschreibung |
|---------|-------------|
| `workbench.action.files.save` | Speichern |
| `workbench.action.files.saveAll` | Alle speichern |
| `workbench.action.closeActiveEditor` | Tab schließen |
| `workbench.action.reloadWindow` | Window neu laden |

### Terminal

| Command | Beschreibung |
|---------|-------------|
| `workbench.action.terminal.new` | Neues Terminal |
| `workbench.action.terminal.focus` | Terminal fokussieren |
| `workbench.action.terminal.clear` | Terminal leeren |

## Diagnostics (Fehler/Warnungen)

```json
{
  "uri": "file:///project/src/app.ts",
  "diagnostics": [
    {
      "severity": 1,
      "message": "Property 'x' does not exist on type 'Y'",
      "range": {
        "start": {"line": 10, "character": 5},
        "end": {"line": 10, "character": 10}
      },
      "source": "typescript"
    }
  ]
}
```

**Severity Levels:**
- 1 = Error
- 2 = Warning
- 3 = Information
- 4 = Hint

## Tipps für optimale Nutzung

1. **Editor-State prüfen** - Vor Edits `get_active_editor` aufrufen
2. **Diagnostics nutzen** - Fehler systematisch beheben
3. **Commands kombinieren** - Format + Save als Workflow
4. **Terminal für Builds** - Tests/Builds über Terminal ausführen
5. **Workspace-aware** - Pfade relativ zum Workspace nutzen

## Einschränkungen

- VS Code muss geöffnet sein
- Extension muss aktiv sein
- Nur lokale Instanz (kein Remote VS Code)
- Einige Commands erfordern User-Bestätigung

## Häufige Fehler

| Fehler | Ursache | Lösung |
|--------|---------|--------|
| Connection refused | VS Code nicht gestartet | VS Code öffnen |
| File not found | Falscher Pfad | Absoluten Pfad verwenden |
| Command not found | Falscher Command-Name | Command-ID prüfen |
| No active editor | Kein Tab offen | Erst Datei öffnen |

## Referenzen

- [VS Code MCP Developer Guide](https://code.visualstudio.com/api/extension-guides/ai/mcp)
- [MCP Server Configuration](https://code.visualstudio.com/docs/copilot/customization/mcp-servers)
- [Built-in Commands](https://code.visualstudio.com/api/references/commands)
- [Model Context Protocol](https://modelcontextprotocol.io/)
