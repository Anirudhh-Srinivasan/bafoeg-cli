"""Geteilte Test-Fixtures und -Konstanten für die Automation-Tests."""
from __future__ import annotations

import os
import textwrap
from pathlib import Path

# Beispiel-YAML für Formblatt 1, vollständig (alle Pflichtfelder).
FB1_VOLLSTAENDIG = textwrap.dedent("""\
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
""")

# Unvollständiges Beispiel: nur Name + Mail.
FB1_UNVOLLSTAENDIG = textwrap.dedent("""\
    vorname: Erika
    nachname: Beispiel
    email: erika@example.org
""")


def write_yaml(tmp_path: Path, name: str, content: str) -> Path:
    """Schreibt eine YAML-Datei in ``tmp_path`` und gibt den Pfad zurück."""
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p
