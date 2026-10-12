"""Checkliste der BAföG-Formblätter 1–9 und je nach Situation benötigte Belege."""

from __future__ import annotations

QUELLE_UNTERLAGEN = (
    "bafög.de – 'Alle Antragsformulare' (Formblätter Stand v2025, "
    "verifiziert 2026-10-12)"
)

FORMBLAETTER = {
    1: {
        "name": "Antrag auf Ausbildungsförderung",
        "url": "https://www.xn--bafg-7qa.de/bafoeg/shareddocs/downloads/formblaetter/v2025/formblatt_1.pdf",
        "wer": "Antragsteller/in",
    },
    2: {
        "name": "Bescheinigung nach §9 BAföG (Ausbildungsstätte)",
        "url": "https://www.xn--bafg-7qa.de/bafoeg/shareddocs/downloads/formblaetter/v2025/formblatt_2.pdf",
        "wer": "Ausbildungsstätte (Hochschule/Schule)",
    },
    3: {
        "name": "Einkommenserklärung (Eltern / Ehegatte / Lebenspartner)",
        "url": "https://www.xn--bafg-7qa.de/bafoeg/shareddocs/downloads/formblaetter/v2025/formblatt_3.pdf",
        "wer": "Vater, Mutter, ggf. Ehegatte/Lebenspartner (jeweils eigene Erklärung)",
    },
    4: {
        "name": "Kinder der auszubildenden Person",
        "url": "https://www.xn--bafg-7qa.de/bafoeg/shareddocs/downloads/formblaetter/v2025/formblatt_4.pdf",
        "wer": "Antragsteller/in (bei Kindern unter 14 Jahren)",
    },
    5: {
        "name": "Leistungsbescheinigung nach §48 BAföG",
        "url": "https://www.xn--bafg-7qa.de/bafoeg/shareddocs/downloads/formblaetter/v2025/formblatt_5.pdf",
        "wer": "Hochschule (für Höhere Fachschule / Akademie / Hochschule ab 5. FS)",
    },
    6: {
        "name": "Ausbildung im Ausland (Zusatzblatt)",
        "url": "https://www.xn--bafg-7qa.de/bafoeg/shareddocs/downloads/formblaetter/v2025/formblatt_6.pdf",
        "wer": "Antragsteller/in bei Auslandsaufenthalten",
    },
    7: {
        "name": "Aktualisierung des Einkommens",
        "url": "https://www.xn--bafg-7qa.de/bafoeg/shareddocs/downloads/formblaetter/v2025/formblatt_7.pdf",
        "wer": "Antragsteller/in bei Einkommensänderung im laufenden Bewilligungszeitraum",
    },
    8: {
        "name": "Antrag auf Vorausleistung",
        "url": "https://www.xn--bafg-7qa.de/bafoeg/shareddocs/downloads/formblaetter/v2025/formblatt_8.pdf",
        "wer": "Antragsteller/in (Eltern zahlen keinen Unterhalt)",
    },
    9: {
        "name": "Folgeantrag auf Ausbildungsförderung (nur Studierende)",
        "url": "https://www.xn--bafg-7qa.de/bafoeg/shareddocs/downloads/formblaetter/v2025/formblatt_9.pdf",
        "wer": "Studierende (für Folgeantrag beim gleichen Amt)",
    },
}


SITUATIONEN = {
    "erstantrag_student": {
        "label": "Erstantrag Studierende/r (Hochschule)",
        "formblaetter": [1, 2, 3, 4],
        "formblaetter_optional": [5],  # ab 5. FS
        "belege": [
            "Personalausweis oder Reisepass (Kopie)",
            "Immatrikulationsbescheinigung",
            "Meldebescheinigung (bei eigener Wohnung)",
            "Mietvertrag oder Wohnungsgeberbescheinigung",
            "Lebenslauf (lückenlos)",
            "Nachweise eigenes Einkommen (Lohnabrechnung, Werkvertrag, "
            "Stipendium, Waisenrente)",
            "Nachweise Vermögensveränderungen der letzten 6 Monate",
            "Aufenthaltstitel bei nicht-deutscher Staatsbürgerschaft",
        ],
    },
    "folgeantrag_student": {
        "label": "Folgeantrag Studierende/r",
        "formblaetter": [9, 3, 4],
        "formblaetter_optional": [5],  # ab 5. FS
        "belege": [
            "Folgeantebensoekonigungsbescheinigung der Hochschule",
            "§9-Bescheinigung oder Immatrikulationsbescheinigung",
            "Nachweise zum Einkommen (Eltern aktualisiert über FB 7, "
            "wenn nötig)",
        ],
    },
    "erstantrag_schueler": {
        "label": "Erstantrag Schüler/in",
        "formblaetter": [1, 2, 3],
        "formblaetter_optional": [4],
        "belege": [
            "Personalausweis",
            "Schulbescheinigung",
            "Meldebescheinigung",
            "Nachweise eigenes Einkommen",
        ],
    },
    "auslandsantrag": {
        "label": "Auslands-BAföG",
        "formblaetter": [1, 2, 3, 4, 5, 6],
        "formblaetter_optional": [],
        "belege": [
            "Formblatt 6 ist Pflicht bei Auslandsantrag",
            "Immatrikulationsbescheinigung der ausländischen Hochschule",
            "Sprachnachweis",
            "Nachweise zum Lebensunterhalt im Gastland",
            "Zuständiges Amt: laut Ämterverzeichnis zu Formblatt 6",
        ],
    },
    "vorausleistung": {
        "label": "Antrag auf Vorausleistung",
        "formblaetter": [1, 2, 3, 4, 8],
        "formblaetter_optional": [],
        "belege": [
            "Nachweis, dass Eltern trotz Aufforderung keinen Unterhalt "
            "leisten",
            "Aufforderungsschreiben des Amts",
            "Einkommensverhältnisse der Eltern",
        ],
    },
    "aktualisierung": {
        "label": "Aktualisierungsantrag Einkommen",
        "formblaetter": [7],
        "formblaetter_optional": [],
        "belege": [
            "Neue Einkommensnachweise (Eltern, Ehegatte, eigenes)",
            "Einkommensteuerbescheid bei erheblicher Abweichung",
        ],
    },
}


def formblatt(nummer: int) -> dict | None:
    """Liefert ein einzelnes Formblatt oder None."""
    fb = FORMBLAETTER.get(nummer)
    if not fb:
        return None
    return {"nummer": nummer, **fb}


def alle_formblaetter() -> list[dict]:
    """Alle Formblätter 1–9 als Liste."""
    return [
        {"nummer": n, **fb} for n, fb in sorted(FORMBLAETTER.items())
    ]


def situation(schluessel: str) -> dict | None:
    """Liefert die Checkliste zu einer bestimmten Situation."""
    sit = SITUATIONEN.get(schluessel)
    if not sit:
        return None
    formbl = []
    for n in sit["formblaetter"]:
        formbl.append(formblatt(n))
    formbl_opt = []
    for n in sit["formblaetter_optional"]:
        formbl_opt.append(formblatt(n))
    return {
        "schluessel": schluessel,
        "label": sit["label"],
        "formblaetter": formbl,
        "formblaetter_optional": formbl_opt,
        "belege": sit["belege"],
    }


def alle_situationen() -> list[dict]:
    """Alle unterstützten Situationen."""
    result = []
    for s in SITUATIONEN.keys():
        sit = situation(s)
        if sit is not None:
            result.append(sit)
    return result