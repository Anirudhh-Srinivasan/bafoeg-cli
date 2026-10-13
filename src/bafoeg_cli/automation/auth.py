"""Login-Flow gegen BAföG Digital (via BundID / Keycloak-OIDC).

Zwei Wege werden unterstützt:

1. ``headless`` mit Benutzername+Passwort (BundID "Benutzername+Passwort"
   bzw. der "Gast"-Login). Wir starten Chromium headless, füllen das
   Login-Formular auf id.bund.de und warten, bis der Browser wieder
   auf bafoeg-digital.de zur landet.

2. ``headed`` Fallback für eID / ELSTER / 2FA. Wir starten Chromium mit
   UI, zeigen den Browser, lassen den User sich authentifizieren und
   speichern die Session, sobald der Redirect zurück auf
   bafoeg-digital.de erfolgt ist (oder der User explizit "fertig" klickt).

Was **nicht** automatisierbar ist:
- eID (Online-Ausweis): braucht physische AusweisApp2 + Kartenleser + PIN
- ELSTER: brautzt Zertifikat-Dialog im Browser (oder ElsterSecure)
- Bestätigungs-Push / SMS-2FA

In diesen Fällen MUSS der User den Login im sichtbaren Browser abschließen.
"""
from __future__ import annotations

import enum
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

from playwright.sync_api import (
    Browser,
    BrowserContext,
    Page,
    TimeoutError as PWTimeoutError,
)

from .browser import (
    accept_cookies_if_present,
    make_browser,
    make_context,
    wait_hydrated,
    write_storage_state,
)
from .selectors import (
    BUNDID_REDIRECT_TIMEOUT_S,
    LOGIN_URL,
    LoginSelectors,
)
from .session import session_path


class LoginMethod(str, enum.Enum):
    """Welcher Login-Weg soll genutzt werden?"""

    PASSWORD = "password"   # headless-fähig: Benutzername+Passwort auf id.bund.de
    MANUAL = "manual"       # --headed: User macht eID/ELSTER/2FA selbst
    AUTO = "auto"           # PASSWORD versuchen, sonst MANUAL


@dataclass
class LoginResult:
    """Ergebnis eines Login-Versuchs."""

    success: bool
    method: str
    started_at: float
    finished_at: float
    final_url: str
    note: str = ""
    # Wir geben die Storage-State-Pfade NICHT in der Ausgabe aus, nur
    # bestätigen, dass eine geschrieben wurde.
    session_written: bool = False
    # Falls wir auf eine BundID-Seite hängen geblieben sind, nützlich
    # für den User.
    stuck_at: Optional[str] = None
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


def is_already_logged_in(context: BrowserContext) -> bool:
    """Heuristik: prüft, ob die Session noch gültig ist, indem die
    Login-Seite geladen wird. Wenn der Server uns direkt zur Startseite
    (oder zu /antraege) umleitet, sind wir eingeloggt."""
    page = context.new_page()
    try:
        page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=20000)
        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except PWTimeoutError:
            pass
        page.wait_for_timeout(1500)
        # Eingeloggt: wir landen auf der Startseite oder direkt im Antrags-Bereich,
        # NICHT auf /login.
        if not page.url.endswith("/login") and "/login" not in page.url:
            return True
        return False
    except Exception:
        return False
    finally:
        try:
            page.close()
        except Exception:
            pass


