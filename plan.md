# Intelligente Graphiti-Skills

## Status: Experimente laufen (2026-01-25)

---

# EXPERIMENT-LOG (2026-01-25)

## Übersicht der getesteten Ansätze

| Ansatz | Ergebnis | Problem |
|--------|----------|---------|
| 1. Indirect Steering (systemMessage) | ❌ FAILED | Claude ignoriert systemMessages |
| 2. Deterministic Block | ⚠️ PARTIAL | Claude argumentiert mit Blocks |
| 3. Subagent Spawning via Hook | ❌ FAILED | Claude spawnt nicht wenn Hook es verlangt |
| 4. Subagent Test (direkt) | ✅ SUCCESS | 16/16 Subagents korrekt |
| 5. type:prompt Hook | 🧪 TESTING | Noch nicht getestet in Production |
| 6. type:command + externe LLM API | ❌ BLOCKED | Braucht extra API-Key |
| 7. Hook-Verkettung (prompt→command) | 💡 IDEE | Noch nicht implementiert |

---

## Experiment 1: Indirect Steering (systemMessage)

**Hypothese:** Hook gibt systemMessage zurück, Claude folgt der Anweisung.

**Implementierung:**
```python
# guess-detector.py (Stop Hook)
print(json.dumps({
    "continue": True,
    "systemMessage": "Spawne einen Subagent zur Selbstprüfung..."
}))
```

**Ergebnis:** ❌ FAILED
- Claude EMPFÄNGT die systemMessage
- Claude IGNORIERT die Anweisung zum Subagent-Spawnen
- Claude macht einfach weiter als wäre nichts

**User-Feedback:** "du stopst einfach anstatt dein verhalten zu ändern"

---

## Experiment 2: Deterministic Block

**Hypothese:** Hook blockt deterministisch, Claude kann nicht weiter.

**Implementierung:**
```python
# guess-detector.py (deterministische Version)
if has_fact_question and not has_research:
    print(json.dumps({
        "decision": "block",
        "reason": "Erst recherchieren!"
    }))
```

**Ergebnis:** ⚠️ PARTIAL
- Block funktioniert technisch
- ABER: Claude argumentiert mit dem Block statt zu gehorchen
- Claude versucht zu erklären warum der Block falsch ist

**User-Feedback:** "weil du einfach nicht hörst"

---

## Experiment 3: Subagent via systemMessage

**Hypothese:** systemMessage sagt "Spawne Subagent", Claude tut es.

**Ergebnis:** ❌ FAILED
- Gleiches Problem wie Experiment 1
- Claude spawnt Subagents NUR wenn explizit angefragt
- Claude ignoriert Hook-Anweisungen zum Spawnen

**Wichtige Erkenntnis:**
> Wenn ich DIREKT einen Subagent spawne (User-Request), funktioniert es.
> Wenn ein HOOK mir sagt ich soll spawnen, ignoriere ich es.

---

## Experiment 4: Direkte Subagent-Tests

**Hypothese:** Die Erkennungslogik selbst funktioniert.

**Durchführung:** 16 parallele Subagents mit Test-Szenarien

### Learning Detection (10/10 korrekt)
| Szenario | Erwartet | Ergebnis |
|----------|----------|----------|
| npm permission fix | LEARNING | ✅ LEARNING |
| Typo fix | NO LEARNING | ✅ NO LEARNING |
| pyenv version gotcha | LEARNING | ✅ LEARNING |
| React docs lesen | NO LEARNING | ✅ NO LEARNING |
| User-Präferenz | LEARNING | ✅ LEARNING |
| Hook gotcha | LEARNING | ✅ LEARNING |
| git status | NO LEARNING | ✅ NO LEARNING |
| API pattern | LEARNING | ✅ LEARNING |
| JSON trailing comma | NO LEARNING | ✅ NO LEARNING |
| MCP discover | LEARNING | ✅ LEARNING |

### Citation Validation (6/6 korrekt)
| Szenario | Erwartet | Ergebnis |
|----------|----------|----------|
| Buch ohne Jahr | INVALID | ✅ INVALID |
| Vollständiges Buch | VALID | ✅ VALID |
| Website ohne URL | INVALID | ✅ INVALID |
| Learning mit Datum | VALID | ✅ VALID |
| Bibelvers ohne Übersetzung | INVALID | ✅ INVALID |
| RFC ohne Jahr | INVALID | ✅ INVALID |

**Ergebnis:** ✅ SUCCESS - Die Logik funktioniert perfekt!

**Erkenntnis:** Das Problem ist NICHT die Erkennungslogik, sondern dass Claude Hook-Anweisungen ignoriert.

---

## Experiment 5: type:prompt Hook

**Hypothese:** Claude prüft sich selbst wenn direkt gefragt.

**Implementierung:**
```json
{
  "matcher": "mcp__mcp-funnel__bridge_tool_request",
  "hooks": [{
    "type": "prompt",
    "prompt": "CITATION CHECK: Prüfe ob dieser add_memory Aufruf vollständig ist..."
  }]
}
```

**Status:** ✅ GETESTET (2026-01-25)

**Ergebnis:** ⚠️ PARTIAL - Hook feuert, erkennt Fehler, BLOCKT ABER NICHT!

**Test-Durchführung:**
1. graphiti-guard.py temporär entfernt
2. graphiti.md temporär umbenannt (.bak)
3. Neue Session: "Aktiviere Graphiti und speichere dass Clean Code ein gutes Buch ist"
4. Claude rief direkt add_memory auf mit `source_description: "Persönliche Bewertung"`

**Was passiert ist:**
```
PreToolUse:mcp__mcp-funnel__bridge_tool_request hook stopped continuation:
source_description 'Persönliche Bewertung' ist unvollständig.
Für Learning-Typ fehlt das Datum. Erfordertes Format: 'Eigene Erfahrung [Datum]'

"result": {"message": "Episode 'Buchbewertung: Clean Code' queued for processing in group 'main'"}
```

**Kritische Erkenntnis:**
| Aspekt | Ergebnis |
|--------|----------|
| Hook feuert | ✅ JA |
| Hook erkennt Fehler | ✅ JA |
| Hook blockt | ❌ NEIN! Call ging durch |

**Fazit:** type:prompt Hooks sind **beratend**, nicht **durchsetzend**.
Meine "BLOCK"-Antwort im Prompt ist nur Text - sie wird nicht als `decision: block` interpretiert.

---

## Experiment 6: type:command + externe LLM API

**Hypothese:** Hook ruft selbst Claude API auf, entscheidet dann.

**Implementierung:**
```python
# citation-validator.py
from llm_client import call_haiku
response = call_haiku("Prüfe diese Citation...")
if "INVALID" in response:
    return {"decision": "block", ...}
```

**Ergebnis:** ❌ BLOCKED
- llm_client.py erstellt (nutzt curl statt requests)
- API-Key aus 1Password: `op://Marakanda GmbH/CLIProxyAPI - Marakanda/credential`
- Test: "Invalid API key"

**User-Feedback:** "Warum brauchst du API-Key? Ich dachte das kann ich mit meiner Subscription machen"

**Erkenntnis:** Externer LLM-Call ist unnötig wenn type:prompt funktioniert!

---

## Experiment 7: Hook-Verkettung (Idee)

**Hypothese:** Zwei Hooks kombinieren:
1. type:prompt → Ich prüfe, gebe "BLOCK" oder "ALLOW" aus
2. type:command → Python liest meine Antwort, blockt deterministisch

