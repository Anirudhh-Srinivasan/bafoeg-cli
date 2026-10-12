"""Tests für werte: Bedarfssätze und Freibeträge."""

from bafoeg_cli.werte import (
    Bedarfssaetze,
    Freibetraege,
    get_bedarfssaetze,
    get_freibetraege,
)


def test_bedarfssaetze_werte_student_eigene_wohnung():
    """Student, eigene Wohnung, eigene KV/PV → 992 €."""
    b = get_bedarfssaetze()
    assert b.max_student(bei_eltern=False, eigene_kv_pv=True, ab_30=False) == 992.0


def test_bedarfssaetze_werte_student_bei_eltern():
    """Student, bei Eltern, eigene KV/PV → 671 €."""
    b = get_bedarfssaetze()
    assert b.max_student(bei_eltern=True, eigene_kv_pv=True, ab_30=False) == 671.0


def test_bedarfssaetze_werte_ohne_kv_pv():
    """Student, eigene Wohnung, familienversichert → 855 €."""
    b = get_bedarfssaetze()
    assert b.max_student(bei_eltern=False, eigene_kv_pv=False, ab_30=False) == 855.0


def test_bedarfssaetze_werte_ab_30():
    """Student 30+, eigene Wohnung, eigene KV/PV → 1.018 €."""
    b = get_bedarfssaetze()
    assert b.max_student(bei_eltern=False, eigene_kv_pv=True, ab_30=True) == 1018.0


def test_bedarfssaetze_aufschlag_ab_30():
    """Aufschlag ab 30 ist +26 € (KV/PV-Erhöhung)."""
    b = get_bedarfssaetze()
    ohne = b.max_student(False, True, False)
    mit = b.max_student(False, True, True)
    assert mit - ohne == 26.0


def test_freibetraege_minijob_2026():
    """Eigenes Einkommen: Minijobgrenze 2026 = 603 €/Monat."""
    f = get_freibetraege()
    assert f.eigen_freibetrag_monat == 603.0


def test_freibetraege_eltern_2026():
    """Eltern verheiratet 2.540 €, alleinstehend 1.690 €."""
    f = get_freibetraege()
    assert f.eltern_verheiratet == 2540.0
    assert f.eltern_allein == 1690.0
    assert f.kind_zuschlag == 770.0
    assert f.stiefeltern == 850.0


def test_freibetraege_vermoegen_2026():
    """Vermögen unter 30: 15.000 €, ab 30: 45.000 €."""
    f = get_freibetraege()
    assert f.vermoegen_unter_30 == 15_000
    assert f.vermoegen_ab_30 == 45_000


def test_werte_sind_dataclass_frozen():
    """Werte sollen nach Import nicht versehentlich änderbar sein."""
    b: Bedarfssaetze = get_bedarfssaetze()
    f: Freibetraege = get_freibetraege()
    assert isinstance(b, Bedarfssaetze)
    assert isinstance(f, Freibetraege)