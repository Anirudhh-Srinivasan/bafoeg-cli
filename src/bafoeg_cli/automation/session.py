"""Session-Persistenz: speichert/lädt Browser-Storage-State unter XDG-Config.

Layout::

    $XDG_CONFIG_HOME/bafoeg-cli/   (default: ~/.config/bafoeg-cli)
    ├── session.json               # Playwright storage_state (Cookies + LocalStorage)
    └── config.toml                # Optionale User-Defaults (z.B. bevorzugter Login-Weg)

Sicherheit
----------
- ``session.json`` enthält abgeleitete Session-Cookies, die Zugriff auf
  das BAföG-Konto gewähren. Daher wird sie mit Modus 0600 angelegt.
- Es werden **niemals** Klartext-Passwörter oder Benutzernamen gespeichert.
- Wir empfehlen zusätzlich Verschlüsselung der Platte oder zumindest
  ein verschlüsseltes Home-Verzeichnis.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

from .selectors import SESSION_FILENAME

CONFIG_DIR_ENV = "BAFOEG_CONFIG_DIR"
XDG_CONFIG_ENV = "XDG_CONFIG_HOME"


def default_config_dir() -> Path:
    """Liefert das Konfig-Verzeichnis nach XDG-Konvention."""
    override = os.environ.get(CONFIG_DIR_ENV)
    if override:
        return Path(override).expanduser()
    xdg = os.environ.get(XDG_CONFIG_ENV)
    if xdg:
        return Path(xdg) / "bafoeg-cli"
    return Path.home() / ".config" / "bafoeg-cli"


def ensure_config_dir() -> Path:
    """Legt das Konfig-Verzeichnis an (falls fehlend) und gibt es zurück."""
    d = default_config_dir()
    d.mkdir(parents=True, exist_ok=True)
    # 0700 auf das Verzeichnis: niemand außer dem Eigentümer darf rein.
    try:
        os.chmod(d, 0o700)
    except OSError:
        pass
    return d


def session_path() -> Path:
    """Pfad zur session.json."""
    return ensure_config_dir() / SESSION_FILENAME


def session_exists() -> bool:
    return session_path().exists()


def delete_session() -> bool:
    """Löscht die Session. Gibt True zurück, wenn etwas gelöscht wurde."""
    p = session_path()
    if p.exists():
        p.unlink()
        return True
    return False


def is_session_fresh(max_age_s: int = 60 * 30) -> bool:
    """Grobe Heuristik: ist die Session weniger als ``max_age_s`` Sekunden alt?

    Wir verlassen uns nicht auf das Alter der Datei allein (Cookies können
    abgelaufen sein), aber für die schnelle "habe ich eine Session?"-Prüfung
    ist das Alter nützlich.
    """
    p = session_path()
    if not p.exists():
        return False
    import time
    age = time.time() - p.stat().st_mtime
    return age < max_age_s


def write_config_defaults(data: dict[str, Any]) -> Path:
    """Schreibt eine optionale TOML-Config mit User-Defaults (falls tomliib da)."""
    import json
    p = ensure_config_dir() / "config.json"
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    try:
        os.chmod(p, 0o600)
    except OSError:
        pass
    return p


def prompt_username_password(
    username_env: str = "BAFOEG_USERNAME",
    password_env: str = "BAFOEG_PASSWORD",
) -> tuple[str, str]:
    """Liest Benutzername+Passwort aus Env-Variablen oder fragt interaktiv nach.

    Niemals auf der Festplatte persistieren. Niemals loggen.
    """
    user = os.environ.get(username_env, "").strip()
    pw = os.environ.get(password_env, "")
    if user and pw:
        return user, pw
    if not sys.stdin.isatty():
        raise RuntimeError(
            f"Keine Zugangsdaten: bitte {username_env} und {password_env} "
            "setzen oder interaktiv in einem TTY aufrufen."
        )
    import getpass
    if not user:
        user = input("BundID-Benutzername (E-Mail): ").strip()
    if not pw:
        pw = getpass.getpass("BundID-Passwort: ")
    if not user or not pw:
        raise RuntimeError("Benutzername und Passwort sind beide erforderlich.")
    return user, pw


def credentials_present(
    username_env: str = "BAFOEG_USERNAME",
    password_env: str = "BAFOEG_PASSWORD",
) -> bool:
    return bool(
        os.environ.get(username_env, "").strip()
        and os.environ.get(password_env, "")
    )