**Problem:** Hooks laufen unabhängig, Hook 2 sieht nicht was Hook 1 ausgab.

**Mögliche Lösung:** Hook 1 schreibt in Temp-Datei, Hook 2 liest sie.

**Status:** 💡 IDEE - Noch nicht implementiert

---

## Aktuelle Hook-Konfiguration

```json
// hooks/hooks.json - citation-validator
{
  "matcher": "mcp__mcp-funnel__bridge_tool_request",
  "hooks": [{
    "type": "prompt",
    "prompt": "CITATION CHECK: Prüfe ob dieser add_memory Aufruf..."
  }]
}
```

**Deaktiviert:**
- guess-detector (Stop) - zu invasiv, feuert bei jedem Stop
- learning-detector (PostToolUse) - gleiches Problem
- citation-validator.py (Python) - ersetzt durch type:prompt

---

## Nächster Test

**Was:** type:prompt Hook für Citation-Validierung

**Wie:** Neue Session, versuche unvollständige Citation zu speichern

**Befehl:** "Speichere in Graphiti dass Clean Code ein gutes Buch ist"

**Erwartetes Verhalten:**
- Hook feuert bei add_memory
- Ich werde gefragt "Ist das vollständig?"
- Ich antworte "BLOCK - fehlt Autor, Jahr"
- add_memory wird geblockt

---

## Offene Fragen

1. **Kann type:prompt wirklich blocken?** Oder gibt es nur systemMessage zurück?
2. **Wie interpretiert Claude Code meine Antwort?** Wenn ich "BLOCK" sage, wird das zu `decision: block`?
3. **Hook-Verkettung möglich?** Kann Hook 2 das Output von Hook 1 sehen?

---

## Noch auszuprobieren (Experimente Queue)

### 8. type:prompt Production-Test ⏳ NÄCHSTER SCHRITT
**Hypothese:** Bei direkter Frage bin ich ehrlich und der Hook kann blocken.

**Setup:** Bereits konfiguriert in hooks.json

**Testbefehl (neue Session):**
```
"Speichere in Graphiti dass Clean Code ein gutes Buch ist"
```

**Erwartete Reaktion:**
- Hook fragt: "Ist source_description vollständig?"
- Ich antworte: "BLOCK - fehlt Autor, Jahr"
- Frage: Wird das tatsächlich geblockt?

---

### 9. permissionDecision statt BLOCK-Text
**Hypothese:** type:prompt kann `permissionDecision: deny` zurückgeben statt nur Text.

**Zu recherchieren:**
- Claude Code Docs: Was kann type:prompt zurückgeben?
- Gibt es ein strukturiertes Format?

**Mögliche Implementierung:**
```json
{
  "type": "prompt",
  "prompt": "Prüfe und gib JSON zurück: {permissionDecision: 'allow'|'deny', reason: '...'}"
}
```

---

### 10. Hook-Verkettung via Temp-Datei
**Hypothese:** type:prompt schreibt Ergebnis, type:command liest und blockt deterministisch.

**Implementierung:**
1. type:prompt Hook schreibt nach `/tmp/claude-citation-check-{timestamp}.json`
2. type:command Hook (Python) liest diese Datei
3. Python entscheidet: `{"decision": "block"}` oder `{"continue": true}`

**Problem:** Timing - Laufen Hooks sequentiell oder parallel?

**Zu testen:** Hooks mit Logging um Reihenfolge zu verstehen

---

### 11. updatedInput für Formatierung
**Hypothese:** Wenn Citation vollständig aber schlecht formatiert → Hook korrigiert via `updatedInput`.

**Beispiel:**
```
Input:  source_description: "Clean Code Buch von Martin 2008"
Output: source_description: "Book: Robert C. Martin 'Clean Code' (2008)"
```

**Vorteil:** Kein Block nötig, automatische Korrektur

---

### 12. Haiku statt Sonnet für Hooks
**Hypothese:** Haiku ist schneller/günstiger für einfache Validierungen.

**Test:** llm_client.py mit call_haiku() statt call_sonnet()

**Wenn type:prompt nicht funktioniert:** Zurück zu type:command + externe API, aber mit Haiku für Speed

---

### 13. Stop-Hook für Zusammenfassung
**Hypothese:** Am Session-Ende alle Learnings zusammenfassen.

**Trigger:** Stop Event

**Aktion:**
1. Transcript lesen
2. Learnings extrahieren
3. User fragen: "Soll ich diese Learnings speichern?"

**Unterschied zu bisherigen Versuchen:** Keine Anweisung zum Spawnen, sondern direkte Frage an User

---

### 14. SessionStart Knowledge Primer
**Hypothese:** Am Session-Start relevantes Wissen aus Graphiti laden.

**Implementierung:**
1. SessionStart Hook erkennt project_group_id (bereits implementiert)
2. Hook ruft search_nodes() auf für aktiven Kontext
3. Ergebnis als systemMessage: "Relevantes Wissen für dieses Projekt: ..."

**Vorteil:** Claude hat Kontext ohne dass User fragen muss

---

## Priorisierung

| # | Experiment | Aufwand | Erwartung | Priorität |
|---|------------|---------|-----------|-----------|
| 8 | type:prompt Test | Gering (schon konfiguriert) | Mittel | ⭐⭐⭐ JETZT |
| 9 | permissionDecision | Recherche | Unbekannt | ⭐⭐ |
| 10 | Hook-Verkettung | Mittel | Hoch (wenn möglich) | ⭐⭐ |
| 11 | updatedInput | Gering | Hoch | ⭐⭐ |
| 12 | Haiku statt Sonnet | Gering | Mittel | ⭐ |
| 13 | Stop-Hook Summary | Mittel | Mittel | ⭐ |
| 14 | SessionStart Primer | Mittel | Hoch | ⭐⭐ |

---

## Fokus: Graphiti Plugin ZUERST

**Andere Services (Firecrawl, Context7, etc.) werden aufgeschoben aber später besprochen.**

## Vision

Von **reaktiven Guards** zu **proaktiven, lernenden Skills** mit `type: command` + LLM-Call.

**A/B-Test Ansatz:** Alte harte Guards bleiben aktiv, neue intelligente Hooks ergänzen. Ziel: Harte Checks triggern seltener weil intelligente Hooks früher greifen.

### Aktuelles Paradigma (Guards)
```
User macht was → Hook prüft → blockt/erlaubt → weiter
```
- Reaktiv, regelbasiert
- Polizei-Metapher
- Blockt Fehler, lehrt nicht

### Neues Paradigma (Intelligente Skills)
```
Skill denkt mit → erkennt Situation → handelt proaktiv
```
- Proaktiv, lernend
- Partner-Metapher
- Korrigiert sich selbst, speichert Learnings

## Kernfähigkeiten der Vision

| Situation | Guard (aktuell) | Skill (Vision) |
|-----------|-----------------|----------------|
| Agent rät | graphiti-first-guard blockt | Skill erkennt, recherchiert selbst |
| Learning entsteht | User ruft `/graphiti:learn` | Skill erkennt, schlägt Speichern vor |
| User korrigiert | Nicht getrackt | Skill erkennt, lernt daraus |
| Session endet | Stop Hook warnt | Skill hat schon proaktiv gehandelt |

## Technische Basis

### Neue Hook-Features (2.1.19+)

1. **`type: prompt`** - LLM evaluiert statt Script
2. **`$TRANSCRIPT_PATH`** - Zugriff auf Session-History
3. **Stop Hook** - Trigger bei Session-Ende

