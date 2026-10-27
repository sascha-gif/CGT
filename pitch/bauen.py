#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGT Pitch — Seitengenerator

Liest je Projekt eine Datei `projekte/<slug>/inhalt.md` und schreibt daraus
`site/<slug>/index.html`. Kopf, Fuss, Farben und Verhalten kommen aus
`vorlage/` und sind fuer alle Projekte gleich.

Aufruf:
    python3 bauen.py --neu <name>    # neues Projekt aus der Blankovorlage
    python3 bauen.py                 # alle Projekte bauen
    python3 bauen.py <name> [<name>] # nur diese bauen
    python3 bauen.py --uebersicht    # zusaetzlich site/index.html (NUR INTERN!)

Nur Python-Standardbibliothek. Kein pip, kein Node, kein Build-Werkzeug.
"""

import base64
import html
import os
import re
import secrets
import shutil
import sys
from datetime import date
from urllib.parse import quote

WURZEL   = os.path.dirname(os.path.abspath(__file__))
VORLAGE  = os.path.join(WURZEL, "vorlage")
PROJEKTE = os.path.join(WURZEL, "projekte")
AUSGABE  = os.path.join(WURZEL, "site")
VORSCHAU = os.path.join(WURZEL, "vorschau")

BILD_ENDUNGEN = (".jpg", ".jpeg", ".png", ".webp", ".avif", ".gif", ".svg",
                 ".mp4", ".webm", ".m4v")

# Fuer die Einzeldatei: welcher Dateityp wird wie eingebettet
MIME = {
    ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
    ".webp": "image/webp", ".avif": "image/avif", ".gif": "image/gif",
    ".svg": "image/svg+xml",
    ".mp4": "video/mp4", ".webm": "video/webm", ".m4v": "video/mp4",
}
VIDEO_ENDUNGEN = (".mp4", ".webm", ".m4v")

# Wird nach site/vercel.json geschrieben. X-Robots-Tag haelt die Seiten
# zusaetzlich zum Meta-Tag aus den Suchmaschinen heraus.
VERCEL_JSON = """{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        { "key": "X-Robots-Tag", "value": "noindex, nofollow" },
        { "key": "X-Content-Type-Options", "value": "nosniff" },
        { "key": "Referrer-Policy", "value": "strict-origin-when-cross-origin" }
      ]
    }
  ]
}
"""

# Kopfdaten des Projekts, das gerade gebaut wird. Bausteine wie das
# Kontaktformular brauchen daraus die Empfaengeradresse.
FELDER = {}

MONATE = ("Januar", "Februar", "Maerz", "April", "Mai", "Juni", "Juli",
          "August", "September", "Oktober", "November", "Dezember")


# ===========================================================================
# Kleine Helfer
# ===========================================================================

# Zeichen ohne Verwechslungsgefahr: kein 0/O, kein 1/l/I.
ZUFALLSZEICHEN = "abcdefghjkmnpqrstuvwxyz23456789"


def zufallsteil(laenge=6):
    """Zufaelliger Anhang fuer die Adresse. Damit ist eine Pitch-Seite nicht
    zu erraten: wer den Link nicht hat, findet sie nicht."""
    return "".join(secrets.choice(ZUFALLSZEICHEN) for _ in range(laenge))


def sicher(text):
    """Text so absichern, dass er gefahrlos in HTML landet."""
    return html.escape(str(text), quote=True)


def datum_lang(roh):
    """2026-10-09 oder 09.10.2026 -> 9. Oktober 2026. Sonst unveraendert."""
    roh = str(roh).strip()
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", roh)
    if m:
        j, mo, t = int(m.group(1)), int(m.group(2)), int(m.group(3))
    else:
        m = re.match(r"^(\d{1,2})\.(\d{1,2})\.(\d{4})$", roh)
        if not m:
            return roh
        t, mo, j = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if not 1 <= mo <= 12:
        return roh
    return "%d. %s %d" % (t, MONATE[mo - 1], j)


def inline(text):
    """Markdown im Fliesstext: fett, kursiv, Link, Code. Alles andere wird
    vorher abgesichert, damit kein fremdes HTML durchrutscht."""
    t = sicher(text)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![\*\w])\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", t)
    # Links: [Text](ziel) — nur http(s), mailto, tel und relative Pfade
    def link(m):
        beschriftung, ziel = m.group(1), m.group(2).strip()
        if not re.match(r"^(https?:|mailto:|tel:|[./#]|[\w\-]+[./])", ziel):
            return beschriftung
        extern = ' target="_blank" rel="noopener"' if ziel.startswith("http") else ""
        return '<a href="%s"%s>%s</a>' % (ziel, extern, beschriftung)
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link, t)
    t = t.replace(" -- ", " &ndash; ")
    return t


def zahl_zerlegen(roh):
    """'187' -> ('', '187', ''),  '+12 %' -> ('+', '12', ' %'),
    'ab 2027' -> (None, None, None), wenn keine Zahl enthalten ist."""
    m = re.search(r"\d[\d.,]*", roh)
    if not m:
        return None, None, None
    return roh[:m.start()], m.group(0), roh[m.end():]


# ===========================================================================
# Einlesen: Kopfdaten + Inhalt
# ===========================================================================

def kopfdaten_lesen(text):
    """Trennt den --- Block am Anfang vom restlichen Text."""
    felder = {}
    if not text.startswith("---"):
        return felder, text
    # Schlusszeile ist eine Zeile, die NUR aus --- besteht.
    schluss = re.search(r"^---[ \t]*$", text[3:], re.M)
    if not schluss:
        return felder, text
    kopf = text[3:3 + schluss.start()]
    rest = text[3 + schluss.end():].lstrip("\n")
    for zeile in kopf.splitlines():
        zeile = zeile.strip()
        # // und # sind Notizen fuer das Team, keine Felder.
        if (not zeile or zeile.startswith("#") or zeile.startswith("//")
                or ":" not in zeile):
            continue
        name, wert = zeile.split(":", 1)
        wert = wert.strip().strip('"').strip("'")
        felder[name.strip().lower()] = wert
    return felder, rest


def bloecke_teilen(zeilen):
    """Zerlegt den Inhalt in eine Liste von (art, daten)-Paaren."""
    ergebnis = []
    i = 0
    puffer = []

    def puffer_leeren():
        if puffer:
            ergebnis.append(("text", list(puffer)))
            puffer.clear()

    while i < len(zeilen):
        zeile = zeilen[i]

        # Fenced Block:  ::: name argument
        if zeile.strip().startswith(":::"):
            kopf = zeile.strip()[3:].strip()
            if kopf:
                name = kopf.split()[0].lower()
                argument = kopf[len(name):].strip()
                inhalt = []
                tiefe = 1
                i += 1
                while i < len(zeilen):
                    schluss = zeilen[i].strip()
                    if schluss.startswith(":::"):
                        if schluss[3:].strip():
                            tiefe += 1          # weiterer Baustein beginnt
                        else:
                            tiefe -= 1          # nacktes ::: schliesst
                            if tiefe == 0:
                                break
                    inhalt.append(zeilen[i])
                    i += 1
                puffer_leeren()
                ergebnis.append(("block", (name, argument, inhalt)))
            i += 1
            continue

        # Abschnittsueberschrift:  ## Titel {hell}
        if zeile.startswith("## "):
            puffer_leeren()
            titel = zeile[3:].strip()
            mods = []
            m = re.search(r"\{([^}]*)\}\s*$", titel)
            if m:
                mods = [x.strip().lower() for x in m.group(1).split(",") if x.strip()]
                titel = titel[:m.start()].strip()
            ergebnis.append(("abschnitt", (titel, mods)))
            i += 1
            continue

        puffer.append(zeile)
        i += 1

    puffer_leeren()
    return ergebnis


# ===========================================================================
# Darstellung: Fliesstext
# ===========================================================================

def text_rendern(zeilen):
    """Absaetze, Listen, Zitate, Bilder, Tabellen, Trennlinien, h3/h4."""
    teile = []
    i = 0
    n = len(zeilen)

    while i < n:
        zeile = zeilen[i]
        blank = zeile.strip()

        if not blank:
            i += 1
            continue

        # Trennlinie
        if re.match(r"^-{3,}$", blank):
            teile.append("<hr>")
            i += 1
            continue

        # Ueberschriften innerhalb eines Abschnitts
        if blank.startswith("#### "):
            teile.append("<h4>%s</h4>" % inline(blank[5:].strip()))
            i += 1
            continue
        if blank.startswith("### "):
            teile.append("<h3>%s</h3>" % inline(blank[4:].strip()))
            i += 1
            continue
        # "## " kommt hier nur innerhalb eines ::: Bausteins an -- auf oberster
        # Ebene hat bloecke_teilen() daraus schon einen Abschnitt gemacht.
        if blank.startswith("## "):
            teile.append('<h2 data-auftritt>%s</h2>' % inline(blank[3:].strip()))
            i += 1
            continue

        # Alleinstehendes Bild:  ![Bildtext](bilder/x.jpg)
        m = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)$", blank)
        if m:
            text, quelle = m.group(1), m.group(2).strip()
            bu = ('<figcaption>%s</figcaption>' % inline(text)) if text else ""
            teile.append(
                '<figure class="bild" data-auftritt="zoom">'
                '<img src="%s" alt="%s" loading="lazy" decoding="async">%s</figure>'
                % (sicher(quelle), sicher(text), bu)
            )
            i += 1
            continue

        # Tabelle
        if blank.startswith("|") and i + 1 < n and re.match(r"^\s*\|[\s:|-]+\|\s*$", zeilen[i + 1]):
            kopf = [z.strip() for z in blank.strip("|").split("|")]
            i += 2
            koerper = []
            while i < n and zeilen[i].strip().startswith("|"):
                koerper.append([z.strip() for z in zeilen[i].strip().strip("|").split("|")])
                i += 1
            kopfhtml = "".join("<th>%s</th>" % inline(z) for z in kopf)
            zeilenhtml = "".join(
                "<tr>%s</tr>" % "".join("<td>%s</td>" % inline(z) for z in r)
                for r in koerper
            )
            teile.append(
                '<div class="tabellenrahmen" data-auftritt>'
                "<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>"
                % (kopfhtml, zeilenhtml)
            )
            continue

        # Zitat
        if blank.startswith("> "):
            satz = []
            while i < n and zeilen[i].strip().startswith("> "):
                satz.append(zeilen[i].strip()[2:])
                i += 1
            teile.append('<blockquote data-auftritt>%s</blockquote>' % inline(" ".join(satz)))
            continue

        # Aufzaehlung
        if re.match(r"^[-*+]\s+", blank):
            punkte = []
            while i < n and re.match(r"^[-*+]\s+", zeilen[i].strip()):
                punkte.append(re.sub(r"^[-*+]\s+", "", zeilen[i].strip()))
                i += 1
            teile.append(
                '<ul class="haken" data-auftritt>%s</ul>'
                % "".join("<li>%s</li>" % inline(p) for p in punkte)
            )
            continue

        # Nummerierte Liste
        if re.match(r"^\d+\.\s+", blank):
            punkte = []
            while i < n and re.match(r"^\d+\.\s+", zeilen[i].strip()):
                punkte.append(re.sub(r"^\d+\.\s+", "", zeilen[i].strip()))
                i += 1
            teile.append(
                "<ol data-auftritt>%s</ol>"
                % "".join("<li>%s</li>" % inline(p) for p in punkte)
            )
            continue

        # Absatz
        absatz = []
        while i < n and zeilen[i].strip() and not re.match(
            r"^(#{2,4}\s|>\s|[-*+]\s|\d+\.\s|\|)", zeilen[i].strip()
        ) and not re.match(r"^-{3,}$", zeilen[i].strip()):
            absatz.append(zeilen[i].strip())
            i += 1
        satz = " ".join(absatz)
        klasse = ' class="fuehrung"' if satz.startswith("!! ") else ""
        if klasse:
            satz = satz[3:]
        teile.append("<p%s data-auftritt>%s</p>" % (klasse, inline(satz)))

    return "\n".join(teile)


# ===========================================================================
# Darstellung: Bausteine (::: ... :::)
# ===========================================================================

# ===========================================================================
# Sinnbilder und Markenzeichen
# Strichzeichnungen im 24x24-Raster, einfarbig ueber currentColor. Kein
# externer Dienst, keine Schriftart - die Pfade stehen hier im Code.
# ===========================================================================

SINNBILDER = {
    "berg":       '<path d="m8 3 4 8 5-5 5 15H2L8 3z"/>',
    "kompass":    '<circle cx="12" cy="12" r="10"/><path d="m16.24 7.76-2.12 6.36-6.36 2.12 2.12-6.36 6.36-2.12z"/>',
    "schild":     '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/>',
    "film":       '<rect width="18" height="18" x="3" y="3" rx="2"/><path d="M7 3v18M17 3v18M3 7.5h4M17 7.5h4M3 12h18M3 16.5h4M17 16.5h4"/>',
    "abspielen":  '<circle cx="12" cy="12" r="10"/><path d="m10 7.8 6.5 4.2-6.5 4.2z"/>',
    "fernseher":  '<rect width="20" height="14" x="2" y="7" rx="2"/><path d="m17 2-5 5-5-5"/>',
    "qr":         '<rect width="7" height="7" x="3" y="3" rx="1"/><rect width="7" height="7" x="14" y="3" rx="1"/><rect width="7" height="7" x="3" y="14" rx="1"/><path d="M14 14h3v3h-3zM20.5 14v3M14 20.5h3M20.5 20.5h.01"/>',
    "handy":      '<rect width="13" height="20" x="5.5" y="2" rx="2.5"/><path d="M12 18h.01"/>',
    "warenkorb":  '<circle cx="9" cy="20.5" r="1.3"/><circle cx="18" cy="20.5" r="1.3"/><path d="M2 2.5h2.6l2.7 12.1a2 2 0 0 0 2 1.6h8.5a2 2 0 0 0 2-1.5l1.7-7.2H5.4"/>',
    "rucksack":   '<path d="M4 10.5A4.5 4.5 0 0 1 8.5 6h7a4.5 4.5 0 0 1 4.5 4.5V19a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2z"/><path d="M8.5 6V4.5A2.5 2.5 0 0 1 11 2h2a2.5 2.5 0 0 1 2.5 2.5V6M8.5 21v-4.5A1.5 1.5 0 0 1 10 15h4a1.5 1.5 0 0 1 1.5 1.5V21M9 10.5h6"/>',
    "flasche":    '<path d="M10 2h4v3.4a3 3 0 0 0 .6 1.8l.8 1.1a4 4 0 0 1 .6 2.2V20a2 2 0 0 1-2 2h-4a2 2 0 0 1-2-2v-9.5a4 4 0 0 1 .6-2.2l.8-1.1A3 3 0 0 0 10 5.4z"/><path d="M8 13h8"/>',
    "zelt":       '<path d="M3 21 13.5 3M10.5 3 21 21M3 21h18M12 12.5 16.5 21M12 12.5 7.5 21"/>',
    "blatt":      '<path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.5 19 2c1 2 2 4.2 2 8 0 5.5-4.8 10-10 10z"/><path d="M2 21c0-3 1.9-5.4 5.1-6"/>',
    "globus":     '<circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>',
    "menschen":   '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.9M16 3.1a4 4 0 0 1 0 7.8"/>',
    "buch":       '<path d="M12 7.5v13.5M3 18a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h5a4 4 0 0 1 4 4 4 4 0 0 1 4-4h5a1 1 0 0 1 1 1v13a1 1 0 0 1-1 1h-6a3 3 0 0 0-3 3 3 3 0 0 0-3-3z"/>',
    "stern":      '<path d="M11.5 2.6a.6.6 0 0 1 1 0l2.4 5 5.4.8a.6.6 0 0 1 .35 1l-3.9 3.8.9 5.4a.6.6 0 0 1-.87.63L12 16.7l-4.8 2.53a.6.6 0 0 1-.87-.63l.9-5.4-3.9-3.8a.6.6 0 0 1 .34-1l5.4-.8z"/>',
    "haken":      '<circle cx="12" cy="12" r="10"/><path d="m8.5 12 2.5 2.5 4.5-5"/>',
    "uhr":        '<circle cx="12" cy="12" r="10"/><path d="M12 6.5V12l3.5 2"/>',
    "schnee":     '<path d="M12 2v20M4.2 7 19.8 17M19.8 7 4.2 17M12 6.2 9.3 3.5M12 6.2l2.7-2.7M12 17.8l-2.7 2.7M12 17.8l2.7 2.7"/>',
    "feuer":      '<path d="M12 22c3.9 0 7-2.8 7-6.5 0-5-4-6.5-4-10.5-2 1-3 3-3 5-1-.5-2-2-2-3.5C7.5 8 5 10.8 5 15.5 5 19.2 8.1 22 12 22z"/>',
    "funke":      '<path d="m12 3 1.9 4.6 4.6 1.9-4.6 1.9L12 16l-1.9-4.6L5.5 9.5l4.6-1.9z"/><path d="m19 14.6.8 2 2 .8-2 .8-.8 2-.8-2-2-.8 2-.8z"/>',
    "pin":        '<path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0z"/><circle cx="12" cy="10" r="3"/>',
    "pfeil":      '<path d="M4 12h15M13 6l6 6-6 6"/>',
    "wachstum":   '<path d="M3 20.5h18M7 20.5V14M12 20.5V8.5M17 20.5v-16"/>',
    "ziel":       '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.4"/>',
    "herz":       '<path d="M12 21 4.8 13.9C3.4 12.5 2 10.7 2 8.5A4.5 4.5 0 0 1 12 5.6 4.5 4.5 0 0 1 22 8.5c0 2.2-1.4 4-2.8 5.4z"/>',
    "spiel":      '<rect width="20" height="12.5" x="2" y="5.8" rx="6.2"/><path d="M6.5 12h3.5M8.25 10.25v3.5M15 13.2h.01M17.8 10.6h.01"/>',
    "gabel":      '<path d="M4 2v6a3 3 0 0 0 3 3 3 3 0 0 0 3-3V2M7 2v9M7 11v11M18 2c-1.6 2-2.2 4.2-2.2 7 0 2 .8 3.2 2.2 3.2V22"/>',
    "schere":     '<circle cx="6" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M20 4 8.1 15.9M14.5 14.5 20 20M8.1 8.1 12 12"/>',
    "siegel":     '<circle cx="12" cy="9" r="6.5"/><path d="M8 14.5 6.5 22l5.5-2.8L17.5 22 16 14.5"/>',
    "schuh":      '<path d="M2 16.5h19.5a1 1 0 0 0 1-1v-.9a2 2 0 0 0-1.4-1.9l-5.1-1.7a3 3 0 0 1-1.3-.9l-2.4-2.8a2 2 0 0 0-1.6-.8H6a1 1 0 0 0-1 1V13H2z"/><path d="M5 10.5h2.5M9.2 8.6l1.6 1.9"/>',
    "dokument":   '<path d="M14 2H7a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7z"/><path d="M14 2v5h5M9 13h6M9 17h4"/>',
    "fabrik":     '<path d="M2 20.5h20"/><path d="M3.5 20.5V10l5.5 3.5V10l5.5 3.5V6.5h5.5v14"/><path d="M18 10.5h.01M18 14.5h.01"/>',
    "laden":      '<path d="m3 9.5 1.2-4.9A1 1 0 0 1 5.2 4h13.6a1 1 0 0 1 1 .6L21 9.5"/><path d="M3 9.5a3 3 0 0 0 6 0 3 3 0 0 0 6 0 3 3 0 0 0 6 0"/><path d="M4.5 12.3V20a1 1 0 0 0 1 1h13a1 1 0 0 0 1-1v-7.7"/>',
    "monitor":    '<rect width="20" height="14" x="2" y="3.5" rx="2"/><path d="M8.5 21h7M12 17.5V21"/>',
    "blitz":      '<path d="M13 2 4 14h7l-1 8 9-12h-7z"/>',
    "etikett":    '<path d="m20.6 13.4-7.2 7.2a2 2 0 0 1-2.8 0l-7.2-7.2a2 2 0 0 1-.6-1.5l.3-7a2 2 0 0 1 1.9-1.9l7-.3a2 2 0 0 1 1.5.6l7.1 7.1a2 2 0 0 1 0 2.8z"/><circle cx="7.6" cy="7.6" r="1.4"/>',
    "luft":       '<path d="M3 8h10.5a3 3 0 1 0-3-3M3 12h15a3 3 0 1 1-3 3M3 16h8.5a2.5 2.5 0 1 1-2.5 2.5"/>',
    "schloss":    '<rect width="15" height="10.5" x="4.5" y="11" rx="2"/><path d="M7.8 11V7a4.2 4.2 0 0 1 8.4 0v4"/>',
    "stapel":     '<path d="m12 2.5 9.5 4.8-9.5 4.8-9.5-4.8z"/><path d="m2.5 12.2 9.5 4.8 9.5-4.8M2.5 17l9.5 4.8L21.5 17"/>',
    "haus":       '<path d="M3 10.5 12 3l9 7.5"/><path d="M5.5 9.5V20a1 1 0 0 0 1 1h11a1 1 0 0 0 1-1V9.5"/>',
}

# Wort-/Bildmarken der Plattformen. Pfade aus den offiziellen Markenzeichen,
# flaechig gezeichnet (fill), deshalb getrennt von den Strichsinnbildern.
MARKENZEICHEN = {
    "facebook":  ('#1877F2', 'M9.101 23.691v-7.98H6.627v-3.667h2.474v-1.58c0-4.085 1.848-5.978 5.858-5.978.401 0 .955.042 1.468.103a8.68 8.68 0 0 1 1.141.195v3.325a8.623 8.623 0 0 0-.653-.036 26.805 26.805 0 0 0-.733-.009c-.707 0-1.259.096-1.675.309a1.686 1.686 0 0 0-.679.622c-.258.42-.374.995-.374 1.752v1.297h3.919l-.386 2.103-.287 1.564h-3.246v8.245C19.396 23.238 24 18.179 24 12.044c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.628 3.874 10.35 9.101 11.647Z'),
    "instagram": ('#E4405F', 'M12 0C8.74 0 8.333.015 7.053.072 5.775.132 4.905.333 4.14.63c-.789.306-1.459.717-2.126 1.384S.935 3.35.63 4.14C.333 4.905.131 5.775.072 7.053.012 8.333 0 8.74 0 12s.015 3.667.072 4.947c.06 1.277.261 2.148.558 2.913.306.788.717 1.459 1.384 2.126.667.666 1.336 1.079 2.126 1.384.766.296 1.636.499 2.913.558C8.333 23.988 8.74 24 12 24s3.667-.015 4.947-.072c1.277-.06 2.148-.262 2.913-.558.788-.306 1.459-.718 2.126-1.384.666-.667 1.079-1.335 1.384-2.126.296-.765.499-1.636.558-2.913.06-1.28.072-1.687.072-4.947s-.015-3.667-.072-4.947c-.06-1.277-.262-2.149-.558-2.913-.306-.789-.718-1.459-1.384-2.126C21.319 1.347 20.651.935 19.86.63c-.765-.297-1.636-.499-2.913-.558C15.667.012 15.26 0 12 0zm0 2.16c3.203 0 3.585.016 4.85.071 1.17.055 1.805.249 2.227.415.562.217.96.477 1.382.896.419.42.679.819.896 1.381.164.422.36 1.057.413 2.227.057 1.266.07 1.646.07 4.85s-.015 3.585-.074 4.85c-.061 1.17-.256 1.805-.421 2.227-.224.562-.479.96-.899 1.382-.419.419-.824.679-1.38.896-.42.164-1.065.36-2.235.413-1.274.057-1.649.07-4.859.07-3.211 0-3.586-.015-4.859-.074-1.171-.061-1.816-.256-2.236-.421-.569-.224-.96-.479-1.379-.899-.421-.419-.69-.824-.9-1.38-.165-.42-.359-1.065-.42-2.235-.045-1.26-.061-1.649-.061-4.844 0-3.196.016-3.586.061-4.861.061-1.17.255-1.814.42-2.234.21-.57.479-.96.9-1.381.419-.419.81-.689 1.379-.898.42-.166 1.051-.361 2.221-.421 1.275-.045 1.65-.06 4.859-.06zm0 3.678a6.162 6.162 0 1 0 0 12.324 6.162 6.162 0 0 0 0-12.324zM12 16a4 4 0 1 1 0-8 4 4 0 0 1 0 8zm7.846-10.405a1.441 1.441 0 1 1-2.881 0 1.441 1.441 0 0 1 2.881 0z'),
    "youtube":   ('#FF0000', 'M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z'),
    "tiktok":    ('',        'M12.525.02c1.31-.02 2.61-.01 3.91-.02.08 1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.05-2.89-.35-4.2-.97-.57-.26-1.1-.59-1.62-.93-.01 2.92.01 5.84-.02 8.75-.08 1.4-.54 2.79-1.35 3.94-1.31 1.92-3.58 3.17-5.91 3.21-1.43.08-2.86-.31-4.08-1.03-2.02-1.19-3.44-3.37-3.65-5.71-.02-.5-.03-1-.01-1.49.18-1.9 1.12-3.72 2.58-4.96 1.66-1.44 3.98-2.13 6.15-1.72.02 1.48-.04 2.96-.04 4.44-.99-.32-2.15-.23-3.02.37-.63.41-1.11 1.04-1.36 1.75-.21.51-.15 1.07-.14 1.61.24 1.64 1.82 3.02 3.5 2.87 1.12-.01 2.19-.66 2.77-1.61.19-.33.4-.67.41-1.06.1-1.79.06-3.57.07-5.36.01-4.03-.01-8.05.02-12.07z'),
    "x":         ('',        'M18.901 1.153h3.68l-8.04 9.19L24 22.846h-7.406l-5.8-7.584-6.638 7.584H.474l8.6-9.83L0 1.154h7.594l5.243 6.932ZM17.61 20.644h2.039L6.486 3.24H4.298z'),
    "weibo":     ('#E6162D', 'M10.098 20.323c-3.977.391-7.414-1.406-7.672-4.02-.259-2.609 2.759-5.047 6.74-5.441 3.979-.394 7.413 1.404 7.671 4.018.259 2.6-2.759 5.049-6.737 5.439l-.002.004zM9.05 17.219c-.384.616-1.208.884-1.829.602-.612-.279-.793-.991-.406-1.593.379-.595 1.176-.861 1.793-.601.622.263.82.972.442 1.592zm1.27-1.627c-.141.237-.449.35-.689.257-.236-.09-.313-.354-.185-.591.138-.233.436-.348.672-.263.239.09.319.351.199.597h.003zm.207-2.962c-1.904-.493-4.052.453-4.88 2.131-.846 1.712-.024 3.611 1.894 4.235 1.986.645 4.325-.339 5.138-2.183.802-1.808-.195-3.682-2.152-4.183zm7.844-1.187c-.333-.1-.567-.167-.392-.601.383-.941.423-1.753.008-2.33-.781-1.088-2.919-1.03-5.37-.014 0 0-.769.337-.573-.271.376-1.208.32-2.222-.265-2.807-1.327-1.33-4.861.046-7.891 3.069C1.42 10.75 0 13.166 0 15.254c0 3.995 5.12 6.424 10.129 6.424 6.566 0 10.937-3.816 10.937-6.846 0-1.833-1.542-2.871-2.924-3.311l.229-.078zM19.712 5.59c.267-.291.405-.676.405-1.07 0-.447-.178-.875-.495-1.191a1.69 1.69 0 0 0-1.191-.494c-.361 0-.711.115-1 .328a.37.37 0 0 0-.089.515.37.37 0 0 0 .515.089.93.93 0 0 1 1.243.106.94.94 0 0 1 .081 1.222.37.37 0 0 0 .052.52.37.37 0 0 0 .52-.052l-.041.027zM21.76 7.27a4.03 4.03 0 0 0 .968-2.622 4.05 4.05 0 0 0-1.188-2.864A4.05 4.05 0 0 0 18.676.596a4.04 4.04 0 0 0-1.636.345.56.56 0 1 0 .452 1.025 2.93 2.93 0 0 1 1.184-.25 2.93 2.93 0 0 1 2.082.863 2.93 2.93 0 0 1 .159 3.97.56.56 0 0 0 .843.74V7.27z'),
}


def sinnbild(name, zusatz=""):
    """Ein Strichsinnbild als Inline-SVG. Unbekannter Name: nichts."""
    pfad = SINNBILDER.get((name or "").strip().lower())
    if not pfad:
        return ""
    return ('<svg class="sinnbild%s" viewBox="0 0 24 24" fill="none" '
            'stroke="currentColor" stroke-width="1.5" stroke-linecap="round" '
            'stroke-linejoin="round" aria-hidden="true">%s</svg>'
            % ((" " + zusatz) if zusatz else "", pfad))


def markenzeichen(name):
    """Plattformlogo als Inline-SVG. Rueckgabe: (html, farbe)."""
    eintrag = MARKENZEICHEN.get((name or "").strip().lower())
    if not eintrag:
        return "", ""
    farbe, pfad = eintrag
    return ('<svg class="markenzeichen" viewBox="0 0 24 24" fill="currentColor" '
            'aria-hidden="true"><path d="%s"/></svg>' % pfad), farbe


def kennung_aus(titel):
    """Aus einer Ueberschrift die Sprungmarke machen. Eine Regel, zwei
    Verwendungen: Abschnitte und Querbahnen muessen dieselbe treffen."""
    return re.sub(r"[^a-z0-9]+", "-", (titel or "").lower()).strip("-")[:40]


def inhalt_rendern(zeilen):
    """Wie text_rendern, nimmt aber zusaetzlich ::: Bausteine entgegen.
    Damit darf in einer Karte oder einem Reiter wieder ein Baustein stehen."""
    if not any(z.strip().startswith(":::") for z in zeilen):
        return text_rendern(zeilen)
    teile = []
    for art, daten in bloecke_teilen(zeilen):
        if art == "block":
            teile.append(block_rendern(daten[0], daten[1], daten[2]))
        elif art == "text":
            teile.append(text_rendern(daten))
        else:  # Abschnittsueberschrift gehoert nicht in einen Baustein
            teile.append("<h3>%s</h3>" % inline(daten[0]))
    return "".join(teile)


def karten_lesen(zeilen):
    """Zerlegt den Inhalt eines Karten-/Slider-Blocks an jeder ###-Zeile."""
    karten = []
    aktuell = None
    for zeile in zeilen:
        if zeile.strip().startswith("### "):
            if aktuell:
                karten.append(aktuell)
            aktuell = {"titel": zeile.strip()[4:].strip(), "bild": "",
                       "bildtext": "", "icon": "", "text": []}
            continue
        if aktuell is None:
            continue
        m = re.match(r"^\s*(bild|icon):\s*(.+)$", zeile, re.I)
        if m:
            aktuell[m.group(1).lower()] = m.group(2).strip()
            continue
        aktuell["text"].append(zeile)
    if aktuell:
        karten.append(aktuell)
    return karten


