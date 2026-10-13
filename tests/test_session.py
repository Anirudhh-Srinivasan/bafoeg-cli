"""Tests für die Session-Verwaltung (ohne Browser).

Wir leiten ``XDG_CONFIG_HOME`` und ``BAFOEG_CONFIG_DIR`` per Monkeypatch
in ein Tempdir um, damit kein Test die echte User-Session berührt.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from bafoeg_cli.automation.session import (
    CONFIG_DIR_ENV,
    default_config_dir,
    delete_session,
    ensure_config_dir,
    is_session_fresh,
    prompt_username_password,
    session_exists,
    session_path,
    write_config_defaults,
)


def test_config_dir_xdg_gesetzt(monkeypatch, tmp_path: Path):
    monkeypatch.setenv(CONFIG_DIR_ENV, str(tmp_path / "custom"))
    assert default_config_dir() == tmp_path / "custom"
    d = ensure_config_dir()
    assert d == tmp_path / "custom"
    assert d.exists()
    assert oct(d.stat().st_mode & 0o777) == "0o700"


def test_config_dir_xdg_default(monkeypatch, tmp_path: Path):
    monkeypatch.delenv(CONFIG_DIR_ENV, raising=False)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    assert default_config_dir() == tmp_path / "xdg" / "bafoeg-cli"


def test_config_dir_home_fallback(monkeypatch, tmp_path: Path):
    monkeypatch.delenv(CONFIG_DIR_ENV, raising=False)
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    assert default_config_dir() == tmp_path / ".config" / "bafoeg-cli"


def test_session_pfad_in_config_dir(monkeypatch, tmp_path: Path):
    monkeypatch.setenv(CONFIG_DIR_ENV, str(tmp_path / "c"))
    p = session_path()
    assert p.parent == tmp_path / "c"
    assert p.name == "session.json"


def test_session_exist_roundtrip(monkeypatch, tmp_path: Path):
    monkeypatch.setenv(CONFIG_DIR_ENV, str(tmp_path / "c"))
    assert session_exists() is False
    # Künstlich anlegen.
    session_path().write_text("{}", encoding="utf-8")
    assert session_exists() is True
    assert delete_session() is True
    assert session_exists() is False
    assert delete_session() is False  # idempotent


def test_session_fresh(monkeypatch, tmp_path: Path):
    monkeypatch.setenv(CONFIG_DIR_ENV, str(tmp_path / "c"))
    assert is_session_fresh() is False
    session_path().write_text("{}", encoding="utf-8")
    assert is_session_fresh(max_age_s=60) is True


def test_prompt_username_password_aus_env(monkeypatch, tmp_path: Path):
    monkeypatch.setenv(CONFIG_DIR_ENV, str(tmp_path / "c"))
    monkeypatch.setenv("BAFOEG_USERNAME", "max@example.org")
    monkeypatch.setenv("BAFOEG_PASSWORD", "geheim-123")
    user, pw = prompt_username_password()
    assert user == "max@example.org"
    assert pw == "geheim-123"


def test_prompt_username_password_unterdrueckt_logging(monkeypatch, tmp_path: Path, caplog):
    """Das Passwort darf NICHT in caplog oder sonstwo auftauchen."""
    monkeypatch.setenv(CONFIG_DIR_ENV, str(tmp_path / "c"))
    monkeypatch.setenv("BAFOEG_USERNAME", "x")
    monkeypatch.setenv("BAFOEG_PASSWORD", "SUPER-SECRET-PW-9876")
    user, pw = prompt_username_password()
    assert "SUPER-SECRET-PW-9876" not in caplog.text
    assert "SUPER-SECRET-PW-9876" not in os.environ.get("PATH", "")


def test_prompt_ohne_env_ohne_tty_fehler(monkeypatch, tmp_path: Path):
    monkeypatch.setenv(CONFIG_DIR_ENV, str(tmp_path / "c"))
    monkeypatch.delenv("BAFOEG_USERNAME", raising=False)
    monkeypatch.delenv("BAFOEG_PASSWORD", raising=False)
    # stdin ist im pytest kein TTY.
    with pytest.raises(RuntimeError, match="TTY"):
        prompt_username_password()


def test_write_config_defaults_mode_0600(monkeypatch, tmp_path: Path):
    monkeypatch.setenv(CONFIG_DIR_ENV, str(tmp_path / "c"))
    p = write_config_defaults({"hinweis": "nur test"})
    assert p.exists()
    # Modus 0600 (nur Eigentümer) auf unterstützten Plattformen.
    mode = oct(p.stat().st_mode & 0o777)
    assert mode in ("0o600", "0o700")  # manche FS clippen 0o600 zu 0o700
