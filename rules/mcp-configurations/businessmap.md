# BusinessMap MCP Server

> **Stand:** Januar 2026

Vollständige Referenz für den BusinessMap MCP Server - Kanban-Projektmanagement und Workflow-Automatisierung.

## MCP-Funnel Aktivierung

```
discover_tools_by_words("businessmap", enable=true)
```

## Überblick

BusinessMap (früher Kanbanize) ist eine Enterprise Kanban-Plattform für Projektmanagement. Der MCP Server bietet **42 Tools** für vollständige Kontrolle über Workspaces, Boards, Cards, Subtasks, Parent-Child-Beziehungen, Custom Fields und mehr.

## Tool-Kategorien (42 Tools)

### Workspace Management (3 Tools)

| Tool | Beschreibung |
|------|-------------|
| `list_workspaces` | Alle Workspaces auflisten |
| `get_workspace` | Workspace-Details abrufen |
| `create_workspace` | Neuen Workspace erstellen |

### Board Management (8 Tools)

| Tool | Beschreibung |
|------|-------------|
| `list_boards` | Boards in Workspace(s) auflisten |
| `search_board` | Board nach ID oder Name suchen |
| `get_current_board_structure` | Komplette Board-Struktur (Workflows, Columns, Lanes) |
| `create_board` | Neues Board erstellen |
| `get_columns` | Alle Spalten eines Boards |
| `get_lanes` | Alle Swimlanes eines Boards |
| `get_lane` | Details einer Swimlane |
| `create_lane` | Neue Swimlane erstellen |

### Card Management (23 Tools)

#### Basic Card Operations

| Tool | Beschreibung |
|------|-------------|
| `list_cards` | Cards eines Boards mit optionalen Filtern |
| `get_card` | Detaillierte Card-Informationen |
| `get_card_size` | Size/Points einer Card |
| `create_card` | Neue Card erstellen |
| `move_card` | Card in andere Column/Swimlane verschieben |
| `update_card` | Card-Eigenschaften aktualisieren |
| `set_card_size` | Size/Points setzen |

#### Card Comments

| Tool | Beschreibung |
|------|-------------|
| `get_card_comments` | Alle Kommentare einer Card |
| `get_card_comment` | Spezifischen Kommentar abrufen |

#### Card Custom Fields & Types

| Tool | Beschreibung |
|------|-------------|
| `get_card_custom_fields` | Custom Fields einer Card |
| `get_card_types` | Verfügbare Card Types |

#### Card Outcomes & History

| Tool | Beschreibung |
|------|-------------|
| `get_card_outcomes` | Outcomes einer Card |
| `get_card_history` | History eines Outcomes |

#### Card Relationships

| Tool | Beschreibung |
|------|-------------|
| `get_card_linked_cards` | Verlinkte Cards abrufen |

#### Card Subtasks

| Tool | Beschreibung |
|------|-------------|
| `get_card_subtasks` | Alle Subtasks einer Card |
| `get_card_subtask` | Spezifischen Subtask abrufen |
| `create_card_subtask` | Neuen Subtask erstellen |

#### Card Parent-Child Relationships

| Tool | Beschreibung |
|------|-------------|
| `get_card_parents` | Parent-Cards auflisten |
| `get_card_parent` | Prüfen ob Card ein Parent ist |
| `add_card_parent` | Parent-Beziehung erstellen |
| `remove_card_parent` | Parent-Beziehung entfernen |
| `get_card_parent_graph` | Parent-Graph (inkl. deren Parents) |
| `get_card_children` | Child-Cards auflisten |

### Custom Field Management (1 Tool)

| Tool | Beschreibung |
|------|-------------|
| `get_custom_field` | Custom Field Details abrufen |

### Workflow & Cycle Time Analysis (2 Tools)

| Tool | Beschreibung |
|------|-------------|
| `get_workflow_cycle_time_columns` | Cycle Time Columns eines Workflows |
| `get_workflow_effective_cycle_time_columns` | Effektive Cycle Time Columns |

### User Management (3 Tools)

| Tool | Beschreibung |
|------|-------------|
| `list_users` | Alle Benutzer auflisten |
| `get_user` | Benutzer-Details |
| `get_current_user` | Aktuell eingeloggten User |

### System (2 Tools)

| Tool | Beschreibung |
|------|-------------|
| `health_check` | API-Verbindung prüfen |
| `get_api_info` | API-Informationen |

## Kernkonzepte

### Board-Struktur

```
Workspace
└── Board
    ├── Workflow
    │   ├── Columns (Spalten)
    │   │   ├── Backlog
    │   │   ├── In Progress
    │   │   └── Done
    │   └── Lanes (Swimlanes)
    │       ├── High Priority
    │       ├── Normal
    │       └── Low Priority
    └── Cards
        ├── Subtasks
        ├── Parent-Child Links
        └── Custom Fields
```

### Card Lifecycle

```
Backlog → Requested → In Progress → Review → Done
   ↓          ↓           ↓          ↓       ↓
 Blocked   Blocked    Blocked    Blocked  Archived
```

### Parent-Child Hierarchie

BusinessMap unterstützt verschachtelte Karten:
- **Initiatives** → **Epics** → **Stories** → **Tasks**
- `get_card_parent_graph` zeigt die komplette Hierarchie
- `get_card_children` zeigt alle Unter-Karten

## Beispiel-Workflows

### Board-Übersicht abrufen

```
1. list_workspaces
   → Alle Workspaces mit IDs

2. list_boards (workspace_id)
   → Boards im Workspace

3. get_current_board_structure (board_id)
   → Vollständige Struktur mit Columns/Lanes
```

### Neue Card erstellen

