"""BAföG-Bedarfssätze, Freibeträge und Sozialpauschalen.

Quelle: bafög.de (Bundesministerium für Bildung und Forschung) sowie die
konsolidierte Fassung des BAföG (gesetze-im-internet.de).

Stand: gültig seit Wintersemester 2024/25, unverändert für das Jahr 2026.
Geplante Erhöhung der Wohnpauschale auf 440 € zum WS 2026/27 ist noch
nicht in Kraft (Stand: 12.10.2026, vorbehaltlich späterer Verkündung).
"""

from __future__ import annotations

from dataclasses import dataclass

QUELLE = "bafög.de / gesetze-im-internet.de (BAföG, Stand WS 2024/25)"
STAND = "WS 2024/25, unverändert 2026 (verifiziert 2026-10-12)"
GUELTIG_AB = "01.10.2024 (laufende Bewilligungszeiträume) / 01.08.2024 (neue)"


@dataclass(frozen=True)
class Bedarfssaetze:
    """Studierende nach §13 Abs. 1 Nr. 2, Abs. 2 Nr. 2, §13a BAföG."""

    grundbedarf_student: float = 475.0
    wohnung_eigene_wohnung: float = 380.0
    wohnung_bei_eltern: float = 59.0
    kv_zuschlag: float = 102.0
    pv_zuschlag: float = 35.0
    # §13a Abs. 3: ab 30 erhöht sich der KV/PV-Zuschlag für Studierende
    # um insgesamt 26 € (1.018 statt 992 € Höchstsatz).
    kv_pv_aufschlag_ab_30: float = 26.0
    auslandszuschlag: float = 0.0  # §13 Abs. 3, hier nicht berechnet

    def max_student(self, bei_eltern: bool, eigene_kv_pv: bool, ab_30: bool) -> float:
        """Theoretischer Höchstsatz Studierende (§13 + §13a)."""
        wohn = self.wohnung_bei_eltern if bei_eltern else self.wohnung_eigene_wohnung
        base = self.grundbedarf_student + wohn
        if eigene_kv_pv:
            base += self.kv_zuschlag + self.pv_zuschlag
            if ab_30:
                base += self.kv_pv_aufschlag_ab_30
        return round(base, 2)


@dataclass(frozen=True)
class Freibetraege:
    """§23, §25, §29 BAföG (seit 01.08.2024 / 01.01.2026 Minijob)."""

    # Eigenes Einkommen (§23): Minijobgrenze 2026 = 603 €/Monat
    eigen_freibetrag_monat: float = 603.0
    # Eltern verheiratet zusammenlebend
    eltern_verheiratet: float = 2540.0
    # Eltern einzeln (alleinerziehend / getrennt / geschieden)
    eltern_allein: float = 1690.0
    # Stiefelternteil / neuer Ehegatte
    stiefeltern: float = 850.0
    # Pro unterhaltsberechtigtem Kind ohne förderfähige Ausbildung
    kind_zuschlag: float = 770.0
    # §25 Abs. 4: vom Überschuss 50% + 5% je Kind
    relativ_grundanteil: float = 0.50
    relativ_pro_kind: float = 0.05
    # Vermögensfreibetrag (§29)
    vermoegen_unter_30: float = 15_000.0
    vermoegen_ab_30: float = 45_000.0
    vermoegen_je_kind_oder_partner: float = 2_300.0
    # Werbungskostenpauschale (§21 Abs. 3) und Sozialpauschale
    werbungskosten_monat: float = 102.50
    sozialpauschale_abhaengig: float = 0.223  # 22,3%
    sozialpauschale_selbst: float = 0.388
    sozialpauschale_beamtet_rentner: float = 0.165


@dataclass(frozen=True)
class BedarfssatzQuelle:
    """Quellenangabe je Bedarfsposition für JSON-Output."""

    paragraph: str
    wert: str
    hinweis: str = ""


STUDIERENDE_QUELLEN = {
    "grundbedarf": BedarfssatzQuelle("§13 Abs. 1 Nr. 2 BAföG", "475 €"),
    "wohnung_eigene_wohnung": BedarfssatzQuelle("§13 Abs. 2 Nr. 2 BAföG", "380 €"),
    "wohnung_bei_eltern": BedarfssatzQuelle("§13 Abs. 2 Nr. 2 BAföG", "59 €"),
    "kv_zuschlag": BedarfssatzQuelle("§13a Abs. 1 BAföG", "102 €"),
    "pv_zuschlag": BedarfssatzQuelle("§13a Abs. 1 BAföG", "35 €"),
    "kv_pv_aufschlag_ab_30": BedarfssatzQuelle(
        "§13a Abs. 3 BAföG",
        "+26 €",
        "Aufschlag auf den KV/PV-Zuschlag ab 30 (Höchstsatz 1.018 €)",
    ),
}

FREIBETRAEGE_QUELLEN = {
    "eigen_freibetrag_monat": BedarfssatzQuelle(
        "§23 BAföG + Minijobgrenze 2026",
        "603 €",
        "Anpassung zum 01.01.2026 (vorher 556 € / 1.1.2025)",
    ),
    "eltern_verheiratet": BedarfssatzQuelle("§25 Abs. 1 Nr. 1 BAföG", "2.540 €"),
    "eltern_allein": BedarfssatzQuelle(
        "§25 Abs. 1 Nr. 2 BAföG", "1.690 €"
    ),
    "stiefeltern": BedarfssatzQuelle("§25 Abs. 3 Nr. 1 BAföG", "850 €"),
    "kind_zuschlag": BedarfssatzQuelle("§25 Abs. 3 Nr. 2 BAföG", "770 €"),
    "relativ_grundanteil": BedarfssatzQuelle("§25 Abs. 4 BAföG", "50 %"),
    "relativ_pro_kind": BedarfssatzQuelle("§25 Abs. 4 BAföG", "5 %"),
    "vermoegen_unter_30": BedarfssatzQuelle("§29 Abs. 1 Nr. 1 BAföG", "15.000 €"),
    "vermoegen_ab_30": BedarfssatzQuelle("§29 Abs. 1 Nr. 1 BAföG", "45.000 €"),
    "vermoegen_je_kind_oder_partner": BedarfssatzQuelle(
        "§29 Abs. 1 Nr. 2 BAföG", "2.300 €"
    ),
}


def get_bedarfssaetze() -> Bedarfssaetze:
    """Bedarfssätze Stand WS 2024/25 (gilt auch 2026)."""
    return Bedarfssaetze()


def get_freibetraege() -> Freibetraege:
    """Freibeträge Stand 2026 (mit Minijob-Anpassung 01.01.2026)."""
    return Freibetraege()