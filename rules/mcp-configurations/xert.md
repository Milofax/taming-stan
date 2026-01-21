# XERT MCP Server

> **Stand:** Januar 2026

Vollständige Referenz für den XERT MCP Server - Zugriff auf Fitness Signature, Training Load, Workouts und Aktivitäten.

## MCP-Funnel Aktivierung

```
discover_tools_by_words("xert", enable=true)
```

## Überblick

XERT ist eine fortschrittliche Trainingsplattform für Radfahrer, die mit dem "Fitness Signature" Modell arbeitet. Statt nur FTP zu messen, analysiert XERT die komplette Leistungskurve und berechnet daraus individuelle Trainingsempfehlungen.

## Verfügbare Tools

| Tool | Beschreibung |
|------|-------------|
| `xert__xert-get-training-info` | Fitness Signature, Training Status, XSS, WOTD |
| `xert__xert-list-workouts` | Liste aller gespeicherten Workouts |
| `xert__xert-get-workout` | Workout-Details mit Intervallen |
| `xert__xert-download-workout` | Workout als ZWO/ERG exportieren |
| `xert__xert-list-activities` | Aktivitäten in einem Zeitraum |
| `xert__xert-get-activity` | Aktivität mit XSS-Metriken und MPA-Daten |
| `xert__xert-upload-fit` | FIT-Datei hochladen |

## Kernkonzepte

### Fitness Signature

Die "Fitness Signature" ist XERTs alternatives Modell zur reinen FTP-Messung. Sie besteht aus drei Komponenten:

| Parameter | Bedeutung | Einheit |
|-----------|-----------|---------|
| **TP** (Threshold Power) | Schwellenleistung, vergleichbar mit FTP | Watt |
| **HIE** (High Intensity Energy) | Anaerobe Kapazität oberhalb der Schwelle | kJ |
| **PP** (Peak Power) | Maximale Spitzenleistung | Watt |

**Zusätzlich:**
- **LTP** (Lower Threshold Power) - Untere Schwelle, ca. 75% von TP

### Training Status

XERT bewertet den aktuellen Trainingszustand:

| Status | Bedeutung | Form (Stars) |
|--------|-----------|--------------|
| `Fresh` | Erholt, bereit für hartes Training | 3-5 |
| `Tired` | Moderate Ermüdung | 2 |
| `Very Tired` | Stark ermüdet, Erholung nötig | 0-1 |

### Training Load

Die Trainingsbelastung wird in zwei Dimensionen bewertet:

| Load | Beschreibung |
|------|--------------|
| **High Intensity Load** | Belastung durch intensive Einheiten |
| **Low Intensity Load** | Belastung durch Grundlagentraining |

Beide Werte werden als `Optimal`, `Maintenance`, `Overreaching` oder `Detraining` klassifiziert.

### XSS (Xert Strain Score)

XSS ist XERTs Pendant zu TSS (Training Stress Score), aber basierend auf der Fitness Signature.

- **Focus XSS** - XSS in verschiedenen Leistungsbereichen
- **Difficulty Score** - Wie anspruchsvoll war die Aktivität relativ zur Fitness

### Focus (Athlete Type)

XERT klassifiziert Athleten und Workouts nach "Focus":

| Focus | Power Duration | Typisch für |
|-------|----------------|-------------|
| `Sprint` | < 30s | Track Sprinter |
| `Pursuiter` | 30s - 2min | Pursuit, Crits |
| `Breakaway Specialist` | 2-4min | Angriffe, Kuppen |
| `Climber` | 4-8min | Bergfahrer |
| `GC Specialist` | 8-20min | Zeitfahren, Anstiege |
| `Rouleur` | 20min - 1h | Classics, Fluchtgruppen |
| `Endurance` | > 1h | Langstrecke |

### MPA (Maximum Power Available)

MPA ist die momentan verfügbare Maximalleistung, die sich während einer Aktivität ändert:

- Startet bei PP (Peak Power)
- Fällt bei Belastung über TP
- Erholt sich bei Belastung unter TP
- **Breakthrough** = MPA erreicht tatsächliche Leistung

### Breakthroughs

Ein Breakthrough entsteht, wenn die tatsächliche Leistung die MPA-Kurve erreicht. Dies zeigt, dass die Fitness Signature aktualisiert werden sollte.

## Datenmodelle

### Training Info Response

```json
{
  "thresholdPower": 267,
  "lowerThresholdPower": 200,
  "highIntensityEnergy": 21.5,
  "peakPower": 1150,
  "trainingStatus": "Fresh",
  "formStars": 4.2,
  "highLoad": { "value": 52, "status": "Optimal" },
  "lowLoad": { "value": 78, "status": "Optimal" },
  "xss": {
    "total": 2450,
    "lastDay": 85,
    "lastWeek": 420
  },
  "wotd": {
    "name": "SMART - Endurance",
    "focus": "Endurance",
    "xss": 75,
    "duration": 3600
  }
}
```