def login_password(
    browser: Browser,
    username: str,
    password: str,
    headless: bool = True,
) -> LoginResult:
    """Headless-Login mit Benutzername+Passwort gegen BundID.

    Setzt voraus, dass der User einen BundID-Account mit
    "Benutzername+Passwort" hat. Für eID/ELSTER siehe :func:`login_manual`.
    """
    started = time.time()
    result = LoginResult(
        success=False,
        method=LoginMethod.PASSWORD.value,
        started_at=started,
        finished_at=0.0,
        final_url="",
    )
    context = make_context(browser)
    page = context.new_page()
    try:
        page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=30000)
        wait_hydrated(page)
        accept_cookies_if_present(page)

        # Stufe 1: "Anträge für Studium, Schule oder Ausbildung"
        try:
            page.locator(LoginSelectors.auswahl_antraege_button).first.click(timeout=5000)
            page.wait_for_timeout(1500)
        except PWTimeoutError:
            result.note = "Anträge-Button nicht gefunden – Login-Seite hat sich verändert?"
            result.stuck_at = page.url
            result.final_url = page.url
            return result

        # Stufe 2: "Weiter mit BundID" → Datenschutz "Einverstanden"
        try:
            page.locator(LoginSelectors.weiter_mit_bundid).first.click(timeout=5000)
            page.wait_for_timeout(1500)
        except PWTimeoutError:
            result.note = "'Weiter mit BundID' nicht gefunden."
            result.stuck_at = page.url
            result.final_url = page.url
            return result

        try:
            page.locator(LoginSelectors.einverstanden).first.click(timeout=5000)
        except PWTimeoutError:
            # Dialog war ggf. schon weg oder wurde gar nicht gezeigt.
            pass

        # Warten auf BundID
        try:
            page.wait_for_url("**/id.bund.de/**", timeout=BUNDID_REDIRECT_TIMEOUT_S * 1000)
        except PWTimeoutError:
            result.note = "Redirect zu id.bund.de ist nicht erfolgt."
            result.stuck_at = page.url
            result.final_url = page.url
            return result

        page.wait_for_timeout(2500)

        # Stufe 3: Auf id.bund.de "Anmelden" klicken
        try:
            page.locator(LoginSelectors.id_bund_de_anmelden).first.click(timeout=5000)
            page.wait_for_timeout(2500)
        except PWTimeoutError:
            # Vielleicht sind wir schon eingeloggt, oder die Seite ist anders.
            pass

        # Stufe 4: Benutzername + Passwort
        try:
            page.locator(LoginSelectors.bundid_username).first.fill(username, timeout=10000)
        except PWTimeoutError:
            result.note = "Username-Feld auf id.bund.de nicht gefunden."
            result.stuck_at = page.url
            result.final_url = page.url
            return result

        try:
            page.locator(LoginSelectors.bundid_password).first.fill(password, timeout=5000)
        except PWTimeoutError:
            result.note = "Passwort-Feld auf id.bund.de nicht gefunden."
            result.stuck_at = page.url
            result.final_url = page.url
            return result

        try:
            page.locator(LoginSelectors.bundid_submit).first.click(timeout=5000)
        except PWTimeoutError:
            result.note = "Submit-Button auf id.bund.de nicht gefunden."
            result.stuck_at = page.url
            result.final_url = page.url
            return result

        # Warten, bis der Browser wieder auf bafoeg-digital.de ist
        # (oder der User auf einem 2FA-Schritt landet, den wir nicht
        # automatisieren können).
        try:
            page.wait_for_url(
                "**/bafoeg-digital.de/**",
                timeout=30000,
            )
        except PWTimeoutError:
            result.note = (
                "Nach dem Submit wurde kein Redirect zu bafoeg-digital.de "
                "beobachtet – möglicherweise ist eine 2FA-Abfrage aktiv."
            )
            result.stuck_at = page.url
            result.final_url = page.url
            return result

        page.wait_for_timeout(3000)

        # Erfolg prüfen: Landen wir noch auf /login?
        if "/login" in page.url:
            result.note = (
                "Nach dem Login-Versuch befinden wir uns immer noch auf "
                "/login – Credentials falsch oder BundID lehnt ab."
            )
            result.stuck_at = page.url
            result.final_url = page.url
            return result

        # Session persistieren.
        write_storage_state(context, session_path())
        result.success = True
        result.session_written = True
        result.final_url = page.url
        result.note = "Login erfolgreich (BundID Benutzername+Passwort)."
        return result
    except Exception as e:
        result.note = f"Unerwarteter Fehler: {e!r}"
        result.stuck_at = page.url
        result.final_url = page.url
        return result
    finally:
        result.finished_at = time.time()
        try:
            page.close()
        except Exception:
            pass
        try:
            context.close()
        except Exception:
            pass


