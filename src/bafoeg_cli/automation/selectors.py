"""Zentrale Selektoren, URLs und Konfigurationskonstanten.

Alle gegen bafoeg-digital.de tatsächlich beobachteten Selektoren, URLs
und API-Endpunkte sind hier gesammelt. Recherche-Datum: 2026-10-12.

Wenn BAföG Digital die Selektoren ändert, muss nur diese Datei
angepasst werden. Die anderen Module beziehen ihre Selektoren von hier.

Beobachtete Infrastruktur
-------------------------
- Frontend (React-Native-Web/Expo): https://bafoeg-digital.de/
- Auth (Keycloak/OIDC):            https://auth.bafoeg-digital.de/realms/bafoeg
- Backend-API:                     https://backend.bafoeg-digital.de/api/v1/...
- IdP / BundID:                    https://id.bund.de/
- Telemetrie:                      https://matomo.bafoeg-digital.de/matomo.js
"""
from __future__ import annotations

from dataclasses import dataclass

# ---- URLs -----------------------------------------------------------------

# Frontend-Wurzel (www. → 308 → apex).
BASE_URL: str = "https://bafoeg-digital.de"

# Login-Einstiegsseite (zwei Stufen: "Wofür?" → "Weiter mit BundID" → id.bund.de).
LOGIN_URL: str = f"{BASE_URL}/login"

# OIDC-Issuer und -Endpunkte, beobachtet am 2026-10-12.
OIDC_ISSUER: str = "https://auth.bafoeg-digital.de/realms/bafoeg"
OIDC_AUTHORIZATION_ENDPOINT: str = (
    f"{OIDC_ISSUER}/protocol/openid-connect/auth"
)
OIDC_TOKEN_ENDPOINT: str = f"{OIDC_ISSUER}/protocol/openid-connect/token"
OIDC_USERINFO_ENDPOINT: str = (
    f"{OIDC_ISSUER}/protocol/openid-connect/userinfo"
)
OIDC_LOGOUT_ENDPOINT: str = (
    f"{OIDC_ISSUER}/protocol/openid-connect/logout"
)
OIDC_JWKS_URI: str = f"{OIDC_ISSUER}/protocol/openid-connect/certs"

# Backend-API (öffentlich beobachtbar).
BACKEND_BASE: str = "https://backend.bafoeg-digital.de/api/v1"
BACKEND_MAINTENANCE: str = f"{BACKEND_BASE}/public/maintenance-status"
BACKEND_LOGIN_MAINTENANCE: str = f"{BACKEND_BASE}/public/login-maintenance-status"
BACKEND_INFOBANNER: str = f"{BACKEND_BASE}/public/infobanner"

# Standard-Client-ID des Frontends. Wird für Logout und Token-Refresh
# benötigt, falls vorhanden. Falls Keycloak hier nichts verlangt, ist
# "bafoeg-digital-web" ein begründeter Default (übliche Konvention).
DEFAULT_CLIENT_ID: str = "bafoeg-digital-web"

# User-Agent: ehrlich kennzeichnen, damit die Betreiber Kontakt aufnehmen
# können, falls Bots Probleme verursachen.
USER_AGENT: str = (
    "bafoeg-cli/0.2 (+https://github.com/smlfg/bafoeg-cli; "
    "Kontakt via GitHub-Issues)"
)


# ---- Selektoren -----------------------------------------------------------


