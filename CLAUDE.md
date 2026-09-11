# CLAUDE.md — Coldewey Goetz Trade (CGT)

Wissens-Repo für **Coldewey Goetz Trade**. Verantwortlich ist **Sascha**, ohne
technisches Team im Rücken.

**Diese Datei zu Beginn jeder Session lesen.**

## Was dieses Repo ist — und was nicht

Eine **Ablage für Betriebswissen**, kein Software-Projekt. Es gibt hier keinen Code,
keinen Build, kein Deployment. Wenn das später dazukommt, wird diese Datei erweitert.

## Zusammenarbeit

- **Deutsch, per Du.** Sachlich und auf den Punkt, wenig Fachjargon.
- Technische Schritte einfach erklären — bei Unklarheiten direkt sagen: wann, wie, wo.
- Kosten und Wirtschaftlichkeit mitdenken, auch bei KI-Aufrufen.
- **Nichts erfinden.** Was nicht belegt ist, kommt nicht als Fakt ins Repo — offene
  Fragen gehören nach `docs/offene-punkte.md`, nicht in einen plausibel klingenden Satz.

## Ablage

| Ordner | Inhalt |
|---|---|
| `docs/` | Das Wissen — ein Thema pro Datei, Index in `docs/README.md` |

Neue Ordner erst anlegen, wenn `docs/` wirklich unübersichtlich wird. Eine flache
Ablage, die man überblickt, schlägt eine saubere Hierarchie, die keiner pflegt.

## Regeln für Einträge

1. **Quelle und Datum dazu.** Woher kommt die Information (Mail, Telefonat, Vertrag,
   Website) und von wann ist sie? Ohne Datum ist ein Preis oder eine Kondition wertlos.
2. **Begründung mitschreiben.** Nicht nur „Lieferant X liefert ab 500 Stück", sondern
   auch, warum diese Grenze so verhandelt wurde.
3. **Widersprüche stehen lassen und markieren**, statt sie glattzubügeln. Wenn zwei
   Angaben nicht zusammenpassen, ist genau das die wichtige Information.
4. **Keine Secrets.** Keine Passwörter, Zugangsdaten oder API-Schlüssel im Repo —
   auch nicht in Beispielen. Notieren, *wo* sie liegen, nie *was* sie sind.
5. **Personenbezogene Daten sparsam.** Ansprechpartner mit Rolle und Firmenkontakt ja,
   Privates nein.

## Schreibweise

- Firmenname ausgeschrieben **Coldewey Goetz Trade**, Kürzel **CGT**.
- Dateinamen klein, mit Bindestrichen: `lieferant-xy.md`, `zoll-einfuhr.md`.
- Markdown, Überschriften ab `##`, keine Tabellen-Monster — lieber mehrere Dateien.
