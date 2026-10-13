"""API-Wrapper für Antrags-Operationen gegen ``backend.bafoeg-digital.de``.

Dieses Modul geht davon aus, dass die Backend-API unter
``https://backend.bafoeg-digital.de/api/v1/`` liegt und JSON spricht.

Wir wissen aus der Recherche (Recherche 2026-10-12), dass der
Maintenance-Status unter ``/api/v1/public/maintenance-status`` abrufbar ist.
Die genauen Antrags-Endpunkte sind nicht öffentlich dokumentiert; wir
verwenden die plausiblen Pfade und behandeln 404 als "noch nicht
bekannt" – der Code wird durch Live-Tests gegen eine echte Session
verifiziert (was wir nicht ohne Samuels Credentials durchführen können).

Sicherheit
----------
- Die Session-Cookies werden aus ``session.json`` (Playwright
  storage_state) geladen und an die HTTP-Requests angehängt.
- Wir loggen **niemals** Response-Bodies, weil sie personenbezogene
  Antragsdaten enthalten können.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse

import urllib.request
import urllib.error
import ssl

from .formblatt1 import Formblatt1
from .selectors import BACKEND_BASE
from .session import session_path
from .browser import load_storage_state


# ---- HTTP-Helfer ----------------------------------------------------------


def _build_ssl_context() -> ssl.SSLContext:
    """Default-SSL-Kontext. Falls eine Firmen-CA nötig ist, kann der User
    ``BAFOEG_CA_BUNDLE`` auf den Pfad zum CA-Bundle setzen."""
    ca = os.environ.get("BAFOEG_CA_BUNDLE")
    if ca and Path(ca).exists():
        return ssl.create_default_context(cafile=ca)
    return ssl.create_default_context()


def _request(
    method: str,
    url: str,
    *,
    cookies: dict[str, str] | None = None,
    json_body: Any = None,
    headers: dict[str, str] | None = None,
    timeout_s: int = 30,
) -> tuple[int, dict[str, str], str]:
    """Schlanker HTTP-Wrapper mit Cookie-Support. Gibt (status, headers, body) zurück."""
    req_headers = {
        "Accept": "application/json",
        "User-Agent": "bafoeg-cli/0.2",
    }
    if json_body is not None:
        body_bytes = json.dumps(json_body, ensure_ascii=False).encode("utf-8")
        req_headers["Content-Type"] = "application/json; charset=utf-8"
    else:
        body_bytes = None
    if cookies:
        cookie_str = "; ".join(f"{k}={v}" for k, v in cookies.items())
        req_headers["Cookie"] = cookie_str
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, data=body_bytes, method=method, headers=req_headers)
    ctx = _build_ssl_context()
    try:
        with urllib.request.urlopen(req, timeout=timeout_s, context=ctx) as resp:
            return resp.status, dict(resp.headers.items()), resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers.items()), e.read().decode("utf-8", errors="replace")


def _session_cookies() -> dict[str, str]:
    """Lädt die in der Session gespeicherten Cookies als Dict."""
    sp = session_path()
    if not sp.exists():
        return {}
    state = load_storage_state(sp)
    cookies = state.get("cookies", []) or []
    return {c["name"]: c["value"] for c in cookies if "name" in c and "value" in c}


# ---- Status / Postfach ----------------------------------------------------


@dataclass
class AntragStatusEintrag:
    """Ein einzelner Antrag im Postfach."""

    antrag_id: str
    status: str
    bewilligungszeitraum_von: str = ""
    bewilligungszeitraum_bis: str = ""
    aktualisiert: str = ""
    rohdaten: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PostfachUebersicht:
    """Übersicht über alle Anträge + Postfachsnachrichten."""

    anträge: list[AntragStatusEintrag]
    nachrichten: list[dict[str, Any]]
    abgefragt_am: float
    quelle: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "quelle": self.quelle,
            "abgefragt_am": self.abgefragt_am,
            "antraege": [a.to_dict() for a in self.anträge],
            "nachrichten": self.nachrichten,
        }


def fetch_status(
    api_base: str = BACKEND_BASE,
) -> PostfachUebersicht:
    """Holt den Antragsstatus + Postfachsnachrichten.

    Wir versuchen mehrere plausible Endpunkte, bis einer antwortet.
    Fehler werden als leere Liste zurückgegeben + Hinweis im ``nachrichten``-
    Block, damit der User weiß, dass etwas geändert werden muss.
    """
    cookies = _session_cookies()
    abgefragt = time.time()

    if not cookies:
        return PostfachUebersicht(
            anträge=[],
            nachrichten=[{
                "hinweis": "Keine gültige Session. Bitte 'bafoeg login' zuerst ausführen.",
            }],
            abgefragt_am=abgefragt,
            quelle=api_base,
        )

    # Plausible Endpunkte. Wir testen sie der Reihe nach.
    plausible_endpoints = [
        "/antraege",
        "/antrag",
        "/antraege/uebersicht",
        "/antraege/meine",
        "/postfach",
        "/postfach/nachrichten",
    ]

    anträge: list[AntragStatusEintrag] = []
    nachrichten: list[dict[str, Any]] = []
    notizen: list[str] = []
    for ep in plausible_endpoints:
        url = f"{api_base}{ep}"
        status, _headers, body = _request("GET", url, cookies=cookies)
        if status == 200:
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                continue
            # Wenn es nach einer Antragsliste aussieht:
            if isinstance(data, list) or (isinstance(data, dict) and "antraege" in data):
                items = data if isinstance(data, list) else data.get("antraege", [])
                for it in items:
                    if isinstance(it, dict):
                        anträge.append(AntragStatusEintrag(
                            antrag_id=str(it.get("id") or it.get("antragId") or it.get("antrag_id") or ""),
                            status=str(it.get("status") or it.get("state") or "unbekannt"),
                            bewilligungszeitraum_von=it.get("bewilligungszeitraumVon", ""),
                            bewilligungszeitraum_bis=it.get("bewilligungszeitraumBis", ""),
                            aktualisiert=it.get("aktualisiert") or it.get("updatedAt") or "",
                            rohdaten={k: v for k, v in it.items()
                                      if k not in {"id", "antragId", "antrag_id",
                                                   "status", "state",
                                                   "bewilligungszeitraumVon", "bewilligungszeitraumBis",
                                                   "aktualisiert", "updatedAt"}},
                        ))
                notizen.append(f"Anträge aus {ep} geladen.")
            elif isinstance(data, dict) and ("nachrichten" in data or "messages" in data):
                items = data.get("nachrichten") or data.get("messages") or []
                nachrichten.extend(items if isinstance(items, list) else [items])
                notizen.append(f"Nachrichten aus {ep} geladen.")
        elif status in (401, 403):
            nachrichten.append({
                "hinweis": (
                    f"Session bei {ep} abgelehnt (HTTP {status}). "
                    "Bitte 'bafoeg login' erneut ausführen."
                ),
            })
            return PostfachUebersicht(
                anträge=anträge,
                nachrichten=nachrichten,
                abgefragt_am=abgefragt,
                quelle=api_base,
            )
        # status 404 / andere: stillschweigend nächster Endpunkt

    if not anträge and not nachrichten:
        nachrichten.append({
            "hinweis": (
                "Keiner der bekannten API-Endpunkte hat geantwortet. "
                "Die Endpunkte von bafoeg-digital.de haben sich "
                "möglicherweise geändert. Bitte Selektoren/Endpunkte in "
                "src/bafoeg_cli/automation/ prüfen."
            ),
        })

    if notizen:
        nachrichten.append({"_meta": notizen})

    return PostfachUebersicht(
        anträge=anträge,
        nachrichten=nachrichten,
        abgefragt_am=abgefragt,
        quelle=api_base,
    )


# ---- Antrag: Entwurf speichern, einreichen --------------------------------


@dataclass
class AntragAktionErgebnis:
    """Ergebnis einer Antrags-Operation (Entwurf speichern, Submit, etc.)."""

    success: bool
    aktion: str
    antrag_id: str = ""
    status_code: int = 0
    note: str = ""
    server_response: Optional[dict[str, Any]] = None
    rohdaten: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _post_antrag(
    endpoint: str,
    payload: dict[str, Any],
    *,
    confirm: bool = True,
    api_base: str = BACKEND_BASE,
) -> AntragAktionErgebnis:
    """Hilfsfunktion: POSTet einen Antrag an die Backend-API."""
    cookies = _session_cookies()
    if not cookies:
        return AntragAktionErgebnis(
            success=False,
            aktion=endpoint,
            status_code=0,
            note="Keine gültige Session. Bitte 'bafoeg login' zuerst ausführen.",
        )
    url = f"{api_base}{endpoint}"
    status, _headers, body = _request("POST", url, cookies=cookies, json_body=payload)
    try:
        parsed = json.loads(body) if body else None
    except json.JSONDecodeError:
        parsed = {"_raw": body[:200]}
    ok = 200 <= status < 300
    antrag_id = ""
    if isinstance(parsed, dict):
        antrag_id = str(parsed.get("id") or parsed.get("antragId") or "")
    return AntragAktionErgebnis(
        success=ok,
        aktion=endpoint,
        antrag_id=antrag_id,
        status_code=status,
        note=("OK" if ok else f"HTTP {status}"),
        server_response=parsed if isinstance(parsed, dict) else None,
    )


def entwurf_speichern(
    fb1: Formblatt1,
    api_base: str = BACKEND_BASE,
) -> AntragAktionErgebnis:
    """Speichert die Formblatt-1-Daten als Entwurf.

    Setzt voraus, dass ``fb1.validate()`` OK ist. Falls nicht, wird das
    in der ``note`` gemeldet und kein API-Call gemacht.
    """
    ok, missing = fb1.validate()
    if not ok:
        return AntragAktionErgebnis(
            success=False,
            aktion="entwurf_speichern",
            status_code=0,
            note="Formblatt 1 unvollständig. Fehlende Pflichtfelder: "
                 + ", ".join(missing),
        )
    return _post_antrag("/antraege/entwurf", fb1.to_api_payload(), api_base=api_base)


def antrag_einreichen(
    fb1: Formblatt1,
    *,
    confirm: bool = False,
    api_base: str = BACKEND_BASE,
) -> AntragAktionErgebnis:
    """Reicht den Antrag FINAL ein.

    Sicherheits-Hürde: ``confirm=True`` ist erforderlich. Ohne dieses
    Argument (oder ohne ``--confirm``-Flag in der CLI) wird der Aufruf
    verweigert. Das schützt vor versehentlichem Absenden.
    """
    if not confirm:
        return AntragAktionErgebnis(
            success=False,
            aktion="submit",
            status_code=0,
            note=(
                "ENDGÜLTIGES Einreichen verweigert: bestätige mit --confirm. "
                "Bis dahin nur Entwurf mit 'bafoeg antrag fill' speichern."
            ),
        )
    ok, missing = fb1.validate()
    if not ok:
        return AntragAktionErgebnis(
            success=False,
            aktion="submit",
            status_code=0,
            note="Formblatt 1 unvollständig. Fehlende Pflichtfelder: "
                 + ", ".join(missing),
        )
    return _post_antrag("/antraege/einreichen", fb1.to_api_payload(), api_base=api_base)


# ---- Dokumenten-Upload ----------------------------------------------------


@dataclass
class UploadErgebnis:
    """Ergebnis eines Dokumenten-Uploads."""

    success: bool
    dokument_name: str
    status_code: int = 0
    note: str = ""
    server_response: Optional[dict[str, Any]] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def dokument_uploaden(
    datei_pfad: str,
    *,
    dokument_typ: str = "beleg",
    beschreibung: str = "",
    antrag_id: str = "",
    api_base: str = BACKEND_BASE,
) -> UploadErgebnis:
    """Lädt ein Dokument (Beleg, Immatrikulationsbescheinigung, etc.) hoch.

    Implementiert als Multipart-Upload gegen einen plausiblen Endpunkt.
    Ohne ``urllib3`` (wir nehmen absichtlich nur die Stdlib) bauen wir
    den Multipart-Body von Hand.
    """
    p = Path(datei_pfad)
    if not p.exists() or not p.is_file():
        return UploadErgebnis(
            success=False,
            dokument_name=datei_pfad,
            note=f"Datei nicht gefunden: {datei_pfad}",
        )

    cookies = _session_cookies()
    if not cookies:
        return UploadErgebnis(
            success=False,
            dokument_name=p.name,
            note="Keine gültige Session. Bitte 'bafoeg login' zuerst ausführen.",
        )

    boundary = f"----bafoegcli{os.urandom(8).hex()}"
    file_bytes = p.read_bytes()
    parts: list[bytes] = []
    for key, val in [
        ("typ", dokument_typ),
        ("beschreibung", beschreibung),
        ("antragId", antrag_id),
    ]:
        parts.append(
            f"--{boundary}\r\n"
            f"Content-Disposition: form-data; name=\"{key}\"\r\n\r\n"
            f"{val}\r\n".encode("utf-8")
        )
    parts.append(
        f"--{boundary}\r\n"
        f"Content-Disposition: form-data; name=\"datei\"; filename=\"{p.name}\"\r\n"
        f"Content-Type: application/octet-stream\r\n\r\n".encode("utf-8")
    )
    parts.append(file_bytes)
    parts.append(f"\r\n--{boundary}--\r\n".encode("utf-8"))
    body = b"".join(parts)

    url = f"{api_base}/dokumente/upload"
    headers = {
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "Content-Length": str(len(body)),
        "Cookie": "; ".join(f"{k}={v}" for k, v in cookies.items()),
    }
    req = urllib.request.Request(url, data=body, method="POST", headers=headers)
    ctx = _build_ssl_context()
    try:
        with urllib.request.urlopen(req, timeout=60, context=ctx) as resp:
            status = resp.status
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        status = e.code
        raw = e.read().decode("utf-8", errors="replace")
    try:
        parsed = json.loads(raw) if raw else None
    except json.JSONDecodeError:
        parsed = None
    ok = 200 <= status < 300
    return UploadErgebnis(
        success=ok,
        dokument_name=p.name,
        status_code=status,
        note=("OK" if ok else f"HTTP {status}"),
        server_response=parsed,
    )
