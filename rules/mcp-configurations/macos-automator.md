# macOS Automator MCP Server

> **Stand:** Januar 2026

Vollständige Referenz für den macOS Automator MCP Server - AppleScript und JXA Automatisierung.

## MCP-Funnel Aktivierung

```
discover_tools_by_words("macos automator", enable=true)
```

## Überblick

Der macOS Automator MCP Server ermöglicht die Ausführung von AppleScript und JXA (JavaScript for Automation) direkt aus dem LLM-Kontext. Er enthält über 200 vorgefertigte Automations-Rezepte und ermöglicht vollständige Kontrolle über macOS-Anwendungen.

## Verfügbare Tools

| Tool | Beschreibung |
|------|-------------|
| `macos-automator__execute_script` | AppleScript oder JXA ausführen |
| `macos-automator__get_scripting_tips` | Vorgefertigte Scripts aus Knowledge Base abrufen |

## Tool-Details

### execute_script

Führt AppleScript oder JXA aus.

**Script-Quellen (mutually exclusive):**
- `script_content` - Inline Script-Code
- `script_path` - Absoluter Pfad zu Script-Datei
- `kb_script_id` - ID eines vorgefertigten Scripts

```json
{
  "script_content": "tell application \"Finder\" to get name of desktop",
  "language": "applescript",
  "timeout_seconds": 30
}
```

**Mit Knowledge Base Script:**
```json
{
  "kb_script_id": "safari_get_front_tab_url"
}
```

**Mit Input-Daten:**
```json
{
  "kb_script_id": "finder_create_folder_at_path",
  "input_data": {
    "folder_name": "Neuer Ordner",
    "parent_path": "~/Desktop"
  }
}
```

### get_scripting_tips

Durchsucht die Knowledge Base mit 200+ vorgefertigten Scripts.

```json
{
  "list_categories": true
}
```

```json
{
  "category": "safari",
  "search_term": "url",
  "limit": 10
}
```

**Kategorien:**
- `finder` - Datei-Operationen
- `safari` / `chrome` - Browser-Kontrolle
- `mail` - E-Mail Automatisierung
- `calendar` - Kalender-Operationen
- `terminal` - Terminal-Befehle
- `system` - System-Einstellungen
- `music` - Musik-App Steuerung
- Und viele mehr...

## AppleScript Grundlagen

### Tell Blocks

```applescript
tell application "Finder"
    get name of every file of desktop
end tell
```

### Variablen und Listen

```applescript
set myList to {"a", "b", "c"}
set firstItem to item 1 of myList
```

### Dialoge

```applescript
display dialog "Hello!" buttons {"OK"} default button "OK"
display notification "Task complete" with title "Automation"
```

## JXA (JavaScript for Automation)

```javascript
const finder = Application('Finder');
const desktop = finder.desktop;
desktop.files().map(f => f.name());
```

## Beispiel-Workflows

### Browser-Automation

```
1. get_scripting_tips (category: "safari")
   → Verfügbare Safari-Scripts

2. execute_script
   - kb_script_id: "safari_get_front_tab_url"
   → Aktuelle URL

3. execute_script
   - kb_script_id: "safari_open_url"
   - input_data: {"url": "https://example.com"}
```

### Datei-Management

```
execute_script
- script_content: |
    tell application "Finder"
        make new folder at desktop with properties {name:"Backup"}
        move (every file of desktop whose name extension is "pdf") to folder "Backup" of desktop
    end tell
```

### System-Einstellungen

```
// Dark Mode umschalten
execute_script
- kb_script_id: "systemsettings_toggle_dark_mode_ui"

// Volume setzen
execute_script
- script_content: "set volume output volume 50"
```

### Terminal-Befehle

```
execute_script
- kb_script_id: "terminal_app_run_command_new_tab"
- input_data: {"command": "npm run build"}
```

### Clipboard-Operationen

```
// Clipboard lesen
execute_script
- script_content: "the clipboard"

// Clipboard setzen
execute_script
- script_content: "set the clipboard to \"Copied text\""
```

### E-Mail senden

```
execute_script
- script_content: |
    tell application "Mail"
        set newMessage to make new outgoing message with properties {
            subject:"Test",
            content:"Hello from automation"
        }
        tell newMessage
            make new to recipient with properties {address:"test@example.com"}
        end tell
        send newMessage
    end tell
```

## Permissions

**Erforderlich:**
1. **Automation Permission**
   - System Settings > Privacy & Security > Automation
   - Terminal/App muss Zugriff auf Ziel-Apps haben

2. **Accessibility Permission**
   - System Settings > Privacy & Security > Accessibility
   - Für UI-Scripting via System Events

## Tipps für optimale Nutzung

1. **Knowledge Base nutzen** - Vorgefertigte Scripts sind getestet
2. **get_scripting_tips zuerst** - Verfügbare Scripts entdecken
3. **input_data für Parameter** - Sauberer als String-Manipulation
4. **timeout_seconds anpassen** - Für langsame Apps erhöhen
5. **System Events für UI** - Wenn kein nativer AppleScript-Support

## Häufige Scripts aus Knowledge Base

| Script ID | Funktion |
|-----------|----------|
| `safari_get_front_tab_url` | Aktuelle Safari-URL |
| `safari_get_all_tabs_urls` | Alle offenen Tabs |
| `finder_create_new_folder_desktop` | Ordner auf Desktop |
| `systemsettings_toggle_dark_mode_ui` | Dark Mode umschalten |
| `music_playback_controls` | Musik Play/Pause/Next |
| `terminal_app_run_command_new_tab` | Terminal-Befehl |

## Häufige Fehler

| Fehler | Ursache | Lösung |
|--------|---------|--------|
| Not authorized | Fehlende Permission | System Settings > Privacy |
| Application not found | App-Name falsch | Exakten App-Namen verwenden |
| Syntax error | AppleScript-Fehler | Script in Script Editor testen |
| Timeout | Script zu langsam | timeout_seconds erhöhen |

## Referenzen

- [macOS Automator MCP](https://github.com/steipete/macos-automator-mcp)
- [AppleScript Guide](https://developer.apple.com/library/archive/documentation/AppleScript/Conceptual/AppleScriptLangGuide/)
- [JXA Cookbook](https://github.com/JXA-Cookbook/JXA-Cookbook)
- [Accessibility Programming Guide](https://developer.apple.com/library/archive/documentation/Accessibility/Conceptual/AccessibilityMacOSX/)
