# Playwright MCP Server

> **Stand:** Januar 2026

Vollständige Referenz für den Playwright MCP Server - Browser-Automatisierung und Web-Testing.

## MCP-Funnel Aktivierung

```
discover_tools_by_words("playwright", enable=true)
```

## Überblick

Der Playwright MCP Server ermöglicht Browser-Automatisierung direkt aus dem LLM-Kontext. Er nutzt Microsoft Playwright für zuverlässige Cross-Browser-Automation von Chromium, Firefox und WebKit.

## Verfügbare Tools

| Tool | Beschreibung |
|------|-------------|
| `playwright_navigate` | Zu einer URL navigieren |
| `playwright_screenshot` | Screenshot der aktuellen Seite |
| `playwright_click` | Element anklicken |
| `playwright_fill` | Formularfeld ausfüllen |
| `playwright_select` | Dropdown-Wert auswählen |
| `playwright_hover` | Über Element hovern |
| `playwright_evaluate` | JavaScript im Browser ausführen |
| `playwright_get_text` | Text eines Elements extrahieren |
| `playwright_get_attribute` | Attribut eines Elements abrufen |
| `playwright_wait_for_selector` | Auf Element warten |
| `playwright_press` | Taste drücken |
| `playwright_scroll` | Seite scrollen |
| `playwright_close` | Browser-Session schließen |

## Kernkonzepte

### Selektoren

Playwright unterstützt verschiedene Selektor-Strategien:

```
CSS:           button.submit
XPath:         //button[@type='submit']
Text:          text=Submit
Role:          role=button[name='Submit']
Test ID:       [data-testid='submit-btn']
```

**Best Practice:** Priorität in dieser Reihenfolge:
1. `data-testid` - Stabilste Option
2. `role` - Accessibility-basiert
3. `text` - User-sichtbarer Text
4. CSS - Wenn nichts anderes funktioniert

### Browser-Kontext

- **Persistent Session** - Browser bleibt zwischen Aufrufen offen
- **Isolated Context** - Cookies/Storage bleiben erhalten
- **Headless Mode** - Standardmäßig ohne GUI

## Workflow-Beispiele

### Login-Automation

```
1. playwright_navigate
   - url: "https://app.example.com/login"

2. playwright_fill
   - selector: "[name='email']"
   - value: "user@example.com"

3. playwright_fill
   - selector: "[name='password']"
   - value: "***"

4. playwright_click
   - selector: "button[type='submit']"

5. playwright_wait_for_selector
   - selector: "[data-testid='dashboard']"
```

### Daten extrahieren

```
1. playwright_navigate (url: "https://example.com/table")

2. playwright_evaluate
   - script: "Array.from(document.querySelectorAll('tr')).map(r => r.innerText)"
   → Gibt Array aller Tabellenzeilen zurück

3. playwright_screenshot (für visuelle Verifizierung)
```

### Formular ausfüllen

```
1. playwright_navigate (url: "https://form.example.com")

2. playwright_fill (selector: "#name", value: "Max Mustermann")
3. playwright_fill (selector: "#email", value: "max@example.com")

4. playwright_select
   - selector: "#country"
   - value: "DE"

5. playwright_click (selector: "#terms-checkbox")
6. playwright_click (selector: "button[type='submit']")
```

### Screenshot-basierte Analyse

```
1. playwright_navigate (url: "https://dashboard.example.com")

2. playwright_wait_for_selector
   - selector: "[data-loaded='true']"
   - timeout: 10000

3. playwright_screenshot
   - name: "dashboard"
   - storeBase64: true
   → Screenshot als Base64-Image zurück
```

### Screenshot-Optionen

```json
{
  "name": "screenshot-name",
  "selector": "#specific-element",
  "width": 1200,
  "height": 800,
  "storeBase64": true,
  "savePng": true,
  "downloadsDir": "~/Downloads"
}
```

**Rückgabe-Formate:**
- `storeBase64: true` (default) - Screenshot als Base64-Image im Response
- `savePng: true` - Zusätzlich als PNG-Datei speichern
- Beide Optionen können kombiniert werden

## JavaScript Evaluation

Mit `playwright_evaluate` kann beliebiges JS ausgeführt werden:

```javascript
// Alle Links extrahieren
"Array.from(document.links).map(a => ({text: a.text, href: a.href}))"

// LocalStorage auslesen
"JSON.parse(localStorage.getItem('userData'))"

// Scroll-Position ermitteln
"window.scrollY"

// Custom Interaktion
"document.querySelector('.hidden-menu').classList.add('visible')"
```

## Warten auf Elemente

```json
{
  "selector": ".dynamic-content",
  "timeout": 30000,
  "state": "visible"
}
```

**States:**
- `visible` - Element sichtbar
- `hidden` - Element versteckt
- `attached` - Im DOM vorhanden
- `detached` - Aus DOM entfernt

## Tipps für robuste Automation

1. **Explizit warten** - Immer `wait_for_selector` vor Interaktionen
2. **Stabile Selektoren** - `data-testid` > `class` > `xpath`
3. **Timeouts setzen** - Realistische Werte für langsame Seiten
4. **Fehler behandeln** - Try/Catch-Logik in Workflows einbauen
5. **Screenshots für Debugging** - Bei Fehlern Screenshot machen

## Häufige Anwendungsfälle

| Use Case | Tools |
|----------|-------|
| E2E Testing | navigate, fill, click, wait, screenshot |
| Data Scraping | navigate, evaluate, get_text |
| Form Submission | fill, select, click |
| Visual Regression | screenshot |
| Session Recording | Kombination aller Tools |

## Bekannte Einschränkungen

- **Keine Datei-Uploads** - Nicht direkt unterstützt
- **CAPTCHAs** - Können nicht automatisch gelöst werden
- **2FA** - Benötigt manuelle Intervention
- **Heavy SPAs** - Können lange Ladezeiten haben

## Häufige Fehler

| Fehler | Ursache | Lösung |
|--------|---------|--------|
| Element not found | Selektor falsch oder Element nicht geladen | Selektor prüfen, wait_for_selector nutzen |
| Timeout | Seite/Element lädt zu langsam | Timeout erhöhen |
| Click intercepted | Anderes Element überlappt | Warten bis Overlay verschwindet |
| Navigation failed | URL nicht erreichbar | URL prüfen, Netzwerk checken |

## Referenzen

- [Playwright Dokumentation](https://playwright.dev/docs/intro)
- [Selectors Guide](https://playwright.dev/docs/selectors)
- [Best Practices](https://playwright.dev/docs/best-practices)
- [Execute Automation MCP](https://www.npmjs.com/package/@executeautomation/playwright-mcp-server)