### Activity Response

```json
{
  "id": 12345678,
  "name": "Morning Ride",
  "startTime": "2026-01-08T07:30:00Z",
  "duration": 5400,
  "distance": 45.2,
  "xss": 95,
  "focus": "Endurance",
  "difficulty": 3.2,
  "breakthrough": false,
  "mpaData": {
    "minMpa": 890,
    "timeBelowMpa": 120,
    "nearBreakthroughs": 2
  },
  "signature": {
    "tp": 267,
    "hie": 21.5,
    "pp": 1150
  }
}
```

### Workout Response

```json
{
  "id": 987654,
  "name": "SMART - Sweet Spot 2x20",
  "description": "Classic sweet spot intervals",
  "focus": "GC Specialist",
  "targetXss": 85,
  "duration": 3600,
  "difficulty": 3.5,
  "intervals": [
    { "type": "warmup", "duration": 600, "powerLow": 50, "powerHigh": 75 },
    { "type": "interval", "duration": 1200, "power": 90 },
    { "type": "recovery", "duration": 300, "power": 50 },
    { "type": "interval", "duration": 1200, "power": 90 },
    { "type": "cooldown", "duration": 300, "power": 50 }
  ]
}
```

## Beispiel-Workflows

### Aktuellen Fitnessstatus abrufen

```
xert-get-training-info
→ Fitness Signature (TP, HIE, PP)
→ Training Status (Fresh/Tired)
→ Form Stars
→ WOTD Empfehlung
```

### Aktivitäten der letzten Woche analysieren

```
1. xert-list-activities
   - from: 7 Tage zurück (Unix Timestamp)
   - to: heute (Unix Timestamp)
2. Analysiere:
   - Gesamt-XSS
   - Breakthroughs
   - Focus-Verteilung
```

### Workout für Trainer exportieren

```
1. xert-list-workouts → Workout-ID finden
2. xert-download-workout
   - id: Workout-ID
   - format: "zwo" (für Zwift) oder "erg" (für andere)
3. Datei an Trainer übertragen
```

### Breakthrough-Analyse

```
1. xert-list-activities (letzte 30 Tage)
2. Filtere nach breakthrough: true
3. Für jeden Breakthrough:
   xert-get-activity (id)
   → Analysiere MPA-Daten und Signatur-Updates
```

## Authentifizierung

XERT verwendet OAuth 2.0 mit Password Grant:

### Initiale Authentifizierung

```bash
cd ~/dotfiles/vendor/xert-mcp
npm run setup-auth
```

Das Script fragt nach:
- XERT E-Mail
- XERT Passwort

Tokens werden automatisch in `.env` gespeichert.

### Token-Erneuerung

- Access Token gültig: **7 Tage**
- Refresh automatisch beim API-Aufruf
- Bei Fehlschlag: `npm run setup-auth` erneut ausführen

### Credentials speichern

Speichere deine XERT-Zugangsdaten sicher in 1Password unter **"XERT API Credentials"**.

## Parameter-Referenz

### xert-list-activities

| Parameter | Typ | Beschreibung |
|-----------|-----|--------------|
| `from` | number | Start-Timestamp (Unix ms) |
| `to` | number | End-Timestamp (Unix ms) |

### xert-get-activity

| Parameter | Typ | Beschreibung |
|-----------|-----|--------------|
| `id` | number | Activity ID |

### xert-download-workout

| Parameter | Typ | Beschreibung |
|-----------|-----|--------------|
| `id` | number | Workout ID |
| `format` | string | `"zwo"` oder `"erg"` |

### xert-get-training-info

| Parameter | Typ | Beschreibung |
|-----------|-----|--------------|
| `format` | string | Optional: WOTD-Format (`"zwo"` oder `"erg"`) |

## API-Limitierungen

Die XERT API bietet **keinen Zugriff** auf:
- Training Advisor Empfehlungen (Mobile App intern)
- Workout-Planung/Scheduling
- Forecast AI Prognosen
- Smart Workout Auswahl-Algorithmus

Diese Features sind nur in der XERT Mobile App und Web-Plattform verfügbar.

## Tipps für optimale Nutzung

1. **Timestamps in Unix ms** - `from`/`to` Parameter als Unix-Millisekunden
2. **Breakthroughs checken** - Regelmäßig auf neue Fitness Signature Updates prüfen
3. **Focus verstehen** - Der Focus zeigt, welcher Athletentyp du bist/trainierst
4. **Form Stars beachten** - 3+ Stars = bereit für hartes Training
5. **XSS statt TSS** - XSS ist genauer als TSS, da es auf deiner Fitness Signature basiert

## Referenzen

- [XERT Online](https://www.xertonline.com/)
- [XERT API Dokumentation](https://www.xertonline.com/API.html)
- [XERT Glossar](https://baronbiosys.com/glossary/)
- [MCP Server Repository](https://github.com/Milofax/xert-mcp)