def karte_html(karte, nummer=None):
    bild = ""
    if karte["bild"]:
        bild = (
            '<div class="karte__bild"><img src="%s" alt="%s" '
            'loading="lazy" decoding="async"></div>'
            % (sicher(karte["bild"]), sicher(karte["titel"]))
        )
    kopfzeile = ""
    if nummer is not None:
        kopfzeile = '<span class="karte__nummer">%02d</span>' % nummer
    zeichen = sinnbild(karte.get("icon", ""), "sinnbild--karte")
    if zeichen:
        kopfzeile = '<span class="karte__zeichen">%s</span>%s' % (zeichen, kopfzeile)
    return (
        '<article class="karte">%s<div class="karte__text">%s<h3>%s</h3>%s</div></article>'
        % (bild, kopfzeile, inline(karte["titel"]), inhalt_rendern(karte["text"]))
    )


def block_rendern(name, argument, zeilen):
    """Einen ::: Baustein in HTML uebersetzen."""

    # --- Kennzahlen:  Wert | Beschriftung
    if name in ("kennzahlen", "zahlen"):
        felder = []
        for zeile in zeilen:
            if "|" not in zeile:
                continue
            wert, text = [x.strip() for x in zeile.split("|", 1)]
            vor, zahl, nach = zahl_zerlegen(wert)
            if zahl is None:
                wertspan = '<span class="kennzahl__wert">%s</span>' % inline(wert)
            else:
                # Jahreszahlen wie 1909 bekommen keinen Tausenderpunkt,
                # "13.000" behaelt ihn. Massgeblich ist die Schreibweise
                # in der inhalt.md.
                gruppiert = "1" if "." in zahl else "0"
                wertspan = (
                    '<span class="kennzahl__wert" data-zaehlen="%s" data-vor="%s" '
                    'data-nach="%s" data-fertig="%s" data-gruppiert="%s">%s</span>'
                    % (sicher(zahl), sicher(vor), sicher(nach), sicher(wert),
                       gruppiert, sicher(wert))
                )
            felder.append(
                '<div class="kennzahl">%s<span class="kennzahl__text">%s</span></div>'
                % (wertspan, inline(text))
            )
        if not felder:
            return ""
        return '<div class="kennzahlen" data-auftritt>%s</div>' % "".join(felder)

    # --- Karten (Raster)
    if name == "karten":
        karten = karten_lesen(zeilen)
        if not karten:
            return ""
        zusatz = " karten--zwei" if argument.strip() == "zwei" else ""
        inner = "".join(
            '<div data-auftritt style="--verzug:%dms">%s</div>' % (idx * 90, karte_html(k))
            for idx, k in enumerate(karten)
        )
        return '<div class="karten%s">%s</div>' % (zusatz, inner)

    # --- Slider (wischen)
    if name in ("slider", "sortiment"):
        karten = karten_lesen(zeilen)
        if not karten:
            return ""
        nummeriert = argument.strip() == "nummeriert"
        spur = "".join(
            karte_html(k, idx + 1 if nummeriert else None)
            for idx, k in enumerate(karten)
        )
        return (
            '<div class="slider" data-auftritt>'
            '<div class="slider__spur">%s</div>'
            '<p class="slider__hinweis">Zum Blättern seitlich wischen &rarr;</p>'
            '<div class="slider__steuer">'
            '<button class="slider__knopf" data-slider="zurueck" type="button" '
            'aria-label="Vorheriges">&#8592;</button>'
            '<button class="slider__knopf" data-slider="vor" type="button" '
            'aria-label="Nächstes">&#8594;</button>'
            "</div></div>" % spur
        )

    # --- Fakten / Konditionen:  Bezeichnung | Wert
    if name in ("fakten", "konditionen", "eckdaten"):
        reihen = []
        for idx, zeile in enumerate(zeilen):
            if "|" not in zeile:
                continue
            bez, wert = [x.strip() for x in zeile.split("|", 1)]
            reihen.append(
                '<div class="fakt" data-auftritt style="--verzug:%dms">'
                '<span class="fakt__name">%s</span>'
                '<span class="fakt__wert">%s</span></div>'
                % (idx * 60, inline(bez), inline(wert))
            )
        if not reihen:
            return ""
        return '<div class="fakten">%s</div>' % "".join(reihen)

    # --- Zeitplan:  Zeitpunkt | Was passiert
    if name in ("zeitplan", "fahrplan"):
        schritte = []
        for idx, zeile in enumerate(zeilen):
            if "|" not in zeile:
                continue
            zeit, was = [x.strip() for x in zeile.split("|", 1)]
            schritte.append(
                '<div class="schritt" data-auftritt="seite" style="--verzug:%dms">'
                '<span class="schritt__zeit">%s</span>'
                '<span class="schritt__was">%s</span></div>'
                % (idx * 110, inline(zeit), inline(was))
            )
        if not schritte:
            return ""
        return '<div class="zeitplan">%s</div>' % "".join(schritte)

    # --- Zitat:  Text, danach eine Zeile mit "-- Quelle"
    if name == "zitat":
        satz, quelle = [], ""
        for zeile in zeilen:
            s = zeile.strip()
            if s.startswith("--"):
                quelle = s.lstrip("-").strip()
            elif s:
                satz.append(s)
        if not satz:
            return ""
        q = ('<div class="zitat__quelle">%s</div>' % inline(quelle)) if quelle else ""
        return (
            '<figure class="zitat" data-auftritt>'
            '<div class="zitat__text">%s</div>%s</figure>'
            % (inline(" ".join(satz)), q)
        )

    # --- Galerie: nur Bildzeilen
    if name == "galerie":
        bilder = []
        for idx, zeile in enumerate(zeilen):
            m = re.match(r"^\s*!\[([^\]]*)\]\(([^)]+)\)\s*$", zeile)
            if not m:
                continue
            text, quelle = m.group(1), m.group(2).strip()
            bu = ('<figcaption>%s</figcaption>' % inline(text)) if text else ""
            bilder.append(
                '<figure data-auftritt="zoom" style="--verzug:%dms">'
                '<img src="%s" alt="%s" loading="lazy" decoding="async">%s</figure>'
                % (idx * 70, sicher(quelle), sicher(text), bu)
            )
        if not bilder:
            return ""
        zusatz = ""
        if argument.strip() in ("drei", "3"):
            zusatz = " galerie--drei"
        elif argument.strip() in ("zwei", "2"):
            zusatz = " galerie--zwei"
        return '<div class="galerie%s">%s</div>' % (zusatz, "".join(bilder))

    # --- Parallaxband:  ::: parallax bilder/x.jpg
    if name in ("parallax", "band"):
        bild = ""
        if argument:
            bild = ('<div class="band__bild" data-parallax="0.18" '
                    'style="background-image:url(\'%s\')"></div>' % sicher(argument))
        return (
            '<section class="band">%s<div class="band__schleier"></div>'
            '<div class="bahn">%s</div></section>'
            % (bild, text_rendern(zeilen))
        )

    # --- Reiter: Inhalte nebeneinander statt untereinander. Spart Hoehe.
    #     Funktioniert ohne JavaScript ueber versteckte Radioschalter.
    if name in ("reiter", "tabs"):
        punkte = karten_lesen(zeilen)
        if not punkte:
            return ""
        block_rendern.zaehler = getattr(block_rendern, "zaehler", 0) + 1
        gruppe = "rt%d" % block_rendern.zaehler

        # Die Schalter muessen direkte Geschwister der Blaetter sein, sonst
        # findet die ~-Regel sie nicht. Beschriftungen stehen getrennt davon
        # in der Leiste und greifen ueber "for" auf die Schalter zu.
        schalter, knoepfe, blaetter, regeln = [], [], [], []
        for i, k in enumerate(punkte):
            kennung = "%s-%d" % (gruppe, i)
            schalter.append(
                '<input class="reiter__schalter" type="radio" name="%s" id="%s"%s>'
                % (gruppe, kennung, " checked" if i == 0 else "")
            )
            knoepfe.append(
                '<label class="reiter__knopf" for="%s">%s<span>%s</span></label>'
                % (kennung, sinnbild(k.get("icon", "")), inline(k["titel"]))
            )
            bild = ""
            if k["bild"]:
                bild = ('<figure class="reiter__bild"><img src="%s" alt="%s" '
                        'loading="lazy" decoding="async"></figure>'
                        % (sicher(k["bild"]), sicher(k["titel"])))
            # Zwei Spalten nur, wenn es ein Bild gibt - sonst stuende rechts
            # eine leere Haelfte.
            blaetter.append(
                '<div class="reiter__blatt%s" data-fuer="%s">%s<div>%s</div></div>'
                % (" reiter__blatt--mit-bild" if bild else "", kennung, bild,
                   inhalt_rendern(k["text"]))
            )
            regeln.append('#%s:checked~[data-fuer="%s"]{display:grid}' % (kennung, kennung))
            regeln.append('#%s:checked~.reiter__leiste label[for="%s"]'
                          '{color:var(--tinte);border-color:var(--akzent)}'
                          % (kennung, kennung))
            regeln.append('#%s:checked~.reiter__leiste label[for="%s"] '
                          '.sinnbild{opacity:1}' % (kennung, kennung))

        return (
            '<div class="reiter" data-auftritt><style>%s</style>%s'
            '<div class="reiter__leiste">%s</div>%s</div>'
            % ("".join(regeln), "".join(schalter), "".join(knoepfe),
               "".join(blaetter))
        )

    # --- Video. Liegt die Datei in bilder/, wird sie eingebunden.
    if name == "video":
        if not argument:
            return ""
        werte = {}
        rest = []
        for zeile in zeilen:
            m = re.match(r"^\s*(poster|titel|text):\s*(.+)$", zeile, re.I)
            if m:
                werte[m.group(1).lower()] = m.group(2).strip()
            elif zeile.strip():
                rest.append(zeile)
        poster = (' poster="%s"' % sicher(werte["poster"])) if werte.get("poster") else ""
        kopf = ('<h3>%s</h3>' % inline(werte["titel"])) if werte.get("titel") else ""
        return (
            '<figure class="video" data-auftritt>%s'
            '<video controls preload="none" playsinline%s>'
            '<source src="%s" type="video/mp4">'
            "Ihr Browser kann dieses Video nicht abspielen."
            "</video>%s</figure>"
            % (kopf, poster, sicher(argument), text_rendern(rest))
        )

    # --- Belege: Zahl, Aussage, Quelle. Ohne Quelle keine Zahl.
    #     Schema je Zeile:  Beschriftung | Wert | Quelle und Datum
    if name in ("belege", "marktdaten"):
        reihen = []
        for idx, zeile in enumerate(zeilen):
            if zeile.count("|") < 2:
                if zeile.strip():
                    sys.stderr.write("  ! Beleg ohne Quelle \u00fcbersprungen: %s\n"
                                     % zeile.strip()[:60])
                continue
            was, wert, quelle = [x.strip() for x in zeile.split("|", 2)]
            reihen.append(
                '<div class="beleg" data-auftritt style="--verzug:%dms">'
                '<div class="beleg__wert">%s</div>'
                '<div class="beleg__text"><span class="beleg__was">%s</span>'
                '<span class="beleg__quelle">%s</span></div></div>'
                % (idx * 70, inline(wert), inline(was), inline(quelle))
            )
        if not reihen:
            return ""
        return '<div class="belege">%s</div>' % "".join(reihen)

    # --- Prospektsimulation: wie der Artikel im Handzettel aussehen wuerde.
    #     Bewusst als Simulation gekennzeichnet, nie als Angebot des Haendlers.
    if name in ("prospekt", "handzettel"):
        haendler = FELDER.get("kunde", "")
        zeile_oben = ""
        hinweis = ("Simulation zur Veranschaulichung. Preise aus dem Volumenband "
                   "des Styleguides abgeleitet \u2014 kein Angebot des H\u00e4ndlers.")
        artikel = []
        aktuell = None

        for zeile in zeilen:
            m = re.match(r"^\s*(haendler|zeile|hinweis):\s*(.+)$", zeile, re.I)
            if m and aktuell is None:
                schluessel, wert = m.group(1).lower(), m.group(2).strip()
                if schluessel == "haendler":
                    haendler = wert
                elif schluessel == "zeile":
                    zeile_oben = wert
                else:
                    hinweis = wert
                continue
            if zeile.strip().startswith("### "):
                if aktuell:
                    artikel.append(aktuell)
                aktuell = {"titel": zeile.strip()[4:].strip(), "bild": "",
                           "preis": "", "statt": "", "zusatz": ""}
                continue
            if aktuell is None:
                continue
            m = re.match(r"^\s*(bild|preis|statt|zusatz):\s*(.+)$", zeile, re.I)
            if m:
                aktuell[m.group(1).lower()] = m.group(2).strip()
        if aktuell:
            artikel.append(aktuell)
        if not artikel:
            return ""

        kacheln = []
        for a in artikel:
            bild = ""
            if a["bild"]:
                bild = ('<div class="zettel__bild"><img src="%s" alt="%s" '
                        'loading="lazy" decoding="async"></div>'
                        % (sicher(a["bild"]), sicher(a["titel"])))
            statt = ('<span class="zettel__statt">statt %s</span>' % inline(a["statt"])) \
                if a["statt"] else ""
            preis = ""
            if a["preis"]:
                teile = a["preis"].replace(".", ",").split(",")
                gross = teile[0]
                klein = (teile[1] if len(teile) > 1 else "00")[:2].ljust(2, "0")
                preis = ('<div class="zettel__preis"><span class="zettel__euro">%s</span>'
                         '<span class="zettel__cent">%s</span></div>'
                         % (sicher(gross), sicher(klein)))
            zusatz = ('<span class="zettel__zusatz">%s</span>' % inline(a["zusatz"])) \
                if a["zusatz"] else ""
            kacheln.append(
                '<article class="zettel">%s<div class="zettel__text">'
                '<h3>%s</h3>%s%s%s</div></article>'
                % (bild, inline(a["titel"]), zusatz, statt, preis)
            )

        kopf = ""
        if haendler or zeile_oben:
            kopf = ('<div class="prospekt__kopf"><span class="prospekt__haendler">%s</span>'
                    '<span class="prospekt__zeile">%s</span></div>'
                    % (inline(haendler), inline(zeile_oben)))

        return (
            '<div class="prospekt" data-auftritt>%s'
            '<div class="prospekt__blatt">%s</div>'
            '<p class="prospekt__hinweis">%s</p></div>'
            % (kopf, "".join(kacheln), inline(hinweis))
        )

    # --- Kontaktformular
    # Ohne Server kann eine Seite nichts verschicken. Das Formular setzt
    # deshalb eine fertige E-Mail im Mailprogramm des Einkaeufers auf.
    # Vorteil: keine Daten an Dritte, funktioniert auch offline.
    if name in ("formular", "kontaktformular"):
        werte = {}
        rest = []
        for zeile in zeilen:
            m = re.match(r"^\s*(empfaenger|titel|text|knopf):\s*(.+)$", zeile, re.I)
            if m:
                werte[m.group(1).lower()] = m.group(2).strip()
            elif zeile.strip():
                rest.append(zeile)

        empf = werte.get("empfaenger") or FELDER.get("mail", "")
        if not empf:
            sys.stderr.write("  ! Formular ohne Empfaenger - weggelassen.\n")
            return ""

        titel = werte.get("titel", "Anfrage senden")
        knopf = werte.get("knopf", "Anfrage senden")
        betreff = "%s \u2014 Anfrage" % FELDER.get("projekt", "Anfrage")

        felder_html = (
            '<div class="feld feld--doppelt">'
            '<div><label for="f-firma">Unternehmen</label>'
            '<input id="f-firma" name="Unternehmen" type="text" autocomplete="organization" required></div>'
            '<div><label for="f-name">Ihr Name</label>'
            '<input id="f-name" name="Name" type="text" autocomplete="name" required></div>'
            "</div>"
            '<div class="feld feld--doppelt">'
            '<div><label for="f-mail">E-Mail</label>'
            '<input id="f-mail" name="E-Mail" type="email" autocomplete="email" required></div>'
            '<div><label for="f-tel">Telefon <span style="text-transform:none;letter-spacing:0">(optional)</span></label>'
            '<input id="f-tel" name="Telefon" type="tel" autocomplete="tel"></div>'
            "</div>"
            '<div class="feld"><label for="f-anliegen">Worum geht es?</label>'
            '<select id="f-anliegen" name="Anliegen">'
            "<option>Muster anfordern</option>"
            "<option>Kalkulation und Konditionen</option>"
            "<option>Termin vereinbaren</option>"
            "<option>Allgemeine Frage</option>"
            "</select></div>"
            '<div class="feld"><label for="f-text">Ihre Nachricht</label>'
            '<textarea id="f-text" name="Nachricht" rows="5"></textarea></div>'
        )

        return (
            '<form class="formular" data-auftritt data-mailto="%s" data-betreff="%s" '
            'action="mailto:%s" method="post" enctype="text/plain">'
            "<h3>%s</h3>%s%s"
            '<div class="knopfreihe">'
            '<button class="knopf knopf--voll" type="submit">%s</button></div>'
            '<p class="formular__hinweis">Mit dem Absenden \u00f6ffnet sich Ihr '
            "E-Mail-Programm mit einer fertigen Nachricht an %s. "
            "Es werden keine Daten an Dritte \u00fcbertragen.</p>"
            "</form>"
            % (sicher(empf), sicher(betreff), sicher(empf), inline(titel),
               text_rendern(rest), felder_html, inline(knopf), sicher(empf))
        )

    # --- Kapitel: bildfuellende Trennseite mit grosser Schrift
    if name == "kapitel":
        bild = ""
        if argument:
            bild = ('<div class="kapitel__bild" style="background-image:url(\'%s\')"></div>'
                    % sicher(argument))
        nummer = schrift = ""
        rest = []
        for zeile in zeilen:
            m = re.match(r"^\s*(nummer|script):\s*(.+)$", zeile, re.I)
            if m:
                if m.group(1).lower() == "nummer":
                    nummer = m.group(2).strip()
                else:
                    schrift = m.group(2).strip()
                continue
            rest.append(zeile)
        kopf = ""
        if nummer:
            kopf += '<span class="kapitel__nummer">%s</span>' % inline(nummer)
        if schrift:
            kopf += '<span class="kapitel__script">%s</span>' % inline(schrift)
        return (
            '<section class="kapitel">%s<div class="kapitel__schleier"></div>'
            '<div class="bahn"><div data-auftritt>%s%s</div></div></section>'
            % (bild, kopf, text_rendern(rest))
        )

    # --- Bildwand: Bild bleibt stehen, Text laeuft vorbei
    if name == "bildwand":
        schritte = karten_lesen(zeilen)
        if not argument or not schritte:
            return text_rendern(zeilen)
        inner = "".join(
            '<div class="bildwand__schritt" data-auftritt>'
            '<span class="bildwand__zahl">%s%02d</span><h3>%s</h3>%s</div>'
            % (sinnbild(k.get("icon", "")), i + 1, inline(k["titel"]),
               inhalt_rendern(k["text"]))
            for i, k in enumerate(schritte)
        )
        return (
            '<div class="bildwand">'
            '<figure class="bildwand__bild"><img src="%s" alt="" '
            'loading="lazy" decoding="async"></figure>'
            '<div class="bildwand__schritte">%s</div></div>'
            % (sicher(argument), inner)
        )

    # --- Aufklapp: Details, die ohne JavaScript funktionieren
    if name in ("aufklapp", "fragen"):
        punkte = karten_lesen(zeilen)
        if not punkte:
            return ""
        inner = "".join(
            "<details><summary>%s</summary>"
            '<div class="aufklapp__inhalt">%s</div></details>'
            % (inline(k["titel"]), inhalt_rendern(k["text"]))
            for k in punkte
        )
        return '<div class="aufklapp" data-auftritt>%s</div>' % inner

    # --- Hinweiskasten
    if name in ("hinweis", "vertraulich"):
        return '<p class="vertraulich" data-auftritt>%s</p>' % inline(
            " ".join(z.strip() for z in zeilen if z.strip())
        )

    # --- Social: Plattformlogo, Zahl, Quelle. Ohne Quelle keine Zahl.
    #     Schema je Zeile:  plattform | Wert | Quelle und Datum | Handle
    if name in ("social", "kanaele"):
        kacheln = []
        for idx, zeile in enumerate(zeilen):
            teile_z = [x.strip() for x in zeile.split("|")]
            if len(teile_z) < 3:
                if zeile.strip():
                    sys.stderr.write("  ! Kanal ohne Quelle \u00fcbersprungen: %s\n"
                                     % zeile.strip()[:60])
                continue
            plattform, wert, quelle = teile_z[0], teile_z[1], teile_z[2]
            handle = teile_z[3] if len(teile_z) > 3 else ""
            logo, farbe = markenzeichen(plattform)
            if not logo:
                sys.stderr.write("  ! Kein Logo f\u00fcr '%s'\n" % plattform)
                logo = sinnbild("globus")
            stil = ("--markenfarbe:%s;" % sicher(farbe)) if farbe else ""
            kacheln.append(
                '<div class="kanal" data-auftritt style="%s--verzug:%dms">'
                '<span class="kanal__logo">%s</span>'
                '<span class="kanal__wert">%s</span>'
                '<span class="kanal__name">%s</span>'
                '<span class="kanal__quelle">%s</span></div>'
                % (stil, idx * 70, logo, inline(wert),
                   inline(handle or plattform.title()), inline(quelle))
            )
        if not kacheln:
            return ""
        return '<div class="kanaele">%s</div>' % "".join(kacheln)

    # --- Sinnbilder: Zeichen statt Satz.  icon | Titel | Beisatz
    if name in ("sinnbilder", "icons", "zeichen"):
        felder = []
        for idx, zeile in enumerate(zeilen):
            if "|" not in zeile:
                continue
            teile_z = [x.strip() for x in zeile.split("|")]
            schluessel, titel = teile_z[0], teile_z[1]
            beisatz = teile_z[2] if len(teile_z) > 2 else ""
            zeichen = sinnbild(schluessel)
            if not zeichen:
                sys.stderr.write("  ! Unbekanntes Sinnbild '%s'\n" % schluessel)
            felder.append(
                '<div class="zeichenfeld" data-auftritt style="--verzug:%dms">'
                '%s<span class="zeichenfeld__titel">%s</span>%s</div>'
                % (idx * 60, zeichen, inline(titel),
                   ('<span class="zeichenfeld__text">%s</span>' % inline(beisatz))
                   if beisatz else "")
            )
        if not felder:
            return ""
        return '<div class="zeichenfelder">%s</div>' % "".join(felder)

    # --- Laufband: Namen ziehen seitlich durch. Eine Zeile je Name.
    #     Der Zug laeuft endlos, deshalb steht die Liste zweimal da.
    if name in ("laufband", "logoband"):
        namen = [z.strip() for z in zeilen if z.strip()]
        if not namen:
            return ""
        glied = "".join('<span class="laufband__glied">%s</span>' % inline(n)
                        for n in namen)
        return (
            '<div class="laufband" data-auftritt>'
            '<div class="laufband__zug">%s</div>'
            '<div class="laufband__zug" aria-hidden="true">%s</div>'
            "</div>" % (glied, glied)
        )

    # --- Querbahn: Beim Runterscrollen laufen die Karten seitlich durch.
    #     Ohne Scroll-Animationen im Browser bleibt ein Wischstreifen uebrig.
    if name in ("quer", "querbahn"):
        karten = karten_lesen(zeilen)
        if not karten:
            return ""
        kopf = ""
        if argument.strip():
            kopf = ('<div class="quer__kopf"><span class="marke">%s</span></div>'
                    % inline(argument.strip()))
        spur = []
        for k in karten:
            bild = ""
            if k["bild"]:
                bild = ('<div class="querkarte__bild"><img src="%s" alt="%s" '
                        'loading="lazy" decoding="async"></div>'
                        % (sicher(k["bild"]), sicher(k["titel"])))
            zeichen = sinnbild(k.get("icon", ""), "sinnbild--karte")
            spur.append(
                '<article class="querkarte">%s<div class="querkarte__text">'
                '%s<h3>%s</h3>%s</div></article>'
                % (bild, zeichen, inline(k["titel"]), inhalt_rendern(k["text"]))
            )
        marke = kennung_aus(argument)
        return (
            '<section class="quer"%s style="--anzahl:%d">'
            '<div class="quer__buehne"><div class="quer__klebe">%s'
            '<div class="quer__spur">%s</div>'
            '<div class="quer__balken"><i></i></div>'
            '<div class="quer__fuss"><p class="quer__hinweis">Seitlich '
            'wischen &rarr;</p><div class="quer__steuer">'
            '<button class="slider__knopf" data-blaettern="zurueck" type="button" '
            'aria-label="Vorheriges">&#8592;</button>'
            '<button class="slider__knopf" data-blaettern="vor" type="button" '
            'aria-label="N\u00e4chstes">&#8594;</button></div></div>'
            "</div></div></section>"
            % ((' id="%s"' % sicher(marke)) if marke else "",
               len(karten), kopf, "".join(spur))
        )

    # Unbekannter Baustein: nicht raten, sondern als Text durchreichen.
    sys.stderr.write("  ! Unbekannter Baustein ':::%s' — als Text übernommen.\n" % name)
    return text_rendern(zeilen)


