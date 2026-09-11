# Themenplanung — Struktur-Vorschlag

*Stand: 11.09.2026. Umsetzung liegt als Google Sheet in Saschas Drive:
„CGT – Themenplanung NEU (Struktur-Vorschlag)". Alle 53 Themen sind migriert.*

Ziel des Umbaus: Saschas ursprüngliche Anforderung aus `CGT.docx` erfüllen —
**aufnehmen, filtern, verteilen, vom Ziel ausgehen, dynamisch, nicht zu komplex.**
Heute funktionieren aufnehmen und verteilen; filtern und „vom Ziel ausgehen" nicht.

## Die zwölf Spalten

| # | Spalte | Typ | Regel |
|---|---|---|---|
| A | **Ziel** | Text | Ergebnissatz, kein Stichwort. „Hard Rock bei PENNY gelistet", nicht „PENNY". Man muss am Satz erkennen, wann er erfüllt ist. |
| B | **Säule** | Dropdown | DELTEX · Epsilon · Cubcoats · NETWORK · CGT intern · Sonstige |
| C | **Marke** | Text | Die Marke, um die es geht. Verbindet Richtung 1 und Richtung 2 — heute fehlt genau das. |
| D | **Händler / Partner** | Text | Wer ist der Adressat |
| E | **Kanal** | Dropdown | LEH · Discounter · Getränkefachhandel · Heimtier · DIY/Garten · Travel Retail · Warenhaus · Online · Textil · Posten · Systemgastronomie · Industrie · Stationär |
| F | **Buyer** | Text | Name + Funktion. **Leer heißt: Stufe 1, gehört in die Recherche — nicht ins Nachfassen.** |
| G | **Stufe** | Dropdown | 1 Zielkunde · 2 Kontakt steht · 3 Erstkontakt · 4 Termin · 5 Muster · 6 Angebot · 7 Listung · **Geparkt** · **Verloren** |
| H | **Owner** | Dropdown | Sascha · Thomas · Martin — **immer genau einer**, nie „Alle" |
| I | **Nächster Schritt** | Text | Verb + Objekt, sofort ausführbar. **„Nachfass" ist kein zulässiger Eintrag** (eigener Maßstab: „keinen unscharfen Status"). |
| J | **Fällig** | Datum | |
| K | **Letzte Bewegung** | Datum | Wann zuletzt die Stufe gewechselt hat. Die wichtigste neue Spalte — sie zeigt Stillstand automatisch. |
| L | **Notiz** | Text | |

Die Hilfswerte für die Dropdowns stehen im Sheet ab Spalte N („HILFSWERTE – nicht
löschen").

## Was neu ist und warum

| Neuerung | Löst |
|---|---|
| **Stufe statt Status** | Man sieht Bewegung statt einer Wand aus „Offen". „Nachfass" wird zur unmöglichen Antwort, weil die Frage lautet: was bringt es eine Stufe weiter? |
| **Geparkt** | Die Strategie sieht „darf bewusst warten" ausdrücklich vor — bisher gab es keinen Ort dafür. Ohne Parkplatz wächst die Liste nur. |
| **Verloren (mit Grund)** | Verlorene Vorgänge verschwinden heute stillschweigend. Der Grund ist die wertvollste Information. |
| **Buyer-Spalte** | Macht die Hauptbruchstelle sichtbar: ohne Namen kein Abschluss. |
| **Letzte Bewegung** | Zeigt Stillstand ohne Nachfragen. Bedingte Formatierung: älter als 21 Tage → rot. |
| **Marke als Spalte** | Beantwortet endlich: Wie weit ist Marke X im Handel? |
| **Ziel als Satz** | Erfüllt das erste der fünf Aktivierungskriterien, das heute bei über 20 Themen gerissen wird. |

## Einrichtung im Sheet (ca. 10 Minuten)

1. **Blatt übernehmen:** Im neuen Sheet Rechtsklick auf den Blatt-Tab →
   *Kopieren nach* → „CGT – Themenplanung" auswählen.
2. **Dropdowns:** Spalte B markieren → *Daten › Datenüberprüfung* → *Liste aus einem
   Bereich* → `O2:O7`. Genauso E → `P2:P16`, G → `Q2:Q10`, H → `R2:R4`.
   (Spaltenbuchstaben nach dem Kopieren prüfen.)
3. **Stillstand sichtbar machen:** Spalte K markieren → *Format › Bedingte
   Formatierung* → *Benutzerdefinierte Formel*: `=UND(K2<>"";HEUTE()-K2>21)` → rot.
4. **Prioritäts-Deckel:** Keine eigene Spalte mehr. Die Stufe ersetzt sie. Wer eine
   Rangfolge braucht: höchstens zehn Themen gleichzeitig markieren.

## Migration — was ich beim Übertragen geändert habe

- **Vier Fristen von 2024 auf 2026 korrigiert** (Fristo, Getränke Quelle, HOL AB!, GLOBUS)
- **Alle Ziele als Ergebnissatz** neu formuliert
- **Jedes „Nachfass" ersetzt** durch einen ausführbaren Schritt
- **„Alle" als Verantwortlicher aufgelöst** (McDonald's/Burger King → Thomas)
- **„KAUFLAND-AP finden"** hatte keinen nächsten Schritt — jetzt einer
- **Coolthings Box auf *Geparkt*** gesetzt: wartet auf Vertragsklärung
- **Getränke Hoffmann doppelt** — als mögliche Dublette markiert, nicht gelöscht
- **Stufen sind ein Vorschlag**, abgeleitet aus der Spalte „Nächster Schritt".
  Beim gemeinsamen Durchgang bestätigen.

## Verteilung nach dem Umbau

| Stufe | Themen |
|---|---|
| 1 Zielkunde | 9 |
| 2 Kontakt steht | 7 |
| 3 Erstkontakt | 27 |
| **4 Termin** | **0** |
| 5 Muster | 5 |
| 6 Angebot | 3 |
| 7 Listung | 1 |
| Geparkt | 1 |

**Stufe 4 ist leer** — und fünf Vorgänge stehen trotzdem schon auf „Muster".
Es gehen also Muster an Leute, die niemand gesprochen hat. Siehe
[zusammenhang.md](zusammenhang.md).
