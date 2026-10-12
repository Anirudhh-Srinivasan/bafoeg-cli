"""Offizielle BAföG-Links: BAföG Digital, Ämterverzeichnis, Rechtstexte."""

from __future__ import annotations

QUELLE_LINKS = (
    "bafög.de (offizielles Portal des BMBF), "
    "verwaltungsportal.bund.de, gesetze-im-internet.de (verifiziert "
    "2026-10-12)"
)

KATEGORIEN = {
    "antrag_online": {
        "label": "BAföG digital – Online-Antrag",
        "links": [
            {
                "name": "BAföG-Digital Antragsassistent",
                "url": "https://bafoeg-digital.de/",
                "beschreibung": (
                    "Vollständig digitale Antragstellung; "
                    "Schritt-für-Schritt-Assistent mit Plausibilitätsprüfung."
                ),
            },
            {
                "name": "bafög.de – Antrag stellen",
                "url": (
                    "https://www.xn--bafg-7qa.de/bafoeg/de/antrag-stellen/"
                    "antrag-stellen_node.html"
                ),
                "beschreibung": (
                    "Übersicht Erstantrag, Folgeantrag, Aktualisierung; "
                    "Links zu BAföG-Digital."
                ),
            },
        ],
    },
    "amt_finden": {
        "label": "Zuständiges Amt für Ausbildungsförderung finden",
        "links": [
            {
                "name": "bafög.de – Ämterverzeichnis",
                "url": (
                    "https://www.xn--bafg-7qa.de/bafoeg/de/"
                    "antrag-stellen/ihre-ausbildungsstaette/"
                    "wo-ist-mein-antrag-zu-stellen-/wo-ist-mein-antrag-"
                    "zu-stellen-_node.html"
                ),
                "beschreibung": (
                    "Suche nach zuständigem Amt nach Studiensitz/Wohnort; "
                    "auch für Auslands-BAföG."
                ),
            },
            {
                "name": "Verwaltungsportal Hessen – BAföG",
                "url": (
                    "https://verwaltungsportal.hessen.de/"
                    "leistung?leistung_id=B100019"
                ),
                "beschreibung": (
                    "Beispiel für länderspezifische Online-Verfahren."
                ),
            },
        ],
    },
    "rechtstexte": {
        "label": "Gesetzliche Grundlagen",
        "links": [
            {
                "name": "BAföG (gesetze-im-internet.de)",
                "url": (
                    "https://www.gesetze-im-internet.de/baf_g/"
                    "index.html"
                ),
                "beschreibung": (
                    "Volltext Bundesausbildungsförderungsgesetz; §§13, "
                    "15, 18, 23, 25, 29, 48."
                ),
            },
            {
                "name": "bafög.de – Bedarfssätze (offiziell)",
                "url": (
                    "https://www.xn--bafg-7qa.de/bafoeg/de/das-bafoeg-"
                    "alle-infos-auf-einen-blick/"
                    "foerderungsarten-und-foerderungshoehe/"
                    "foerderungshoehe/foerderungshoehe_node.html"
                ),
                "beschreibung": (
                    "Amtliche Darstellung der aktuellen Bedarfssätze "
                    "(Stand und Inkrafttreten)."
                ),
            },
            {
                "name": "bafög.de – Freibeträge",
                "url": (
                    "https://www.xn--bafg-7qa.de/bafoeg/de/das-bafoeg-"
                    "alle-infos-auf-einen-blick/foerderungsarten-und-"
                    "foerderungshoehe/welche-freibetraege-werden-"
                    "gewaehrt/welche-freibetraege-werden-gewaehrt_node.html"
                ),
                "beschreibung": (
                    "Amtliche Darstellung der Freibeträge eigenes "
                    "Einkommen, Eltern, Ehegatte."
                ),
            },
        ],
    },
    "formulare": {
        "label": "Formblätter und Vordrucke",
        "links": [
            {
                "name": "bafög.de – Alle Antragsformulare",
                "url": (
                    "https://www.xn--bafg-7qa.de/bafoeg/de/"
                    "antrag-stellen/alle-antragsformulare/"
                    "alle-antragsformulare_node.html"
                ),
                "beschreibung": (
                    "Direktdownloads Formblätter 1–9 (Stand v2025), "
                    "barrierearm/barrierefrei wo möglich."
                ),
            },
            {
                "name": "Bundesverwaltungsamt – Rückzahlung BAföG",
                "url": (
                    "https://www.bva.bund.de/DE/Services/Buerger/"
                    "Ausbildungsfoerderung/"
                    "ausbildungsfoerderung_node.html"
                ),
                "beschreibung": (
                    "Rückzahlung, Freistellung, einkommensabhängiger "
                    "Zahlungsaufschub."
                ),
            },
        ],
    },
}


def alle_links() -> list[dict]:
    """Alle Links, gruppiert nach Kategorie."""
    result = []
    for key, kat in KATEGORIEN.items():
        result.append(
            {
                "kategorie": key,
                "label": kat["label"],
                "links": kat["links"],
            }
        )
    return result


def kategorie(name: str) -> dict | None:
    """Liefert eine einzelne Kategorie oder None."""
    kat = KATEGORIEN.get(name)
    if not kat:
        return None
    return {
        "kategorie": name,
        "label": kat["label"],
        "links": kat["links"],
    }