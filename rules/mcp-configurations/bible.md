#PITH:1.2
#MCP:bible|stand:2026-01

!!erst:Bei Bibelzitaten/Passagen→IMMER mcp-bible nutzen
  |trigger:"Bibel"|"Vers"|"Passage"|"Kapitel"|Buchnamen(Johannes,Matthäus,Römer,etc.)
  |workflow:discover_tools_by_words("bible",enable=true)→get_passage(passage,version)
  |verstoß:Zitieren aus Gedächtnis→potentiell falsch→Vertrauen zerstört
  |warnsignal:Bibelvers-Gedanke ohne get_passage=STOP→erst Tool nutzen

!zuständig:Bibelpassagen|13 Übersetzungen(8 EN + 5 DE)|Multiple Passagen mit Semikolon
!nicht_zuständig:Bibelkommentare|Theologische Auslegung|Historischer Kontext
!aktivierung:discover_tools_by_words("bible",enable=true)

## tools
get_passage:passage+version→Bibeltext abrufen

## versionen
english:ESV(wörtlich)|NIV(dynamisch)|KJV(klassisch)|NASB|NKJV|NLT|AMP|MSG
german:SCH2000(modern,genau)|HOF(verständlich)|LUTH1545(historisch)|NGU-DE|SCH1951

## version_auswahl
!standard_de:SCH2000(empfohlen)|HOF(einfacher)
!standard_en:ESV(empfohlen)|NIV(zugänglich)
!user_sprache:User schreibt Deutsch→deutsche Version|User schreibt Englisch→englische Version

## workflow
deutsch:get_passage("Johannes 3:16","SCH2000")
english:get_passage("John 3:16","ESV")
multiple:get_passage("Johannes 3:16; Römer 8:28","SCH2000")
bereich:get_passage("Psalm 23:1-6","SCH2000")

## passage_format
einzelvers:"Buch Kapitel:Vers"→"Johannes 3:16"
bereich:"Buch Kapitel:Vers-Vers"→"Psalm 23:1-6"
mehrere:"Passage1; Passage2"→"Johannes 3:16; Römer 8:28"
kapitel:"Buch Kapitel"→"Psalm 23"

## fehler
nicht_gefunden→Schreibweise prüfen(deutsch vs englisch)|Version prüfen
timeout→erneut versuchen|kleinere Passage
