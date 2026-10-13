"""Formblatt 1 – Stammdaten.

BAföG Formblatt 1 erfasst die persönlichen Daten der/des Antragstellenden.
Wir halten das Mapping hier zentral, damit YAML → API-Payload klar ist.

Die offizielle Quelle für die Felder ist das PDF "Formblatt 1" auf
bafög.de / die Web-Version auf bafoeg-digital.de. Da die Web-Felder
clientseitig gerendert werden, ist die belastbarste Schnittstelle die
Backend-API. Wir definieren daher das Mapping als YAML-Schema und
verschicken die Daten als JSON an ``backend.bafoeg-digital.de``.

Feldnamen in YAML → API-Feldname
---------------------------------
Wir verwenden die in der Web-UI beobachteten Schlüssel. Falls die
Backend-API abweichende Schlüssel erwartet, wird das hier zentral
angepasst.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional

import yaml

# Felder, die im Formblatt 1 typischerweise erwartet werden.
# Optionalität gemäß amtlicher Form (Stand WS 2024/25, unverändert 2026).
FB1_FELDER: list[dict[str, Any]] = [
    {"key": "vorname", "label": "Vorname", "pflicht": True, "typ": "string"},
    {"key": "nachname", "label": "Nachname", "pflicht": True, "typ": "string"},
    {"key": "geburtsdatum", "label": "Geburtsdatum (TT.MM.JJJJ)", "pflicht": True, "typ": "date"},
    {"key": "geburtsort", "label": "Geburtsort", "pflicht": False, "typ": "string"},
    {"key": "staatsangehoerigkeit", "label": "Staatsangehörigkeit", "pflicht": True, "typ": "string"},
    {"key": "geschlecht", "label": "Geschlecht", "pflicht": False, "typ": "enum:m,w,d,x"},
    {"key": "strasse", "label": "Straße", "pflicht": True, "typ": "string"},
    {"key": "hausnummer", "label": "Hausnummer", "pflicht": True, "typ": "string"},
    {"key": "plz", "label": "Postleitzahl", "pflicht": True, "typ": "string"},
    {"key": "ort", "label": "Ort", "pflicht": True, "typ": "string"},
    {"key": "land", "label": "Land (falls nicht DE)", "pflicht": False, "typ": "string"},
    {"key": "email", "label": "E-Mail", "pflicht": True, "typ": "email"},
    {"key": "telefon", "label": "Telefon (optional)", "pflicht": False, "typ": "string"},
    {"key": "iban", "label": "IBAN (Konto für Auszahlung)", "pflicht": True, "typ": "iban"},
    {"key": "bic", "label": "BIC (falls IBAN nicht DE)", "pflicht": False, "typ": "string"},
    {"key": "ausbildung_typ", "label": "Art der Ausbildung", "pflicht": True,
     "typ": "enum:studium,schule,ausbildung"},
    {"key": "ausbildung_ort", "label": "Ausbildungsort (Hochschule/Schule)", "pflicht": True, "typ": "string"},
    {"key": "ausbildung_beginn", "label": "Beginn der Ausbildung (TT.MM.JJJJ)", "pflicht": True, "typ": "date"},
    {"key": "ausbildung_ende_geplant", "label": "Geplantes Ende (TT.MM.JJJJ)", "pflicht": True, "typ": "date"},
    {"key": "bewilligungszeitraum_von", "label": "Bewilligungszeitraum von (TT.MM.JJJJ)", "pflicht": True, "typ": "date"},
    {"key": "bewilligungszeitraum_bis", "label": "Bewilligungszeitraum bis (TT.MM.JJJJ)", "pflicht": True, "typ": "date"},
    {"key": "bei_eltern_wohnend", "label": "Wohnung bei den Eltern", "pflicht": True, "typ": "bool"},
    {"key": "eigene_krankenversicherung", "label": "Eigene Kranken-/Pflegeversicherung", "pflicht": True, "typ": "bool"},
    {"key": "ab_30", "label": "Älter als 30", "pflicht": False, "typ": "bool"},
    {"key": "verheiratet", "label": "Verheiratet / eingetr. LP", "pflicht": False, "typ": "bool"},
    {"key": "eigene_kinder_anzahl", "label": "Anzahl eigener Kinder", "pflicht": False, "typ": "int"},
]

# Pflichtfelder (für die Validierung).
FB1_PFLICHT = [f["key"] for f in FB1_FELDER if f.get("pflicht")]


@dataclass
class Formblatt1:
    """Stammdaten für Formblatt 1.

    Alle Felder sind optional getypt; ``validate()`` prüft die
    Vollständigkeit. Die Datums-Formate werden zur Validierung und für
    die Anzeige einheitlich als ``TT.MM.JJJJ`` erwartet.
    """

    vorname: str = ""
    nachname: str = ""
    geburtsdatum: str = ""
    geburtsort: str = ""
    staatsangehoerigkeit: str = ""
    geschlecht: str = ""
    strasse: str = ""
    hausnummer: str = ""
    plz: str = ""
    ort: str = ""
    land: str = "DE"
    email: str = ""
    telefon: str = ""
    iban: str = ""
    bic: str = ""
    ausbildung_typ: str = ""
    ausbildung_ort: str = ""
    ausbildung_beginn: str = ""
    ausbildung_ende_geplant: str = ""
    bewilligungszeitraum_von: str = ""
    bewilligungszeitraum_bis: str = ""
    bei_eltern_wohnend: bool = False
    eigene_krankenversicherung: bool = True
    ab_30: bool = False
    verheiratet: bool = False
    eigene_kinder_anzahl: int = 0

    # Interne Felder für den Antrags-Kontext.
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_api_payload(self) -> dict[str, Any]:
        """Wandelt die Daten in das für die Backend-API erwartete Format.

        Annahme: Die API erwartet die Felder mit den gleichen Schlüsseln
        wie das YAML. Falls die API andere Schlüssel erwartet, wird
        genau diese Methode angepasst.
        """
        d = self.to_dict()
        d.pop("metadata", None)
        return {"formblatt": "1", "version": "WS2024/25", "daten": d}

    def missing_required(self) -> list[str]:
        """Gibt eine Liste der fehlenden Pflichtfelder zurück.

        Semantik:
        - String-Pflichtfelder ohne Inhalt gelten als fehlend.
        - Bool-Pflichtfelder sind nie "fehlend" – ``False`` ist eine
          gültige Antwort (z.B. "Wohnung bei den Eltern: nein").
        - Numerische Pflichtfelder fehlen nur, wenn sie ``None`` sind.
          ``0`` ist ein gültiger Wert (z.B. ``eigene_kinder_anzahl=0``).
        """
        missing: list[str] = []
        for key in FB1_PFLICHT:
            v = getattr(self, key, None)
            if v is None:
                missing.append(key)
                continue
            if isinstance(v, bool):
                # Bool-Felder (Ja/Nein): False ist eine gültige Antwort.
                continue
            if isinstance(v, str) and not v.strip():
                missing.append(key)
            # Numerische Werte gelten als gesetzt, wenn sie nicht None sind.
        return missing

    def validate(self) -> tuple[bool, list[str]]:
        """Gibt (ok, fehlende_pflichtfelder) zurück."""
        missing = self.missing_required()
        return (len(missing) == 0, missing)


def load_formblatt1_from_yaml(path: str) -> Formblatt1:
    """Lädt Formblatt 1 aus einer YAML-Datei.

    Erwartet ein flaches Mapping von Schlüssel → Wert. Unbekannte Schlüssel
    werden ignoriert (und im ``metadata.unknown_keys`` abgelegt, damit
    der User sie sehen kann).
    """
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"YAML-Wurzel in {path} muss ein Mapping sein, ist {type(raw).__name__}")
    known = {f.name for f in Formblatt1.__dataclass_fields__.values()}  # type: ignore[attr-defined]
    fb = Formblatt1()
    unknown: list[str] = []
    for k, v in raw.items():
        if k in known:
            setattr(fb, k, v)
        else:
            unknown.append(k)
    if unknown:
        fb.metadata["unknown_keys"] = unknown
    return fb


def formblatt1_template_yaml() -> str:
    """Liefert ein kommentiertes YAML-Template mit allen Feldern."""
    lines = ["# BAföG Formblatt 1 – Stammdaten", "# Datum-Format: TT.MM.JJJJ", ""]
    for feld in FB1_FELDER:
        prefix = "# " if not feld["pflicht"] else ""
        lines.append(f"{prefix}{feld['key']}:  # {feld['label']} ({feld['typ']})")
    return "\n".join(lines) + "\n"