```
1. get_current_board_structure (board_id)
   → Column-IDs und Lane-IDs abrufen

2. get_card_types
   → Verfügbare Card Types

3. create_card
   - board_id: 123
   - column_id: 456
   - lane_id: 789
   - title: "Neue Feature-Anforderung"
   - description: "Details..."
   - type_id: 1
   - assignee_ids: [10, 11]
```

### Card durch Workflow bewegen

```
1. list_cards (board_id, filters)
   → Card-ID finden

2. get_current_board_structure (board_id)
   → Ziel-Column-ID finden

3. move_card
   - card_id: 1234
   - column_id: 567 (z.B. "In Progress")
   - lane_id: 890 (optional)
```

### Subtasks verwalten

```
1. get_card_subtasks (card_id)
   → Bestehende Subtasks

2. create_card_subtask
   - card_id: 1234
   - description: "Subtask erledigen"
   - assignee_id: 10

3. update_card (subtask als erledigt markieren)
```

### Sprint/Release planen

```
1. list_cards mit Filter
   - board_id
   - lane_id (z.B. "Backlog" Lane)
   - custom_fields: {"sprint": "Sprint 5"}

2. Für jede Card:
   move_card → In Sprint-Lane verschieben

3. get_card_size für Story Points Summe
```

### Cycle Time Analyse

```
1. get_workflow_cycle_time_columns (workflow_id)
   → Columns die für Cycle Time zählen

2. get_workflow_effective_cycle_time_columns
   → Tatsächlich aktive Columns

3. list_cards mit done_from/done_to Filter
   → Abgeschlossene Cards für Analyse
```

### Parent-Child Struktur aufbauen

```
1. create_card (Epic)
   → epic_id zurück

2. create_card (Story 1)
3. create_card (Story 2)

4. add_card_parent
   - card_id: story1_id
   - parent_card_id: epic_id

5. add_card_parent
   - card_id: story2_id
   - parent_card_id: epic_id

6. get_card_children (epic_id)
   → Zeigt beide Stories
```

## Environment-Variablen

| Variable | Beschreibung | Erforderlich |
|----------|-------------|--------------|
| `BUSINESSMAP_API_TOKEN` | API Token | Ja |
| `BUSINESSMAP_API_URL` | API URL (z.B. `https://account.businessmap.io/api/v2`) | Ja |
| `BUSINESSMAP_READ_ONLY_MODE` | `true` für nur Lesen | Nein (default: false) |
| `BUSINESSMAP_DEFAULT_WORKSPACE_ID` | Standard Workspace | Nein |
| `LOG_LEVEL` | 0=DEBUG, 1=INFO, 2=WARN, 3=ERROR | Nein (default: 1) |

## Read-Only Modus

Für sichere Exploration ohne Änderungen:
```json
{
  "BUSINESSMAP_READ_ONLY_MODE": "true"
}
```

In diesem Modus sind alle schreibenden Operationen deaktiviert:
- `create_*` - Blockiert
- `update_*` - Blockiert
- `move_card` - Blockiert
- Lese-Operationen - Erlaubt

## Card Filter-Optionen

Bei `list_cards` verfügbare Filter:

| Filter | Beschreibung |
|--------|-------------|
| `card_ids` | Spezifische Card-IDs |
| `column_id` | Cards in bestimmter Column |
| `lane_id` | Cards in bestimmter Lane |
| `type_id` | Nach Card Type filtern |
| `assignee_ids` | Nach Assignees filtern |
| `owner_ids` | Nach Ownern filtern |
| `created_from/to` | Erstelldatum-Range |
| `done_from/to` | Abschlussdatum-Range |
| `custom_fields` | Nach Custom Field Werten |
| `is_blocked` | Nur blockierte Cards |
| `tags` | Nach Tags filtern |

## Custom Fields

BusinessMap unterstützt verschiedene Custom Field Typen:
- Text
- Number
- Date
- Dropdown (Single/Multi-Select)
- User Picker
- Card Picker

```
1. get_card_custom_fields (card_id)
   → Alle Custom Fields mit Werten

2. update_card
   - card_id
   - custom_fields: {"field_123": "neuer Wert"}
```

## Tipps für optimale Nutzung

1. **Board-Struktur cachen** - `get_current_board_structure` einmal abrufen
2. **IDs merken** - Workspace/Board/Column IDs wiederverwenden
3. **Batch-Abfragen** - `list_cards` mit Filtern statt einzelner `get_card`
4. **Read-Only für Analyse** - Sicherheit bei reinen Reports
5. **Parent-Graph nutzen** - Hierarchie-Überblick mit einem Call

## Häufige Fehler

| Fehler | Ursache | Lösung |
|--------|---------|--------|
| 401 Unauthorized | Token ungültig | Token prüfen/erneuern |
| 404 Not Found | Falsche ID | IDs via list_* verifizieren |
| 403 Forbidden | Keine Berechtigung | Admin-Rechte für Workspace |
| Read-only mode | Schreiboperation blockiert | READ_ONLY_MODE=false setzen |

## Integration mit anderen Tools

### Mit Morgen (Kalender)

```
1. BusinessMap: list_cards (Deadlines abrufen)
2. Morgen: create_event (Deadline als Termin)
```

### Mit GitHub

```
1. GitHub: get_issue (Bug-Report)
2. BusinessMap: create_card (Card aus Issue)
3. BusinessMap: update_card (GitHub-Link hinzufügen)
```

## Referenzen

- [BusinessMap MCP GitHub](https://github.com/edicarloslds/businessmap-mcp)
- [BusinessMap API Dokumentation](https://businessmap.io/api)
- [Interactive API Docs](https://demo.kanbanize.com/openapi#/)
- [BusinessMap Help Center](https://businessmap.io/help)