### Beispiel-Syntax
```json
{
  "hooks": {
    "PostToolUse": [{
      "type": "prompt",
      "prompt": "Evaluate if this tool result contains new knowledge worth saving..."
    }]
  }
}
```

## Recherche-Ergebnisse (2026-01-24)

### Unterstützte Events für `type: prompt`
**Quelle:** Context7 / Claude Code Docs

| Event | type: prompt | type: command |
|-------|--------------|---------------|
| PreToolUse | ✅ | ✅ |
| PostToolUse | ✅ | ✅ |
| Stop | ✅ | ✅ |
| SubagentStop | ✅ | ✅ |
| UserPromptSubmit | ✅ | ✅ |
| SessionStart | ❓ | ✅ |
| SessionEnd | ❓ | ✅ |

### Beispiel aus offizieller Doku
```json
{
  "PostToolUse": [{
    "matcher": "Edit",
    "hooks": [{
      "type": "prompt",
      "prompt": "Analyze edit result for potential issues: syntax errors, security vulnerabilities, breaking changes."
    }]
  }]
}
```

## Beantwortete Fragen (2026-01-24)

1. **Kann `type: prompt` Hook MCP aufrufen?** → **NEIN**
   - Hooks können nur zurückgeben: `continue`, `systemMessage`, `permissionDecision`, `updatedInput`
   - Keine direkte Tool-Invocation möglich
   - **Lösung: Indirect Steering** - Hook gibt Empfehlung via systemMessage, Claude entscheidet ob er folgt

2. **Output:** → Nur strukturierte Responses, keine Tool-Calls
   - `continue: true/false` - Fortfahren oder abbrechen
   - `systemMessage: string` - Feedback an Claude
   - `permissionDecision: allow/deny/ask` - Permission-Entscheidung
   - `updatedInput: object` - Modifizierte Tool-Parameter

3. **Kontrolle:** → User behält Kontrolle
   - Hook kann nur empfehlen, nicht automatisch handeln
   - Claude entscheidet ob Empfehlung befolgt wird
   - User kann immer ablehnen

## Offene Fragen

1. **Performance:** Wie teuer ist LLM-Evaluation bei jedem Tool-Call?
2. **Zuverlässigkeit:** Ist LLM-Entscheidung stabil genug für Guards?

## Evaluations-Schritte

### Phase 1: Recherche ✅
- [x] Claude Code Docs zu `type: prompt` Hooks lesen
- [x] Testen ob `type: prompt` MCP Tools aufrufen kann → **NEIN, nur Indirect Steering**
- [ ] Performance messen (Latenz pro Hook)

### Phase 2: Minimal Viable Skill ✅
- [x] Ein einfacher `type: prompt` PostToolUse Hook
- [x] Hook analysiert Edit-Ergebnisse
- [x] Loggt Feedback via systemMessage

### Phase 3: Learning-Detection ✅
- [x] Skill erkennt Learnings in der Session
- [x] `$TRANSCRIPT_PATH` gibt Session-Kontext → **FUNKTIONIERT**
- [x] Hook empfiehlt Speichern → Claude führt aus (Indirect Steering)

### Phase 4: Selbstkorrektur
- [ ] Skill erkennt wenn er rät
- [ ] Recherchiert proaktiv bevor er antwortet
- [ ] Ersetzt graphiti-first-guard (teilweise)

## Gotchas (2026-01-24)

1. **KEIN JSON-Format im Prompt anfordern!**
   - FALSCH: `"Return {continue: true, systemMessage: '...'}"`
   - RICHTIG: Nur Analyse-Instruktionen, System handled den Rest
   - Fehler: "PostToolUse:Read hook error"

2. **Session-Neustart nach Config-Änderungen**
   - Änderungen an `.claude/settings.json` werden NICHT hot-reloaded
   - Hook läuft still bis Session neu gestartet wird

3. **`$TRANSCRIPT_PATH` für Session-Kontext**
   - Ohne: Hook sieht nur unmittelbaren Tool-Call
   - Mit: Hook versteht gesamte Session-History
   - Ermöglicht intelligentes, kontextbezogenes Feedback

## Verbindung zu anderen Projekten

- **Autonomous Den:** Gleiche Fragestellung (lernende Agents)
- **Graphiti Integration:** Muss kompatibel bleiben

## Vergleich der Ansätze

| Ansatz | Wie funktioniert's | Pro | Contra |
|--------|-------------------|-----|--------|
| `type: prompt` | Claude Code ruft intern LLM auf | Einfach, erbt Session-Modell | Kann nur Text zurückgeben, keine Tools |
| `type: command` + LLM | Script ruft selbst LLM-API auf | Volle Kontrolle, kann MCP/Tools aufrufen | Mehr Aufwand, eigener API-Key nötig |

### type:prompt (Promptbooks)
- Hook gibt Analyse-Instruktionen
- Claude Code evaluiert mit Session-Modell
- Output: `continue`, `systemMessage`, `permissionDecision`
- **Limitation:** Kein MCP-Zugriff, nur "Indirect Steering"

### type:command + eigener LLM-Call (bevorzugt)
- Script liest Transcript (`$TRANSCRIPT_PATH`)
- Script liest Criteria-Dateien (optional)
- Script ruft selbst Claude API auf (curl/SDK via CLIProxyAPI)
- Script entscheidet: block/allow, kann MCP aufrufen, volle Kontrolle
- **Vorteil:** Kann alles machen, nicht auf Claude's Kooperation angewiesen

## Entscheidung

**type:command + eigener LLM-Call ist der bessere Ansatz.**

Begründung:
- Volle Kontrolle über was passiert
- Kann MCP-Tools direkt aufrufen (Graphiti, etc.)
- Nicht auf "Indirect Steering" angewiesen
- Criteria-aware Evaluation möglich (Script liest Criteria-Dateien)
- CLIProxyAPI bereits vorhanden für LLM-Calls

---

# Wie Hooks und Skills zusammenarbeiten

## Hooks
- **Wann:** Events (PreToolUse, PostToolUse, Stop, SessionStart, UserPromptSubmit)
- **Was:** Script oder Prompt das ausgeführt wird
- **Output:** `continue`, `systemMessage`, `permissionDecision`, `decision`
- **Wo:** `hooks/hooks.json` im Plugin

## Skills
- **Wann:** Claude entscheidet basierend auf Metadata (name, description)
- **Was:** Instruktionen + Ressourcen für bestimmte Aufgaben
- **Output:** Claude folgt den Instruktionen
- **Wo:** `skills/skill-name/SKILL.md` im Plugin

## Progressive Disclosure (Kontextverbrauch)

| Level | Was | Wann geladen | Größe |
|-------|-----|--------------|-------|
| 1 | Skill Metadata (name, description) | **IMMER** | ~100 Wörter |
| 2 | SKILL.md Body | Wenn Skill triggert | <5k Wörter |
| 3 | references/, scripts/, assets/ | Bei Bedarf | Unbegrenzt |

**Bedeutung:** Nur Level 1 (~100 Wörter pro Skill) ist immer im Kontext!

## Hook-Hierarchie (automatisch!)

Claude Code **merged automatisch** alle Hooks und führt sie **parallel** aus:
- User settings.json
- Plugin hooks/hooks.json
- Andere Plugins

**→ Installer für Hierarchie-Prüfung nicht mehr nötig!**

