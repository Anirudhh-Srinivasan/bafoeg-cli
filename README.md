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
bafoeg rechner               # BAföG-Bedarfsrechner (§13/§13a/§23/§25/§29)
bafoeg fristen               # Antrags-, Folgeantrags- und §48-Fristen
bafoeg unterlagen            # Formblätter 1-9 + Checkliste je nach Situation
bafoeg links                 # BAföG Digital, Ämterverzeichnis, Rechtstexte
bafoeg login                 # Login BAföG Digital (BundID) – headless oder --headed
bafoeg status                # Antragsstatus + Postfach (braucht Session)
bafoeg antrag fill           # Formblatt 1 aus YAML → Entwurf speichern
bafoeg antrag submit         # Antrag ENDGÜLTIG einreichen (verlangt --confirm)
bafoeg docs upload           # Beleg/Dokument hochladen
bafoeg formblatt-template    # YAML-Template für Formblatt 1
bafoeg --version
bafoeg --help
```

## Automation gegen BAföG Digital

> **Status: experimentell.** Die Module `bafoeg_cli.automation.*` sind
> implementiert, der Code ist getestet (Unit-Tests mit gemockter
> Backend-API und gefakter Session), aber **kein End-to-End-Lauf
> gegen `bafoeg-digital.de` wurde live verifiziert** – das geht nur
> mit Samuels BundID-Zugang (siehe unten). Live-Tests, die echte
> 2FA/eID-Schritte durchlaufen, sind bewusst nicht Teil der CI.

### Was die Automation-Kommandos tun

| Befehl                            | Was passiert                                                                                                       |
|-----------------------------------|--------------------------------------------------------------------------------------------------------------------|
| `bafoeg login`                    | Spielt den Login-Flow gegen BundID durch, speichert die Session in `$XDG_CONFIG_HOME/bafoeg-cli/session.json`.    |
| `bafoeg status`                   | Fragt Antragsstatus + Postfachsnachrichten gegen die Backend-API ab.                                               |
| `bafoeg antrag fill --daten F`    | Liest Formblatt 1 aus `F` (YAML), validiert, speichert Entwurf gegen die Backend-API (`/antraege/entwurf`).        |
| `bafoeg antrag submit --daten F`  | Wie oben, **aber** ruft `/antraege/einreichen` (endgültig) – verlangt zwingend `--confirm`.                         |
| `bafoeg docs upload --datei D`    | Multipart-Upload eines Belegs/Dokuments (`/dokumente/upload`).                                                      |
| `bafoeg formblatt-template`       | Druckt ein ausgefülltes YAML-Template mit allen Formblatt-1-Feldern (mit Kommentaren).                              |

Jeder dieser Befehle unterstützt `--json` für strukturierte Ausgabe
an Agenten.

### Login-Wege

`bafoeg login` hat zwei Methoden:

- **`password`** (headless): BundID-Account mit Benutzername+Passwort.
  Startet Chromium headless, füllt das Formular auf `id.bund.de` und
  speichert die Session. **Voraussetzung:** BundID-Konto mit
  Benutzername+Passwort-Verfahren – **nicht** für eID/ELSTER.
- **`manual`** (`--headed`): sichtbarer Browser. Der User authentifiziert
  sich selbst (AusweisApp2/eID, ELSTER-Zertifikat oder 2FA-Push). Das
  Programm wartet bis zu `--manual-max-wait` Sekunden und speichert
  die Session, sobald der Redirect zurück auf `bafoeg-digital.de`
  erfolgt ist.
- **`auto`** (Default): versucht erst `password`, fällt auf `manual`
  mit `--headed` zurück.

Für eID/ELSTER/2FA ist **immer** der `--headed`-Weg nötig. Das ist
kein Workaround, sondern Absicht: Diese Verfahren haben eine
kryptographische Komponente (Kartenleser, Zertifikat-Dialog,
Push-Bestätigung), die nicht scriptbar ist.

Zugangsdaten werden ausschließlich aus den Umgebungsvariablen
`BAFOEG_USERNAME` und `BAFOEG_PASSWORD` gelesen (oder interaktiv in
einem TTY abgefragt) und **nie** auf der Festplatte gespeichert.
Persistente Session (`session.json`): Modus `0600`.

### Was live getestet ist vs. was Samuels Zugang braucht

Live verifiziert (gegen `bafoeg-digital.de`) sind nur die im
Recherche-Commit dokumentierten Selektoren und URLs sowie der
`/api/v1/public/maintenance-status`-Endpunkt – ohne Login und ohne
eigene Daten.

Was **nicht** live getestet werden konnte (braucht Samuels BundID):

- Funktioniert der headless `password`-Login? → id.bund.de lädt
  unter Headless oft eine andere Login-Maske (CAPTCHA-Challenge),
  abhängig vom Browser-Fingerprint.
- Stimmen die Pfade `/antraege`, `/antraege/entwurf`,
  `/antraege/einreichen`, `/dokumente/upload`? → plausibel, aber
  nicht öffentlich dokumentiert (Annahme auf Basis der
  Frontend-Routen).
- Akzeptiert die Backend-API das genaue Payload-Schema
  (`formblatt/version/daten` mit `camelCase`-Unterstrich-Mix)?

Was Samuel liefern muss, um das zu klären:

1. **BundID-Account** für die Test-Person, mit
   Benutzername+Passwort **und** idealerweise einem Test-eID,
   damit beide Login-Wege durchgespielt werden können.
2. **Ein leeres BAföG-Digital-Konto** ohne Echtantrag (oder mit
   einem absichtlich gestellten Test-Antrag, der im Anschluss
   zurückgezogen wird). Wir wollen versehentliche echte Anträge
   vermeiden.
3. Falls vorhanden: HAR oder Postman-Collection eines echten
   Login-Calls (gegen `id.bund.de` und gegen
   `backend.bafoeg-digital.de`), damit wir die exakten
   Endpunkt-Pfade und Feldnamen verifizieren können.
4. **Bestätigung des endgültigen Submits.** `bafoeg antrag submit
   --confirm` ruft eine echte Einreichung aus – das ist nicht
   reversibel. Vor Live-Tests einmal mit Samuels OK, danach
   idealerweise in einer Staging-Instanz.

### Beispiel-Session

```bash
# Einmalig: headless anmelden (BundID mit Benutzername+Passwort)
BAFOEG_USERNAME='max@example.org' BAFOEG_PASSWORD='...' \
  bafoeg login --method password --json

