"""Tests für den Bedarfsrechner."""

from bafoeg_cli.rechner import (
    EigenesEinkommen,
    Elterneinkommen,
    RechnerInput,
    Vermoegen,
    berechne,
)


def _kv_inp(**kwargs) -> RechnerInput:
    """Default: eigene Wohnung, eigene KV/PV, max Bedarf (992 €)."""
    kwargs.setdefault("bei_eltern", False)
    kwargs.setdefault("eigene_krankenversicherung", True)
    return RechnerInput(**kwargs)


def test_voller_anspruch_ohne_anrechnung():
    """Maximaler Bedarf, keine Anrechnungen → voller Höchstsatz."""
    inp = _kv_inp()
    erg = berechne(inp)
    assert erg.bedarf_monat == 992.0
    assert erg.anrechnung_eltern == 0.0
    assert erg.anrechnung_eigen == 0.0
    assert erg.foerderung_monat == 992.0


def test_bei_eltern_kv_ohne_anrechnung():
    """Bei Eltern, eigene KV, sonst leer → 671 €."""
    inp = _kv_inp(bei_eltern=True)
    erg = berechne(inp)
    assert erg.bedarf_monat == 671.0
    assert erg.foerderung_monat == 671.0


def test_ohne_kv_pv_smoke():
    """Student, eigene Wohnung, familienversichert → 855 €."""
    inp = RechnerInput(
        bei_eltern=False,
        eigene_krankenversicherung=False,
    )
    erg = berechne(inp)
    assert erg.bedarf_monat == 855.0


def test_anrechnung_eltern_unter_freibetrag():
    """Eltern verdienen unter Freibetrag → keine Anrechnung."""
    inp = _kv_inp(
        eltern=Elterneinkommen(
            vater=1500.0,
            mutter=500.0,
            verheiratet_zusammen=True,
        ),
    )
    erg = berechne(inp)
    # Gesamt 2000 < 2540 → keine Anrechnung
    assert erg.anrechnung_eltern == 0.0
    assert erg.foerderung_monat == 992.0


def test_anrechnung_eltern_ueber_freibetrag():
    """Eltern verheiratet 4.000 €/Mon → Überschuss 1.460 €.

    50 % anrechnungsfrei = 730 €; relatives Kind: 0 → 50 %.
    Anrechnung = 1.460 * 0,5 = 730 €.
    Förderung = 992 - 730 = 262 €.
    """
    inp = _kv_inp(
        eltern=Elterneinkommen(
            vater=2500.0,
            mutter=1500.0,
            verheiratet_zusammen=True,
        ),
    )
    erg = berechne(inp)
    assert erg.bedarf_monat == 992.0
    assert erg.anrechnung_eltern == 730.0
    assert erg.foerderung_monat == 262.0


def test_anrechnung_eltern_getrennt():
    """Eltern getrennt, jeder 2.000 € → Grundfrei 2×1.690 = 3.380.

    Überschuss = 4.000 - 3.380 = 620; 50 % relativ frei = 310 €.
    """
    inp = _kv_inp(
        eltern=Elterneinkommen(
            vater=2000.0,
            mutter=2000.0,
            verheiratet_zusammen=False,
        ),
    )
    erg = berechne(inp)
    assert erg.details["eltern"]["anrechnung_monat"] == 310.0


def test_anrechnung_eigenes_einkommen_unter_freibetrag():
    """Eigenes Einkommen 400 €/Mon < 603 € → keine."""
    inp = _kv_inp(
        eigen=EigenesEinkommen(brutto_monat=400.0),
    )
    erg = berechne(inp)
    assert erg.anrechnung_eigen == 0.0
    assert erg.foerderung_monat == 992.0


def test_anrechnung_eigenes_einkommen_ueber_freibetrag():
    """Eigenes Einkommen 800 €/Mon → 800 - 603 = 197 €."""
    inp = _kv_inp(
        eigen=EigenesEinkommen(brutto_monat=800.0),
    )
    erg = berechne(inp)
    assert erg.anrechnung_eigen == 197.0


def test_anrechnung_kombiniert():
    """Beide Seiten rechnen an: Bedarf 992, Eltern-Anr. > 0, Eigen 100."""
    inp = _kv_inp(
        eltern=Elterneinkommen(
            vater=3000.0, mutter=1000.0, verheiratet_zusammen=True
        ),
        eigen=EigenesEinkommen(brutto_monat=703.0),
    )
    erg = berechne(inp)
    assert erg.bedarf_monat == 992.0
    assert erg.anrechnung_eltern > 0
    assert erg.anrechnung_eigen == 100.0
    assert erg.foerderung_monat == (
        erg.bedarf_monat - erg.anrechnung_eltern - erg.anrechnung_eigen
    )


def test_vermoegen_unter_freibetrag():
    """Vermögen 5.000 € unter 30 → keine Sperre."""
    inp = _kv_inp(
        vermoegen=Vermoegen(betrag=5_000.0, ab_30=False),
    )
    erg = berechne(inp)
    assert erg.details["vermoegen"]["ueber_freibetrag"] is False
    assert erg.foerderung_monat > 0


def test_vermoegen_ueber_freibetrag_unter_30():
    """Vermögen 20.000 € unter 30 > 15.000 → keine Förderung."""
    inp = _kv_inp(
        vermoegen=Vermoegen(betrag=20_000.0, ab_30=False),
    )
    erg = berechne(inp)
    assert erg.details["vermoegen"]["ueber_freibetrag"] is True
    assert erg.foerderung_monat == 0.0


def test_vermoegen_ab_30_erhoeht():
    """Vermögen 30.000 € ab 30 < 45.000 → keine Sperre."""
    inp = _kv_inp(
        vermoegen=Vermoegen(betrag=30_000.0, ab_30=True),
    )
    erg = berechne(inp)
    assert erg.details["vermoegen"]["ueber_freibetrag"] is False


def test_foerderung_nie_negativ():
    """Anrechnung kann Bedarf nicht übersteigen (max 0)."""
    inp = _kv_inp(
        eltern=Elterneinkommen(
            vater=10_000.0, mutter=10_000.0, verheiratet_zusammen=True
        ),
        eigen=EigenesEinkommen(brutto_monat=2_000.0),
    )
    erg = berechne(inp)
    assert erg.foerderung_monat >= 0.0


def test_ab_30_erhoeht_hoechstsatz():
    """Student ab 30: Bedarf = 1.018 €."""
    inp = RechnerInput(
        bei_eltern=False,
        eigene_krankenversicherung=True,
        ab_30=True,
    )
    erg = berechne(inp)
    assert erg.bedarf_monat == 1018.0
    assert erg.foerderung_monat == 1018.0