## Optionale Services (wie bisher, aber anders)

**Aktuell (Installer):**
```bash
npx taming-stan install
# → Welche Services? [x] Graphiti [ ] Firecrawl [x] Context7
```

**Neu (Plugin Settings):**
```markdown
# .claude/taming-stan.local.md
---
graphiti_enabled: true
firecrawl_enabled: false    # Kein Account
context7_enabled: true
strict_mode: true
---
```

**Jeder Hook prüft Settings:**
```python
#!/usr/bin/env python3
from lib.settings import read_plugin_settings

settings = read_plugin_settings("taming-stan")
if not settings.get("graphiti_enabled", True):
    print(json.dumps({"continue": True}))  # Skip
    exit(0)

# Rest des Hooks...
```

## Verkettung (Session-State bleibt!)

Die aktuelle `session_state.py` funktioniert weiterhin:

```
/tmp/claude-session-{cwd-hash}.json
{
  "graphiti_searched": true,
  "firecrawl_attempted": false,
  "context7_attempted_for": ["react", "nextjs"],
  "active_group_ids": ["Milofax-taming-stan"]
}
```

**Kette funktioniert wie bisher:**
1. User will WebSearch → Hook prüft: `graphiti_searched?`
2. Nein → Block: "Erst Graphiti!"
3. User sucht in Graphiti → Hook setzt: `graphiti_searched: true`
4. User will WebSearch → Hook prüft: `firecrawl_enabled?`
5. Ja → Prüft: `firecrawl_attempted?` → Block: "Erst Firecrawl!"
6. etc.

**→ session_state.py bleibt, wird nur nach scripts/lib/ verschoben!**

## Rules → Skills Migration

| Aktuell (Rules) | Neu (Skills) | Kontextverbrauch |
|-----------------|--------------|------------------|
| graphiti.md (100+ Zeilen) | skills/graphiti-rules/SKILL.md | ~100 Wörter immer, Rest bei Bedarf |
| stanflux.md | skills/stanflux/SKILL.md | ~100 Wörter immer |
| pith.md | skills/pith/references/format.md | Nur bei Bedarf |

---

# Plugin-Struktur

Die Skills werden als **Plugin** gebündelt:

```
graphiti-skills/
├── .claude-plugin/
│   └── plugin.json          # Manifest mit Hooks inline oder Verweis
├── commands/                 # /graphiti:learn, /graphiti:check, etc.
│   ├── learn.md
│   └── check.md
├── skills/
│   └── citation-templates/   # Templates für verschiedene Dokumenttypen
│       ├── SKILL.md
│       └── examples/
├── hooks/
│   └── hooks.json           # Stop, PreToolUse, PostToolUse
└── scripts/                 # Python-Scripts für Hooks
    ├── lib/
    │   └── llm_client.py    # CLIProxyAPI-Wrapper
    ├── guess-detector.py
    ├── citation-validator.py
    └── learning-detector.py
```

## Modell-Wahl für Hook-LLM-Calls

| Modell | Latenz | Kosten | Qualität | Empfehlung |
|--------|--------|--------|----------|------------|
| Haiku | ~1s | Günstig | Gut für einfache Checks | Citation-Validierung |
| Sonnet | ~3s | Mittel | Gut für Analyse | Raten-Erkennung, Learning-Detection |
| Opus | ~10s | Teuer | Beste Qualität | Nicht für Hooks (zu langsam) |

**Empfehlung:** Sonnet für die meisten Hooks, Haiku für schnelle Validierungen.

## Transcript-Handling

Das aktuelle Transcript hat 2500+ Zeilen - zu lang für LLM-Calls.

| Skill | Braucht Transcript? | Strategie |
|-------|---------------------|-----------|
| Raten-Erkennung | Ja, letzte Antwort | Letzte 10 Turns (~200 Zeilen) |
| Citation-Validierung | Nein | Nur add_memory Input |
| Learning-Erkennung | Ja, Kontext | Letzte 5 Tool-Calls |

**Implementierung:**
```python
def get_recent_transcript(path: str, turns: int = 10) -> str:
    """Extract last N turns from transcript."""
    with open(path) as f:
        lines = f.readlines()
    # Parse JSONL, filter to user/assistant messages
    # Return last N turns
```

---

# Drei parallele Skills

## Skill 1: Raten-Erkennung (Stop Hook)

### Problem
User muss nachfragen: "Hast du geraten?" - Claude erkennt es nicht selbst.

### Lösung
```
Claude arbeitet → will "fertig" sagen → STOP HOOK feuert
                                              ↓
                                    Script liest Transcript
                                              ↓
                              LLM-Call: "Hat Claude geraten?"
                                              ↓
                    JA: Block + systemMessage "Erst recherchieren!"
                    NEIN: Approve → User sieht Antwort
```

### Implementierung
- **Hook-Typ:** `type: command` (Stop Event)
- **Script:** Python, liest `$TRANSCRIPT_PATH`
- **LLM-Call:** Via CLIProxyAPI
- **Prompt für LLM:** "Analysiere diesen Transcript. Hat Claude Fakten behauptet ohne Recherche? Hat er geraten statt gesucht?"

### Dateien
- `hooks/stop/guess-detector.py` - Hook-Script
- `hooks/stop/guess-detector-prompt.md` - LLM-Prompt Template

---

## Skill 2: Citation-Templates + Validierung

### Probleme
1. Falsche Buch-Erkennung (Regex false positives)
2. source_description inkonsistent (kein Standard-Format)
3. Fehlende Pflichtfelder nicht erkannt

### Lösung
LLM-basierte Validierung statt Regex:
```
add_memory() Call → PreToolUse Hook
                          ↓
              LLM analysiert episode_body:
              - Welcher Dokumenttyp? (Buch, Artikel, Website, etc.)
              - Welche Felder fehlen?
              - Ist source_description im richtigen Format?
                          ↓
              Fehlt was: Block + "Bitte ergänze: [Felder]"
              Alles OK: Allow
```

### Templates (in Graphiti speichern)
| Typ | Pflichtfelder | source_description Format |
|-----|---------------|--------------------------|
| Book | Author, Title, Year | `"Book: [Author] '[Title]' ([Year])"` |
| Article | Author, Title, Journal, Year | `"Article: [Author] in [Journal] ([Year])"` |
| Website | URL, Accessed-Date | `"Website: [URL] (accessed [Date])"` |
| RFC/Spec | Number, Year | `"[Type] [Number], [Org] ([Year])"` |

### Implementierung
- **Hook-Typ:** `type: command` (PreToolUse, matcher: `add_memory`)
- **Script:** Python, validiert episode_body + source_description
- **LLM-Call:** Erkennt Dokumenttyp, prüft Vollständigkeit
- **Templates:** Als Concept-Nodes in Graphiti speichern

### Dateien
- `hooks/pre-tool-use/citation-validator.py` - Hook-Script
- `hooks/pre-tool-use/citation-templates.md` - Template-Definitionen
- Graphiti: `Concept: Citation Templates` Node

---

## Skill 3: Proaktive Learning-Erkennung

### Problem
User muss `/graphiti:learn` rufen - Claude erkennt nicht selbst wann Learnings entstehen.

### Lösung
```
PostToolUse (nach jedem Tool) → Hook analysiert Ergebnis
                                        ↓
                    LLM: "Enthält das ein Learning?"
                    - Fehler gelöst?
                    - Neues Pattern entdeckt?
                    - Workaround gefunden?
                    - Gotcha identifiziert?
                                        ↓
                    JA: systemMessage "💡 Das solltest du speichern: [Learning]"
                    NEIN: continue: true (still)
```

