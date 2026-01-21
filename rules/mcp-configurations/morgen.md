# Morgen MCP Server

> **Stand:** Januar 2026

Vollständige Referenz für den Morgen MCP Server - Kalender-Management und Terminplanung.

## MCP-Funnel Aktivierung

```
discover_tools_by_words("morgen", enable=true)
```

## Überblick

Der Morgen MCP Server ermöglicht Zugriff auf die Morgen Kalender API. Morgen ist ein intelligenter Kalender, der mehrere Kalender-Accounts vereint und smarte Scheduling-Features bietet.

## Verfügbare Tools

| Tool | Beschreibung |
|------|-------------|
| `morgen__morgen_list_calendars` | Alle Kalender auflisten |
| `morgen__morgen_update_calendar_metadata` | Kalender-Name/Farbe ändern |
| `morgen__morgen_list_events` | Events mit optionalem Datums-Filter |
| `morgen__morgen_create_event` | Neuen Termin erstellen |
| `morgen__morgen_update_event` | Bestehenden Termin aktualisieren |
| `morgen__morgen_delete_event` | Termin löschen |

## Tool-Details

### list_calendars

Listet alle verbundenen Kalender auf.

```json
{}
```

**Response:**
```json
{
  "success": true,
  "calendars": [
    {
      "id": "cal_123",
      "name": "Work Calendar",
      "color": "#4285F4",
      "accountId": "acc_456"
    }
  ]
}
```

### list_events

Listet Events mit Datums-Filterung.

```json
{
  "account_id": "acc_123",
  "calendar_ids": ["cal_123", "cal_456"],
  "start": "2026-01-15T00:00:00",
  "end": "2026-01-22T23:59:59"
}
```

**Wichtig:**
- `account_id` und `calendar_ids` sind erforderlich
- `calendar_ids` ist ein Array (alle müssen zum selben Account gehören)
- Datetime im Format `YYYY-MM-DDTHH:mm:ss` (LocalDateTime), KEINE Z-Suffix!
- Max. 6 Monate Zeitfenster

### create_event

Erstellt einen neuen Termin.

```json
{
  "account_id": "acc_123",
  "calendar_id": "cal_123",
  "title": "Team Meeting",
  "start": "2026-01-20T10:00:00",
  "duration": "PT1H",
  "time_zone": "Europe/Berlin",
  "description": "Weekly sync",
  "location": "Conference Room A"
}
```

**Parameter:**

| Parameter | Typ | Beschreibung |
|-----------|-----|--------------|
| `account_id` | string | Account-ID (erforderlich) |
| `calendar_id` | string | Kalender-ID (erforderlich) |
| `title` | string | Titel des Events (erforderlich) |
| `start` | string | Start-Zeit (LocalDateTime, erforderlich) |
| `duration` | string | Dauer in ISO 8601 (z.B. "PT1H", "PT30M", erforderlich) |
| `time_zone` | string | IANA Zeitzone z.B. "Europe/Berlin" (optional) |
| `is_all_day` | boolean | Ganztägiges Event (optional) |
| `description` | string | Beschreibung (optional) |
| `location` | string | Ort (optional) |
| `participants` | array | Liste von E-Mail-Adressen (optional) |
| `free_busy_status` | string | "free" oder "busy" (default: "busy") |
| `privacy` | string | "public", "private", "secret" (default: "public") |

### update_event

Aktualisiert einen bestehenden Termin.

```json
{
  "event_id": "evt_789",
  "account_id": "acc_123",
  "calendar_id": "cal_123",
  "title": "Updated Meeting Title",
  "start": "2026-01-20T14:00:00",
  "duration": "PT1H"
}
```

**Wichtig:** Bei Änderung von Zeitangaben (start, duration, time_zone, is_all_day) müssen alle vier Felder angegeben werden.

Für wiederkehrende Events: `series_update_mode` mit "single", "future" oder "all".

### delete_event

Löscht einen Termin.

```json
{
  "event_id": "evt_789",
  "account_id": "acc_123",
  "calendar_id": "cal_123"
}
```

Für wiederkehrende Events: `series_update_mode` mit "single", "future" oder "all".

### update_calendar_metadata

Ändert Anzeigename oder Farbe eines Kalenders in Morgen (ohne den ursprünglichen Kalender-Provider zu ändern).

```json
{
  "calendar_id": "cal_123",
  "account_id": "acc_123",
  "override_name": "Neuer Name",
  "override_color": "#FF5733",
  "busy": true
}
```

| Parameter | Typ | Beschreibung |
|-----------|-----|--------------|
| `calendar_id` | string | Kalender-ID (erforderlich) |
| `account_id` | string | Account-ID (erforderlich) |
| `override_name` | string | Anzeigename in Morgen |
| `override_color` | string | Farbe in Hex-Format |
| `busy` | boolean | Ob Events für Verfügbarkeit zählen |

## Kernkonzepte

### Datetime-Format