# ===========================================================================
# Seite zusammensetzen
# ===========================================================================

def koerper_bauen(bloecke):
    """Baut aus der Blockliste den Seitenkoerper."""
    teile = []
    offen = False
    nummer = [0]          # laufende Abschnittsnummer fuer die kleine Marke
    sprungmarken = []     # Titel und Kennung fuer die Fusszeile

    def abschnitt_schliessen():
        nonlocal offen
        if offen:
            teile.append("</div></section>")
            offen = False

    def abschnitt_oeffnen(titel, mods):
        nonlocal offen
        abschnitt_schliessen()
        klassen = ["abschnitt"]
        for m in mods:
            if m in ("hell", "dunkel", "akzent", "versetzt"):
                klassen.append("abschnitt--" + m)
        kennung = kennung_aus(titel)
        if titel:
            sprungmarken.append((kennung or "abschnitt", titel))
        kopf = ""
        if titel:
            nummer[0] += 1
            marke = mods_label(mods) or "%02d" % nummer[0]
            kopf = (
                '<header class="abschnitt__kopf" data-auftritt>'
                '<span class="marke">%s</span><h2>%s</h2></header>'
                % (inline(marke), inline(titel))
            )
        teile.append(
            '<section class="%s" id="%s"><div class="bahn">%s'
            % (" ".join(klassen), sicher(kennung or "abschnitt"), kopf)
        )
        offen = True

    def mods_label(mods):
        for m in mods:
            if m.startswith("label="):
                return m.split("=", 1)[1]
        return ""

    for art, daten in bloecke:
        if art == "abschnitt":
            abschnitt_oeffnen(daten[0], daten[1])
        elif art == "block":
            name, argument, zeilen = daten
            if name in ("parallax", "band", "kapitel", "quer", "querbahn"):
                # Volle Breite: ausserhalb eines Abschnitts
                abschnitt_schliessen()
                if name in ("quer", "querbahn") and argument.strip():
                    sprungmarken.append((kennung_aus(argument), argument.strip()))
                teile.append(block_rendern(name, argument, zeilen))
            else:
                if not offen:
                    teile.append('<section class="abschnitt"><div class="bahn">')
                    offen = True
                teile.append(block_rendern(name, argument, zeilen))
        else:  # text
            if not any(z.strip() for z in daten):
                continue
            if not offen:
                teile.append('<section class="abschnitt"><div class="bahn">')
                offen = True
            teile.append(text_rendern(daten))

    abschnitt_schliessen()
    return "\n".join(teile), sprungmarken