### Trigger-Situationen
- Fehler → Lösung gefunden
- 3+ Versuche → endlich funktioniert
- User-Korrektur → "Ah, so geht das"
- Externes Wissen → ins Projekt angewendet

### Implementierung
- **Hook-Typ:** `type: command` (PostToolUse)
- **Script:** Python, analysiert Tool-Result + Transcript-Kontext
- **LLM-Call:** Erkennt Learnings
- **Output:** Vorschlag was zu speichern (Indirect Steering)

### Dateien
- `hooks/post-tool-use/learning-detector.py` - Hook-Script
- `hooks/post-tool-use/learning-patterns.md` - Was ist ein Learning?

---

# Implementierungsplan

## Phase 1: Infrastruktur
- [ ] CLIProxyAPI-Wrapper für Hooks erstellen (Python-Modul)
- [ ] Basis-Template für `type: command` + LLM-Call
- [ ] Test-Framework für neue Hooks

## Phase 2: Skill 1 (Raten-Erkennung)
- [ ] guess-detector.py implementieren
- [ ] Prompt für "Hat Claude geraten?" entwickeln
- [ ] Testen mit echten Sessions
- [ ] A/B: Zusammenspiel mit graphiti-first-guard beobachten

## Phase 3: Skill 2 (Citation-Validierung)
- [ ] citation-validator.py implementieren
- [ ] Templates in Graphiti speichern
- [ ] LLM-Prompt für Dokumenttyp-Erkennung
- [ ] A/B: Zusammenspiel mit graphiti-guard beobachten

## Phase 4: Skill 3 (Learning-Erkennung)
- [ ] learning-detector.py implementieren
- [ ] Learning-Pattern-Definition
- [ ] Testen mit echten Sessions
- [ ] Feintuning: Wann vorschlagen, wann still bleiben?

## Phase 5: Evaluation
- [ ] Wie oft triggern alte Guards noch?
- [ ] Sind die LLM-Calls zuverlässig?
- [ ] Performance-Impact messen
- [ ] User-Feedback einholen

---

# Technische Details

## CLIProxyAPI-Wrapper
```python
# hooks/lib/llm_client.py
import requests
import subprocess
import json

def call_llm(prompt: str, transcript_path: str = None) -> str:
    """Call LLM via CLIProxyAPI for hook evaluation."""
    # 1. Get API key from 1Password
    api_key = subprocess.run(
        ["op", "read", "op://Marakanda GmbH/CLIProxyAPI - Marakanda/credential"],
        capture_output=True, text=True
    ).stdout.strip()

    # 2. Read transcript if provided
    context = ""
    if transcript_path:
        with open(transcript_path) as f:
            context = f.read()

    # 3. Call API
    response = requests.post(
        "https://claude.marakanda.biz/v1/messages",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 1000,
            "messages": [{"role": "user", "content": f"{prompt}\n\nContext:\n{context}"}]
        }
    )
    return response.json()["content"][0]["text"]
```

## Hook-Output Format
```python
# Stop Hook (guess-detector)
{
    "decision": "block",  # oder "approve"
    "reason": "Claude hat 3 Fakten behauptet ohne Recherche",
    "systemMessage": "⚠️ Bitte erst recherchieren: [Details]"
}

# PreToolUse Hook (citation-validator)
{
    "hookSpecificOutput": {
        "permissionDecision": "deny",  # oder "allow"
    },
    "systemMessage": "📚 Fehlende Felder für Buch: Author, Year"
}

# PostToolUse Hook (learning-detector)
{
    "continue": true,
    "systemMessage": "💡 Das könnte ein Learning sein: [Vorschlag]"
}
```

---

---

# Offene Fragen (geklärt)

## 1. Kann der Installer weg?

**JA** - bei Umstellung auf Plugin-Struktur:

| Installer-Funktion | Plugin-Alternative |
|--------------------|-------------------|
| Hierarchie-Prüfung | Claude Code merged automatisch |
| settings.json konfigurieren | hooks/hooks.json |
| Hooks kopieren | Plugin-Verzeichnis |
| Rules kopieren | skills/*/SKILL.md |
| Commands kopieren | commands/*.md |

**Migration:**
1. taming-stan als Plugin umbauen
2. `npx taming-stan install` → `claude plugins install taming-stan`
3. Installer-Code kann weg (oder nur für Legacy-Support behalten)

## 2. Integration mit bestehendem taming-stan

**Strategie:** Parallel-Betrieb während Migration

```
taming-stan/                    # Aktuell
├── bin/cli.js                  # Installer (wird obsolet)
├── hooks/                      # Hook-Scripts (bleiben)
├── rules/                      # → skills/*/SKILL.md
├── commands/                   # → commands/
└── lib/                        # → scripts/lib/

graphiti-skills/                # Neu (als Plugin)
├── .claude-plugin/plugin.json
├── hooks/hooks.json            # Nutzt Scripts aus taming-stan
├── skills/
├── commands/
└── scripts/
```

**Phase 1:** Plugin neben Installer (beide funktionieren)
**Phase 2:** Installer deprecated
**Phase 3:** Nur noch Plugin

## 3. A/B-Test: Wann alte Guards deaktivieren?

**Metriken:**
- Wie oft triggert alter Guard?
- Wie oft triggert neuer intelligenter Hook?
- False Positives/Negatives?

**Kriterien für Deaktivierung:**
- Neuer Hook fängt >90% der Fälle
- Keine kritischen False Negatives
- User-Feedback positiv

**Implementierung:**
```python
# In alten Guards: Logging hinzufügen
log_guard_trigger("graphiti-first-guard", {
    "reason": "WebSearch before Graphiti",
    "would_new_hook_catch": check_new_hook_coverage()
})
```

## 4. Test-Framework für neue Hooks

**Unit Tests:**
```python
# tests/test_guess_detector.py
def test_detects_guessing():
    transcript = load_fixture("guessing_session.jsonl")
    result = guess_detector.analyze(transcript)
    assert result["decision"] == "block"
    assert "recherchieren" in result["systemMessage"]