Morgen verwendet **LocalDateTime** ohne Timezone-Suffix:
- Richtig: `2026-01-20T10:00:00`
- Falsch: `2026-01-20T10:00:00Z`

Die Timezone wird separat als Parameter übergeben.

### Response-Struktur

**Erfolg:**
```json
{
  "success": true,
  "event": {...}
}
```

**Fehler:**
```json
{
  "error": "Event not found",
  "status_code": 404
}
```

**Validierungsfehler:**
```json
{
  "error": "Invalid datetime format",
  "validation_error": true
}
```

### Event-Struktur

```json
{
  "id": "evt_123",
  "calendarId": "cal_456",
  "title": "Meeting",
  "start": "2026-01-20T10:00:00",
  "end": "2026-01-20T11:00:00",
  "description": "Description text",
  "location": "Office",
  "attendees": [
    {"email": "person@example.com"}
  ],
  "timezone": "Europe/Berlin"
}
```

## Beispiel-Workflows

### Tagesübersicht abrufen

```
1. morgen__morgen_list_calendars
   → Alle Kalender mit IDs und Account-IDs

2. morgen__morgen_list_events
   - account_id: "acc_123"
   - calendar_ids: ["cal_123"]
   - start: "2026-01-20T00:00:00"
   - end: "2026-01-20T23:59:59"
   → Alle Termine des Tages
```

### Meeting planen

```
1. morgen__morgen_list_calendars
   → Arbeitskalender-ID und Account-ID finden

2. morgen__morgen_list_events (für gewünschten Tag)
   → Freie Slots identifizieren

3. morgen__morgen_create_event
   - account_id: "acc_123"
   - calendar_id: "work_cal"
   - title: "1:1 mit Max"
   - start: "2026-01-22T14:00:00"
   - duration: "PT30M"
   - time_zone: "Europe/Berlin"
```

### Termin verschieben

```
1. morgen__morgen_list_events (um Event-ID zu finden)

2. morgen__morgen_update_event
   - event_id: "evt_789"
   - account_id: "acc_123"
   - calendar_id: "cal_123"
   - start: "2026-01-23T10:00:00"
   - duration: "PT1H"
   - time_zone: "Europe/Berlin"
   - is_all_day: false
```

### Wochenplanung

```
morgen__morgen_list_events
- account_id: "acc_123"
- calendar_ids: ["cal_123", "cal_456"]
- start: "2026-01-22T00:00:00"
- end: "2026-01-28T23:59:59"
→ Alle Events der Woche zur Analyse
```

### Termin mit Teilnehmern

```
morgen__morgen_create_event
- account_id: "acc_123"
- calendar_id: "cal_123"
- title: "Team Sync"
- start: "2026-01-25T09:00:00"
- duration: "PT1H"
- time_zone: "Europe/Berlin"
- participants: ["alice@company.com", "bob@company.com"]
- location: "Zoom"
- description: "Weekly team synchronization"
```

## Zeitzonen

Unterstützte Zeitzonen (Beispiele):
- `Europe/Berlin`
- `Europe/London`
- `America/New_York`
- `America/Los_Angeles`
- `Asia/Tokyo`
- `UTC`

**Best Practice:** Immer explizit die Timezone angeben!

## Tipps für optimale Nutzung

1. **Kalender-IDs cachen** - list_calendars einmal aufrufen, IDs merken
2. **Zeitzone immer angeben** - Verhindert Verwirrung bei verschiedenen Calendars
3. **LocalDateTime nutzen** - Kein Z-Suffix, Timezone separat
4. **Datum-Range begrenzen** - Nicht zu viele Events auf einmal laden
5. **Event-ID für Updates** - Immer erst list_events für die ID

## Validierung

Der Server validiert automatisch:
- Datetime-Format (LocalDateTime)
- Timezone-Strings (IANA Format)
- E-Mail-Adressen für Participants
- Farb-Codes (Hex-Format)
- Duration (ISO 8601 Format, z.B. PT1H, PT30M)

## Häufige Fehler

| Fehler | Ursache | Lösung |
|--------|---------|--------|
| Invalid datetime | Falsches Format | LocalDateTime ohne Z verwenden |
| Calendar not found | Falsche ID | list_calendars für aktuelle IDs |
| Event not found | Event gelöscht/ID falsch | list_events zur Verifizierung |
| Validation error | Parameter ungültig | Fehlermeldung prüfen |

## Integration mit WHOOP

Für den Gesundheitscoach-Workflow:

```
1. WHOOP: Recovery-Score des Tages abrufen
2. Morgen: Termine des Tages auflisten
3. Analyse: Bei niedriger Recovery intensive Meetings vermeiden
4. Morgen: Events ggf. verschieben oder blocken
```

## Referenzen

- [Morgen Kalender](https://morgen.so)
- [Morgen Developer Portal](https://platform.morgen.so/developers-api)
- [MorgenMCP GitHub](https://github.com/k3KAW8Pnf7mkmdSMPHz27/MorgenMCP)
- [Morgen API Docs](https://api.morgen.so/v3/)
