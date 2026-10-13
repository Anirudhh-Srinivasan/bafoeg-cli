"""Playwright-Browser-Wrapper.

Kapselt den Browser-/Context-Lifecycle und stellt Hilfsfunktionen für
Hydration-Waits und das Akzeptieren von Cookie-Bannern bereit.

Bewusst schlank gehalten: jede Aktion, die echte BundID-Auth erfordert,
soll in :mod:`bafoeg_cli.automation.auth` leben.
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from playwright.sync_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    TimeoutError as PWTimeoutError,
    sync_playwright,
)

from .selectors import (
    HYDRATION_TIMEOUT_S,
    LoginSelectors,
    USER_AGENT,
)


def is_browser_available() -> bool:
    """Prüft, ob Playwright Chromium installiert ist.

    Wir versuchen einen leichten Headless-Start; wenn der Browser nicht
    installiert ist, schlägt das fehl.
    """
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            browser.close()
        return True
    except Exception:
        return False


def ensure_browser_installed() -> None:
    """Installiert Chromium, falls fehlend. Idempotent."""
    try:
        from playwright._impl._driver import compute_driver_executable
    except Exception:
        compute_driver_executable = None  # type: ignore
    # Wir versuchen erst einen no-op-Start, um zu sehen, ob alles da ist.
    if is_browser_available():
        return
    # Fallback: Install über das offizielle CLI.
    cmd = ["playwright", "install", "chromium"]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=300)
    except FileNotFoundError:
        raise RuntimeError(
            "Playwright-CLI nicht gefunden. Bitte 'pip install playwright' "
            "ausführen und 'playwright install chromium' manuell starten."
        ) from None
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"playwright install chromium fehlgeschlagen: "
            f"{e.stderr.decode(errors='replace')}"
        ) from None


@contextmanager
def make_browser(headless: bool = True) -> Iterator[tuple[Playwright, Browser]]:
    """Context Manager: liefert (Playwright, Browser) und räumt am Ende auf."""
    ensure_browser_installed()
    pw = sync_playwright().start()
    browser: Browser | None = None
    try:
        browser = pw.chromium.launch(headless=headless)
        yield pw, browser
    finally:
        if browser is not None:
            try:
                browser.close()
            except Exception:
                pass
        try:
            pw.stop()
        except Exception:
            pass


def make_context(
    browser: Browser,
    storage_state_path: Path | None = None,
    locale: str = "de-DE",
) -> BrowserContext:
    """Erzeugt einen Browser-Kontext mit optionalem Session-Storage.

    Wenn ``storage_state_path`` existiert, werden Cookies und LocalStorage
    daraus geladen – sonst ein leerer Kontext.
    """
    kwargs: dict = {
        "user_agent": USER_AGENT,
        "locale": locale,
        "viewport": {"width": 1280, "height": 800},
    }
    if storage_state_path and storage_state_path.exists():
        kwargs["storage_state"] = str(storage_state_path)
    return browser.new_context(**kwargs)


def wait_hydrated(page: Page, timeout_s: int = HYDRATION_TIMEOUT_S) -> None:
    """Wartet darauf, dass die React-Native-Web-App hydratisiert ist.

    Wir warten auf ein Element, das auf der Antrags-Seite immer da ist
    (Body > ein paar Buttons). Das ist bewusst grob – die Site hat
    keinen sauberen Lade-Indikator.
    """
    try:
        page.wait_for_load_state("domcontentloaded", timeout=timeout_s * 1000)
    except PWTimeoutError:
        pass
    try:
        page.wait_for_load_state("networkidle", timeout=timeout_s * 1000)
    except PWTimeoutError:
        pass
    # Extra-Wartezeit, weil React-Native-Web nach networkidle oft noch
    # weitere Bundles lädt.
    page.wait_for_timeout(2000)
    # Sanity-Check: Body muss da sein und muss mehr als 100 Zeichen Text
    # enthalten (gegen leere SPA-Shells).
    text_len = len(page.inner_text("body") or "")
    if text_len < 100:
        raise RuntimeError(
            f"Seite nicht hydratisiert nach {timeout_s}s "
            f"(nur {text_len} Zeichen Text im Body)"
        )


def accept_cookies_if_present(page: Page) -> bool:
    """Akzeptiert das Cookie-Banner, falls vorhanden. Gibt True zurück,
    wenn ein Klick erfolgte."""
    try:
        btn = page.locator(LoginSelectors.cookie_akzeptieren).first
        if btn.count() == 0 or not btn.is_visible():
            return False
        btn.click(timeout=2000)
        page.wait_for_timeout(500)
        return True
    except Exception:
        return False


def write_storage_state(context: BrowserContext, dest: Path) -> None:
    """Persistiert Cookies + LocalStorage des Kontexts nach ``dest``."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    state = context.storage_state()
    # storage_state() gibt ein Dict zurück. Wir schreiben es als JSON,
    # damit der User die Datei einsehen kann (sie enthält KEINE Logins,
    # nur abgeleitete Session-Cookies).
    with tempfile.NamedTemporaryFile(
        "w", delete=False, dir=str(dest.parent), prefix=".session-", suffix=".tmp"
    ) as tf:
        json.dump(state, tf, ensure_ascii=False, indent=2)
        tmp_path = tf.name
    os.replace(tmp_path, dest)
    # Restriktive Permissions: nur der Eigentümer darf lesen/schreiben.
    try:
        os.chmod(dest, 0o600)
    except OSError:
        pass


def load_storage_state(path: Path) -> dict:
    """Lädt ein Storage-State-Dict. Wirft FileNotFoundError."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
