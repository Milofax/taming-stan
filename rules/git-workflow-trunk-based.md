#PITH:1.2
#RULE:git-workflow-trunk-based|stand:2026-01

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

## branching(trunk_based)
!strategie:trunk_based|main+sehr kurze branches
  |main:trunk,alle arbeiten quasi direkt darauf
  |branches:max 1-2 Tage,dann merge|NIEMALS lange branches
  |feature_flags:Unfertige Features verstecken statt auf Branch parken
  |workflow:kurzer_branch→kleine_commits→schneller_merge
!wann:Große Teams|Mature CI/CD|Feature Flags vorhanden
!voraussetzung:Gute Testabdeckung|Feature Flag System|Erfahrenes Team

## pr_workflow
!pr:branch→PR→schnelles review→merge
  |größe:<200 LOC ideal,max 400 LOC|größer→aufteilen
  |beschreibung:Was geändert,Warum,Wie testen
  |geschwindigkeit:PRs sollten innerhalb Stunden gemerged werden
!merge:rebase oder squash(lineare History)

## branch_protection
!!main_schutz:NIEMALS direct push to main
  |require_pr:Alle Änderungen via PR
  |require_review:min 1 Approval
  |require_ci:Tests müssen grün sein
  |require_up_to_date:Branch aktuell vor Merge

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