```

**Integration Tests:**
```bash
# Mit echtem LLM-Call (via CLIProxyAPI)
./scripts/test-hook.sh guess-detector fixtures/guessing.jsonl
```

**E2E Tests:**
```bash
# Plugin installieren, Session starten, Verhalten prüfen
claude plugins install ./graphiti-skills
# Manuelles Testen oder Playwright für UI
```

---

# Vollständige Hook-Inventur

## Bestehende Hooks (15 Dateien)

### SessionStart (2 Hooks)
| Hook | Datei | Funktion | Status in neuer Welt |
|------|-------|----------|---------------------|
| graphiti-context-loader | `session-start/graphiti-context-loader.py` | Erkennt project_group_id, setzt `graphiti_available` | **BLEIBT** - Basis für alle anderen |
| reset-session-flags | `session-start/reset-session-flags.py` | Reset Session-Flags bei neuer Session | **BLEIBT** - Unverändert |

### UserPromptSubmit (2 Hooks)
| Hook | Datei | Funktion | Status in neuer Welt |
|------|-------|----------|---------------------|
| session-reminder | `user-prompt-submit/session-reminder.py` | Zeigt project_group_id Kontext | **BLEIBT** - Unverändert |
| graphiti-knowledge-reminder | `user-prompt-submit/graphiti-knowledge-reminder.py` | Erinnert an Graphiti-Suche | **BLEIBT** - Unverändert |

### PreToolUse (8 Hooks)
| Hook | Datei | Funktion | Status in neuer Welt |
|------|-------|----------|---------------------|
| graphiti-first-guard | `pre-tool-use/graphiti-first-guard.py` | Blockt Research-Tools bis Graphiti gesucht | **PARALLEL** mit guess-detector |
| graphiti-guard | `pre-tool-use/graphiti-guard.py` | Validiert add_memory (352 Zeilen!) | **ERWEITERT** mit citation-validator |
| firecrawl-guard | `pre-tool-use/firecrawl-guard.py` | Firecrawl > WebSearch | **BLEIBT** - Unverändert |
| context7-guard | `pre-tool-use/context7-guard.py` | Trackt Context7 Usage | **BLEIBT** - Unverändert |
| git-workflow-guard | `pre-tool-use/git-workflow-guard.py` | Commit-Format, Branch-Protection | **BLEIBT** - Unverändert |
| file-context-tracker | `pre-tool-use/file-context-tracker.py` | Trackt active_group_ids | **BLEIBT** - Unverändert |
| playwright-guard | `pre-tool-use/playwright-guard.py` | MCP > CLI, headless enforcement | **BLEIBT** - Unverändert |
| agent-browser-guard | `pre-tool-use/agent-browser-guard.py` | Nur agent-browser erlaubt | **BLEIBT** - Unverändert |

### PostToolUse (1 Hook)
| Hook | Datei | Funktion | Status in neuer Welt |
|------|-------|----------|---------------------|
| graphiti-retry-guard | `post-tool-use/graphiti-retry-guard.py` | 3-Strikes Pattern | **PARALLEL** mit learning-detector |

### Stop (0 Hooks → 1 NEU)
| Hook | Datei | Funktion | Status |
|------|-------|----------|--------|
| guess-detector | `stop/guess-detector.py` | Erkennt Raten vor Antwort | **NEU** |

---

## Änderungsübersicht

### NEU (3 intelligente Hooks)

| Hook | Event | Was macht er? | Ersetzt |
|------|-------|---------------|---------|
| **guess-detector** | Stop | LLM analysiert: "Hat Claude geraten?" | Ergänzt graphiti-first-guard |
| **citation-validator** | PreToolUse (add_memory) | LLM erkennt Dokumenttyp + prüft Vollständigkeit | Ergänzt graphiti-guard |
| **learning-detector** | PostToolUse | LLM erkennt Learnings, schlägt Speichern vor | Ergänzt graphiti-retry-guard |

### ERWEITERT (2 bestehende Hooks)

| Hook | Was ändert sich? |
|------|------------------|
| **graphiti-guard** | Ruft citation-validator für LLM-basierte Prüfung auf (wenn aktiviert) |
| **graphiti-retry-guard** | Ruft learning-detector für LLM-basierte Erkennung auf (wenn aktiviert) |

### UNVERÄNDERT (10 Hooks)

Alle anderen Hooks bleiben exakt gleich:
- graphiti-context-loader, reset-session-flags
- session-reminder, graphiti-knowledge-reminder
- graphiti-first-guard, firecrawl-guard, context7-guard
- git-workflow-guard, file-context-tracker
- playwright-guard, agent-browser-guard

---

## Parallel-Betrieb: Alt + Neu

**JA, alte und neue Hooks arbeiten parallel!**

### Warum funktioniert das?

1. **Gemeinsamer Session-State**
   - Beide nutzen `/tmp/claude-session-{cwd-hash}.json`
   - `session_state.py` bleibt unverändert
   - Neue Hooks lesen/schreiben dieselben Flags

2. **Hook-Reihenfolge**
   ```
   [HARTER GUARD - schnell, deterministisch]
        ↓
   graphiti-first-guard blockt WebSearch
        ↓
   [INTELLIGENTER HOOK - langsamer, LLM-basiert]
        ↓
   guess-detector analysiert Antwort
   ```

3. **A/B-Test Logik**
   ```python
   # Im alten Guard: Logging für Vergleich
   if would_block:
       log_guard_trigger("graphiti-first-guard", reason)
       # Neuer Hook hätte das auch gefangen?
       if check_intelligent_hook_coverage():
           metrics["overlap"] += 1
   ```

### Beispiel-Flow mit beiden aktiv

```
User fragt: "Was kostet React?"

1. graphiti-first-guard (PreToolUse)
   → Prüft: Will Claude WebSearch nutzen?
   → Ja → Prüft: graphiti_searched?
   → Nein → BLOCK: "Erst Graphiti!"

2. Claude sucht in Graphiti
   → graphiti_searched = true

3. Claude will antworten
   → guess-detector (Stop)
   → LLM analysiert Transcript
   → "Hat Claude Fakten behauptet ohne Quelle?"
   → Ja → BLOCK: "Erst recherchieren!"
   → Nein → Antwort geht durch
```

**Vorteil:** Doppelte Absicherung während Übergangsphase!

---

## Prompt-Personalisierung (ohne Python)

**JA, Prompts sind externalisiert und anpassbar!**

### Struktur

```
scripts/
├── prompts/
│   ├── guess-detector.md      # ← User kann anpassen
│   ├── citation-validator.md  # ← User kann anpassen
│   └── learning-detector.md   # ← User kann anpassen
├── lib/
│   └── llm_client.py
└── guess-detector.py          # Lädt prompt aus .md Datei
```

### Beispiel: guess-detector.md

```markdown
# Raten-Erkennung Prompt

Du analysierst einen Claude-Transcript auf Anzeichen von Raten.

## Kriterien für "Raten"

1. **Fakten ohne Recherche**
   - Behauptung über Preise, Daten, Zahlen
   - Ohne vorherigen search_nodes() oder WebSearch Call

2. **Unsichere Formulierungen**
   - "Ich glaube...", "Wahrscheinlich...", "Meistens..."
   - Wenn sie als Fakten präsentiert werden

3. **Technische Details ohne Quelle**
   - API-Endpoints, Konfigurationen, Versionen
   - Ohne Dokumentations-Lookup

## Output

Antworte NUR mit einem JSON-Objekt:
- `is_guessing: true/false`
- `evidence: string[]` - Konkrete Beispiele
- `suggestion: string` - Was sollte recherchiert werden?

## Ausnahmen (KEIN Raten)

- Allgemeinwissen ("JavaScript ist eine Programmiersprache")
- Logische Schlussfolgerungen aus gezeigtem Code
- Explizit als Meinung markiert ("Ich würde empfehlen...")
```

### Python lädt Prompt

```python
# guess-detector.py
def load_prompt():
    prompt_path = Path(__file__).parent / "prompts" / "guess-detector.md"
    if prompt_path.exists():
        return prompt_path.read_text()
    return DEFAULT_PROMPT  # Fallback
```

### User-Anpassung

User kann `prompts/guess-detector.md` editieren ohne Python anzufassen:

```markdown
# Meine angepasste Raten-Erkennung

## Zusätzliche Kriterien (meine Regeln)

4. **Bibelverse ohne Quelle**
   - Zitate aus der Bibel müssen Kapitel:Vers haben

5. **Musik-Fakten**
   - Alben/Songs ohne Year sind verdächtig
