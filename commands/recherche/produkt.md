#PITH:1.2
#CMD:produkt-recherche|stand:2026-01

!zweck:Produkt/Produktkategorie mit mehreren unabhängigen Quellen recherchieren
!prinzip:Mehrere unabhängige Quellen VOR Kaufentscheidung
!prinzip:Service-Bewertungen(Trustpilot)≠Produktqualität
!kontext:Standort Salzburg/AT|EU-Versand bevorzugen

## workflow
1. kategorie_identifizieren→passende Quellen laden
2. unabhängige_tests:mind. 2-3 Quellen prüfen
3. zertifizierungen:kategorie-spezifisch prüfen
4. service_check:Trustpilot(NUR für Lieferung/Service)
5. community:Reddit,Fachforen
6. synthese:EINE klare Empfehlung(nicht "Optionen auflisten")

## quellen_allgemein_dach
stiftung_warentest:test.de|breit(Elektronik,Haushalt,Finanzen,Gesundheit)|DE|kostenpflichtig
öko_test:oekotest.de|schadstoffe,umwelt,gesundheit|DE|kostenpflichtig
vki_konsument:konsument.at|AT-pendant zu Stiftung Warentest|AT|kostenpflichtig
verbraucherzentrale:verbraucherzentrale.de|warnungen,abzocke,recht|DE|gratis

## kategorie:supplements
quellen_primär:
  stiftung_warentest:test.de|dosierung,schadstoffe,wirksamkeit|kostenpflichtig
  öko_test:oekotest.de|schadstoffe,deklaration|kostenpflichtig
  consumerlab:consumerlab.com|laboranalysen,reinheit,dosierung|$39/Jahr
  labdoor:labdoor.com|laboranalysen,rankings|gratis
quellen_sekundär:
  examine:examine.com|evidenz zu wirkstoffen(nicht marken)|gratis
  verbraucherzentrale:verbraucherzentrale.de|warnungen|gratis
zertifizierungen:NSF|USP Verified|GMP|ISO 22000|Informed Sport|LEFO(AT)
transparenz_check:COA verfügbar?|Rohstoff-Herkunft?|Third-Party-Testing?
service_check:Trustpilot(NUR lieferung/service,NICHT produktqualität)
red_flags:"proprietary blend"|keine Dosierungen|Wundermittel-Claims|nur Eigen-Zertifizierungen

## kategorie:elektronik
quellen_primär:
  stiftung_warentest:test.de|breite tests|DE|kostenpflichtig
  rtings:rtings.com|tiefe messungen(TV,monitor,kopfhörer,soundbar)|gratis
  vki_konsument:konsument.at|AT-fokus|kostenpflichtig
quellen_sekundär:
  wirecutter:nytimes.com/wirecutter|kuratierte "best of"|gratis
  chip:chip.de|DE-fokus,viele tests|gratis(mit werbung)
zertifizierungen:CE|TÜV|Energy Star
red_flags:nur Amazon-Reviews|keine Garantie|unbekannter Hersteller

## kategorie:software
quellen_primär:
  g2:g2.com|größte datenbank,verifizierte nutzer|gratis
  capterra:capterra.com|gute filter,preisvergleich|gratis
  omr_reviews:omr.com/reviews|DACH-fokus|gratis
quellen_sekundär:
  trustradius:trustradius.com|enterprise-fokus|gratis
  producthunt:producthunt.com|neue/innovative tools|gratis
  reddit:r/software,r/selfhosted,r/sysadmin|ehrliche diskussionen|gratis
zertifizierungen:SOC2|ISO 27001|GDPR-konform
red_flags:keine Preistransparenz|Lock-in|keine Trial|keine GDPR-Compliance

## kategorie:auto
quellen_primär:
  euro_ncap:euroncap.com|crashtest-standard europa|gratis
  adac:adac.de|umfassende tests,pannenstatistik|DE
  öamtc:oeamtc.at|übernimmt Euro NCAP,AT-fokus|AT
  tcs:tcs.ch|CH-fokus|CH
quellen_sekundär:
  auto_motor_sport:auto-motor-und-sport.de|fahrberichte,vergleiche
zertifizierungen:Euro NCAP Sterne(5=beste)|TÜV
red_flags:keine Euro NCAP Daten|schlechte Pannenstatistik

## kategorie:outdoor
quellen_primär:
  outdoor_gear_lab:outdoorgearlab.com|tiefe tests,side-by-side vergleiche|gratis
  stiftung_warentest:test.de|periodische tests|kostenpflichtig
quellen_sekundär:
  reddit:r/CampingGear,r/hiking,r/Ultralight,r/BuyItForLife|community erfahrungen|gratis
  bergfreunde_magazin:bergfreunde.de/magazin|kaufberatung(händler!)|gratis
achtung:REI,Bergfreunde=Händler,nicht unabhängig!
zertifizierungen:bluesign|GOTS|Fair Wear Foundation

## kategorie:lebensmittel
quellen_primär:
  öko_test:oekotest.de|schadstoffe,pestizide,mineralöl|kostenpflichtig
  stiftung_warentest:test.de|qualität,geschmack,deklaration|kostenpflichtig
quellen_sekundär:
  foodwatch:foodwatch.org|skandale aufdecken,lobbykritik|gratis
  verbraucherzentrale:verbraucherzentrale.de|mogelpackungen,täuschung|gratis
zertifizierungen:Bio(EU,Demeter,Naturland)|Fairtrade|MSC(fisch)|ASC(aquakultur)|Nutri-Score
red_flags:Health Claims ohne Beleg|"natürlich" ohne Bio-Siegel

## trustpilot_einordnung
zeigt:Lieferung|Kundenservice|Shop-Erfahrung|Retouren-Abwicklung
zeigt_NICHT:Produktqualität|Wirksamkeit|Inhaltsstoffe|Langlebigkeit
manipulation_möglich:selektive Einladungen|Fake-Reviews|gekaufte Bewertungen
schwellenwerte:<3.0=Service-Warnung|>4.5=gut|dazwischen=genauer hinschauen
wichtig:Anzahl Reviews beachten(>500 aussagekräftiger als 50)

## output_format
1. quellen_tabelle:welche Quellen wurden geprüft,was sagen sie
2. zertifizierungen:welche hat das Produkt/Hersteller
3. service_check:Trustpilot Rating+häufige Beschwerden
4. community:was sagt Reddit/Fachforen
5. synthese:EINE klare Empfehlung mit Begründung
6. quellen_links:URLs zu den verwendeten Tests/Reviews
