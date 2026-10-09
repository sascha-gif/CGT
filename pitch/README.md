# Pitch-Seiten

Eine Webseite pro Kunde oder Projekt. Kopf, Fuß, Farben und Verhalten sind
überall gleich — nur Texte, Bilder und Zahlen wechseln. Jedes Projekt bekommt
ein eigenes Verzeichnis und damit eine eigene Adresse.

Zielgruppe sind **Einkäufer im Handel** — LEH, Discount, Fachhandel. Die Seite
ist dafür gebaut: zuerst die Zahl, dann der Markt, dann die Ware, dann
Konditionen, dann der Termin. Sie wird meistens auf dem **Handy** geöffnet,
deshalb ist alles vom kleinen Bildschirm aus entworfen.

---

## Für das Team: ein neues Projekt anlegen

**Du brauchst nichts zu installieren und nichts zu programmieren.**

Sag Claude im Repo:

> Neues Pitch-Projekt für *\<Kunde\>* zum Thema *\<Produkt oder Lizenz\>*.

Dazu lieferst du:

| Was | Wie viel | Anmerkung |
|---|---|---|
| **Kunde** | ein Name | z. B. ALDI SÜD, Netto, Kaufland |
| **Thema** | ein Name | Produkt, Marke oder Lizenz |
| **Ein Satz Nutzen** | eine Zeile | was der Einkäufer davon hat |
| **Zahlen** | 3–4 Stück | je Zahl eine kurze Beschriftung |
| **Begründung** | 2–4 Sätze | warum jetzt — belegbar, keine Werbesprache |
| **Artikel** | je Artikel 2 Zeilen | Name, Kurzbeschreibung |
| **Konditionen** | Stichpunkte | Liefereinheit, Palette, MHD, Lieferzeit |
| **Termine** | 3–5 Punkte | bis zur Listungsentscheidung |
| **Bilder** | so viele wie da | Hero-Bild, Artikelbilder, Stimmungsbild |

Die Bilder legst du in `pitch/projekte/<projektname>/bilder/` ab. Dateinamen
klein und mit Bindestrichen. JPG, PNG, WEBP oder SVG.

Claude füllt daraus `inhalt.md` aus, baut die Seite und sagt dir die Adresse.

Wer es selbst anlegen will:

```bash
cd pitch
python3 bauen.py --neu aldi-sued-mercedes
```

Das kopiert die Blankovorlage und vergibt sofort eine Adresse mit Zufallsteil
(siehe *Adressen* weiter unten).

**Was fehlt, wird nicht erfunden.** Fehlt eine Zahl, fällt der Block weg oder
Claude fragt nach. Erfundene Konditionen vor einem Einkäufer sind teurer als
eine kürzere Seite.

---

## Wie es technisch funktioniert

```
pitch/
├── bauen.py                     Generator (Python, keine Zusatzpakete)
├── vorlage/
│   ├── seite.html               Gerüst: Kopf und Fuß für ALLE Seiten
│   └── assets/
│       ├── stil.css             Farben, Schrift, Raster — zentral
│       └── bewegung.js          Scroll-Effekte, Parallax, Slider
├── projekte/
│   ├── _vorlage/inhalt.md       Blanko zum Kopieren, mit Erklärungen
│   └── <projektname>/
│       ├── inhalt.md            der ganze Inhalt dieses Projekts
│       └── bilder/              die Bilder dieses Projekts
└── site/                        ERZEUGT — hier liegt das Ergebnis
    └── <slug>/index.html
```

Die Seite bauen:

```bash
cd pitch
python3 bauen.py --neu mein-projekt   # neues Projekt anlegen
python3 bauen.py                      # alle Projekte bauen
python3 bauen.py mein-projekt         # nur eines bauen
python3 bauen.py --uebersicht         # zusätzlich interne Startseite
```

Ansehen: `pitch/site/<slug>/index.html` im Browser öffnen. Es braucht keinen
Server.

**`site/` nie von Hand bearbeiten.** Der nächste Build überschreibt alles.
Geändert wird immer `inhalt.md`.

---

## Was in `inhalt.md` steht

Oben zwischen zwei `---` die **Kopfdaten**:

```
slug:            aldi-sued-musterlizenz
kunde:           ALDI SÜD
projekt:         Musterlizenz Pflegeserie
claim:           Ein Satz, der sagt, was der Einkäufer davon hat.
kanal:           LEH / Aktionsware
datum:           2026-10-09
status:          entwurf
ansprechpartner: Sascha Coldewey
mail:            sascha@helpingbrands.de
hero-bild:       bilder/hero.jpg
akzent:                            # leer = CGT-Grün
```

`status: entwurf` blendet oben einen roten Balken ein. **Vor dem Versand an
den Einkäufer auf `freigegeben` ändern** — sonst steht „Entwurf" auf der Seite.

Darunter der Inhalt. `## Titel` beginnt einen Abschnitt:

| Schreibweise | Wirkung |
|---|---|
| `## Titel` | normaler Abschnitt, weiß |
| `## Titel {hell}` | grauer Hintergrund |
| `## Titel {dunkel}` | dunkler Abschnitt |
| `## Titel {versetzt}` | Überschrift bleibt am Desktop seitlich stehen |
| `## Titel {label=Sortiment}` | eigene Marke statt der laufenden Nummer |

Zeilen, die mit `//` beginnen, sind Notizen und erscheinen **nicht** auf der
Seite.

### Bausteine

Alles zwischen `:::` und `:::`.

**Kennzahlen** — zählen beim Scrollen hoch:
```
::: kennzahlen
187 | Zielhändler in Europa
39 | davon Priorität A
:::
```

**Sortiment zum Wischen** — `nummeriert` weglassen, wenn keine Nummern:
```
::: slider nummeriert
### Artikel eins
bild: bilder/artikel-1.jpg
Kurzbeschreibung.
:::
```

**Karten nebeneinander** — gleiche Schreibweise wie `slider`:
```
::: karten
### Display
bild: bilder/display.jpg
Was mitgeliefert wird.
:::
```

**Konditionen:**
```
::: fakten
Liefereinheit | 12 Stück im Display
Lieferzeit ab Abruf | 6 Wochen
:::
```

**Zeitplan:**
```
::: zeitplan
KW 42 | Muster und Kalkulation beim Einkauf
KW 47 | Listungsentscheidung
:::
```

**Parallaxband** über die volle Breite — **einmal pro Seite reicht**:
```
::: parallax bilder/stimmung.jpg
## Ein Satz, der hängen bleibt.
Ein, zwei Sätze dazu.
:::
```

**Weiter:** `::: zitat` (mit `-- Quelle` in der letzten Zeile),
`::: galerie` (nur Bildzeilen), `::: hinweis` (gelber Kasten).

Normales Markdown geht überall: Absätze, `- Aufzählungen`, Tabellen mit `|`,
`**fett**`, `[Links](...)`, `![Bildtext](bilder/x.jpg)`. Ein Absatz, der mit
`!! ` beginnt, wird größer gesetzt — gut als Einstieg in einen Abschnitt.

---

## Das Aussehen ändern

| Was | Wo |
|---|---|
| Farben, Schrift, Abstände, Raster | `vorlage/assets/stil.css` (ganz oben) |
| Kopfzeile, Fußzeile, Impressum | `vorlage/seite.html` |
| Scroll-Effekte, Parallax, Slider | `vorlage/assets/bewegung.js` |
| Akzentfarbe nur für ein Projekt | `akzent:` in dessen `inhalt.md` |

Eine Änderung in `vorlage/` wirkt nach dem nächsten Build auf **alle** Seiten.

---

## Bewusste Entscheidungen

- **Keine externen Schriften und keine fremden Server.** Alles liegt im
  Verzeichnis. Damit entsteht kein Datenschutzthema bei Google Fonts, und die
  Seite lädt auch bei schlechtem Netz im Markt.
- **Kein Framework, kein Build-Werkzeug, kein `npm`.** Nur Python aus der
  Standardinstallation. Das läuft in fünf Jahren noch.
- **`noindex` in jeder Seite.** Pitch-Seiten gehören nicht in Google.
- **Wer „Bewegung reduzieren" eingestellt hat, bekommt alles sofort und
  statisch.** Das ist Absicht, kein Fehler.
- **Druckansicht ist mitgedacht.** Strg+P erzeugt ein brauchbares PDF, falls
  ein Einkäufer die Seite ausdruckt.