def seite_bauen(felder, koerper, vorlage_html, sprungmarken=()):
    kunde   = felder.get("kunde", "")
    projekt = felder.get("projekt", "Pitch")
    claim   = felder.get("claim", "")
    titel   = felder.get("titel", "%s — %s" % (projekt, kunde) if kunde else projekt)
    akzent  = felder.get("akzent", "").strip()
    herobild = felder.get("hero-bild", felder.get("herobild", "")).strip()
    entwurf  = felder.get("status", "").strip().lower() in ("entwurf", "draft")

    # Absender der Seite. Voreinstellung ist CGT; ein Projekt, das im Namen
    # eines Partners verschickt wird, setzt die Felder in seiner inhalt.md.
    ab_kurz   = felder.get("absender", "CGT")
    ab_zusatz = felder.get("absender-zusatz", "Coldewey Goetz Trade")
    ab_name   = felder.get("absender-name", "CGT UG")
    ab_zeilen = felder.get(
        "absender-zeilen",
        "Coldewey Goetz Trade | Biebricher Allee 36 \u00b7 65187 Wiesbaden | "
        "Amtsgericht Wiesbaden \u00b7 HRB 35897",
    )
    ab_fuehrung = felder.get("absender-fuehrung",
                             "Gesch\u00e4ftsf\u00fchrung: Sascha Coldewey, Thomas Goetz")

    ab_recht = felder.get(
        "absender-recht",
        "CGT UG (haftungsbeschr\u00e4nkt)" if ab_name == "CGT UG" else ab_name,
    )

    kopf_absender = ('<a class="kopf__logo" href="#">%s <span>%s</span></a>'
                     % (sicher(ab_kurz), sicher(ab_zusatz)))


    # Hero
    # Bildausschnitt pro Projekt steuerbar. Voreinstellung ist die Mitte;
    # steht das Motiv aussermittig, verschwindet es sonst am Handy im
    # Beschnitt. Beispiel:  hero-position: 20% center
    hero_pos = felder.get("hero-position", "").strip()
    hero_bild_html = ""
    if herobild:
        hero_bild_html = (
            '<div class="hero__bild" data-parallax="0.22" '
            'style="background-image:url(\'%s\')%s"></div>'
            % (sicher(herobild),
               (";background-position:%s" % sicher(hero_pos)) if hero_pos else "")
        )

    # Markenlogo im Hero. Ist zusaetzlich ein Partnerlogo gesetzt, entsteht
    # ein Doppel: Partner (der Empfaenger) links, Marke rechts.
    markenlogo = felder.get("marken-logo", "").strip()
    partnerlogo = felder.get("partner-logo", "").strip()
    logo_html = ""
    if markenlogo and partnerlogo:
        logo_html = (
            '<div class="hero__paar" data-auftritt>'
            '<img class="hero__logo hero__logo--partner" src="%s" alt="%s">'
            '<span class="hero__mal" aria-hidden="true">&times;</span>'
            '<img class="hero__logo" src="%s" alt="%s"></div>'
            % (sicher(partnerlogo), sicher(kunde or "Partner"),
               sicher(markenlogo), sicher(felder.get("marke", projekt)))
        )
    elif markenlogo:
        logo_html = ('<img class="hero__logo" src="%s" alt="%s" data-auftritt>'
                     % (sicher(markenlogo), sicher(felder.get("marke", projekt))))

    schild = ""
    if kunde:
        schild = ('<div class="hero__schild" data-auftritt>Pitch für %s</div>'
                  % sicher(kunde))

    fusszeilen = []
    if felder.get("kanal"):
        fusszeilen.append("Kanal: " + felder["kanal"])
    if felder.get("datum"):
        fusszeilen.append("Stand: " + datum_lang(felder["datum"]))
    if felder.get("ansprechpartner"):
        fusszeilen.append("%s, %s" % (felder["ansprechpartner"], ab_name))
    hero_fuss = ""
    if fusszeilen:
        hero_fuss = ('<div class="hero__fuss" data-auftritt style="--verzug:320ms">%s</div>'
                     % "".join("<span>%s</span>" % inline(z) for z in fusszeilen))

    hero = (
        '<header class="hero">%s<div class="hero__schleier"></div>'
        '<div class="bahn">%s%s<h1 data-auftritt style="--verzug:80ms">%s</h1>'
        '%s%s</div><div class="hero__runter" aria-hidden="true"></div></header>'
        % (
            hero_bild_html,
            logo_html,
            schild,
            inline(projekt),
            ('<p class="hero__claim" data-auftritt style="--verzug:200ms">%s</p>' % inline(claim))
            if claim else "",
            hero_fuss,
        )
    )

    # Kontaktblock in der Fusszeile der Seite
    name = felder.get("ansprechpartner", "")
    mail = felder.get("mail", felder.get("email", ""))
    tel  = felder.get("telefon", "")
    knoepfe = []
    if mail:
        betreff = quote("%s \u2014 R\u00fcckfrage" % projekt)
        knoepfe.append('<a class="knopf knopf--voll" href="mailto:%s?subject=%s">%s</a>'
                       % (sicher(mail), betreff, "Gespr\u00e4ch vereinbaren"))
    if tel:
        knoepfe.append('<a class="knopf knopf--rand" href="tel:%s">%s</a>'
                       % (sicher(re.sub(r"[^\d+]", "", tel)), sicher(tel)))

    # Abschluss: der Handlungsaufruf am Seitenende. Texte sind pro Projekt
    # \u00fcberschreibbar, sonst greift eine neutrale Standardformulierung.
    kontakt_html = ""
    if name or mail or tel or felder.get("abschluss-text"):
        a_titel = felder.get("abschluss-titel", "Reden wir \u00fcber die Listung.")
        a_text = felder.get(
            "abschluss-text",
            "Muster, Kalkulation und Liefertermine kl\u00e4ren wir in einem Termin \u2014 "
            "kurzfristig und ohne Umwege.",
        )
        zeile = " &middot; ".join(
            x for x in (sicher(name), (sicher(ab_name) if name else ""), sicher(tel)) if x
        )
        kontakt_html = (
            '<section class="abschnitt abschnitt--hell" id="kontakt"><div class="bahn">'
            '<div class="kontakt" data-auftritt>'
            "<h3>%s</h3><p>%s</p>"
            '<div class="knopfreihe">%s</div>'
            '<p style="margin-top:22px;font-size:.88rem">%s</p>'
            "</div></div></section>"
            % (inline(a_titel), inline(a_text), "".join(knoepfe), zeile)
        )

    # Fusszeile: Anschrift, Sprungmarken, Kontakt
    fuss_anschrift = (
        '<span class="fuss__marke">%s</span>%s'
        % (sicher(ab_name),
           "<br>".join(inline(z.strip()) for z in ab_zeilen.split("|") if z.strip()))
    )

    fuss_navigation = ""
    if sprungmarken:
        punkte = "".join('<li><a href="#%s">%s</a></li>' % (sicher(k), inline(t))
                         for k, t in sprungmarken[:8])
        fuss_navigation = ("<h4>Auf dieser Seite</h4><ul>%s</ul>" % punkte)

    fuss_kontakt = "<h4>Kontakt</h4>" + inline(ab_fuehrung)
    if mail:
        fuss_kontakt += '<br><a href="mailto:%s">%s</a>' % (sicher(mail), sicher(mail))
    if tel:
        fuss_kontakt += '<br><a href="tel:%s">%s</a>' % (
            sicher(re.sub(r"[^\d+]", "", tel)), sicher(tel))

    schema = felder.get("schema", "").strip().lower()
    koerperklasse = ' class="schema-dunkel"' if schema in ("dunkel", "dark") else ""

    ersatz = {
        "KOERPERKLASSE":   koerperklasse,
        "KOPF_ABSENDER":   kopf_absender,
        "FUSS_ANSCHRIFT":  fuss_anschrift,
        "FUSS_NAVIGATION": fuss_navigation,
        "FUSS_KONTAKT":    fuss_kontakt,
        "TITEL":        sicher(titel),
        "BESCHREIBUNG": sicher(felder.get("beschreibung", claim or projekt)),
        "AKZENT":       ('<style>:root{--akzent:%s;--akzent-dunkel:%s;}</style>'
                         % (sicher(akzent), sicher(akzent))) if akzent else "",
        "ENTWURFSBALKEN": ('<div class="entwurfsbalken">Entwurf — noch nicht freigegeben</div>'
                           if entwurf else ""),
        "KUNDE":        sicher(kunde),
        "HERO":         hero,
        "KOERPER":      koerper,
        "KONTAKT":      kontakt_html,
        "COPYRIGHT":    sicher(ab_recht),
        "JAHR":         str(date.today().year),
        "STAND":        datum_lang(felder.get("datum", "")) if felder.get("datum") else "",
    }

    seite = vorlage_html
    for schluessel, wert in ersatz.items():
        seite = seite.replace("{{%s}}" % schluessel, wert)
    return seite