def login_manual(
    browser: Browser,
    max_wait_s: int = 300,
) -> LoginResult:
    """Headless=False-Login: User macht eID/ELSTER/2FA selbst im sichtbaren Browser.

    Wir öffnen die Login-Seite, lassen den User sich authentifizieren und
    warten, bis er entweder auf einer Seite außerhalb von /login landet
    (was Erfolg bedeutet) oder ``max_wait_s`` Sekunden vorbei sind.
    """
    started = time.time()
    result = LoginResult(
        success=False,
        method=LoginMethod.MANUAL.value,
        started_at=started,
        finished_at=0.0,
        final_url="",
    )
    context = make_context(browser)
    page = context.new_page()
    try:
        page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=30000)
        wait_hydrated(page)
        accept_cookies_if_present(page)

        # Stufe 1 + 2 wie oben, damit der User auf id.bund.de landet.
        try:
            page.locator(LoginSelectors.auswahl_antraege_button).first.click(timeout=5000)
            page.wait_for_timeout(1500)
            page.locator(LoginSelectors.weiter_mit_bundid).first.click(timeout=5000)
            page.wait_for_timeout(1500)
            page.locator(LoginSelectors.einverstanden).first.click(timeout=5000)
        except PWTimeoutError:
            # Bestimmte Schritte sind vielleicht schon passiert oder die
            # Selektoren haben sich geändert – wir versuchen einfach weiter.
            pass

        # Warten auf id.bund.de
        try:
            page.wait_for_url("**/id.bund.de/**", timeout=BUNDID_REDIRECT_TIMEOUT_S * 1000)
        except PWTimeoutError:
            result.note = "Redirect zu id.bund.de ist nicht erfolgt."
            result.stuck_at = page.url
            result.final_url = page.url
            return result

        # Jetzt: User übernehmen lassen. Wir pollen die URL, bis wir
        # entweder auf bafoeg-digital.de ohne /login sind, oder Timeout.
        deadline = time.time() + max_wait_s
        while time.time() < deadline:
            page.wait_for_timeout(2000)
            if "bafoeg-digital.de" in page.url and "/login" not in page.url:
                page.wait_for_timeout(3000)  # Stabilisierung
                write_storage_state(context, session_path())
                result.success = True
                result.session_written = True
                result.final_url = page.url
                result.note = (
                    "Login manuell abgeschlossen (eID/ELSTER/2FA), "
                    "Session gespeichert."
                )
                return result
            if "id.bund.de/error" in page.url or "error" in page.url.lower():
                result.note = f"Fehlerseite beobachtet: {page.url}"
                result.stuck_at = page.url
                result.final_url = page.url
                return result

        result.note = (
            f"Manueller Login nicht innerhalb von {max_wait_s}s abgeschlossen."
        )
        result.stuck_at = page.url
        result.final_url = page.url
        return result
    except Exception as e:
        result.note = f"Unerwarteter Fehler: {e!r}"
        result.stuck_at = page.url
        result.final_url = page.url
        return result
    finally:
        result.finished_at = time.time()
        try:
            page.close()
        except Exception:
            pass
        try:
            context.close()
        except Exception:
            pass


def run_login(
    method: LoginMethod = LoginMethod.AUTO,
    username: str = "",
    password: str = "",
    headless: bool = True,
    manual_max_wait_s: int = 300,
) -> LoginResult:
    """Höhere Login-Funktion: wählt je nach Methode den richtigen Pfad.

    ``method=AUTO`` versucht erst headless mit Credentials; wenn keine
    vorhanden sind ODER headless fehlschlägt, fällt es auf ``MANUAL`` mit
    ``--headed`` zurück.
    """
    with make_browser(headless=headless) as (_pw, browser):
        if method == LoginMethod.PASSWORD:
            if not username or not password:
                return LoginResult(
                    success=False,
                    method=LoginMethod.PASSWORD.value,
                    started_at=time.time(),
                    finished_at=time.time(),
                    final_url="",
                    note="Methode=password verlangt username und password.",
                )
            return login_password(browser, username, password, headless=headless)

        if method == LoginMethod.MANUAL:
            return login_manual(browser, max_wait_s=manual_max_wait_s)

        # AUTO
        if username and password and headless:
            res = login_password(browser, username, password, headless=True)
            if res.success:
                return res
            # Fallback auf manual, falls Browser verfügbar und Session leer.
            # Aber: wir starten einen NEUEN Browser mit headless=False.
        # Wenn wir hier landen, ist entweder AUTO mit Fallback oder
        # AUTO ohne Credentials → manuell.
        # Browser schließen, neuen mit headless=False starten.
        try:
            browser.close()
        except Exception:
            pass
    # Neuer Browser, sichtbar.
    with make_browser(headless=False) as (_pw, browser):
        return login_manual(browser, max_wait_s=manual_max_wait_s)
