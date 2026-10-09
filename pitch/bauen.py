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

BILD_ENDUNGEN = (".jpg", ".jpeg", ".png", ".webp", ".avif", ".gif", ".svg")

# Fuer die Einzeldatei: welcher Dateityp wird wie eingebettet
MIME = {
    ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
    ".webp": "image/webp", ".avif": "image/avif", ".gif": "image/gif",
    ".svg": "image/svg+xml",
}

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
                i += 1
                while i < len(zeilen) and not zeilen[i].strip().startswith(":::"):
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

def karten_lesen(zeilen):
    """Zerlegt den Inhalt eines Karten-/Slider-Blocks an jeder ###-Zeile."""
    karten = []
    aktuell = None
    for zeile in zeilen:
        if zeile.strip().startswith("### "):
            if aktuell:
                karten.append(aktuell)
            aktuell = {"titel": zeile.strip()[4:].strip(), "bild": "", "bildtext": "", "text": []}
            continue
        if aktuell is None:
            continue
        m = re.match(r"^\s*bild:\s*(.+)$", zeile, re.I)
        if m:
            aktuell["bild"] = m.group(1).strip()
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
    return (
        '<article class="karte">%s<div class="karte__text">%s<h3>%s</h3>%s</div></article>'
        % (bild, kopfzeile, inline(karte["titel"]), text_rendern(karte["text"]))
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
        return '<div class="galerie">%s</div>' % "".join(bilder)

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
            '<span class="bildwand__zahl">%02d</span><h3>%s</h3>%s</div>'
            % (i + 1, inline(k["titel"]), text_rendern(k["text"]))
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
            % (inline(k["titel"]), text_rendern(k["text"]))
            for k in punkte
        )
        return '<div class="aufklapp" data-auftritt>%s</div>' % inner

    # --- Hinweiskasten
    if name in ("hinweis", "vertraulich"):
        return '<p class="vertraulich" data-auftritt>%s</p>' % inline(
            " ".join(z.strip() for z in zeilen if z.strip())
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
        kennung = re.sub(r"[^a-z0-9]+", "-", titel.lower()).strip("-")[:40]
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
            if name in ("parallax", "band", "kapitel"):
                # Volle Breite: ausserhalb eines Abschnitts
                abschnitt_schliessen()
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
    hero_bild_html = ""
    if herobild:
        hero_bild_html = ('<div class="hero__bild" data-parallax="0.22" '
                          'style="background-image:url(\'%s\')"></div>' % sicher(herobild))

    markenlogo = felder.get("marken-logo", "").strip()
    logo_html = ""
    if markenlogo:
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

    ersatz = {
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

    # Jedes Bild als Datenblock einsetzen
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
            with open(pfad, "rb") as f:
                roh = base64.b64encode(f.read()).decode("ascii")
            seite = seite.replace(verweis, "data:%s;base64,%s" % (MIME[endung], roh))
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
    for schluessel in ("hero-bild", "herobild", "marken-logo"):
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
