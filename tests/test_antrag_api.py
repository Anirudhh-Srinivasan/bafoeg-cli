"""Tests für den Antrags-API-Wrapper.

Wir mocken den HTTP-Layer, damit keine echten Calls gegen
backend.bafoeg-digital.de laufen.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from bafoeg_cli.automation import antrag
from bafoeg_cli.automation.formblatt1 import Formblatt1
from bafoeg_cli.automation.session import session_path

from _automation_fixtures import write_yaml


# --- HTTP-Mocking-Helpers --------------------------------------------------


class FakeResponse:
    def __init__(self, status=200, body=b"{}", headers=None):
        self.status = status
        self._body = body
        self.headers = headers or {"Content-Type": "application/json"}

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def make_fb1() -> Formblatt1:
    return Formblatt1(
        vorname="Max", nachname="Mustermann",
        geburtsdatum="01.01.2000", staatsangehoerigkeit="deutsch",
        strasse="Bsp.", hausnummer="1", plz="12345", ort="Berlin",
        email="max@example.org", iban="DE89370400440532013000",
        ausbildung_typ="studium", ausbildung_ort="Uni",
        ausbildung_beginn="01.10.2026", ausbildung_ende_geplant="30.09.2029",
        bewilligungszeitraum_von="01.10.2026", bewilligungszeitraum_bis="30.09.2027",
        bei_eltern_wohnend=False, eigene_krankenversicherung=True,
    )


def fake_session(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Legt eine fake session.json an, damit die Wrapper denken, sie seien eingeloggt."""
    monkeypatch.setenv("BAFOEG_CONFIG_DIR", str(tmp_path / "c"))
    (tmp_path / "c").mkdir(exist_ok=True)
    fake = {
        "cookies": [
            {"name": "AUTH_SESSION_ID", "value": "abc123",
             "domain": "bafoeg-digital.de", "path": "/",
             "expires": -1, "httpOnly": True, "secure": True, "sameSite": "Lax"},
            {"name": "KC_RESTART", "value": "xyz",
             "domain": ".bafoeg-digital.de", "path": "/",
             "expires": -1, "httpOnly": True, "secure": True, "sameSite": "Lax"},
        ],
        "origins": [],
    }
    (tmp_path / "c" / "session.json").write_text(json.dumps(fake), encoding="utf-8")
    assert session_path().exists()


# --- fetch_status ----------------------------------------------------------


def test_fetch_status_ohne_session_kein_absturz(monkeypatch, tmp_path):
    monkeypatch.setenv("BAFOEG_CONFIG_DIR", str(tmp_path / "c"))
    ue = antrag.fetch_status()
    assert ue.anträge == []
    assert any("login" in (n.get("hinweis", "")).lower() for n in ue.nachrichten)


def test_fetch_status_mit_session_erfolg(monkeypatch, tmp_path):
    fake_session(monkeypatch, tmp_path)
    calls: list[str] = []

    def fake_request(method, url, **kwargs):
        calls.append(f"{method} {url}")
        if url.endswith("/antraege"):
            body = json.dumps([{
                "id": "ANT-001",
                "status": "entwurf",
                "bewilligungszeitraumVon": "01.10.2026",
                "bewilligungszeitraumBis": "30.09.2027",
                "aktualisiert": "2026-10-12T10:00:00Z",
            }])
            return 200, {"Content-Type": "application/json"}, body
        return 404, {}, ""

    monkeypatch.setattr(antrag, "_request", fake_request)
    ue = antrag.fetch_status()
    assert len(ue.anträge) == 1
    assert ue.anträge[0].antrag_id == "ANT-001"
    assert ue.anträge[0].status == "entwurf"
    assert "/antraege" in calls[0]


def test_fetch_status_session_ungueltig(monkeypatch, tmp_path):
    fake_session(monkeypatch, tmp_path)

    def fake_request(method, url, **kwargs):
        return 401, {}, json.dumps({"error": "unauthorized"})

    monkeypatch.setattr(antrag, "_request", fake_request)
    ue = antrag.fetch_status()
    assert any("abgelehnt" in n.get("hinweis", "") for n in ue.nachrichten)


# --- entwurf_speichern -----------------------------------------------------


