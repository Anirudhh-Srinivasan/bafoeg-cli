"""Tests für Fristen, Formblätter und Links."""

from bafoeg_cli import fristen, links, unterlagen


# --- fristen ----------------------------------------------------------


def test_fristen_nicht_leer():
    assert len(fristen.FRISTEN) > 0


def test_fristen_enthalten_wichtige_begriffe():
    """Sicherstellen, dass die Pflicht-Fristen enthalten sind."""
    namen = {f.name for f in fristen.FRISTEN}
    assert "Erstantrag" in namen
    assert "Folgeantrag (Studierende)" in namen
    assert "Leistungsnachweis (§48 BAföG)" in namen
    assert "Widerspruch gegen Bescheid" in namen


def test_fristen_haben_rechtsgrundlage():
    for f in fristen.FRISTEN:
        assert "§" in f.rechtsgrundlage or "VwGO" in f.rechtsgrundlage


def test_fristen_json_format():
    data = fristen.alle_fristen()
    assert isinstance(data, list)
    for eintrag in data:
        assert set(eintrag.keys()) >= {
            "name", "rechtsgrundlage", "frist", "detail"
        }


# --- unterlagen -------------------------------------------------------


def test_formblaetter_alle():
    fb = unterlagen.alle_formblaetter()
    assert {f["nummer"] for f in fb} == {1, 2, 3, 4, 5, 6, 7, 8, 9}


def test_formblatt_lookup():
    fb = unterlagen.formblatt(5)
    assert fb is not None
    assert fb["nummer"] == 5
    assert "Leistungsbescheinigung" in fb["name"]


def test_formblatt_unbekannt():
    assert unterlagen.formblatt(99) is None


def test_situationen_vorhanden():
    s = unterlagen.alle_situationen()
    assert any(x["schluessel"] == "erstantrag_student" for x in s)
    assert any(x["schluessel"] == "folgeantrag_student" for x in s)
    assert any(x["schluessel"] == "auslandsantrag" for x in s)


def test_situation_erstantrag_student_enthalten_formblaetter():
    sit = unterlagen.situation("erstantrag_student")
    assert sit is not None
    nums = [fb["nummer"] for fb in sit["formblaetter"]]
    assert 1 in nums
    assert 2 in nums
    assert 3 in nums


def test_situation_auslandsantrag_enthalten_formblatt_6():
    sit = unterlagen.situation("auslandsantrag")
    assert sit is not None
    nums = [fb["nummer"] for fb in sit["formblaetter"]]
    assert 6 in nums


def test_situation_unbekannt():
    assert unterlagen.situation("gibt_es_nicht") is None


# --- links ------------------------------------------------------------


def test_links_kategorien_vorhanden():
    for key in ("antrag_online", "amt_finden", "rechtstexte", "formulare"):
        assert links.kategorie(key) is not None


def test_links_bafoeg_digital_enthaltend():
    kat = links.kategorie("antrag_online")
    assert kat is not None
    urls = [l["url"] for l in kat["links"]]
    assert any("bafoeg-digital" in u for u in urls)


def test_links_amt_finden_enthaltend():
    kat = links.kategorie("amt_finden")
    assert kat is not None
    assert len(kat["links"]) >= 1


def test_links_rechtstexte_gesetze_im_internet():
    kat = links.kategorie("rechtstexte")
    assert kat is not None
    urls = [l["url"] for l in kat["links"]]
    assert any("gesetze-im-internet.de" in u for u in urls)


def test_links_alle_kategorien():
    data = links.alle_links()
    assert isinstance(data, list)
    assert len(data) >= 3


# --- cli Smoke-Tests --------------------------------------------------


def test_cli_build_parser():
    from bafoeg_cli.cli import build_parser

    p = build_parser()
    # Top-level subparsers
    sub = next(
        action
        for action in p._actions
        if action.dest == "befehl"
    )
    assert "rechner" in sub.choices
    assert "fristen" in sub.choices
    assert "unterlagen" in sub.choices
    assert "links" in sub.choices


def test_cli_fristen_json(capsys):
    from bafoeg_cli.cli import main

    rc = main(["fristen", "--json"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "\"quelle\"" in out
    assert "\"fristen\"" in out


def test_cli_unterlagen_formblatt_5(capsys):
    from bafoeg_cli.cli import main

    rc = main(["unterlagen", "--formblatt", "5", "--json"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "Formblatt" in out or "Leistungsbescheinigung" in out


def test_cli_links_kategorie(capsys):
    from bafoeg_cli.cli import main

    rc = main(["links", "--kategorie", "antrag_online", "--json"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "bafoeg-digital" in out or "BAföG-Digital" in out


def test_cli_rechner_smoke(capsys):
    from bafoeg_cli.cli import main

    rc = main(["rechner", "--eigene-kv", "--json"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "foerderung_monat_euro" in out
    assert "992" in out


def test_cli_rechner_mit_eltern_ueber_freibetrag(capsys):
    from bafoeg_cli.cli import main

    # Eltern verheiratet 4.500 €/Mon → Überschuss 1.960 € → 50 % → 980 €
    rc = main(
        [
            "rechner",
            "--eigene-kv",
            "--einkommen-vater",
            "3000",
            "--einkommen-mutter",
            "1500",
            "--eigen-einkommen",
            "800",
            "--json",
        ]
    )
    out = capsys.readouterr().out
    assert rc == 0
    assert "anrechnung_eltern_euro" in out
    assert "980" in out