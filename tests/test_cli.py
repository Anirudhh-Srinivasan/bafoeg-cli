"""Tests für das CLI-Ende (Exit-Codes, Fehler)."""

import pytest

from bafoeg_cli.cli import main


def test_cli_unterlagen_situation(capsys):
    rc = main(
        ["unterlagen", "--situation", "erstantrag_student", "--json"]
    )
    out = capsys.readouterr().out
    assert rc == 0
    assert "formblaetter" in out
    assert "belege" in out


def test_cli_unterlagen_unbekannte_situation(capsys):
    rc = main(["unterlagen", "--situation", "foo"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "Unbekannte Situation" in err


def test_cli_unterlagen_unbekanntes_formblatt(capsys):
    rc = main(["unterlagen", "--formblatt", "42"])
    assert rc == 2


def test_cli_links_unbekannte_kategorie():
    with pytest.raises(SystemExit) as exc:
        main(["links", "--kategorie", "was_anderes"])
    assert exc.value.code == 2


def test_cli_version():
    rc = main(["--version"])
    assert rc == 0