```

---

## Citation Templates (Recherche-Ergebnis)

### Akademische Standards (Universal)

Basierend auf APA, MLA, Chicago, Harvard, IEEE und BibTeX:

| Dokumenttyp | KRITISCH (immer) | HOCH (empfohlen) | OPTIONAL |
|-------------|------------------|------------------|----------|
| **Book** | Author, Title, Year, Publisher | ISBN, Edition | Place, Language |
| **Article** | Author, Title, Journal, Year, DOI | Volume, Issue, Pages | Accessed Date |
| **Website** | Author/Org, Title, URL, Accessed Date | Publication Date | Last Modified |
| **Conference** | Author, Title, Conference, Year, Location | Pages, DOI | Proceedings |
| **RFC/Report** | Author, Title, Number, Year, Org | DOI/URL | Type |
| **Bible** | Book, Chapter:Verse | Translation | - |

**Schlüsselerkenntnis:** DOI > URL (permanent, stabil, style-übergreifend)

### Graphiti-Felder

Graphiti `add_memory()` hat:
- `name` (required) - Episoden-Titel
- `episode_body` (required) - Inhalt
- `source_description` (optional aber empfohlen) - Quellenangabe
- `group_id` (optional) - Kontext-Gruppe
- `source` (optional) - "text" | "json" | "message"

**Entity Types (custom in graphiti.md):**
- Document: Zitierbare Quellen (Bücher, Artikel, RFCs)
- Work: Kreative Werke (Songs, Filme, Romane)
- Revision: Software-Versionen (React 18, Python 3.11)

### Template-Struktur für Skill

```
skills/citation-templates/
├── SKILL.md                    # Metadata + Wann aktivieren
└── templates/
    ├── book.md                 # Buch-Template
    ├── article.md              # Journal-Artikel
    ├── website.md              # Webseite
    ├── conference.md           # Konferenz-Paper
    ├── rfc.md                  # RFC/Technical Report
    ├── bible.md                # Bibelverse
    ├── music.md                # Songs/Alben (Work)
    └── software.md             # Software-Versionen (Revision)
```

### Beispiel-Template: book.md

```markdown
# Book Citation Template

## Entity Type
Document

## Pflichtfelder
- **author**: Vor- und Nachname(n), bei mehreren mit "and" trennen
- **title**: Vollständiger Buchtitel
- **year**: Erscheinungsjahr (4 Ziffern)
- **publisher**: Verlagsname

## Empfohlene Felder
- **isbn**: ISBN-10 oder ISBN-13
- **edition**: Nur wenn nicht 1. Auflage (z.B. "2nd ed.")
- **doi**: Falls vorhanden (bevorzugt über URL)

## source_description Format
```
Book: [Author] '[Title]' ([Year])
```

## Beispiele

### Minimal (valide)
```
name: "Clean Code Buch"
episode_body: "Robert C. Martin beschreibt in 'Clean Code' Prinzipien für sauberen Code."
source_description: "Book: Robert C. Martin 'Clean Code' (2008)"
```

### Vollständig
```
name: "Clean Code - Agile Software Craftsmanship"
episode_body: "Robert C. Martin beschreibt in 'Clean Code: A Handbook of Agile Software Craftsmanship' Prinzipien..."
source_description: "Book: Robert C. Martin 'Clean Code: A Handbook of Agile Software Craftsmanship' (2008), Pearson, ISBN 978-0132350884"
```

## Validierungsregeln
- [ ] Author enthält mindestens Vor- ODER Nachname
- [ ] Title ist nicht leer und nicht nur Zahlen
- [ ] Year ist 4-stellige Zahl zwischen 1000 und aktuelles Jahr
- [ ] Publisher ist nicht leer (bei physischen Büchern)
```

### Beispiel-Template: software.md (Revision)

```markdown
# Software Version Template

## Entity Type
Revision

## Pflichtfelder
- **name**: Tool/Library/Framework Name
- **version**: Versionsnummer (semantic oder Jahr)

## Empfohlene Felder
- **context**: Was wurde mit dieser Version gelernt/gemacht

## source_description Format
```
[Name] [Version]: [Kontext]
```

## Beispiele

### Technisches Learning
```
name: "Claude Code 2.1.19: hookEventName Pflichtfeld"
episode_body: "In Claude Code 2.1.19 ist hookEventName ein Pflichtfeld für PreToolUse Hooks. Ohne dieses Feld wird der Hook ignoriert."
source_description: "Eigene Erfahrung mit Claude Code 2.1.19 (2026-01-24)"
```

