#PITH:1.2
#RULE:git-workflow-git-flow|stand:2026-01

## versioning
!!semver:MAJOR.MINOR.PATCH|Breaking.Feature.Fix
  |MAJOR:Breaking Changes(API-Inkompatibilität,Nutzer muss Code ändern)
  |MINOR:Neue Features(rückwärtskompatibel)
  |PATCH:Bugfixes(rückwärtskompatibel)
  |0.x.x:Initial Development(instabil)
  |1.0.0:Erste stabile API
!!changelog:keepachangelog.com Format
  |sections:Added,Changed,Deprecated,Removed,Fixed,Security
  |unreleased:[Unreleased] für WIP
  |bei_release:Version+Datum+Änderungen dokumentieren

## commits
!!conventional_commits:type(scope):description
  |types:feat|fix|docs|style|refactor|perf|test|build|ci|chore
  |version_bump:feat→MINOR|fix→PATCH|feat!oder BREAKING CHANGE→MAJOR
  |beispiele:feat(auth):add OAuth login|fix(api):handle null response|docs:update README
!message:50 Zeichen Subject,Imperativ|Body:Warum nicht Was|Footer:Issue-Refs,Breaking Changes
!atomic:Ein Commit=Eine logische Änderung

## branching(git_flow)
!strategie:git_flow|main+develop+feature+release+hotfix
  |main:NUR Production-Releases,getaggt mit Version
  |develop:Integration,hier kommen Features zusammen
  |feature/*:Neue Features,von develop abzweigen,nach develop mergen
  |release/*:Release vorbereiten,von develop,nach main+develop mergen
  |hotfix/*:Notfall-Fixes für Production,von main,nach main+develop mergen
!workflow:
  |feature:develop→feature/*→develop
  |release:develop→release/*→main+develop(Tag setzen)
  |hotfix:main→hotfix/*→main+develop(Tag setzen)
!wann:Scheduled Releases(z.B. alle 2 Wochen)|Versioned Software|Mehrere Versionen gleichzeitig pflegen
!warnung:Komplex,viel Overhead|Für die meisten Projekte overkill

## pr_workflow
!pr:branch→PR→review→merge
  |größe:<200 LOC ideal,max 400 LOC|größer→aufteilen
  |beschreibung:Was geändert,Warum,Wie testen
  |ziel:feature/*→develop|release/*→main+develop|hotfix/*→main+develop
!merge:merge_commit(vollständige History erhalten)

## branch_protection
!!main_schutz:NIEMALS direct push to main
  |require_pr:Alle Änderungen via PR
  |require_review:min 1 Approval(kritisch:2+)
  |require_ci:Tests müssen grün sein
!!develop_schutz:Auch develop schützen
  |require_pr:Features via PR
  |require_review:min 1 Approval

## repo_hygiene
!pflicht:README.md,LICENSE,.gitignore
  |readme:Was,Installation,Nutzung,Lizenz
  |license:MIT für meiste Projekte|choosealicense.com
  |gitignore:Am Projektstart erstellen|gitignore.io
!optional:CONTRIBUTING.md,SECURITY.md,CODEOWNERS,.github/templates

## security
!!aktivieren:Dependabot,Secret_Scanning,Push_Protection
  |dependabot:automatische PRs für vulnerable dependencies
  |secret_scanning:erkennt Secrets in Code
  |push_protection:blockiert Push mit Secrets
!nie:Secrets committen|.env+credentials in .gitignore
