# CLAUDE.md — CGT UG

Wissens-Repo der **CGT UG** (Coldewey Goetz Trade). Verantwortlich ist **Sascha**,
Geschäftsführer, ohne technisches Team im Rücken.

**Diese Datei zu Beginn jeder Session lesen.**

## Was CGT macht — die Kurzfassung

CGT ist der Ansprechpartner für Lizenzen und Produkte, die sich wirklich verkaufen.
**Drei Personen:** Sascha und Thomas (Geschäftsführung), Martin (Business
Development) — bewusst nicht mehr.

Zwei Richtungen: **Marken und Lizenzen beschaffen** (über das internationale
Netzwerk) und **Handel gewinnen** (LEH, Discount, Fachhandel). Der Wert entsteht in
der Verbindung.

**Drei strategische Säulen:** **DELTEX** (Kernpartner, LEH — Aldi, Lidl, Kaufland,
Penny), **Epsilon** (Getränke + Pocket-Money-Toys), **Cubcoats** (neues
Wachstumsfeld).

> Leitlinie: **Die richtigen Themen erkennen – und erfolgreich ins Ziel bringen.**

Maßgeblich ist [`docs/strategie.md`](docs/strategie.md). Gesamtbild:
[`docs/zusammenhang.md`](docs/zusammenhang.md).

## Was dieses Repo ist — und was nicht

Eine **Ablage für Betriebswissen**, kein Software-Projekt. Kein Code, kein Build,
kein Deployment.

**Eine bewusste Ausnahme:** [`pitch/`](pitch/README.md) — das Baukastensystem
für Pitch-Seiten. Das ist Code und widerspricht dem Satz darüber. Der
Widerspruch bleibt stehen, weil die Entscheidung so gefallen ist: Sascha
braucht pro Kunde eine eigene Seite, und sie soll aus einer Vorlage entstehen,
nicht jedes Mal neu. Für alles andere gilt der Satz weiter.

**Tagesaufgaben gehören nicht hierher.** Dafür gibt es das Google Sheet
„CGT – Themenplanung" (Eigner Thomas Götz), siehe
[`docs/themenplanung.md`](docs/themenplanung.md).

## Zusammenarbeit

- **Deutsch, per Du.** Sachlich und auf den Punkt, wenig Fachjargon.
- Technische Schritte einfach erklären — bei Unklarheiten direkt sagen: wann, wie, wo.
- **Visuell:** einfach und klassisch. Weißer Hintergrund, klare Hierarchie, keine
  Effekt-Optik. Erst Struktur klären, dann visualisieren.
- **Nichts erfinden.** Was nicht belegt ist, kommt nicht als Fakt ins Repo —
  offene Fragen gehören nach [`docs/offene-punkte.md`](docs/offene-punkte.md).

## Regeln für Einträge

1. **Quelle und Datum dazu.** Ohne Datum ist eine Kondition wertlos.
2. **Begründung mitschreiben**, nicht nur das Ergebnis.
3. **Widersprüche stehen lassen und markieren.** Wo Strategie und Tabelle
   auseinandergehen, gilt die Strategie als Maßstab — der Widerspruch wird benannt,
   nicht geglättet.
4. **Keine Secrets.** Notieren, *wo* sie liegen, nie *was* sie sind.
5. **Keine Namen externer Ansprechpartner** und keine persönlichen Einschätzungen
   zu ihnen, bis Sascha entschieden hat, wo dieses Wissen leben soll. Bewusst so.

## Fallstricke

**„PET" heißt Heimtier, nicht Kunststoff.** Das Strategiepapier sagt „PET-Lizenzen
für **Hund und Katze**" — im Sheet sind das Fressnapf, OBI, DEHNER. Aber dieselbe
Tabelle schreibt in einer Getränke-Notiz „Fruit Juice PET 350 ml" und meint die
Flasche. Nie raten — am Händler festmachen.

**Zeilenzahl im Sheet ist nicht Gewicht.** Epsilon hat 22 Themen, DELTEX 10 — aber
**DELTEX ist der größte Partner** nach Umsatz, Projekten und Potenzial. Nie nach
Themenanzahl priorisieren.

**Die Priorität-Spalte ist wertlos** — 46 von 53 Themen stehen auf „Hoch". Nicht
als Signal verwenden.

**„Nachfass" ist kein nächster Schritt.** Der eigene Maßstab verlangt „eine
Handlung, die sofort ausgeführt werden kann — keinen unscharfen Status". „Nachfass"
steht rund 17 Mal da.

**Cubcoats und Miloy laufen beide unter Deltex** — Cubcoats ist trotzdem eine eigene
strategische Säule. Beides gilt. Miloy ist aktuell, aber inhaltlich undokumentiert.

**Epsilon ist nicht die Deltex-Unit „Getränke Vertrieb".** Beide machen Getränke,
werden getrennt geführt, überschneiden sich nicht.

**Das Ansprechpartner-Verzeichnis existiert bereits** — Blatt *Kontakte & Research*
der Retail-Longlist, 142 Händler. Es ist nur an der wichtigen Stelle leer (Buyer
Name 1/142). Nie behaupten, es fehle ein Werkzeug — es fehlt die Recherche.

**Die Retail-Longlist ist die Pet-Absatzliste**: 187 Händler europaweit, 39 auf
Priorität A, neun Marken zugeordnet. In der Themenplanung stehen davon **drei**.

## Pitch-Seiten bauen

Fragt jemand nach einer **neuen Pitch-Seite für einen Kunden**, gilt
[`pitch/README.md`](pitch/README.md). Kurz:

1. `cd pitch && python3 bauen.py --neu <projektname>` — legt den Ordner an
   und vergibt eine Adresse mit Zufallsteil
2. Bilder nach `pitch/projekte/<projektname>/bilder/` legen
3. `inhalt.md` aus den gelieferten Texten und Zahlen füllen
4. `python3 bauen.py <projektname>`
5. Ergebnis liegt zweifach vor:
   - `pitch/vorschau/<slug>.html` — **alles in einer Datei**, zum Anschauen und
     Verschicken. Diese Datei nennen, wenn jemand die Seite sehen will.
   - `pitch/site/<slug>/index.html` — Fassung für den Server, braucht die
     Ordner `assets/` und `bilder/` daneben

Den **Zufallsteil im `slug` nie nachträglich ändern** — sonst sind bereits
verschickte Links tot. Vor dem Versand an einen Einkäufer `status:` von
`entwurf` auf `freigegeben` setzen, sonst steht ein roter Balken auf der Seite.

Kopf, Fuß, Farben und Effekte sind für alle Seiten gleich und stehen in
`pitch/vorlage/`. Dort wird geändert, wenn sich das Aussehen ändern soll —
nie in einer einzelnen Projektseite.

**Auch hier gilt Regel 1: nichts erfinden.** Fehlt eine Kondition, eine EAN
oder ein Termin, bleibt der Block weg oder es wird nachgefragt. Eine erfundene
Zahl vor einem Einkäufer kostet mehr als eine kürzere Seite.

## Schreibweise

- Firma **CGT UG**, ausgeschrieben **Coldewey Goetz Trade**.
- Säulen: **DELTEX**, **Epsilon**, **Cubcoats**. Kunde/Kernpartner: Deltex Handels GmbH.
- Dateinamen klein, mit Bindestrichen.
- Markdown, Überschriften ab `##`. Lieber mehrere Dateien als Tabellen-Monster.