- **Die Übersicht `site/index.html` ist intern.** Wird sie öffentlich
  gestellt, sieht jeder Kunde, wem sonst noch etwas angeboten wird. Deshalb
  entsteht sie nur auf ausdrückliche Anforderung (`--uebersicht`).

---

## Adressen

Jede Seite liegt unter einer eigenen Adresse mit **Zufallsteil**:

```
https://pitch.cgt-ug.de/aldi-sued-mercedes-kdgqvy/
                                            ^^^^^^
```

Das ist bewusst so. Ohne den Zufallsteil könnte jemand andere Kunden durch
Raten finden — `/aldi-sued/`, `/lidl/`, `/netto/` sind schnell durchprobiert.
Mit Zufallsteil ist die Seite ohne Link praktisch nicht auffindbar, und der
Einkäufer braucht trotzdem kein Passwort.

`python3 bauen.py --neu <name>` vergibt den Zufallsteil automatisch. Er steht
danach als `slug:` in der `inhalt.md` und ändert sich nicht mehr — **einmal
verschickte Links bleiben also gültig.**

Zusätzlich steht `noindex` in jeder Seite und als Kopfzeile auf dem Server.
Google nimmt die Seiten damit nicht auf.

---

## Hosting: Vercel einrichten

Entschieden am 09.10.2026: **Vercel**, eigene Domain, automatischer Build bei
jedem Push. Einmal einrichten, danach läuft es von allein.

**Vorher:** Dieser Zweig muss auf `main` gelandet sein — Vercel baut sonst
nichts.

1. **vercel.com** öffnen, **Sign up with GitHub**, mit dem Konto anmelden,
   dem das Repo gehört.
2. **Add New… → Project** → Repository `sascha-gif/CGT` → **Import**.
3. Beim Import diese Felder setzen — **das ist der entscheidende Schritt:**

   | Feld | Wert |
   |---|---|
   | Framework Preset | **Other** |
   | Root Directory | **`pitch/site`** |
   | Build Command | leer lassen (Override aus) |
   | Output Directory | leer lassen |
   | Install Command | leer lassen |

   Es wird nichts kompiliert. Vercel liefert die fertigen Dateien aus,
   die im Repo liegen.
4. **Deploy** drücken. Nach etwa einer Minute steht die Seite unter einer
   `*.vercel.app`-Adresse.
5. **Settings → Deployment Protection** prüfen: Für *Production* muss der
   Schutz **aus** sein. Sonst sieht der Einkäufer einen Vercel-Login statt
   der Seite.
6. **Settings → Domains** → eigene Domain eintragen, z. B. `pitch.cgt-ug.de`.
   Vercel nennt einen CNAME-Eintrag, der beim Domain-Anbieter hinterlegt wird.
7. **Settings → Git → Production Branch** auf `main` stellen.

Ab dann gilt: `python3 bauen.py` ausführen, Änderung nach `main` pushen —
zwei Minuten später ist die Seite live.

**Die Startseite der Domain zeigt bewusst einen Fehler.** Es gibt keine
Übersicht im Netz, sonst sähe jeder Kunde, wem sonst noch etwas angeboten
wird. Nur die Projektadressen funktionieren.

### Was du dabei wissen solltest

**Vercel bekommt eine Kopie des gesamten Repos**, nicht nur `pitch/site` —
auch `docs/`. Das Repo bleibt privat und Vercel veröffentlicht nur den
Root-Ordner, aber die Dateien liegen auf deren Build-Servern. Wenn das nicht
in Ordnung ist, gibt es zwei Alternativen:

- ein **zweites Repo** nur für die fertigen Seiten, oder
- **manuelles Hochladen** statt Git-Anbindung.

Beides macht die Einrichtung etwas umständlicher und jede Veröffentlichung
einen Schritt länger. Sag Bescheid, dann baue ich es um.

---

## Noch offen

- **Verbindliche CGT-Farben und Logo.** Das Grün in
  `vorlage/assets/stil.css` ist ein **Vorschlag**, keine belegte Hausfarbe —
  dafür gibt es im Repo keine Quelle. Die Kopfzeile trägt bisher nur den
  Schriftzug „CGT". Sobald CI-Vorgaben da sind, wird an einer Stelle
  getauscht und alle Seiten ziehen nach.
- **Wer gibt eine Seite frei**, bevor sie an einen Einkäufer geht? Solange
  `status: entwurf` steht, zeigt die Seite oben einen roten Balken.
