# Offene Punkte

*Stand: 11.09.2026*

Erledigtes mit Datum und Ergebnis nach unten schieben — nicht löschen.

## Wichtigste Lücke

**Die Buyer-Recherche.** Das Ansprechpartner-Verzeichnis **existiert** — Blatt
*Kontakte & Research* der [Retail-Longlist](retail-longlist.md), 142 Händler mit
Website, HQ und Supplier-Portal, dazu Tools, E-Mail-Muster und ein 8-Schritte-Plan.
Gefüllt ist es an der entscheidenden Stelle nicht: **Buyer Name 1 von 142, Buyer
E-Mail 0 von 142.** Das Sheet lässt diese Felder bewusst leer, damit sie
recherchiert werden — genau das ist nicht passiert.

Es fehlt also kein Werkzeug, sondern der terminierte Recherche-Block.

Zu entscheiden bleibt: **wo die Namen liegen** — in der Longlist, in einem CRM,
oder hier. Im Repo stehen bisher **keine externen Personennamen**; Einkäuferdaten
sind personenbezogen und blieben versioniert liegen.

## Mercedes-Lizenz (neu, 11.09.2026)

Details und Bewertung: [mercedes-lizenz.md](mercedes-lizenz.md).

- **Was darf CGT vergeben?** Umfang der Master-Lizenz — Territorien, Kategorien,
  Laufzeit — ist nicht dokumentiert. Vor der BLE zu klären.
- **Rolle von Marc und Marko** — Lizenzgeber, Mitgesellschafter, Partner?
- **Royalty-Basis** einheitlich definieren (Net Sales, was ist abzugsfähig)
- **Kategorien-Grid** statt pauschaler 10 % über alle Warengruppen
- **Leistungsschwelle für Exklusivität** im Kurzfristmodell
- **Approval-Prozess** für Designs, Muster, Verpackung
- **Verhältnis Online-Lizenz ↔ Territorial-Exklusivität**
- **Produzenten-Provision**: offenlegen oder als Leistung bepreisen?
- **BLE-Minimum**: Was muss bis 03.10. stehen, wenn der Styleguide nicht fertig wird?

## Pitch-Seiten (neu, 09.10.2026)

Das Baukastensystem steht: [`../pitch/README.md`](../pitch/README.md).

**Entschieden am 09.10.2026 (Sascha):**

- **Hosting: Vercel**, angebunden an das Repo, eigene Domain. Begründung:
  nach dem Push ist die Seite ohne weiteres Zutun live — bei drei Personen
  ohne technisches Team zählt das mehr als die Ersparnis bei eigenem
  Webspace. Die Einrichtung ist in `pitch/README.md` Schritt für Schritt
  beschrieben; sie ist **noch nicht ausgeführt** und braucht einmal ein
  Vercel-Konto.
- **Zugriff: Adresse mit Zufallsteil**, kein Passwort. Begründung: ein
  Passwort ist eine Hürde, an der Einkäufer abspringen. Der Zufallsteil
  verhindert das Durchprobieren von `/aldi-sued/`, `/lidl/`, `/netto/`.
  Wer den Link hat, kommt rein — und kann ihn weitergeben. Das ist der
  bewusst in Kauf genommene Rest.

**Damit verbunden, noch nicht geklärt:**

- **Welche Domain?** `pitch.cgt-ug.de` ist ein Vorschlag, keine
  vorhandene Adresse.
- **Vercel bekommt beim Git-Anschluss eine Kopie des gesamten Repos**,
  nicht nur der Pitch-Seiten — auch `docs/`. Das Repo bleibt privat und
  veröffentlicht wird nur `pitch/site`, aber die Dateien liegen auf
  Vercels Build-Servern. Wenn das nicht gewollt ist: zweites Repo nur
  für die Seiten, oder manuelles Hochladen.

**Weiter offen:**

- **Verbindliche CGT-Farben und ein Logo.** Im Repo steht dazu nichts. Das
  Grün in `pitch/vorlage/assets/stil.css` ist ein **Vorschlag**, keine
  belegte Hausfarbe, und die Kopfzeile trägt bisher nur den Schriftzug
  „CGT".
- **Wer gibt eine Pitch-Seite frei**, bevor sie an einen Einkäufer geht?
  Solange `status: entwurf` steht, zeigt die Seite einen roten Balken.

## Entscheidet über die Ideen ([ideen.md](ideen.md))

- **Wie verdient CGT heute?** Provision, Retainer, Marge oder Beteiligung — je Säule?
  Ohne das lässt sich nicht beurteilen, welcher Hebel wirklich etwas ändert.
- **Wem gehört die Retail-Longlist?** Sie ist für DELTEX gebaut. Darf CGT sie
  Dritten als Leistung anbieten?

## Zu CGT

- Gründungsjahr
- Vertragsmodell je Säule — Projektbasis, Retainer, Beteiligung?
- **Deltex Miloy / TK Maxx** — läuft, zweite Kollektion. Offen bleibt:
  Warengruppe und Sortiment · Zahlen zu Kollektion 1 (Menge, Marge, Nachbestellung) ·
  ist TK Maxx exklusiv oder darf Miloy auch woanders hin · welche Länder ·
  **und warum steht der einzige Wiederholungskunde mit null Themen in der Planung?**
