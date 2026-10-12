# bafoeg-cli

BAföG-CLI für Agenten und Menschen: Bedarfsrechner, Fristen, Formblätter
und offizielle Links nach BAföG (§§13, 13a, 15, 18, 23, 25, 29, 48).

Stand der Werte: WS 2024/25 (gilt unverändert für das Jahr 2026).
Geplante Erhöhung der Wohnpauschale auf 440 € zum WS 2026/27 ist noch
nicht in Kraft.

Jeder Befehl hat ein `--json`-Flag für strukturierte Ausgabe an Agenten.

## Installation

Aus dem Repo:

```bash
pip install -e .
# oder mit Dev-Deps für Tests:
pip install -e ".[dev]"
```

Danach steht das Kommando `bafoeg` zur Verfügung.

## Befehle

```text
bafoeg rechner     # BAföG-Bedarfsrechner (§13/§13a/§23/§25/§29)
bafoeg fristen     # Antrags-, Folgeantrags- und §48-Fristen
bafoeg unterlagen  # Formblätter 1-9 + Checkliste je nach Situation
bafoeg links       # BAföG Digital, Ämterverzeichnis, Rechtstexte
bafoeg --version
bafoeg --help
```

### `rechner` – Bedarfsrechner

Berechnet den voraussichtlichen monatlichen BAföG-Höchstsatz und zieht
Eltern- und eigenes Einkommen gemäß den Freibeträgen ab. Vereinfachtes
Modell: Brutto = Netto (Werbungskosten und Sozialpauschalen werden nicht
abgezogen). Verbindlich ist nur der Bescheid des Amts für
Ausbildungsförderung.

Wichtige Flags:

```
--bei-eltern          # Wohnung bei den Eltern (nur 59 € Wohnpauschale)
--eigene-kv           # eigene Kranken- und Pflegeversicherung
                      # (KV/PV-Zuschlag 137 €)
--ab-30               # ab 30 Jahre (Aufschlag 26 €, Höchstsatz 1.018 €)
--verheiratet         # verheiratet / eingetr. Lebenspartnerschaft
--eltern-getrennt     # Eltern getrennt lebend (sonst 2.540 € Freibetrag)
--einkommen-vater     # monatliches Nettoeinkommen Vater
--einkommen-mutter    # monatliches Nettoeinkommen Mutter
--weitere-kinder      # weitere Kinder im Haushalt ohne förderfähige Ausbildung
--eigen-einkommen     # eigenes Bruttoeinkommen im Bewilligungszeitraum
--ehegatte-einkommen  # Einkommen Ehegatte / eingetr. Lebenspartner
--eigene-kinder       # eigene Kinder ohne Ausbildung
--vermoegen           # eigenes Vermögen (§29)
--json                # Ausgabe als JSON
```

#### Beispiele

Maximaler Höchstsatz (eigene Wohnung, eigene KV/PV, ohne Einkommen):

```bash
bafoeg rechner --eigene-kv --json
```

```json
{
  "quelle": "bafög.de / gesetze-im-internet.de (BAföG, Stand WS 2024/25)",
  "stand": "WS 2024/25, unverändert 2026 (verifiziert 2026-10-12)",
  "gueltig_ab": "01.10.2024 (laufende Bewilligungszeitraume) / 01.08.2024 (neue)",
  "hinweis": "Vereinfachtes Modell – verbindlich ist nur der Bescheid des Amts für Ausbildungsförderung.",
  "ergebnis": {
    "bedarf_monat_euro": 992.0,
    "anrechnung_eltern_euro": 0.0,
    "anrechnung_eigen_euro": 0.0,
    "foerderung_monat_euro": 992.0,
    "details": {
      "vermoegen": { "...": "..." },
      "eltern": { "...": "..." },
      "eigen": { "...": "..." }
    },
    "hinweise": [
      "Vereinfachte Schätzung – verbindlich ist nur der Bescheid des Amts für Ausbildungsförderung.",
      "Werbungskosten und Sozialpauschalen sind hier nicht abgezogen."
    ]
  },
  "rechner_eingabe": {
    "bei_eltern": false,
    "eigene_krankenversicherung": true,
    "ab_30": false,
    "verheiratet": false
  }
}
```