# ===========================================================================
# Dateien
# ===========================================================================

# Kantenlaenge und Qualitaet der Bilder in der Vorschaudatei. Eingebettete
# Bilder werden durch die Kodierung ein Drittel groesser, und eine Datei
# ueber rund zwei Megabyte laedt in Dateivorschauen nicht mehr zuverlaessig.
# WEBP halbiert gegenueber JPEG bei gleicher Anmutung.
VORSCHAU_BREITE = 1000
VORSCHAU_GUETE = 72


EINBETT_GRENZE = 5 * 1024 * 1024    # groesseres wird nicht in die Einzeldatei gelegt


def bild_fuer_vorschau(pfad, endung):
    """Verkleinert ein Bild fuer die Einzeldatei und wandelt es in WEBP.
    Ohne Pillow wird das Bild unveraendert eingebettet -- dann ist die
    Vorschaudatei eben groesser, kaputt geht nichts."""
    if endung in (".svg", ".gif") or endung in VIDEO_ENDUNGEN:
        with open(pfad, "rb") as f:
            return f.read(), MIME[endung]
    try:
        from PIL import Image
    except ImportError:
        with open(pfad, "rb") as f:
            return f.read(), MIME[endung]

    import io as _io
    with Image.open(pfad) as im:
        hat_alpha = im.mode in ("RGBA", "LA", "P")
        if im.width > VORSCHAU_BREITE:
            hoehe = round(im.height * VORSCHAU_BREITE / im.width)
            im = im.resize((VORSCHAU_BREITE, hoehe), Image.LANCZOS)
        puffer = _io.BytesIO()
        im.convert("RGBA" if hat_alpha else "RGB").save(
            puffer, "WEBP", quality=VORSCHAU_GUETE, method=6)
        return puffer.getvalue(), "image/webp"


