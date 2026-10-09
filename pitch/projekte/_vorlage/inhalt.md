---
// ===========================================================================
// KOPFDATEN — alles zwischen den beiden --- Zeilen.
// Schema: name: wert.  Was nicht gebraucht wird, einfach leer lassen.
// ===========================================================================

slug:            neues-projekt
kunde:           ALDI SÜD
projekt:         Produkt- oder Lizenzname
claim:           Ein Satz, der dem Einkäufer sagt, was er davon hat.
kanal:           LEH / Aktionsware
datum:           2026-10-09
status:          entwurf

ansprechpartner: Sascha Coldewey
mail:            sascha@helpingbrands.de
telefon:

hero-bild:       bilder/hero.jpg

// Akzentfarbe nur setzen, wenn das Projekt eine eigene braucht.
// Leer = CGT-Grün aus dem Stylesheet.
akzent:

// Text im Abschlussblock. Leer = Standardformulierung.
abschluss-titel:
abschluss-text:
---

// ===========================================================================
// AUFBAU DER SEITE
//
// "## Titel"              = neuer Abschnitt
// "## Titel {hell}"       = grauer Hintergrund
// "## Titel {dunkel}"     = dunkler Abschnitt
// "## Titel {versetzt}"   = Überschrift bleibt am Desktop seitlich stehen
//
// Bausteine stehen zwischen ::: und :::  (siehe unten)
// Zeilen mit // sind Notizen und erscheinen NICHT auf der Seite.
//
// Reihenfolge unten ist die bewährte für Einkäufer: erst die Zahl,
// dann der Markt, dann die Ware, dann Konditionen, dann der Termin.
// ===========================================================================


## Das Thema in 30 Sekunden

!! Ein Vorspann-Absatz. Das "!! " am Anfang macht ihn größer — damit startet
jeder Abschnitt, der eingeordnet werden muss.

::: kennzahlen
// Schema:  Wert | Beschriftung.  Zahlen zählen beim Scrollen hoch.
187 | Zielhändler in Europa
39 | davon Priorität A
9 | zugeordnete Marken
2026 | Verfügbar ab
:::


## Warum jetzt {hell}

Was ist am Markt los, das die Listung jetzt sinnvoll macht. Zwei bis vier Sätze,
keine Werbesprache. Einkäufer prüfen, ob die Begründung trägt.

- Erster belegbarer Punkt
- Zweiter belegbarer Punkt
- Dritter belegbarer Punkt


::: parallax bilder/stimmung.jpg
## Ein Satz, der hängen bleibt.

Das Parallaxband läuft über die volle Breite, das Bild bewegt sich langsamer
als die Seite. Einmal pro Seite reicht — sonst nutzt es sich ab.
:::


## Das Sortiment

::: slider nummeriert
// Jede "### Zeile" beginnt einen neuen Artikel.
// "bild:" ist optional. Am Handy wird gewischt, am Desktop gibt es Pfeile.

### Artikel eins
bild: bilder/artikel-1.jpg
Kurzbeschreibung. Was es ist, für wen, in welcher Einheit.

### Artikel zwei
bild: bilder/artikel-2.jpg
Kurzbeschreibung.

### Artikel drei
bild: bilder/artikel-3.jpg
Kurzbeschreibung.
:::


## Konditionen und Logistik {versetzt}

::: fakten
// Schema:  Bezeichnung | Wert
Liefereinheit | 12 Stück im Display
Palette | 48 Displays, 1 Lage
Mindesthaltbarkeit | 24 Monate
Lieferzeit ab Abruf | 6 Wochen
Verpackung | FSC-zertifiziert, recyclingfähig
:::

// Für echte Tabellen normales Markdown benutzen — am Handy wird seitlich
// gerollt, das ist so gewollt.

| Artikel | EAN | VK-Empfehlung | Einheit |
|---|---|---|---|
| Artikel eins | 4000000000001 | 3,99 € | 12er |
| Artikel zwei | 4000000000002 | 4,99 € | 12er |


## Unterstützung am Regal {hell}

::: karten
### Display
bild: bilder/display.jpg
Was mitgeliefert wird.

### Handzettel
Was CGT beisteuert.

### Social
Reichweite, falls vorhanden — nur mit Zahl, sonst weglassen.
:::


## Fahrplan bis zur Listung

::: zeitplan
// Schema:  Zeitpunkt | Was passiert
KW 42 | Muster und Kalkulation beim Einkauf
KW 44 | Rückmeldung, Anpassung der Ausstattung
KW 47 | Listungsentscheidung
KW 02 | Anlieferung Zentrallager
:::


## Warum CGT {dunkel}

Kurz und ohne Selbstlob. Was CGT beisteuert, das der Einkäufer sonst selbst
organisieren müsste.

::: zitat
Die richtigen Themen erkennen – und erfolgreich ins Ziel bringen.
-- Leitlinie CGT UG
:::