Student mit Eltern-Einkommen über dem Freibetrag:

```bash
bafoeg rechner --eigene-kv \
  --einkommen-vater 2500 --einkommen-mutter 1500 \
  --eigen-einkommen 800 --json
```

### `fristen` – Fristen

Liefert Erstantrag, Folgeantrag, §48-Leistungsnachweis,
Flexibilitätssemester, Vorausleistung, Aktualisierung, Widerspruch.
Mit Rechtsgrundlage und Detail.

```bash
bafoeg fristen --json
```

### `unterlagen` – Formblätter und Checklisten

Alle Formblätter 1-9:

```bash
bafoeg unterlagen --json
```

Nur Formblatt 5 (Leistungsbescheinigung):

```bash
bafoeg unterlagen --formblatt 5 --json
```

Checkliste für eine bestimmte Situation:

```bash
bafoeg unterlagen --situation erstantrag_student --json
bafoeg unterlagen --situation folgeantrag_student --json
bafoeg unterlagen --situation erstantrag_schueler --json
bafoeg unterlagen --situation auslandsantrag --json
bafoeg unterlagen --situation vorausleistung --json
bafoeg unterlagen --situation aktualisierung --json
```

### `links` – Offizielle Links

```bash
bafoeg links --json
bafoeg links --kategorie antrag_online --json
bafoeg links --kategorie amt_finden --json
bafoeg links --kategorie rechtstexte --json
bafoeg links --kategorie formulare --json
```

Kategorien: `antrag_online` (BAföG-Digital), `amt_finden` (Ämterverzeichnis),
`rechtstexte` (Gesetzestext), `formulare` (Formblätter + BVA Rückzahlung).

## Datenquellen

- **bafög.de** – offizielles Portal des BMBF, Bedarfssätze und Freibeträge
- **gesetze-im-internet.de/baf_g/** – amtlicher Volltext BAföG
- **bva.bund.de** – Bundesverwaltungsamt (Rückzahlung)

Stand der Werte: WS 2024/25, gültig für 2026. Werte, Quellen und
Rechtsgrundlage sind in `src/bafoeg_cli/werte.py` hinterlegt; jede
JSON-Ausgabe enthält `quelle` und `stand`.

## JSON-Konvention

- Schlüssel in snake_case
- `quelle`, `stand`, `gueltig_ab` immer auf Top-Level
- Beträge in Euro (Float, 2 Nachkommastellen)
- `hinweis` und `hinweise` als Arrays
- Keine erfundenen Personendaten (kein Login, keine Ausweisnummern)

## Tests

```bash
pip install -e ".[dev]"
PYTHONPATH=src python3 -m pytest tests/ -v
```

50 Tests (Werte, Rechner, Fristen, Unterlagen, Links, CLI-Smoke).

## CI

- **PII-Guard** (`scripts/pii_guard.py`) – blockiert erfundene Mailadressen / Matrikelnummern
- **gitleaks** – blockiert eingecheckte Secrets

Beide Workflows laufen auf jedem Push und PR.

## Lizenz

MIT – siehe [LICENSE](LICENSE).

## Vorbehalt

Dieses Werkzeug liefert eine **vereinfachte Schätzung** auf Basis der
§§13, 13a, 23, 25, 29, 48 BAföG. Es ersetzt keine Rechtsberatung und
keinen Bescheid des Amts für Ausbildungsförderung. Bei komplexen Fällen
(Krankheit, Ausland, Geschwister, elternunabhängige Förderung) bitte
die zuständige Sachbearbeitung kontaktieren.