def einzeldatei_schreiben(seite, projektordner, slug):
    """Schreibt eine Fassung, in der ALLES in einer Datei steckt: Stylesheet,
    Skript und jedes Bild als eingebettete Daten. Die laesst sich per Doppel-
    klick oeffnen, per Mail verschicken und funktioniert ohne Internet.

    Die Fassung in site/ bleibt davon unberuehrt - die ist fuer den Server."""

    def datei(pfad):
        with open(pfad, encoding="utf-8") as f:
            return f.read()

    # Stylesheet und Skript hineinziehen
    for blatt in ("schriften.css", "stil.css"):
        pfad = os.path.join(VORLAGE, "assets", blatt)
        if os.path.isfile(pfad):
            seite = seite.replace(
                '<link rel="stylesheet" href="assets/%s">' % blatt,
                "<style>\n%s\n</style>" % datei(pfad),
            )
    seite = seite.replace(
        '<script src="assets/bewegung.js" defer></script>',
        "<script>\n%s\n</script>" % datei(os.path.join(VORLAGE, "assets", "bewegung.js")),
    )

    # Jedes Bild als Datenblock einsetzen. Eingebettete Bilder werden durch
    # die Kodierung ein Drittel groesser, deshalb werden sie fuer die
    # Vorschau verkleinert -- eine Datei ueber ein paar Megabyte laedt in
    # Dateivorschauen nicht mehr zuverlaessig. Die Fassung in site/ bleibt
    # unangetastet und behaelt die volle Aufloesung.
    bilderordner = os.path.join(projektordner, "bilder")
    eingebettet = 0
    if os.path.isdir(bilderordner):
        for name in sorted(os.listdir(bilderordner)):
            pfad = os.path.join(bilderordner, name)
            endung = os.path.splitext(name)[1].lower()
            if not os.path.isfile(pfad) or endung not in MIME:
                continue
            verweis = "bilder/" + name
            if verweis not in seite:
                continue
            if endung in VIDEO_ENDUNGEN and os.path.getsize(pfad) > EINBETT_GRENZE:
                sys.stderr.write(
                    "  ! %s ist zu gross fuer die Einzeldatei - in vorschau/ "
                    "fehlt das Video, in site/ ist es da.\n" % name)
                continue
            daten, typ = bild_fuer_vorschau(pfad, endung)
            roh = base64.b64encode(daten).decode("ascii")
            seite = seite.replace(verweis, "data:%s;base64,%s" % (typ, roh))
            eingebettet += 1

    os.makedirs(VORSCHAU, exist_ok=True)
    ziel = os.path.join(VORSCHAU, slug + ".html")
    with open(ziel, "w", encoding="utf-8") as f:
        f.write(seite)
    return ziel, eingebettet, os.path.getsize(ziel)


