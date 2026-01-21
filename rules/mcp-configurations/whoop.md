# WHOOP MCP Server

> **Stand:** Januar 2026

Vollständige Referenz für den WHOOP MCP Server - Zugriff auf Gesundheits- und Fitness-Daten.

## MCP-Funnel Aktivierung

```
discover_tools_by_words("whoop", enable=true)
```

## Überblick

WHOOP ist ein 24/7 Wearable das Recovery, Strain, Sleep und Workouts trackt. Der MCP Server ermöglicht direkten API-Zugriff auf alle Nutzerdaten.

## Verfügbare Tools

### Daten-Tools

| Tool | Beschreibung |
|------|-------------|
| `whoop-get-user-profile` | Benutzerprofil abrufen |
| `whoop-get-user-body-measurements` | Körpermaße (Größe, Gewicht, Max HR) |
| `whoop-get-recovery-collection` | Recovery-Daten (paginiert) |
| `whoop-get-recovery-for-cycle` | Recovery für einen Cycle |
| `whoop-get-cycle-collection` | Cycles abrufen (paginiert) |
| `whoop-get-cycle-by-id` | Einzelnen Cycle abrufen |
| `whoop-get-sleep-collection` | Schlaf-Daten (paginiert) |
| `whoop-get-sleep-by-id` | Einzelne Schlaf-Session |
| `whoop-get-sleep-for-cycle` | Schlaf für einen Cycle |
| `whoop-get-workout-collection` | Workouts (paginiert) |
| `whoop-get-workout-by-id` | Einzelnes Workout |

### Authentifizierungs-Tools

| Tool | Beschreibung |
|------|-------------|
| `whoop-get-authorization-url` | OAuth Authorization URL generieren |
| `whoop-exchange-code-for-token` | Auth-Code gegen Token tauschen |
| `whoop-refresh-token` | Access Token erneuern |
| `whoop-set-access-token` | Token manuell setzen |
| `whoop-revoke-user-access` | Zugriff widerrufen |

## Kernkonzepte

### Physiological Cycle

WHOOP arbeitet nicht mit Kalendertagen, sondern mit **Physiological Cycles** - dem natürlichen Schlaf-Wach-Rhythmus.

- Ein Cycle beginnt mit dem Aufwachen
- Ein Cycle endet mit dem nächsten Schlaf
- Der aktuelle Cycle hat kein `end` Datum

### Score States

Alle Daten haben einen `score_state`:
- `SCORED` - Vollständig ausgewertet, alle Werte vorhanden
- `PENDING_SCORE` - Wird noch ausgewertet
- `UNSCORABLE` - Konnte nicht ausgewertet werden (fehlende Daten)

## Datenmodelle

### Recovery

Recovery ist die tägliche Messung wie bereit der Körper für Belastung ist (0-100%).

```json
{
  "cycle_id": 93845,
  "sleep_id": "123e4567-e89b-12d3-a456-426614174000",
  "user_id": 10129,
  "score_state": "SCORED",
  "score": {
    "recovery_score": 44,
    "resting_heart_rate": 64,
    "hrv_rmssd_milli": 31.813562,
    "spo2_percentage": 95.6875,
    "skin_temp_celsius": 33.7,
    "user_calibrating": false
  }
}
```

**Wichtige Felder:**
- `recovery_score` - 0-100%, Hauptindikator
- `resting_heart_rate` - Ruhepuls in bpm
- `hrv_rmssd_milli` - Herzratenvariabilität in ms
- `spo2_percentage` - Blutsauerstoff (nur WHOOP 4.0)
- `skin_temp_celsius` - Hauttemperatur (nur WHOOP 4.0)

### Sleep

Schlaf-Tracking mit Phasen und Performance-Metriken.

```json
{
  "id": "ecfc6a15-4661-442f-a9a4-f160dd7afae8",
  "cycle_id": 93845,
  "start": "2022-04-24T02:25:44.774Z",
  "end": "2022-04-24T10:25:44.774Z",
  "nap": false,
  "score_state": "SCORED",
  "score": {
    "stage_summary": {
      "total_in_bed_time_milli": 30272735,
      "total_awake_time_milli": 1403507,
      "total_light_sleep_time_milli": 14905851,
      "total_slow_wave_sleep_time_milli": 6630370,
      "total_rem_sleep_time_milli": 5879573,
      "sleep_cycle_count": 3,
      "disturbance_count": 12
    },
    "sleep_needed": {
      "baseline_milli": 27395716,
      "need_from_sleep_debt_milli": 352230,
      "need_from_recent_strain_milli": 208595,
      "need_from_recent_nap_milli": -12312
    },
    "respiratory_rate": 16.11,
    "sleep_performance_percentage": 98,
    "sleep_consistency_percentage": 90,
    "sleep_efficiency_percentage": 91.7
  }
}
```