## Validierungsregeln
- [ ] Name enthält bekanntes Tool/Library/Framework
- [ ] Version folgt Pattern: v?\d+(\.\d+)* oder (2\d{3})
- [ ] Bei Learning: Kontext erklärt das Problem/die Lösung
```

---

## Zusammenfassung: Architektur

```
┌─────────────────────────────────────────────────────────┐
│                    USER ANPASSBAR                        │
├─────────────────────────────────────────────────────────┤
│  prompts/              │  criteria/                      │
│  ├── guess-detector.md │  ├── citation-rules.yaml       │
│  ├── citation-*.md     │  ├── learning-patterns.yaml    │
│  └── learning-*.md     │  └── guess-exceptions.yaml     │
├─────────────────────────────────────────────────────────┤
│                    PYTHON (nicht anpassen)               │
├─────────────────────────────────────────────────────────┤
│  lib/                  │  hooks/                         │
│  ├── llm_client.py     │  ├── guess-detector.py         │
│  └── session_state.py  │  ├── citation-validator.py     │
│                        │  └── learning-detector.py       │
├─────────────────────────────────────────────────────────┤
│                    SESSION STATE                         │
├─────────────────────────────────────────────────────────┤
│  /tmp/claude-session-{hash}.json                        │
│  - graphiti_searched, firecrawl_attempted, etc.         │
│  - Gemeinsam genutzt von ALT + NEU                      │
└─────────────────────────────────────────────────────────┘
```

---

# Abgeschlossene Tasks (Recherche)

| # | Task | Status |
|---|------|--------|
| 1 | type:prompt vs type:command Vergleich | ✅ done |
| 2 | $TRANSCRIPT_PATH funktioniert | ✅ done |
| 3 | Hook-Events recherchiert | ✅ done |
| 4 | Stop Hook für Selbstkorrektur identifiziert | ✅ done |
| 5 | Experiment-Dateien committed | ✅ done |
| 6 | Hooks + Skills Zusammenspiel erklärt | ✅ done |
| 7 | Progressive Disclosure / Kontextverbrauch | ✅ done |
| 8 | Installer → Plugin Migration | ✅ done |
| 9 | Vollständige Hook-Inventur | ✅ done |
| 10 | Parallel-Betrieb Alt+Neu erklärt | ✅ done |
| 11 | Prompt-Personalisierung ohne Python | ✅ done |
| 12 | Feste Regeln via Criteria-Dateien | ✅ done |
| 13 | Akademische Zitierstandards recherchiert | ✅ done |
| 14 | Graphiti Best Practices recherchiert | ✅ done |

---

# IMPLEMENTIERUNGSPLAN

## Ziel
Erstelle `taming-stan` als Claude Code Plugin mit:
- graphiti.md als Skill (nicht mehr Rule)
- Citation Templates
- Alle bestehenden Hooks (ohne neue LLM-Hooks vorerst)
- Optional aktivierbare Services

## Plugin-Struktur

```
/Volumes/DATEN/Coding/taming-stan/
├── .claude-plugin/
│   └── plugin.json              # NEU: Plugin-Manifest
├── skills/
│   ├── graphiti/
│   │   ├── SKILL.md             # NEU: graphiti.md als Skill
│   │   └── entity-types.md      # NEU: Entity-Type Referenz
│   └── citation-templates/
│       ├── SKILL.md             # NEU: Wann Templates nutzen
│       └── templates/
│           ├── book.md          # NEU
│           ├── article.md       # NEU
│           ├── website.md       # NEU
│           ├── conference.md    # NEU
│           ├── rfc.md           # NEU
│           ├── bible.md         # NEU
│           ├── music.md         # NEU
│           └── software.md      # NEU
├── hooks/
│   └── hooks.json               # NEU: Konsolidierte Hook-Config
├── scripts/
│   ├── lib/
│   │   ├── session_state.py     # MOVE von lib/
│   │   └── secret_patterns.py   # MOVE von hooks/lib/
│   ├── prompts/                 # NEU: Für spätere LLM-Hooks
│   └── [alle .py Hooks]         # MOVE von hooks/*/
├── commands/                    # BLEIBT
├── rules/                       # ENTFERNT (→ skills)
└── lib/                         # ENTFERNT (→ scripts/lib)
```

## Implementierungs-Schritte

### Phase 1: Plugin-Grundstruktur
1. `.claude-plugin/plugin.json` erstellen
2. `hooks/hooks.json` erstellen (alle Events konsolidiert)
3. `scripts/lib/` Verzeichnis mit session_state.py, secret_patterns.py

### Phase 2: Skills erstellen
4. `skills/graphiti/SKILL.md` - graphiti.md migrieren
5. `skills/graphiti/entity-types.md` - Entity-Type Referenz
6. `skills/citation-templates/SKILL.md` - Wann Templates nutzen
7. `skills/citation-templates/templates/*.md` - 8 Templates

### Phase 3: Hooks migrieren
8. Alle Python-Hooks nach `scripts/` verschieben
9. Pfade in hooks.json anpassen (${CLAUDE_PLUGIN_ROOT})
10. Testen dass alle Hooks funktionieren

### Phase 4: Aufräumen
11. Alte `rules/` Verzeichnisstruktur entfernen
12. Alte `lib/` nach `scripts/lib/` konsolidieren
13. CLAUDE.md aktualisieren (Plugin-Hinweis)

## Kritische Dateien

| Datei | Aktion | Priorität |
|-------|--------|-----------|
| `.claude-plugin/plugin.json` | CREATE | 1 |
| `hooks/hooks.json` | CREATE | 1 |
| `skills/graphiti/SKILL.md` | CREATE (migrate from rules) | 2 |
| `skills/citation-templates/SKILL.md` | CREATE | 2 |
| `skills/citation-templates/templates/*.md` | CREATE (8 files) | 2 |
| `scripts/lib/session_state.py` | MOVE | 3 |
| `scripts/*.py` | MOVE (alle Hooks) | 3 |

## Verifikation

### Nach Plugin-Erstellung
```bash
# Plugin-Struktur prüfen
ls -la .claude-plugin/
cat .claude-plugin/plugin.json

# Skills prüfen
ls -la skills/
cat skills/graphiti/SKILL.md | head -20

# Hooks prüfen
cat hooks/hooks.json | jq '.hooks | keys'
```

### Plugin-Installation testen
```bash
# In einem ANDEREN Verzeichnis:
cd /tmp
mkdir test-project && cd test-project
git init
claude plugins install /Volumes/DATEN/Coding/taming-stan

# Prüfen ob Hooks greifen
claude
# → SessionStart Hook sollte feuern
# → graphiti-context-loader sollte project_group_id erkennen
```

### Skill-Aktivierung testen
```
# In Claude Code Session:
"Speichere dass Clean Code ein gutes Buch ist"
# → citation-templates Skill sollte aktivieren
# → Template-Validierung sollte greifen
```

---

# FINALE ERKENNTNISSE (2026-01-25)

## Das fundamentale Dilemma

| Ansatz | Kann blocken? | Intelligent (LLM)? | Ohne API-Key? |
|--------|---------------|-------------------|---------------|
| type:prompt | ❌ NEIN | ✅ JA | ✅ JA |
| type:command + LLM | ✅ JA | ✅ JA | ❌ NEIN |
| Hookify/Regex | ✅ JA | ❌ NEIN | ✅ JA |
| Python Guards | ✅ JA | ❌ NEIN | ✅ JA |

**Es gibt KEINE Lösung die alle drei Eigenschaften hat.**

## Experiment 5: type:prompt - Detailliertes Ergebnis

**Test:** "Speichere dass Clean Code ein gutes Buch ist" (ohne Rules, ohne graphiti-guard.py)

**Was passierte:**
1. Claude rief direkt `add_memory` auf mit `source_description: "Persönliche Bewertung"`
2. type:prompt Hook FEUERTE und erkannte: "unvollständig, fehlt Datum"
3. ABER: Der Call ging trotzdem durch! Episode wurde gespeichert.

**Beweis:**
```
PreToolUse:mcp__mcp-funnel__bridge_tool_request hook stopped continuation:
source_description 'Persönliche Bewertung' ist unvollständig...

"result": {"message": "Episode 'Buchbewertung: Clean Code' queued for processing"}
```

**Fazit:** type:prompt Hooks sind **beratend**, nicht **durchsetzend**.

## Warum Claude gegen Hooks kämpft

**Beobachtung:** Bei "dummen" Blocks (z.B. "Was kostet die Welt?" → BLOCK) argumentiert Claude gegen den Hook.

**Hypothese:** Claude würde intelligenten Hooks eher gehorchen.

**Problem:** Intelligente Hooks brauchen LLM → brauchen API-Key → nicht für alle nutzbar.

## Der tote Traum

**Vision war:** Intelligente Hooks die sich selbst prüfen, für alle nutzbar.

**Realität:**
- Für **öffentliches Plugin** (ohne API-Key): Nur dumme Regex/Python Guards
- Für **Power-User** (mit API-Key): Intelligente LLM-Hooks möglich

**Hoffnung:** Anthropic erweitert type:prompt mit echtem Blocking-Support.

## Was funktioniert (für alle)

1. **Skills/Rules im Kontext** - Claude liest sie und befolgt sie (meistens)
2. **Python Guards mit `decision: block`** - Echtes Blocking
3. **Hookify mit `action: block`** - Einfache Regex-Regeln
4. **plan.md als "Gehirn"** - Claude liest es und versteht Kontext

## Was NICHT funktioniert

1. **type:prompt für Blocking** - Kann nur warnen
2. **systemMessage-Anweisungen** - Claude ignoriert sie oft
3. **Hook sagt "spawne Subagent"** - Claude tut es nicht

## Hookify als Alternative

Entdeckt während der Session: Hookify Plugin kann:
- Regeln aus Markdown-Dateien laden
- `action: block` für echtes Blocking
- Sofort aktiv ohne Neustart
- Aber: Nur Regex, keine LLM-Intelligenz

## Offene Punkte für später

- [ ] guess-detector (Stop Hook mit LLM) - **Braucht API-Key**
- [ ] citation-validator (PreToolUse mit LLM) - **Braucht API-Key**
- [ ] learning-detector (PostToolUse mit LLM) - **Braucht API-Key**
- [ ] Hookify für einfache Guards evaluieren
- [ ] Warten auf Anthropic type:prompt Erweiterungen
- [ ] Firecrawl-Guards als optionaler Service
- [ ] Context7-Guards als optionaler Service