def assets_kopieren(ziel):
    quelle = os.path.join(VORLAGE, "assets")
    zielordner = os.path.join(ziel, "assets")
    if os.path.isdir(zielordner):
        shutil.rmtree(zielordner)
    shutil.copytree(quelle, zielordner)


def bilder_kopieren(projektordner, ziel):
    quelle = os.path.join(projektordner, "bilder")
    if not os.path.isdir(quelle):
        return 0
    zielordner = os.path.join(ziel, "bilder")
    if os.path.isdir(zielordner):
        shutil.rmtree(zielordner)
    os.makedirs(zielordner)
    anzahl = 0
    for name in sorted(os.listdir(quelle)):
        pfad = os.path.join(quelle, name)
        if os.path.isfile(pfad) and name.lower().endswith(BILD_ENDUNGEN):
            shutil.copy2(pfad, os.path.join(zielordner, name))
            anzahl += 1
    return anzahl


def bilder_pruefen(projektordner, felder, roh):
    """Warnt, wenn eine Bilddatei referenziert wird, die es nicht gibt."""
    verwiesen = set(re.findall(r"!\[[^\]]*\]\(([^)]+)\)", roh))
    verwiesen |= set(re.findall(r"^\s*bild:\s*(.+)$", roh, re.I | re.M))
    for schluessel in ("hero-bild", "herobild", "marken-logo", "partner-logo"):
        if felder.get(schluessel):
            verwiesen.add(felder[schluessel])
    for block in re.findall(r":::\s*(?:parallax|band)\s+(\S+)", roh):
        verwiesen.add(block)

    fehlend = []
    for pfad in sorted(x.strip() for x in verwiesen):
        if not pfad or pfad.startswith(("http://", "https://")):
            continue
        if not os.path.isfile(os.path.join(projektordner, pfad)):
            fehlend.append(pfad)
    return fehlend