# ODER: eID/ELSTER/2FA – interaktiv
bafoeg login --method manual --headed --json
# (Browser bleibt offen, bis Redirect zurück erfolgt)

# Danach:
bafoeg status --json

bafoeg antrag fill --daten antrag.yaml --require-complete --json
bafoeg antrag submit --daten antrag.yaml --confirm --json   # endgültig
bafoeg docs upload --datei immatrikulation.pdf \
                   --typ immatrikulation \
                   --antrag-id ANT-001 --json
```

`antrag.yaml` (Beispiel; `bafoeg formblatt-template --ausgeben`
liefert die kommentierte Vorlage):

```yaml
vorname: Max
nachname: Mustermann
geburtsdatum: 01.01.2000
staatsangehoerigkeit: deutsch
strasse: Beispielweg
hausnummer: "12"
plz: "12345"
ort: Berlin
email: max@example.org
iban: DE89370400440532013000
ausbildung_typ: studium
ausbildung_ort: Beispiel-Universität Berlin
ausbildung_beginn: 01.10.2026
ausbildung_ende_geplant: 30.09.2029
bewilligungszeitraum_von: 01.10.2026
bewilligungszeitraum_bis: 30.09.2027
bei_eltern_wohnend: false
eigene_krankenversicherung: true
```

### Sicherheits-Modell

- Klartext-Passwörter werden **nie** persistiert, **nie** geloggt.
- Session-Cookies leben in `$XDG_CONFIG_HOME/bafoeg-cli/session.json`,
  Modus `0600`. Der Inhalt erlaubt Zugang zum BAföG-Konto – das
  Verzeichnis gehört dem Anwender (Modus `0700`).
- `antrag submit` ohne `--confirm` wird hart verweigert (Exit-Code 6),
  damit niemand versehentlich "das echte Leben" einreicht.
- Antragsdaten aus `antrag.yaml` verlassen das Gerät nur via
  HTTPS-POST an `backend.bafoeg-digital.de`.

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
# Frischer venv, genauso wie CI:
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev]"
playwright install chromium
PYTHONPATH=src pytest tests/ -v
```

78 Tests (Werte, Rechner, Fristen, Unterlagen, Links, Session,
Formblatt 1, Antrags-API-Wrapper mit gemockter HTTP/Backend,
CLI-Smoke). Stand 2026-10-13.

## CI

- **PII-Guard** (`scripts/pii_guard.py`) – blockiert erfundene Mailadressen / Matrikelnummern
- **gitleaks** – blockiert eingecheckte Secrets

Die ausführliche GitHub-Actions-Workflow-Datei liegt unter
`docs/ci/pii-guard.yml`. Sie ist nicht im Standard-Pfad
`.github/workflows/`, weil der Standard-GitHub-PAT des Maintainers
keinen `workflow`-Scope hat und GitHub das Pushen einer `.yml`-Datei
in `.github/workflows/` blockiert (auch mit beliebigem Suffix).

Aktivierung: Inhalt nach `.github/workflows/pii-guard.yml` kopieren
(über die GitHub-Web-UI oder mit einem Token, der `workflow`-Scope
enthält). Anschließend läuft der PII-Guard auf jedem Push und PR.

Lokal testen:

```bash
python3 scripts/pii_guard.py
```

## Lizenz

MIT – siehe [LICENSE](LICENSE).

## Vorbehalt

Dieses Werkzeug liefert eine **vereinfachte Schätzung** auf Basis der
§§13, 13a, 23, 25, 29, 48 BAföG. Es ersetzt keine Rechtsberatung und
keinen Bescheid des Amts für Ausbildungsförderung. Bei komplexen Fällen
(Krankheit, Ausland, Geschwister, elternunabhängige Förderung) bitte
die zuständige Sachbearbeitung kontaktieren.