@dataclass(frozen=True)
class LoginSelectors:
    """Selektoren für den Login-Flow auf bafoeg-digital.de → id.bund.de.

    Der Flow ist dreistufig:

    1. ``/login`` auf bafoeg-digital.de: Auswahl "Anträge …" ODER
       "Mitwirkung als Eltern/Partner/innen". Wir wählen die Antrags-Variante.
    2. Klick auf "Weiter mit BundID" → Datenschutz-Dialog → "Einverstanden".
    3. Redirect zu id.bund.de, dort Auswahl des Verfahrens.
    """

    # Stufe 1 – BAföG-Digital-Loginseite
    startseite_login_link: str = 'a[href="/login"]'
    auswahl_antraege_button: str = 'button:has-text("Anträge für Studium, Schule oder Ausbildung")'
    auswahl_eltern_button: str = 'button:has-text("Mitwirkung als Eltern oder Partner/innen")'
    cookie_akzeptieren: str = 'button:has-text("Alle akzeptieren")'

    # Stufe 2 – BundID-Einwilligung
    weiter_mit_bundid: str = 'button:has-text("Weiter mit BundID")'
    einverstanden: str = 'button:has-text("Einverstanden")'

    # Stufe 3 – id.bund.de: Verfahrensauswahl
    # Diese Auswahl existiert erst NACH Bestätigung der Datenschutz-Einwilligung.
    # (Sie wird hauptsächlich für die manuelle Variante genutzt – der
    # headless-Flow mit Benutzername+Passwort wird vom Backend automatisch
    # zum ELSTER-Konto-Select weitergeleitet.)
    id_bund_de_anmelden: str = 'a:has-text("Anmelden"), button:has-text("ANMELDEN")'
    id_bund_de_gast: str = 'a:has-text("als Gast anmelden")'

    # Stufe 4 – BundID-Login-Form (Benutzername + Passwort).
    # Diese IDs/Namen sind auf id.bund.de standardisiert. Sie können
    # sich aber jederzeit ändern, weshalb die Live-Tests so wichtig sind.
    bundid_username: str = 'input[name="username"], input#username, input[type="email"]'
    bundid_password: str = 'input[name="password"], input#password, input[type="password"]'
    bundid_submit: str = 'button[type="submit"], button:has-text("Anmelden")'


@dataclass(frozen=True)
class AntragSelectors:
    """Selektoren für Antragsformulare.

    Achtung: Die Antragsstrecke läuft komplett hinter der BundID-Auth.
    Die genauen Feldnamen/-IDs sind ohne gültige Session nicht öffentlich
    beobachtbar. Wir verlassen uns daher primär auf die Backend-API
    (``backend.bafoeg-digital.de/api/v1/...``) statt auf DOM-Selektoren.
    Diese Selektoren sind als Fallback gedacht, falls die API nicht das
    gewünschte Feld liefert.
    """

    # Antragsliste / Übersicht (nach Login).
    antragsliste_container: str = '[data-testid="antragsliste"]'
    antrag_status_badge: str = '[data-testid="antrag-status"]'

    # Formblatt 1 (typische Stammdaten-Felder). Namen folgen der
    # offiziellen Formblatt-1-Bezeichnung der BAföG-Formulare.
    feld_vorname: str = 'input[name="vorname"]'
    feld_nachname: str = 'input[name="nachname"]'
    feld_geburtsdatum: str = 'input[name="geburtsdatum"]'
    feld_staatsangehoerigkeit: str = 'select[name="staatsangehoerigkeit"]'
    feld_strasse: str = 'input[name="strasse"]'
    feld_hausnummer: str = 'input[name="hausnummer"]'
    feld_plz: str = 'input[name="plz"]'
    feld_ort: str = 'input[name="ort"]'
    feld_email: str = 'input[name="email"]'
    feld_telefon: str = 'input[name="telefon"]'
    feld_iban: str = 'input[name="iban"]'

    # Aktions-Buttons.
    entwurf_speichern: str = 'button:has-text("Entwurf speichern")'
    weiter_button: str = 'button:has-text("Weiter")'
    zurueck_button: str = 'button:has-text("Zurück")'


@dataclass(frozen=True)
class PostfachSelectors:
    """Selektoren für das BundID-/Antrags-Postfach."""

    postfach_container: str = '[data-testid="postfach"]'
    nachricht_item: str = '[data-testid="nachricht"]'
    nachricht_ungelesen: str = '[data-testid="nachricht-ungelesen"]'


# ---- Konstanten für den Live-Betrieb --------------------------------------


# Maximale Wartezeit auf Hydration der React-Native-Web-App (Sekunden).
HYDRATION_TIMEOUT_S: int = 20

# Maximale Wartezeit auf den BundID-Redirect (Sekunden).
BUNDID_REDIRECT_TIMEOUT_S: int = 30

# Wo die Session gespeichert wird (relativ zum XDG-Config-Dir).
SESSION_FILENAME: str = "session.json"