def projekt_bauen(slug, vorlage_html):
    projektordner = os.path.join(PROJEKTE, slug)
    inhaltsdatei = os.path.join(projektordner, "inhalt.md")
    if not os.path.isfile(inhaltsdatei):
        sys.stderr.write("  ! %s: inhalt.md fehlt — übersprungen.\n" % slug)
        return False

    with open(inhaltsdatei, encoding="utf-8") as f:
        roh = f.read()

    felder, koerpertext = kopfdaten_lesen(roh)
    zielslug = felder.get("slug", slug).strip() or slug

    # Zeilen, die mit // beginnen, sind Notizen fuer das Team und
    # erscheinen nicht auf der Seite.
    koerpertext = "\n".join(
        z for z in koerpertext.splitlines() if not z.lstrip().startswith("//")
    )

    fehlend = bilder_pruefen(projektordner, felder, koerpertext)
    for pfad in fehlend:
        sys.stderr.write("  ! %s: Bild fehlt — %s\n" % (slug, pfad))

    global FELDER
    FELDER = felder

    bloecke = bloecke_teilen(koerpertext.splitlines())
    koerper, sprungmarken = koerper_bauen(bloecke)
    seite = seite_bauen(felder, koerper, vorlage_html, sprungmarken)

    ziel = os.path.join(AUSGABE, zielslug)
    os.makedirs(ziel, exist_ok=True)
    with open(os.path.join(ziel, "index.html"), "w", encoding="utf-8") as f:
        f.write(seite)
    assets_kopieren(ziel)
    anzahl = bilder_kopieren(projektordner, ziel)

    _, _, groesse = einzeldatei_schreiben(seite, projektordner, zielslug)

    print("  + %-24s -> site/%s/index.html  (%d Bilder)" % (slug, zielslug, anzahl))
    print("    %-24s    vorschau/%s.html  (alles in einer Datei, %.1f MB)"
          % ("", zielslug, groesse / 1048576))
    return True


def uebersicht_bauen(slugs, vorlage_html):
    """Interne Startseite mit allen Projekten. NICHT oeffentlich stellen."""
    eintraege = []
    for slug in slugs:
        datei = os.path.join(PROJEKTE, slug, "inhalt.md")
        if not os.path.isfile(datei):
            continue
        with open(datei, encoding="utf-8") as f:
            felder, _ = kopfdaten_lesen(f.read())
        zielslug = felder.get("slug", slug)
        eintraege.append(
            '<article class="karte"><div class="karte__text">'
            '<span class="karte__nummer">%s</span><h3><a href="%s/">%s</a></h3>'
            "<p>%s</p></div></article>"
            % (sicher(felder.get("kunde", "")), sicher(zielslug),
               inline(felder.get("projekt", zielslug)),
               inline(felder.get("claim", "")))
        )
    koerper = (
        '<section class="abschnitt"><div class="bahn">'
        '<header class="abschnitt__kopf"><span class="marke">Intern</span>'
        "<h2>Alle Pitch-Seiten</h2></header>"
        '<p class="vertraulich">Diese Übersicht ist nur für das Team. '
        "Sie darf nicht öffentlich erreichbar sein — sonst sieht jeder Kunde, "
        "wem sonst noch etwas angeboten wird.</p>"
        '<div class="karten">%s</div></div></section>' % "".join(eintraege)
    )
    felder = {"projekt": "CGT — Pitch-Seiten", "claim": "Interne Übersicht",
              "titel": "CGT — Pitch-Seiten (intern)"}
    seite = seite_bauen(felder, koerper, vorlage_html)
    os.makedirs(AUSGABE, exist_ok=True)
    with open(os.path.join(AUSGABE, "index.html"), "w", encoding="utf-8") as f:
        f.write(seite)
    assets_kopieren(AUSGABE)
    print("  + Übersicht                   -> site/index.html  (nur intern!)")


# ===========================================================================
# Einstieg
# ===========================================================================

def projekt_anlegen(name):
    """Legt ein neues Projekt aus der Blankovorlage an und vergibt eine
    Adresse mit Zufallsteil, damit die Seite nicht zu erraten ist."""
    name = name.lower()
    for von, nach in (("\u00e4", "ae"), ("\u00f6", "oe"), ("\u00fc", "ue"),
                      ("\u00df", "ss")):
        name = name.replace(von, nach)
    name = re.sub(r"[^a-z0-9-]+", "-", name).strip("-")
    if not name:
        sys.stderr.write("Bitte einen Projektnamen angeben.\n")
        return 1

    ziel = os.path.join(PROJEKTE, name)
    if os.path.exists(ziel):
        sys.stderr.write("Es gibt schon ein Projekt '%s'.\n" % name)
        return 1

    shutil.copytree(os.path.join(PROJEKTE, "_vorlage"), ziel)

    slug = "%s-%s" % (name, zufallsteil())
    datei = os.path.join(ziel, "inhalt.md")
    with open(datei, encoding="utf-8") as f:
        text = f.read()
    text = re.sub(r"^slug:.*$", "slug:            " + slug, text, count=1, flags=re.M)
    with open(datei, "w", encoding="utf-8") as f:
        f.write(text)

    print("Projekt angelegt:")
    print("  Inhalt:  projekte/%s/inhalt.md" % name)
    print("  Bilder:  projekte/%s/bilder/" % name)
    print("  Adresse: /%s/   (Zufallsteil, damit niemand sie erraten kann)" % slug)
    print("\nJetzt inhalt.md fuellen, Bilder ablegen, dann:")
    print("  python3 bauen.py %s" % name)
    return 0


def main(argumente):
    if "--neu" in argumente:
        rest = [a for a in argumente if not a.startswith("--")]
        if not rest:
            sys.stderr.write("Aufruf: python3 bauen.py --neu <projektname>\n")
            return 1
        return projekt_anlegen(rest[0])

    mit_uebersicht = "--uebersicht" in argumente
    gewuenscht = [a for a in argumente if not a.startswith("--")]

    with open(os.path.join(VORLAGE, "seite.html"), encoding="utf-8") as f:
        vorlage_html = f.read()

    if gewuenscht:
        slugs = gewuenscht
    else:
        slugs = sorted(
            name for name in os.listdir(PROJEKTE)
            if os.path.isdir(os.path.join(PROJEKTE, name)) and not name.startswith("_")
        )

    if not slugs:
        print("Keine Projekte in projekte/ gefunden.")
        return 0

    print("Baue %d Projekt(e):" % len(slugs))
    gebaut = 0
    for slug in slugs:
        if projekt_bauen(slug, vorlage_html):
            gebaut += 1

    os.makedirs(AUSGABE, exist_ok=True)
    # Damit GitHub Pages die Ordner nicht durch Jekyll schickt
    open(os.path.join(AUSGABE, ".nojekyll"), "w").close()
    # Einstellungen fuer Vercel. Wird bei jedem Bauen neu geschrieben,
    # damit sie nicht versehentlich verloren geht.
    with open(os.path.join(AUSGABE, "vercel.json"), "w", encoding="utf-8") as f:
        f.write(VERCEL_JSON)

    if mit_uebersicht:
        uebersicht_bauen(slugs, vorlage_html)

    print("Fertig: %d von %d." % (gebaut, len(slugs)))
    return 0 if gebaut == len(slugs) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