- **Roberto** (Epsilon, „Fokus Hard Rock!!!") — Rolle unklar
- **JASPER & JUNE** — steht in der Retail-Longlist bei 44 Händlern, fehlt im
  Portfolio der Wissensbasis. Lizenz, Eigenmarke oder Testimonial?
- **Lumoo** — Kickback-Modell steht; Höhe, Laufzeit und Abrechnungsrhythmus fehlen

## Zu Deltex

- Standorte konkret, Geschäftsführung
- Umsatzgrößenordnung
- Getränke Vertrieb: eigene Marken oder reine Fremdmarken-Distribution?
- Posten Geschäft: eigenständig oder mit Partnern?
- Herzbach-Home: taucht in der Themenplanung nicht auf. Ruht der Bereich?
- Laufzeiten und Ablaufdaten der Lizenzen
- Verhältnis **Epsilon ↔ Deltex**: zwei getrennte Säulen, oder überschneidet sich
  Epsilons Getränkegeschäft mit der Deltex-Unit „Getränke Vertrieb"?

## Unklare Themen aus der Planung

- ~~**BLE**~~ — geklärt: **Brand Licensing Europe**, Messe am 6.–7.10.2026 in London.
  Die Namensliste sind die Gesprächspartner dort.
- **SM Penny** — wofür steht SM?
- **Demet** — NDA in Vorbereitung, Gegenstand unbekannt
- **Coolthings Box** — was ist das, welche Verträge müssen „passen"?
- **Nangaparbat** — zweigleisig bei Netto und Kaufland; eine Marke oder zwei Projekte?
- **SMATCH / NETWORK** — Postengeschäft, keine strategische Säule. Bewusst so?

## Zu korrigieren in der Themenplanung

- Vier Fristen auf **2024** statt 2026: Fristo, Getränke Quelle, HOL AB!, GLOBUS
- 46 von 53 auf *Hoch* — verstößt gegen das eigene Kriterium „warum jetzt wichtiger"
- Alle 13 Thomas-Themen ohne Status, alle mit identischer Frist
- „KAUFLAND-AP für Spirituosen finden" hat keinen nächsten Schritt
- ~17× „Nachfass" als nächster Schritt — laut Maßstab ein „unscharfer Status"
- Kein Status **„Später"**, obwohl die Strategie den Parkplatz ausdrücklich vorsieht
- Getränke Hoffmann doppelt — gewollt?
- Kategorie- und Partner-Spalte mischen je mehrere Dimensionen
- Cubcoats: Strategie sagt „neues Wachstumsfeld", Tabelle sagt *Niedrig, ohne Frist* —
  was gilt?

## Zur Retail-Longlist

- **Interzoo-Sprint ist verstrichen.** 39 Prio-A-Accounts vorbereitet, 36
  Pitch-Angles geschrieben, null Meetings eingetragen. Messe war 19.–22.05.2026,
  die nächste erst 2028. Was ist der Ersatzweg zu diesen 39 Accounts?
- **PATS Telford** läuft jährlich im September — nächster Messe-Zugang zu
  Pets at Home. Termin prüfen.
- **Sales Matrix**: nur 24 von 187 Händlern einem der drei zugewiesen. Absicht oder
  liegengeblieben?
- Longlist-Stand ist **April 2026** — Umsatz- und Filialzahlen ggf. veraltet.

## Zugang

- Das zweite Google Sheet (`15jYIfd0rx58…`) ist über den verbundenen
  Google-Account **nicht erreichbar** — „not found". Freigeben oder Inhalt anders liefern.

## Erledigt

- **13.09.2026 — Woran arbeitet Deltex Miloy?** An der **zweiten Kollektion mit
  TK Maxx**. Damit ist Miloy das einzige laufende Geschäft mit einem
  Wiederholungskunden — und gleichzeitig das einzige ohne Spur in der
  Themenplanung. (Sascha)
- **11.09.2026 — Ist Deltex Miloy noch aktuell?** Ja, läuft unter Deltex. (Sascha)
- **11.09.2026 — Wer sind die Partner in New York?** **Ambassadoren**, die Türen zum
  **US-Markt und zu US-Marken** öffnen. (Sascha)
- **11.09.2026 — Überschneiden sich Epsilon und die Deltex-Unit „Getränke Vertrieb"?**
  Nein, beide werden getrennt geführt. (Sascha)
- **11.09.2026 — Was ist Lumoo?** Eine Software; CGT bekommt **Kickback** dafür.
  Eigene Erlösquelle neben den Säulen, quartalsweise abzurechnen. (Sascha)
- **11.09.2026 — Gibt es ein Ansprechpartner-Verzeichnis?** Ja, in der Retail-Longlist
  (Blatt *Kontakte & Research*, 142 Händler). Nur die Buyer-Felder sind leer.

- **11.09.2026 — Was ist Epsilon?** Eine der **drei strategischen Säulen**:
  lizenzierte Getränke und Pocket-Money-Toys, großes Vertriebsnetz, gegenseitiger
  Themengeber. Thomas steuert auf hoher Ebene, Martin geht zum Kunden.
  (Quelle: Strategiepapier 2026/2027)
- **11.09.2026 — Heißt „PET" Heimtier?** Ja. „PET-Lizenzen für Hund und Katze."
  In derselben Tabelle meint „Fruit Juice PET 350 ml" aber die Flasche.
  (Quelle: Strategiepapier 2026/2027)
- **11.09.2026 — Cubcoats: Unit oder Partner?** Beides: kommerziell über Deltex,
  strategisch eine eigene Säule unter Saschas Federführung. (Quellen: Sascha, Strategiepapier)
- **11.09.2026 — Wer ist der größte Partner?** DELTEX, nach Umsatz, Projekten und
  Potenzial. Die höhere Themenzahl bei Epsilon (22 vs. 10) bildet das Gewicht nicht ab.
  (Quelle: Sascha)
- **11.09.2026 — Leistungsportfolio und Teamgröße?** Drei Personen: Sascha und
  Thomas Geschäftsführung, Martin Business Development. Bewusst nicht größer.
  (Quelle: Strategiepapier 2026/2027)