def test_entwurf_speichern_erfolg(monkeypatch, tmp_path):
    fake_session(monkeypatch, tmp_path)

    def fake_request(method, url, **kwargs):
        assert method == "POST"
        assert url.endswith("/antraege/entwurf")
        cookies = kwargs.get("cookies") or {}
        assert cookies.get("AUTH_SESSION_ID") == "abc123"
        assert kwargs["json_body"]["formblatt"] == "1"
        return 200, {}, json.dumps({"id": "ANT-002"})

    monkeypatch.setattr(antrag, "_request", fake_request)
    res = antrag.entwurf_speichern(make_fb1())
    assert res.success is True
    assert res.antrag_id == "ANT-002"
    assert res.status_code == 200


def test_entwurf_speichern_unvollstaendig(monkeypatch, tmp_path):
    fake_session(monkeypatch, tmp_path)
    called = {"n": 0}

    def fake_request(*a, **kw):
        called["n"] += 1
        return 200, {}, "{}"

    monkeypatch.setattr(antrag, "_request", fake_request)
    res = antrag.entwurf_speichern(Formblatt1(vorname="X"))
    assert res.success is False
    assert called["n"] == 0  # gar keine HTTP-Calls
    assert "iban" in res.note
    assert "geburtsdatum" in res.note


def test_entwurf_speichern_ohne_session(monkeypatch, tmp_path):
    monkeypatch.setenv("BAFOEG_CONFIG_DIR", str(tmp_path / "c"))
    res = antrag.entwurf_speichern(make_fb1())
    assert res.success is False
    assert "login" in res.note.lower()


# --- antrag_einreichen -----------------------------------------------------


def test_submit_ohne_confirm_wird_verweigert(monkeypatch, tmp_path):
    fake_session(monkeypatch, tmp_path)
    called = {"n": 0}

    def fake_request(*a, **kw):
        called["n"] += 1
        return 200, {}, "{}"

    monkeypatch.setattr(antrag, "_request", fake_request)
    res = antrag.antrag_einreichen(make_fb1(), confirm=False)
    assert res.success is False
    assert "bestätige" in res.note.lower() or "confirm" in res.note.lower()
    assert called["n"] == 0  # GARANTIERT kein API-Call


def test_submit_mit_confirm_erfolg(monkeypatch, tmp_path):
    fake_session(monkeypatch, tmp_path)

    def fake_request(method, url, **kwargs):
        assert url.endswith("/antraege/einreichen")
        return 201, {}, json.dumps({"id": "ANT-003", "status": "eingereicht"})

    monkeypatch.setattr(antrag, "_request", fake_request)
    res = antrag.antrag_einreichen(make_fb1(), confirm=True)
    assert res.success is True
    assert res.antrag_id == "ANT-003"
    assert res.status_code == 201


# --- dokument_uploaden -----------------------------------------------------


def test_upload_datei_nicht_gefunden(monkeypatch, tmp_path):
    fake_session(monkeypatch, tmp_path)
    res = antrag.dokument_uploaden(str(tmp_path / "gibt-es-nicht.pdf"))
    assert res.success is False
    assert "nicht gefunden" in res.note


def test_upload_ohne_session(monkeypatch, tmp_path):
    monkeypatch.setenv("BAFOEG_CONFIG_DIR", str(tmp_path / "c"))
    fake = tmp_path / "fake.pdf"
    fake.write_bytes(b"%PDF-1.4 fake")
    res = antrag.dokument_uploaden(str(fake))
    assert res.success is False
    assert "login" in res.note.lower()


def test_upload_multipart_body(monkeypatch, tmp_path):
    """Stellt sicher, dass der Multipart-Body korrekt gebaut wird und
    die Datei-Bytes enthalten sind."""
    fake_session(monkeypatch, tmp_path)
    fake = tmp_path / "fake.pdf"
    fake.write_bytes(b"%PDF-1.4 content-12345")
    captured: dict = {}

    class _CapResp:
        status = 200
        headers = {"Content-Type": "application/json"}

        def read(self):
            return b'{"id": "DOC-1"}'

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def fake_urlopen(req, **kw):
        captured["url"] = req.full_url
        captured["method"] = req.method
        captured["data"] = req.data
        captured["headers"] = dict(req.headers)
        return _CapResp()

    monkeypatch.setattr(antrag.urllib.request, "urlopen", fake_urlopen)
    res = antrag.dokument_uploaden(
        str(fake), dokument_typ="immatrikulation",
        beschreibung="Test", antrag_id="ANT-001",
    )
    assert res.success is True
    body = captured["data"]
    assert b"Content-Disposition: form-data" in body
    assert b'name="typ"' in body
    assert b"immatrikulation" in body
    assert b"content-12345" in body
    assert b'filename="fake.pdf"' in body
    ctype = captured["headers"]["Content-type"]
    assert "multipart/form-data" in ctype
    assert "boundary=" in ctype
