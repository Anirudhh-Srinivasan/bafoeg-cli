"""Automation gegen BAföG Digital (bafoeg-digital.de).

Stabilitätshinweise
-------------------
Die echte Website ist eine React-Native-Web-App (Expo), die Inhalte werden
nahezu vollständig clientseitig gerendert. Die Authentifizierung läuft
über einen Keycloak-/OIDC-IdP unter ``auth.bafoeg-digital.de``. Die
nachgelagerte Antrags-API liegt unter ``backend.bafoeg-digital.de``.

Da sich Selektoren und interne Pfade jederzeit ändern können, sind alle
Selektoren in :mod:`bafoeg_cli.automation.selectors` zentralisiert und
sollten bei Site-Änderungen als Erstes angepasst werden.

Sicherheit
----------
- Zugangsdaten werden niemals auf der Festplatte persistiert. Sie werden
  nur aus Umgebungsvariablen (``BAFOEG_USERNAME``, ``BAFOEG_PASSWORD``)
  oder aus einem einmaligen Prompt gelesen.
- Persistiert werden ausschließlich die Sitzungs-Cookies und ein
  Aktualisierungs-Token.
- Personenbezogene Antragsdaten (``antrag.yaml``) verlassen das Gerät
  nicht, sie werden nur an die Backend-API von BAföG Digital gesendet.
"""
from __future__ import annotations

from .selectors import BASE_URL, OIDC_ISSUER, OIDC_AUTHORIZATION_ENDPOINT
from .selectors import LoginSelectors, AntragSelectors, PostfachSelectors

__all__ = [
    "BASE_URL",
    "OIDC_ISSUER",
    "OIDC_AUTHORIZATION_ENDPOINT",
    "LoginSelectors",
    "AntragSelectors",
    "PostfachSelectors",
]
