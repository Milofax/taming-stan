#PITH:1.2
#CMD:graphiti/end-project|Projekt abschließen+Learnings promoten

!zweck:Learnings aus Projekt-Kontext nach main promoten
!trigger:User sagt "Projekt fertig"|"Projekt abschließen"|"Ende Projekt"
!prinzip:Wissen NIEMALS löschen→Zettelkasten

## workflow

### 1_projekt_erkennen
aktion:group_id aus Kontext ermitteln(.graphiti-group|CLAUDE.md|Git Root)
ausgabe:"Projekt: [name], group_id: [id]"
bestätigung:"Ist das das richtige Projekt?"→User bestätigt

### 2_learnings_reviewen
aktion:graphiti__search_nodes(query="",group_ids=["[project-id]"],entity_types=["Learning","Decision"])
ausgabe:Liste aller Learnings+Decisions im Projekt
frage:"Welche davon sind übergreifend relevant und sollen nach `main` promoted werden?"

### 3_learnings_promoten
für_jedes_ausgewählte:
  |original:graphiti__search_memory_facts(query="[learning]",group_ids=["[project-id]"])
  |kopieren:graphiti__add_memory(name="[learning]",episode_body="[details]",source_description="Promoted aus Projekt [name]",group_id="main")
ausgabe:"[N] Learnings nach main promoted"

### 4_abschluss
ausgabe:
  |promoted:"[N] Learnings/Decisions nach main übernommen"
  |hinweis:"Projekt-Wissen bleibt in [project-id] erhalten"
  |hinweis:"Persönliches Wissen in `main` bleibt unberührt"

## anti_patterns
!!nie:clear_graph→Wissen löschen widerspricht Zettelkasten
!nie:Automatisches Promoten ohne User-Bestätigung

## beispiel_dialog
user:"/graphiti:end-project"
claude:"Projekt erkannt: INFRASTRUCTURE (group_id: Milofax-infrastructure). Korrekt?"
user:"ja"
claude:"Gefundene Learnings/Decisions: [Liste]. Welche nach main promoten?"
user:"1, 3, 5"
claude:"3 Learnings nach main promoted. Projekt-Wissen bleibt in Milofax-infrastructure erhalten."
