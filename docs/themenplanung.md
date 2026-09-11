# Themenplanung — das Arbeitswerkzeug

*Stand: 11.09.2026*

| | |
|---|---|
| Wo | Google Sheet „CGT – Themenplanung", Blatt *Themen* |
| Eigner | Thomas Götz |
| Umfang | 53 Themen (Bereich A1:M167, Rest leer) |
| Spalten | Ziel/Thema · Partner · Kategorie · Verantwortlich · Frist · Priorität · Status · Nächster Schritt · Notizen |

Die Tabelle bleibt das **lebende System** für Tagesarbeit. Dieses Repo hält das
Dauerhafte fest, nicht die Aufgaben.

## Wofür sie gebaut wurde

Aus Saschas Rohfassung `CGT.docx`, wörtlich:

> „Insgesamt brauchen wir ein Tool am besten als Google Sheet um die Themen
> aufzunehmen, **zu filtern und zu verteilen**. Ich möchte **vom Ziel ausgehen**
> und dann angeben, wer welches Thema bis wann erledigen muss. Es soll dynamisch
> sein und nicht zu komplex und kompliziert."

Daran gemessen: aufnehmen ✓, verteilen ✓, **filtern ✗**, vom Ziel ausgehen ✗.

## Verteilung

| Verantwortlich | Themen | Schwerpunkt |
|---|---|---|
| Martin | 28 | Handelsseite (Richtung 2) |
| Thomas | 13 | Marken-/Lizenzseite (Richtung 1) |
| Sascha | 11 | Cubcoats, Struktur, Abrechnung |
| „Alle" | 1 | Systemgastronomie |

## Test gegen die eigenen fünf Kriterien

Die Strategie lässt ein Thema nur aktiv werden, wenn fünf Bedingungen erfüllt sind
(siehe [strategie.md](strategie.md)). Vier davon hält die Tabelle nicht ein:

| Kriterium | Befund | |
|---|---|---|
| Ergebnis klar beschrieben | über 20 Themen bestehen nur aus einem Händlernamen | ✗ |
| Eine Person verantwortlich | erfüllt, bis auf ein Thema auf „Alle" | ✓ |
| Nächster Schritt konkret | ~17× „Nachfass"; „KAUFLAND-AP finden" hat gar keinen | ✗ |
| Realistische Frist | 4 Fristen auf **2024**; 13 Themen mit identischem Datum; 5 ohne Frist | ✗ |
| Warum jetzt wichtiger | 46 von 53 auf „Hoch" | ✗ |

Dazu fehlt der von der Strategie ausdrücklich vorgesehene Zustand **„darf bewusst
warten"** — die Status-Spalte kennt nur *Offen*, *In Arbeit*, *Erledigt*.

## Was die Tabelle über das Geschäft verrät

**1. Die beiden Geschäftsrichtungen sind nicht verbunden.**
Kein Feld sagt, welche Marke gerade bei welchem Händler liegt. Man kann nicht
beantworten, wie weit eine Marke im Handel gekommen ist. Genau diese Verbindung
ist aber das Produkt von CGT.

**2. Zeilenzahl bildet Gewicht nicht ab.**
Epsilon 22 Themen, DELTEX 10 (+4 Cubcoats) — DELTEX ist trotzdem der größte
Partner nach Umsatz, Projekten und Potenzial. Die Tabelle misst Aufwand, nicht Wert.

**3. Hard Rock ist kein Thema, sondern eine Kampagne.**
16 Themen, 15 davon bei Martin — über die Hälfte seiner Liste, alle mit demselben
nächsten Schritt („Nachfass"), fast alle auf *Offen*. Das ist ein Vorgang mit 16
Adressaten, kein 16-facher Aufwand.

**4. Der Engpass ist durchgehend der Zugang zum richtigen Ansprechpartner** —
nicht Produkt, nicht Preis. Siehe [handel.md](handel.md).

**5. Muster sind die eigentliche Vorgangsstufe.**
Fünf Themen drehen sich um Muster (NORMA Getränkelizenzen, NORMA Sell-in/Sell-out,
Cubcoats, Mizu, Getränke Hoffmann). Musterstand wäre eine sinnvolle Statusstufe
statt Freitext.

**6. Cubcoats steht gegen die Strategie.**
Vier der fünf Cubcoats-Themen: Priorität *Niedrig*, keine Frist — bei einem Feld,
das die Strategie „unser neues Wachstumsfeld" nennt.

## Bekannte Schwächen

| Was | Wirkung |
|---|---|
| Vier Fristen auf **2024** (Fristo, Getränke Quelle, HOL AB!, GLOBUS) | erscheinen als zwei Jahre überfällig |
| **46 von 53** auf Priorität *Hoch* | Spalte priorisiert nichts mehr |
| Alle 13 Thomas-Themen **ohne Status** | für seinen Bereich nicht filterbar |
| Alle 13 Thomas-Themen mit derselben Frist | Frist trägt keine Information |
| Getränke Hoffmann **doppelt** (Hard Rock / Alkoholfrei) | ggf. gewollt, sollte man wissen |
| Kategorie mischt Marke, Kanal, Warengruppe, Geschäftsart | nicht filterbar |
| Partner mischt Firma, Person, CGT selbst | nicht nach Partner auswertbar |
| „PET" bedeutet Heimtier **und** Kunststoffflasche | Verwechslungsgefahr |
| Tippfehler: „Nachhfass", „Jelenda", „Burger KIng" | |

## Vorschlag: minimale Umbauten

Klein halten — die Anforderung lautet „nicht zu komplex und kompliziert":

1. **Status um „Später" ergänzen.** Gibt dem Parkplatz einen Ort.
2. **Kategorie aufteilen** in *Partner-Säule* (DELTEX / Epsilon / Cubcoats / sonstiges)
   und *Kanal* (LEH / Discount / Getränkefachhandel / Heimtier / Travel Retail / E-Com).
   Erst dann lässt sich filtern.
3. **Priorität auf drei echte Stufen zwingen** — z. B. maximal 10 Themen dürfen
   gleichzeitig „Hoch" sein.
4. **Spalte „Ziel" wörtlich nehmen:** statt „PENNY" → „Hard Rock bei PENNY gelistet".
5. **Marke als eigene Spalte**, damit Richtung 1 und Richtung 2 zusammenfinden.
