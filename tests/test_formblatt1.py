"""Tests für Formblatt-1-YAML-Laden und -Validierung."""
from __future__ import annotations

from pathlib import Path

import pytest

from bafoeg_cli.automation.formblatt1 import (
    FB1_PFLICHT,
    Formblatt1,
    formblatt1_template_yaml,
    load_formblatt1_from_yaml,
)

from _automation_fixtures import FB1_UNVOLLSTAENDIG, FB1_VOLLSTAENDIG, write_yaml


def test_formblatt1_default_ist_leer():
    fb = Formblatt1()
    missing = fb.missing_required()
    # Alle String-Pflichtfelder fehlen. Bool-Felder (bei_eltern_wohnend,
    # eigene_krankenversicherung) haben gültige Default-Antworten und sind
    # daher nie "fehlend"; sie zählen hier nicht mit.
    missing_str = [k for k in missing if k in FB1_PFLICHT]
    expected = {k for k in FB1_PFLICHT
                if k not in {"bei_eltern_wohnend", "eigene_krankenversicherung"}}
    assert set(missing_str) == expected


def test_formblatt1_vollstaendig_ok(tmp_path: Path):
    p = write_yaml(tmp_path, "fb1.yaml", FB1_VOLLSTAENDIG)
    fb = load_formblatt1_from_yaml(str(p))
    ok, missing = fb.validate()
    assert ok is True, f"Fehlend: {missing}"
    assert missing == []
    assert fb.vorname == "Max"
    assert fb.iban == "DE89370400440532013000"
    assert fb.metadata == {} or "unknown_keys" not in fb.metadata


def test_formblatt1_unvollstaendig_listet_fehlende(tmp_path: Path):
    p = write_yaml(tmp_path, "fb1.yaml", FB1_UNVOLLSTAENDIG)
    fb = load_formblatt1_from_yaml(str(p))
    ok, missing = fb.validate()
    assert ok is False
    # IBAN, Geburtsdatum, Adresse, Ausbildung, etc. fehlen.
    assert "iban" in missing
    assert "geburtsdatum" in missing
    assert "strasse" in missing
    assert "ausbildung_typ" in missing
    # vorname/nachname/email sind gesetzt.
    assert "vorname" not in missing
    assert "nachname" not in missing
    assert "email" not in missing


def test_formblatt1_unbekannte_keys_in_metadata(tmp_path: Path):
    p = write_yaml(tmp_path, "fb1.yaml", "vorname: X\nnachname: Y\nemail: a@b.c\nfalsch: 1\n")
    fb = load_formblatt1_from_yaml(str(p))
    assert "falsch" in fb.metadata.get("unknown_keys", [])


def test_formblatt1_template_enthaelt_alle_felder():
    tpl = formblatt1_template_yaml()
    # Wir prüfen eine Auswahl von Feldnamen.
    for key in ("vorname", "nachname", "iban", "ausbildung_typ", "bei_eltern_wohnend"):
        assert key in tpl, f"Feld {key} fehlt im Template"


def test_formblatt1_api_payload_enthaelt_formblatt_marker():
    fb = Formblatt1(vorname="X", nachname="Y")
    payload = fb.to_api_payload()
    assert payload["formblatt"] == "1"
    assert payload["version"] == "WS2024/25"
    assert "daten" in payload
    assert "metadata" not in payload["daten"]


def test_formblatt1_kein_string_bei_0(tmp_path: Path):
    # Der Wert 0 darf für eigene_kinder_anzahl kein "fehlend" auslösen.
    p = write_yaml(tmp_path, "fb1.yaml", "eigene_kinder_anzahl: 0\n")
    fb = load_formblatt1_from_yaml(str(p))
    assert "eigene_kinder_anzahl" not in fb.missing_required()
