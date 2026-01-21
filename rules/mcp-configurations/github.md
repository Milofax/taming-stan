# GitHub MCP Server

> **Stand:** Januar 2026

Vollständige Referenz für den GitHub MCP Server - Zugriff auf GitHub-Repositories, Issues, Pull Requests und mehr.

## MCP-Funnel Aktivierung

```
discover_tools_by_words("github", enable=true)
```

## Überblick

Der offizielle GitHub MCP Server ermöglicht direkten API-Zugriff auf GitHub. Er unterstützt Repository-Management, Issue-Tracking, Pull Requests, Branches und File-Operationen.

## Verfügbare Tools

| Tool | Beschreibung |
|------|-------------|
| `github__create_or_update_file` | Datei in einem Repository erstellen/aktualisieren |
| `github__search_repositories` | Repositories durchsuchen |
| `github__create_repository` | Neues Repository erstellen |
| `github__get_file_contents` | Dateiinhalt aus Repository abrufen |
| `github__push_files` | Mehrere Dateien in einem Commit pushen |
| `github__create_issue` | Neues Issue erstellen |
| `github__create_pull_request` | Pull Request erstellen |
| `github__fork_repository` | Repository forken |
| `github__create_branch` | Neuen Branch erstellen |
| `github__list_commits` | Commits auflisten |
| `github__list_issues` | Issues auflisten |
| `github__update_issue` | Issue aktualisieren |
| `github__add_issue_comment` | Kommentar zu Issue hinzufügen |
| `github__search_code` | Code durchsuchen |
| `github__search_issues` | Issues durchsuchen |
| `github__search_users` | Benutzer durchsuchen |
| `github__get_issue` | Einzelnes Issue abrufen |
| `github__get_pull_request` | Pull Request Details abrufen |
| `github__list_pull_requests` | Pull Requests auflisten |
| `github__create_pull_request_review` | PR Review erstellen |
| `github__merge_pull_request` | PR mergen |
| `github__get_pull_request_files` | Geänderte Dateien in PR abrufen |
| `github__get_pull_request_status` | PR Status abrufen |
| `github__update_pull_request_branch` | PR Branch mit Base-Branch aktualisieren |
| `github__get_pull_request_comments` | PR Kommentare abrufen |
| `github__get_pull_request_reviews` | PR Reviews abrufen |

## Kernkonzepte

### Repository-Struktur

GitHub organisiert Code in Repositories mit:
- **Branches** - Separate Entwicklungszweige
- **Commits** - Versionierte Änderungen
- **Tags** - Markierte Versionen/Releases

### Issue/PR Workflow

```
Issue erstellt → Assigned → In Progress → PR erstellt → Review → Merged → Closed
```

### Authentifizierung

Der Server nutzt einen Personal Access Token (PAT) mit folgenden Berechtigungen:
- `repo` - Vollzugriff auf Repositories
- `read:org` - Organisations-Lesezugriff (optional)
- `gist` - Gist-Zugriff (optional)

## Beispiel-Workflows

### Repository durchsuchen und Datei lesen

```
1. github__search_repositories (query: "mcp server")
2. github__get_file_contents (owner, repo, path: "README.md")
```

### Issue erstellen und zuweisen

```
1. github__create_issue
   - owner: "username"
   - repo: "repo-name"
   - title: "Bug: XYZ funktioniert nicht"
   - body: "Beschreibung..."
   - labels: ["bug", "priority:high"]
2. github__update_issue (assignees hinzufügen)
```

### Pull Request Workflow

```
1. github__create_branch (von main)
2. github__push_files (Änderungen committen)
3. github__create_pull_request
4. github__get_pull_request_status (CI Status prüfen)
5. github__merge_pull_request
```

### Code-Suche

```
github__search_code
- query: "function authenticate language:typescript"
- Findet alle TypeScript-Dateien mit authenticate-Funktion
```

## Wichtige Parameter

### Pagination

Viele List-Operationen unterstützen:
- `per_page` - Ergebnisse pro Seite (max 100)
- `page` - Seitennummer

### Search Queries

GitHub Search Syntax:
- `language:python` - Nach Sprache filtern
- `user:username` - Nach User filtern
- `repo:owner/name` - In spezifischem Repo suchen
- `is:open` / `is:closed` - Status-Filter
- `label:bug` - Nach Label filtern
- `created:>2024-01-01` - Nach Datum filtern

## Rate Limits

- **Authenticated**: 5.000 Requests/Stunde
- **Search API**: 30 Requests/Minute
- Bei Überschreitung: 403 Forbidden mit `X-RateLimit-Reset` Header

## Tipps für optimale Nutzung

1. **Batch-Operationen nutzen** - `push_files` statt einzelner Commits
2. **Search effizient nutzen** - Präzise Queries reduzieren API-Calls
3. **Caching beachten** - GitHub cached Responses, manchmal kurze Verzögerung
4. **Branch-Schutz beachten** - Protected Branches können Merge blockieren
5. **PR-Templates nutzen** - Konsistente PR-Beschreibungen

## Häufige Fehler

| Fehler | Ursache | Lösung |
|--------|---------|--------|
| 404 Not Found | Repo/File existiert nicht oder keine Berechtigung | Berechtigungen prüfen |
| 422 Unprocessable | Ungültige Parameter | Parameter validieren |
| 409 Conflict | Merge-Konflikt oder Branch existiert bereits | Konflikte manuell lösen |
| 403 Forbidden | Rate Limit oder fehlende Permissions | Warten oder Token-Scope erweitern |

## Toolsets

Der GitHub MCP Server organisiert Tools in Toolsets:

| Toolset | Beschreibung | Default |
|---------|-------------|---------|
| `repos` | Repository-Operationen | Ja |
| `issues` | Issues und Labels | Ja |
| `pull_requests` | Pull Requests | Ja |
| `code_security` | Code/Secret Scanning, Dependabot | Nein |
| `actions` | GitHub Actions Workflows | Nein |
| `discussions` | GitHub Discussions | Nein |
| `gists` | GitHub Gists | Nein |
| `notifications` | Benachrichtigungen | Nein |
| `projects` | GitHub Projects v2 | Nein |

**Alle Toolsets aktivieren:**
```bash
--toolsets=all
```

## Zusätzliche Tools (nicht in der Basis-Doku)

| Tool | Beschreibung |
|------|-------------|
| `github__list_notifications` | Benachrichtigungen auflisten |
| `github__mark_notification_read` | Als gelesen markieren |
| `github__list_workflows` | Actions Workflows auflisten |
| `github__run_workflow` | Workflow manuell starten |
| `github__get_workflow_run_logs` | Workflow-Logs abrufen |
| `github__list_discussions` | Discussions auflisten |
| `github__create_discussion` | Discussion erstellen |

## Referenzen

- [GitHub MCP Server (offiziell)](https://github.com/github/github-mcp-server)
- [GitHub REST API](https://docs.github.com/en/rest)
- [Toolsets Dokumentation](https://github.com/github/github-mcp-server/blob/main/docs/tools.md)
