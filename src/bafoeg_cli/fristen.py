"""BAföG-Fristen: Antrag, Folgeantrag, Leistungsnachweis §48, Flexibilitätssemester."""

from __future__ import annotations

from dataclasses import dataclass

QUELLE_FRISTEN = (
    "bafög.de – 'Antrag auf Ausbildungsförderung', "
    "§15, §18 Abs. 2, §48 BAföG (verifiziert 2026-10-12)"
)


@dataclass(frozen=True)
class Frist:
    name: str
    rechtsgrundlage: str
    frist: str
    detail: str


FRISTEN: list[Frist] = [
    Frist(
        name="Erstantrag",
        rechtsgrundlage="§15 Abs. 1, §18 Abs. 2 BAföG",
        frist="Antrag wird ab dem Monat des Eingangs beim Amt bew illigt; "
        "kein rückwirkender Anspruch.",
        detail=(
            "Möglichst bald nach Erhalt der Zulassung/Ausbildungsbestätigung "
            "stellen. Eine formlose Antragstellung zur Fristwahrung ist "
            "möglich, wenn noch nicht alle Formblätter vorliegen."
        ),
    ),
    Frist(
        name="Folgeantrag (Studierende)",
        rechtsgrundlage="§15 Abs. 2 BAföG",
        frist=(
            "Spätestens 2 Monate vor Ablauf des Bewilligungszeitraums "
            "stellen (empfohlen: 4 Monate)."
        ),
        detail=(
            "Wird der Folgeantrag nicht rechtzeitig gestellt, entsteht eine "
            "Zahlungslücke. Formblatt 9 (Folgeantrag) statt Formblatt 1, "
            "sofern das zuständige Amt gleich bleibt."
        ),
    ),
    Frist(
        name="Folgeantrag (Schüler)",
        rechtsgrundlage="§15 Abs. 2 BAföG",
        frist=(
            "Spätestens 2 Monate vor Ende des Schuljahres."
        ),
        detail=(
            "Bewilligungszeitraum ist in der Regel ein Schuljahr; "
            "Antrag auf das neue Schuljahr rechtzeitig stellen."
        ),
    ),
    Frist(
        name="Leistungsnachweis (§48 BAföG)",
        rechtsgrundlage="§48 Abs. 1 BAföG",
        frist=(
            "Mit Beginn des 5. Fachsemesters vorzulegen (Stichtag "
            "in der Regel 30. September / Ende 4. Fachsemester)."
        ),
        detail=(
            "Positiver Leistungsnachweis erfordert die übliche "
            "Leistungsmenge (z.B. 105 ECTS bis Ende 4. FS). Negativer "
            "Leistungsnachweis führt zur Einstellung der Förderung."
        ),
    ),
    Frist(
        name="Verschiebung Leistungsnachweis",
        rechtsgrundlage="§48 Abs. 2 BAföG",
        frist="Antrag auf Verschiebung bei wichtigem Grund (z.B. Krankheit, "
        "Erziehung, Gremientätigkeit).",
        detail=(
            "Bei Verschiebung wird der Vorlagezeitpunkt auf das Ende eines "
            "Folgesemesters verlegt; in der Zwischenzeit wird weiter "
            "gefördert."
        ),
    ),
    Frist(
        name="Flexibilitätssemester",
        rechtsgrundlage="§16 Abs. 4 BAföG (seit WS 2024/25)",
        frist=(
            "Einmalig pro Studiengang (Bachelor ODER Master) zusätzliches "
            "Förderungssemester ohne besonderen Grund."
        ),
        detail=(
            "Verlängert die Förderungshöchstdauer um ein Semester; "
            "kann nicht zur Verlängerung der §48-Frist oder für "
            "Fachrichtungswechsel genutzt werden."
        ),
    ),
    Frist(
        name="Vorausleistung",
        rechtsgrundlage="§36, §37 BAföG; Formblatt 8",
        frist="Wenn Eltern trotz Aufforderung keinen Unterhalt leisten.",
        detail=(
            "Antrag auf Vorausleistung über Formblatt 8; das Amt zahlt "
            "vor und versucht später, das Geld von den Eltern "
            "zurückzuholen."
        ),
    ),
    Frist(
        name="Aktualisierung Einkommen",
        rechtsgrundlage="§24, §30 BAföG; Formblatt 7",
        frist="Innerhalb des Bewilligungszeitraums bei Einkommensänderung.",
        detail=(
            "Aktualisierungsantrag über Formblatt 7, wenn z.B. das "
            "Elterneinkommen im laufenden Jahr erheblich abweicht."
        ),
    ),
    Frist(
        name="Widerspruch gegen Bescheid",
        rechtsgrundlage="§§68 ff. VwGO",
        frist="1 Monat ab Bekanntgabe des Bescheids schriftlich beim Amt.",
        detail=(
            "Widerspruch ist kostenfrei; bei Untätigkeit Klage vor dem "
            "Verwaltungsgericht möglich."
        ),
    ),
]


def alle_fristen() -> list[dict]:
    """Alle Fristen als Dicts (JSON-fähig)."""
    return [
        {
            "name": f.name,
            "rechtsgrundlage": f.rechtsgrundlage,
            "frist": f.frist,
            "detail": f.detail,
        }
        for f in FRISTEN
    ]