**Wichtige Felder:**
- `nap` - true wenn Mittagsschlaf
- `sleep_performance_percentage` - Schlaf vs. Schlafbedarf
- `sleep_consistency_percentage` - Konsistenz der Schlafzeiten
- `sleep_efficiency_percentage` - Zeit im Bett vs. tatsächlicher Schlaf
- `stage_summary` - Schlafphasen in Millisekunden
- `sleep_needed` - Berechneter Schlafbedarf

### Cycle (Strain)

Der tägliche Cycle mit Strain-Score.

```json
{
  "id": 93845,
  "user_id": 10129,
  "start": "2022-04-24T02:25:44.774Z",
  "end": "2022-04-24T10:25:44.774Z",
  "timezone_offset": "-05:00",
  "score_state": "SCORED",
  "score": {
    "strain": 5.2951527,
    "kilojoule": 8288.297,
    "average_heart_rate": 68,
    "max_heart_rate": 141
  }
}
```

**Wichtige Felder:**
- `strain` - Tages-Strain (0-21 Skala)
- `kilojoule` - Verbrannte Energie
- `average_heart_rate` / `max_heart_rate` - Herzfrequenz

### Workout

Einzelne Aktivitäten/Workouts.

```json
{
  "id": "ecfc6a15-4661-442f-a9a4-f160dd7afae8",
  "sport_name": "running",
  "start": "2022-04-24T02:25:44.774Z",
  "end": "2022-04-24T10:25:44.774Z",
  "score_state": "SCORED",
  "score": {
    "strain": 8.2463,
    "average_heart_rate": 123,
    "max_heart_rate": 146,
    "kilojoule": 1569.34,
    "percent_recorded": 100,
    "distance_meter": 1772.77,
    "altitude_gain_meter": 46.64,
    "zone_durations": {
      "zone_zero_milli": 300000,
      "zone_one_milli": 600000,
      "zone_two_milli": 900000,
      "zone_three_milli": 900000,
      "zone_four_milli": 600000,
      "zone_five_milli": 300000
    }
  }
}
```

**Wichtige Sport-IDs:**

| ID | Sport |
|----|-------|
| 0 | Running |
| 1 | Cycling |
| 44 | Yoga |
| 45 | Weightlifting |
| 48 | Functional Fitness |
| 52 | Hiking/Rucking |
| 63 | Walking |
| 70 | Meditation |
| 96 | HIIT |
| 97 | Spin |
| 128 | Stretching |

## Beispiel-Workflows

### Aktuelle Recovery abrufen

```
1. whoop-get-cycle-collection (limit: 1) → Aktuellen Cycle
2. whoop-get-recovery-for-cycle (cycle_id) → Recovery-Score
```

### Schlaf der letzten Woche analysieren

```
1. whoop-get-sleep-collection
   - start: 7 Tage zurück
   - end: heute
2. Berechne Durchschnitte für:
   - sleep_performance_percentage
   - total_slow_wave_sleep_time_milli (Tiefschlaf)
   - total_rem_sleep_time_milli (REM)
```

### Trainingsbelastung auswerten

```
1. whoop-get-workout-collection (letzte 30 Tage)
2. Gruppiere nach sport_name
3. Summiere strain pro Sportart
4. Analysiere zone_durations für Intensitätsverteilung
```

## Rate Limits

- **100 Requests pro Minute**
- Pagination nutzen bei großen Datenmengen
- `next_token` für weitere Seiten verwenden

## Authentifizierung

OAuth 2.0 Flow mit folgenden Tools:

1. **Erstmalige Authentifizierung:**
   - `whoop-get-authorization-url` → URL zum Autorisieren
   - User autorisiert in Browser
   - `whoop-exchange-code-for-token` → Code gegen Token tauschen

2. **Token-Erneuerung:**
   - `whoop-refresh-token` → Automatische Erneuerung mit Refresh Token
   - Refresh Token benötigt `offline` Scope bei OAuth

3. **Manuell:**
   - `whoop-set-access-token` → Token direkt setzen
   - `whoop-revoke-user-access` → Zugriff widerrufen

## Tipps für optimale Nutzung

1. **Immer score_state prüfen** - Nur `SCORED` Daten haben vollständige Werte
2. **Zeitstempel in UTC** - Alle Zeiten sind UTC, `timezone_offset` für lokale Zeit nutzen
3. **Millisekunden beachten** - Schlafzeiten sind in ms, durch 3600000 für Stunden
4. **Cycles statt Tage** - WHOOP denkt in Cycles, nicht Kalendertagen
5. **Recovery braucht Cycle** - Recovery ist immer an einen Cycle gebunden

## Referenzen

- [WHOOP Developer Portal](https://developer.whoop.com/)
- [API Dokumentation](https://developer.whoop.com/api)
- [WHOOP 101 - Konzepte](https://developer.whoop.com/docs/whoop-101)
