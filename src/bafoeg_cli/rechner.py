"""BAföG-Bedarfsrechner (vereinfachtes Modell nach §13, §13a, §23, §25 BAföG).

Dies ist eine **vereinfachte** Schätzung für die Orientierung – nicht
verbindlich. Das zuständige Amt für Ausbildungsförderung entscheidet
auf Basis der eingereichten Unterlagen. Sozialpauschalen und
Werbungskosten werden hier vereinfacht pauschal angesetzt.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .werte import (
    Bedarfssaetze,
    Freibetraege,
    get_bedarfssaetze,
    get_freibetraege,
)


@dataclass
class Elterneinkommen:
    """Monatliches Nettoeinkommen beider Elternteile (vereinfacht)."""

    vater: float = 0.0
    mutter: float = 0.0
    verheiratet_zusammen: bool = True
    weitere_kinder_im_haushalt: int = 0  # ohne förderfähige Ausbildung


@dataclass
class EigenesEinkommen:
    """Eigenes Einkommen im Bewilligungszeitraum (§23)."""

    brutto_monat: float = 0.0
    ist_minijob: bool = True  # abhängig Beschäftigte/r
    ehegatte_einkommen: float = 0.0  # nur falls verheiratet/LP
    kinder_ohne_ausbildung: int = 0


@dataclass
class Vermoegen:
    """Eigenes Vermögen (§29)."""

    betrag: float = 0.0
    ab_30: bool = False
    hat_partner_oder_kind: int = 0  # +2.300 € pro Person


@dataclass
class RechnerInput:
    """Eingaben für die Bedarfsberechnung."""

    bei_eltern: bool = False
    eigene_krankenversicherung: bool = False  # sonst familienversichert
    ab_30: bool = False
    verheiratet: bool = False
    eltern: Elterneinkommen = field(default_factory=Elterneinkommen)
    eigen: EigenesEinkommen = field(default_factory=EigenesEinkommen)
    vermoegen: Vermoegen = field(default_factory=Vermoegen)


@dataclass
class RechnerErgebnis:
    """Ergebnis der vereinfachten BAföG-Berechnung."""

    bedarf_monat: float
    anrechnung_eltern: float
    anrechnung_eigen: float
    foerderung_monat: float
    hinweise: list[str]
    details: dict


def _eltern_anrechnung(
    eltern: Elterneinkommen,
    frei: Freibetraege,
) -> tuple[float, dict]:
    """Anrechnungsbetrag vom Elterneinkommen nach §25.

    Vereinfachung: Brutto = Netto (Werbungskosten und Sozialpauschalen
    werden nicht abgezogen). Wer das genau haben will, soll die
    zuständige BAföG-Berechnung des Amts nutzen.
    """
    if eltern.verheiratet_zusammen:
        gesamt = eltern.vater + eltern.mutter
        grundfrei = frei.eltern_verheiratet
        aufteilung = "verheiratet_zusammen"
    else:
        gesamt = eltern.vater + eltern.mutter
        grundfrei = 2 * frei.eltern_allein
        aufteilung = "getrennt"

    # Aufstockung für Kinder im Haushalt, die nicht in förderfähiger
    # Ausbildung sind
    zuschlag_kinder = eltern.weitere_kinder_im_haushalt * frei.kind_zuschlag
    absolut = max(0.0, gesamt - (grundfrei + zuschlag_kinder))

    # Relativer Freibetrag: 50 % + 5 % je Kind
    relativ_frei_prozent = (
        frei.relativ_grundanteil + eltern.weitere_kinder_im_haushalt * frei.relativ_pro_kind
    )
    anrechnung = absolut * (1.0 - relativ_frei_prozent)

    return round(anrechnung, 2), {
        "aufteilung": aufteilung,
        "einkommen_gesamt": round(gesamt, 2),
        "grundfreibetrag": grundfrei,
        "zuschlag_kinder": zuschlag_kinder,
        "nach_absolut_frei": round(absolut, 2),
        "relativ_freier_anteil": f"{int(relativ_frei_prozent * 100)}%",
        "anrechnung_monat": round(anrechnung, 2),
        "vereinfachung": "Brutto=Netto (Werbungskosten/Sozialversicherung nicht abgezogen)",
    }


def _eigen_anrechnung(
    eigen: EigenesEinkommen,
    frei: Freibetraege,
    verheiratet: bool,
) -> tuple[float, dict]:
    """Eigenes Einkommen wird in voller Höhe auf den Bedarf angerechnet
    soweit es den Freibetrag übersteigt (§23)."""
    # Freibetrag = Minijob-Grenze (603 € ab 01.01.2026) zzgl.
    # Zuschläge für Partner/Kinder (jeweils minus deren Einkommen).
    partner_frei = 0.0
    if verheiratet and eigen.ehegatte_einkommen <= frei.stiefeltern:
        # vereinfacht: Freibetrag = 850 € abzüglich Einkommen
        partner_frei = max(0.0, frei.stiefeltern - eigen.ehegatte_einkommen)

    # Freibeträge für eigene Kinder (vereinfacht: ohne Einkommen)
    kinder_frei = eigen.kinder_ohne_ausbildung * frei.kind_zuschlag

    gesamt_frei = frei.eigen_freibetrag_monat + partner_frei + kinder_frei
    ueberschuss = max(0.0, eigen.brutto_monat - gesamt_frei)
    return round(ueberschuss, 2), {
        "brutto_monat": round(eigen.brutto_monat, 2),
        "freibetrag_basis": frei.eigen_freibetrag_monat,
        "freibetrag_partner": round(partner_frei, 2),
        "freibetrag_kinder": round(kinder_frei, 2),
        "freibetrag_gesamt": round(gesamt_frei, 2),
        "anrechnung_monat": round(ueberschuss, 2),
    }


def _vermoegen_pruefung(
    vermoegen: Vermoegen,
    frei: Freibetraege,
) -> tuple[bool, dict]:
    """Prüft, ob das Vermögen über dem Freibetrag liegt."""
    if vermoegen.ab_30:
        grund = frei.vermoegen_ab_30
    else:
        grund = frei.vermoegen_unter_30
    aufstock = vermoegen.hat_partner_oder_kind * frei.vermoegen_je_kind_oder_partner
    frei_gesamt = grund + aufstock
    ueber = vermoegen.betrag > frei_gesamt
    return ueber, {
        "freibetrag_basis": grund,
        "freibetrag_aufstockung": aufstock,
        "freibetrag_gesamt": frei_gesamt,
        "vermoegen": round(vermoegen.betrag, 2),
        "ueber_freibetrag": ueber,
        "hinweis": (
            "Vermögen über Freibetrag: kein BAföG möglich (§29)."
            if ueber
            else "Vermögen unter Freibetrag."
        ),
    }


def berechne(
    eingabe: RechnerInput,
    bedarf: Bedarfssaetze | None = None,
    frei: Freibetraege | None = None,
) -> RechnerErgebnis:
    """Berechnet den voraussichtlichen BAföG-Höchstsatz und die Anrechnung."""
    bedarf = bedarf or get_bedarfssaetze()
    frei = frei or get_freibetraege()

    # 1. Bedarf
    bedarf_monat = bedarf.max_student(
        bei_eltern=eingabe.bei_eltern,
        eigene_kv_pv=eingabe.eigene_krankenversicherung,
        ab_30=eingabe.ab_30,
    )

    # 2. Vermögensprüfung
    verm_ueber, verm_details = _vermoegen_pruefung(eingabe.vermoegen, frei)

    # 3. Elternanrechnung
    anr_eltern, det_eltern = _eltern_anrechnung(eingabe.eltern, frei)

    # 4. Eigenanrechnung
    anr_eigen, det_eigen = _eigen_anrechnung(
        eingabe.eigen, frei, eingabe.verheiratet
    )

    # 5. Förderung = max(0, Bedarf - Anrechnung)
    foerderung = max(0.0, bedarf_monat - anr_eltern - anr_eigen)
    if verm_ueber:
        foerderung = 0.0

    hinweise = [
        "Vereinfachte Schätzung – verbindlich ist nur der Bescheid des "
        "Amts für Ausbildungsförderung.",
        "Werbungskosten und Sozialpauschalen sind hier nicht abgezogen.",
    ]
    if verm_ueber:
        hinweise.append(
            "Vermögen über dem Freibetrag nach §29 BAföG – Förderung "
            "scheidet aus."
        )

    return RechnerErgebnis(
        bedarf_monat=round(bedarf_monat, 2),
        anrechnung_eltern=anr_eltern,
        anrechnung_eigen=anr_eigen,
        foerderung_monat=round(foerderung, 2),
        hinweise=hinweise,
        details={
            "vermoegen": verm_details,
            "eltern": det_eltern,
            "eigen": det_eigen,
        },
    )


def ergebnis_to_dict(erg: RechnerErgebnis) -> dict:
    """JSON-fähige Form des Ergebnisses."""
    return {
        "bedarf_monat_euro": erg.bedarf_monat,
        "anrechnung_eltern_euro": erg.anrechnung_eltern,
        "anrechnung_eigen_euro": erg.anrechnung_eigen,
        "foerderung_monat_euro": erg.foerderung_monat,
        "details": erg.details,
        "hinweise": erg.hinweise,
    }