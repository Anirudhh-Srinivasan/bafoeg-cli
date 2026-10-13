"""CLI für smlfg/bafoeg-cli.

Subbefehle:
  rechner     BAföG-Bedarfsrechner (§13, §13a, §23, §25, §29)
  fristen     Antrags-, Folgeantrags- und §48-Fristen
  unterlagen  Checkliste Formblätter 1–9 je nach Situation
  links       BAföG Digital, Ämterverzeichnis, Rechtstexte

Jeder Befehl kennt --json für Agenten (oder Default = JSON, wenn
keine TTY).
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from typing import Any

from . import fristen, links, rechner, unterlagen, werte


def _out(data: Any, as_json: bool, pretty: bool = True) -> None:
    """Ausgabe als JSON (für Agenten) oder als lesbarer Text."""
    if as_json:
        if pretty:
            print(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False))
        else:
            print(json.dumps(data, ensure_ascii=False, allow_nan=False))
        return
    # Plaintext – einfache, menschliche Darstellung
    print(json.dumps(data, ensure_ascii=False, indent=2))


def _finite_float(value: str) -> float:
    """Parse a finite decimal amount for calculator CLI arguments."""
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"ungültige Zahl: {value}") from exc
    if not math.isfinite(parsed):
        raise argparse.ArgumentTypeError("der Betrag muss endlich sein")
    return parsed


def cmd_rechner(args: argparse.Namespace) -> int:
    """BAföG-Bedarfsrechner (vereinfacht)."""
    bed = werte.get_bedarfssaetze()
    fr = werte.get_freibetraege()

    out: dict[str, Any] = {
        "quelle": werte.QUELLE,
        "stand": werte.STAND,
        "gueltig_ab": werte.GUELTIG_AB,
        "hinweis": (
            "Vereinfachtes Modell – verbindlich ist nur der Bescheid "
            "des Amts für Ausbildungsförderung."
        ),
    }

    eingabe = rechner.RechnerInput(
        bei_eltern=args.bei_eltern,
        eigene_krankenversicherung=args.eigene_kv,
        ab_30=args.ab_30,
        verheiratet=args.verheiratet,
        eltern=rechner.Elterneinkommen(
            vater=args.einkommen_vater,
            mutter=args.einkommen_mutter,
            verheiratet_zusammen=not args.eltern_getrennt,
            weitere_kinder_im_haushalt=args.weitere_kinder,
        ),
        eigen=rechner.EigenesEinkommen(
            brutto_monat=args.eigen_einkommen,
            ist_minijob=True,
            ehegatte_einkommen=args.ehegatte_einkommen,
            kinder_ohne_ausbildung=args.eigene_kinder,
        ),
        vermoegen=rechner.Vermoegen(
            betrag=args.vermoegen,
            ab_30=args.ab_30,
            hat_partner_oder_kind=(1 if args.verheiratet else 0)
                            + args.eigene_kinder,
        ),
    )
    erg = rechner.berechne(eingabe, bed, fr)
    result = rechner.ergebnis_to_dict(erg)
    if args.json:
        out["ergebnis"] = result
        out["rechner_eingabe"] = {
            "bei_eltern": eingabe.bei_eltern,
            "eigene_krankenversicherung": eingabe.eigene_krankenversicherung,
            "ab_30": eingabe.ab_30,
            "verheiratet": eingabe.verheiratet,
        }
        _out(out, as_json=True, pretty=True)
    else:
        print("BAföG – vereinfachte Bedarfsberechnung")
        print("=" * 60)
        print(f"Quelle: {werte.QUELLE}")
        print(f"Stand:  {werte.STAND}\n")
        print(f"Bedarf (Höchstsatz):       {result['bedarf_monat_euro']:>8.2f} €")
        print(f"Anrechnung Eltern:         {result['anrechnung_eltern_euro']:>8.2f} €")
        print(f"Anrechnung eigenes Eink.:  {result['anrechnung_eigen_euro']:>8.2f} €")
        print(f"Voraussichtliche Förderung: {result['foerderung_monat_euro']:>7.2f} €")
        if result["hinweise"]:
            print("\nHinweise:")
            for h in result["hinweise"]:
                print(f"  - {h}")
        print(f"\nDetails: {json.dumps(result['details'], ensure_ascii=False, indent=2)}")
    return 0


def cmd_fristen(args: argparse.Namespace) -> int:
    """Alle relevanten BAföG-Fristen."""
    if args.json:
        _out(
            {
                "quelle": fristen.QUELLE_FRISTEN,
                "fristen": fristen.alle_fristen(),
            },
            as_json=True,
        )
    else:
        print("BAföG-Fristen")
        print("=" * 60)
        print(f"Quelle: {fristen.QUELLE_FRISTEN}\n")
        for f in fristen.alle_fristen():
            print(f"[{f['name']}] {f['rechtsgrundlage']}")
            print(f"  Frist:   {f['frist']}")
            print(f"  Detail:  {f['detail']}\n")
    return 0


def cmd_unterlagen(args: argparse.Namespace) -> int:
    """Checkliste Formblätter + Belege je nach Situation."""
    if args.situation:
        sit = unterlagen.situation(args.situation)
        if sit is None:
            print(
                f"Unbekannte Situation: {args.situation}",
                file=sys.stderr,
            )
            return 2
        if args.json:
            _out(
                {
                    "quelle": unterlagen.QUELLE_UNTERLAGEN,
                    "situation": sit,
                },
                as_json=True,
            )
        else:
            _print_situation(sit)
        return 0
    if args.formblatt is not None:
        fb = unterlagen.formblatt(args.formblatt)
        if fb is None:
            print(f"Unbekanntes Formblatt: {args.formblatt}", file=sys.stderr)
            return 2
        if args.json:
            _out(
                {
                    "quelle": unterlagen.QUELLE_UNTERLAGEN,
                    "formblatt": fb,
                },
                as_json=True,
            )
        else:
            print(f"Formblatt {fb['nummer']}: {fb['name']}")
            print(f"  Wer:  {fb['wer']}")
            print(f"  URL:  {fb['url']}")
        return 0
    # Default: alle Formblätter + alle Situationen
    if args.json:
        _out(
            {
                "quelle": unterlagen.QUELLE_UNTERLAGEN,
                "formblaetter": unterlagen.alle_formblaetter(),
                "situationen": unterlagen.alle_situationen(),
            },
            as_json=True,
        )
    else:
        print("BAföG-Formblätter")
        print("=" * 60)
        for fb in unterlagen.alle_formblaetter():
            print(f"  FB{fb['nummer']}: {fb['name']}")
        print("\nSituationen (--situation=KEY):")
        for s in unterlagen.alle_situationen():
            print(f"  {s['schluessel']}: {s['label']}")
    return 0


def _print_situation(sit: dict) -> None:
    print(f"Situation: {sit['label']}")
    print("=" * 60)
    print("Formblätter (Pflicht):")
    for fb in sit["formblaetter"]:
        print(f"  - Formblatt {fb['nummer']}: {fb['name']}")
    if sit["formblaetter_optional"]:
        print("\nFormblätter (optional):")
        for fb in sit["formblaetter_optional"]:
            print(f"  - Formblatt {fb['nummer']}: {fb['name']}")
    print("\nBelege:")
    for b in sit["belege"]:
        print(f"  - {b}")


def cmd_links(args: argparse.Namespace) -> int:
    """Offizielle BAföG-Links."""
    if args.kategorie:
        kat = links.kategorie(args.kategorie)
        if kat is None:
            print(f"Unbekannte Kategorie: {args.kategorie}", file=sys.stderr)
            return 2
        if args.json:
            _out(
                {
                    "quelle": links.QUELLE_LINKS,
                    "kategorie": kat,
                },
                as_json=True,
            )
        else:
            _print_kategorie(kat)
        return 0
    if args.json:
        _out(
            {
                "quelle": links.QUELLE_LINKS,
                "kategorien": links.alle_links(),
            },
            as_json=True,
        )
    else:
        print("BAföG-Links")
        print("=" * 60)
        print(f"Quelle: {links.QUELLE_LINKS}\n")
        for k in links.alle_links():
            _print_kategorie(k)
    return 0


def _print_kategorie(kat: dict) -> None:
    print(f"[{kat['kategorie']}] {kat['label']}")
    for l_ in kat["links"]:
        print(f"  - {l_['name']}")
        print(f"    {l_['url']}")
        print(f"    {l_['beschreibung']}")
    print()


# ---- Automation gegen bafoeg-digital.de ---------------------------------


def cmd_login(args: argparse.Namespace) -> int:
    """Login gegen BAföG Digital via BundID.

    Modi:
      password   headless mit BundID-Benutzername+Passwort
      manual     --headed: User macht eID/ELSTER/2FA selbst
      auto       versucht password, fällt auf manual zurück

    Zugangsdaten aus Env BAFOEG_USERNAME / BAFOEG_PASSWORD oder Prompt.
    """
    from .automation.auth import LoginMethod, run_login
    from .automation.session import (
        credentials_present, prompt_username_password, session_exists,
    )

    method = LoginMethod(args.method)
    username = password = ""
    if method in (LoginMethod.PASSWORD, LoginMethod.AUTO):
        if credentials_present():
            username, password = prompt_username_password()
        elif method == LoginMethod.PASSWORD:
            # Strict: ohne Credentials kein headless-Login
            print(
                "Methode 'password' verlangt BAFOEG_USERNAME und "
                "BAFOEG_PASSWORD in der Umgebung.",
                file=sys.stderr,
            )
            return 2

    headless = not args.headed
    result = run_login(
        method=method,
        username=username,
        password=password,
        headless=headless,
        manual_max_wait_s=args.manual_max_wait,
    )

    payload: dict[str, Any] = {
        "befehl": "login",
        "methode": result.method,
        "erfolg": result.success,
        "final_url": result.final_url,
        "hinweis": result.note,
        "session_geschrieben": result.session_written,
        "dauer_s": round(result.finished_at - result.started_at, 2),
    }
    if result.stuck_at:
        payload["stuck_at"] = result.stuck_at
    if result.extra:
        payload["extra"] = result.extra

    if args.json:
        _out(payload, as_json=True)
    else:
        marker = "OK" if result.success else "FEHLGESCHLAGEN"
        print(f"Login: {marker}")
        print(f"  Methode:           {result.method}")
        print(f"  Ziel-URL:          {result.final_url}")
        print(f"  Session gespeichert: {result.session_written}")
        print(f"  Dauer:             {result.finished_at - result.started_at:.1f}s")
        if result.note:
            print(f"  Hinweis:           {result.note}")
        if result.stuck_at:
            print(f"  Stecken geblieben bei: {result.stuck_at}")
    return 0 if result.success else 3


def cmd_status(args: argparse.Namespace) -> int:
    """Antragsstatus + Postfach lesen."""
    from .automation.antrag import fetch_status

    uebersicht = fetch_status()
    payload = {
        "befehl": "status",
        "abgefragt_am": uebersicht.abgefragt_am,
        "quelle": uebersicht.quelle,
        "antraege": [a.to_dict() for a in uebersicht.anträge],
        "nachrichten": uebersicht.nachrichten,
    }
    if args.json:
        _out(payload, as_json=True)
    else:
        print("BAföG-Digital: Antragsstatus")
        print("=" * 60)
        if not uebersicht.anträge:
            print("Keine Anträge gefunden.")
        for a in uebersicht.anträge:
            print(f"  Antrag {a.antrag_id}: {a.status}")
            if a.bewilligungszeitraum_von:
                print(f"    Zeitraum: {a.bewilligungszeitraum_von} – {a.bewilligungszeitraum_bis}")
            if a.aktualisiert:
                print(f"    Aktualisiert: {a.aktualisiert}")
        if uebersicht.nachrichten:
            print("\nHinweise/Nachrichten:")
            for n in uebersicht.nachrichten:
                if isinstance(n, dict) and "hinweis" in n:
                    print(f"  - {n['hinweis']}")
                elif isinstance(n, dict) and "_meta" in n:
                    for m in n["_meta"]:
                        print(f"  (info) {m}")
                else:
                    print(f"  - {n}")
    return 0


def cmd_antrag_fill(args: argparse.Namespace) -> int:
    """Formblatt 1 aus YAML-Datei ausfüllen und Entwurf speichern."""
    from .automation.formblatt1 import load_formblatt1_from_yaml
    from .automation.antrag import entwurf_speichern

    if not args.daten:
        print("--daten <pfad> ist erforderlich", file=sys.stderr)
        return 2
    try:
        fb1 = load_formblatt1_from_yaml(args.daten)
    except (FileNotFoundError, ValueError) as e:
        print(f"Fehler beim Laden der YAML-Datei: {e}", file=sys.stderr)
        return 2

    ok, missing = fb1.validate()
    payload: dict[str, Any] = {
        "befehl": "antrag fill",
        "quelle_yaml": args.daten,
        "formblatt_vollstaendig": ok,
        "fehlende_pflichtfelder": missing,
        "felder_ignoriert": fb1.metadata.get("unknown_keys", []),
    }
    if not ok:
        if args.require_complete:
            payload["hinweis"] = (
                "Formblatt 1 unvollständig – mit --require-complete "
                "wird kein Entwurf gespeichert."
            )
            if args.json:
                _out(payload, as_json=True)
            else:
                print("Formblatt 1 unvollständig:")
                for k in missing:
                    print(f"  - {k}")
            return 4
        payload["hinweis"] = (
            "Formblatt 1 unvollständig – es wird trotzdem versucht, "
            "einen Entwurf zu speichern. Pflichtfelder prüfen!"
        )

    ergebnis = entwurf_speichern(fb1)
    payload["ergebnis"] = ergebnis.to_dict()
    if args.json:
        _out(payload, as_json=True)
    else:
        print("Formblatt 1 – Entwurf speichern")
        print("=" * 60)
        if not ok:
            print("WARNUNG: Pflichtfelder fehlen:")
            for k in missing:
                print(f"  - {k}")
            print()
        print(f"API-Antwort: HTTP {ergebnis.status_code} – {ergebnis.note}")
        if ergebnis.antrag_id:
            print(f"Antrag-ID: {ergebnis.antrag_id}")
    return 0 if ergebnis.success else 5


def cmd_antrag_submit(args: argparse.Namespace) -> int:
    """Antrag ENDGÜLTIG einreichen. Verlangt --confirm."""
    from .automation.formblatt1 import load_formblatt1_from_yaml
    from .automation.antrag import antrag_einreichen

    if not args.confirm:
        print(
            "ENDGÜLTIGES Einreichen verweigert: bestätige mit --confirm. "
            "Bis dahin nur Entwurf mit 'bafoeg antrag fill' speichern.",
            file=sys.stderr,
        )
        return 6
    if not args.daten:
        print("--daten <pfad> ist erforderlich", file=sys.stderr)
        return 2
    try:
        fb1 = load_formblatt1_from_yaml(args.daten)
    except (FileNotFoundError, ValueError) as e:
        print(f"Fehler beim Laden der YAML-Datei: {e}", file=sys.stderr)
        return 2
    ergebnis = antrag_einreichen(fb1, confirm=True)
    payload = {
        "befehl": "antrag submit",
        "quelle_yaml": args.daten,
        "ergebnis": ergebnis.to_dict(),
    }
    if args.json:
        _out(payload, as_json=True)
    else:
        print("Formblatt 1 – ENDGÜLTIG einreichen")
        print("=" * 60)
        print(f"API-Antwort: HTTP {ergebnis.status_code} – {ergebnis.note}")
        if ergebnis.antrag_id:
            print(f"Antrag-ID: {ergebnis.antrag_id}")
    return 0 if ergebnis.success else 5


def cmd_docs_upload(args: argparse.Namespace) -> int:
    """Dokument (Beleg, Immatrikulationsbescheinigung, ...) hochladen."""
    from .automation.antrag import dokument_uploaden

    if not args.datei:
        print("--datei <pfad> ist erforderlich", file=sys.stderr)
        return 2
    res = dokument_uploaden(
        args.datei,
        dokument_typ=args.typ,
        beschreibung=args.beschreibung or "",
        antrag_id=args.antrag_id or "",
    )
    payload = {
        "befehl": "docs upload",
        "datei": res.dokument_name,
        "typ": args.typ,
        "beschreibung": args.beschreibung or "",
        "antrag_id": args.antrag_id or "",
        "ergebnis": res.to_dict(),
    }
    if args.json:
        _out(payload, as_json=True)
    else:
        print("Dokument-Upload")
        print("=" * 60)
        print(f"Datei:   {res.dokument_name}")
        print(f"Typ:     {args.typ}")
        print(f"HTTP:    {res.status_code} – {res.note}")
    return 0 if res.success else 5


def cmd_formblatt_template(args: argparse.Namespace) -> int:
    """YAML-Template für Formblatt 1 ausgeben."""
    from .automation.formblatt1 import formblatt1_template_yaml
    if args.ausgeben:
        print(formblatt1_template_yaml(), end="")
    else:
        print("Hinweis: 'bafoeg formblatt-template' druckt das Template auf stdout.")
    return 0



def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="bafoeg",
        description=(
            "BAföG-CLI: Bedarfsrechner, Fristen, Formblätter und "
            "offizielle Links nach BAföG (§§13, 13a, 15, 18, 23, 25, "
            "29, 48). Stand: WS 2024/25 (gilt auch 2026)."
        ),
    )
    p.add_argument("--version", action="store_true", help="Version")
    sub = p.add_subparsers(dest="befehl")

    # rechner
    pr = sub.add_parser(
        "rechner",
        help="BAföG-Bedarfsrechner (vereinfacht, §13/§13a/§23/§25/§29)",
    )
    pr.add_argument(
        "--bei-eltern", action="store_true", help="Wohnung bei den Eltern"
    )
    pr.add_argument(
        "--eigene-kv",
        action="store_true",
        help="Eigene Kranken-/Pflegeversicherung (KV/PV-Zuschlag 137 €)",
    )
    pr.add_argument("--ab-30", action="store_true", help="Ab 30 Jahre (höherer KV/PV-Zuschlag)")
    pr.add_argument("--verheiratet", action="store_true", help="Verheiratet / Lebenspartnerschaft")
    pr.add_argument("--eltern-getrennt", action="store_true", help="Eltern getrennt lebend")
    pr.add_argument(
        "--einkommen-vater", type=_finite_float, default=0.0, help="Monatliches Nettoeinkommen Vater"
    )
    pr.add_argument(
        "--einkommen-mutter", type=_finite_float, default=0.0, help="Monatliches Nettoeinkommen Mutter"
    )
    pr.add_argument(
        "--weitere-kinder",
        type=int,
        default=0,
        help="Weitere unterhaltsberechtigte Kinder im Haushalt",
    )
    pr.add_argument(
        "--eigen-einkommen", type=_finite_float, default=0.0, help="Eigenes Bruttoeinkommen im Bewilligungszeitraum"
    )
    pr.add_argument(
        "--ehegatte-einkommen",
        type=_finite_float,
        default=0.0,
        help="Einkommen Ehegatte/eingetr. Lebenspartner (Monat)",
    )
    pr.add_argument(
        "--eigene-kinder", type=int, default=0, help="Eigene Kinder ohne Ausbildung"
    )
    pr.add_argument(
        "--vermoegen", type=_finite_float, default=0.0, help="Eigenes Vermögen (§29)"
    )
    pr.add_argument(
        "--json", action="store_true", help="Ausgabe als JSON (für Agenten)"
    )
    pr.set_defaults(func=cmd_rechner)

    # fristen
    pf = sub.add_parser("fristen", help="Antrags-, Folgeantrags- und §48-Fristen")
    pf.add_argument("--json", action="store_true", help="Ausgabe als JSON")
    pf.set_defaults(func=cmd_fristen)

    # unterlagen
    pu = sub.add_parser(
        "unterlagen",
        help="Checkliste Formblätter 1–9 je nach Situation",
    )
    pu.add_argument(
        "--situation",
        help=(
            "Schlüssel einer Situation (z.B. 'erstantrag_student', "
            "'folgeantrag_student', 'auslandsantrag')"
        ),
    )
    pu.add_argument(
        "--formblatt",
        type=int,
        help="Nur ein bestimmtes Formblatt (1–9) ausgeben",
    )
    pu.add_argument("--json", action="store_true", help="Ausgabe als JSON")
    pu.set_defaults(func=cmd_unterlagen)

    # links
    pl = sub.add_parser(
        "links", help="Offizielle BAföG-Links (BAföG Digital, Ämterverzeichnis)"
    )
    pl.add_argument(
        "--kategorie",
        choices=list(links.KATEGORIEN.keys()),
        help="Nur eine bestimmte Kategorie",
    )
    pl.add_argument("--json", action="store_true", help="Ausgabe als JSON")
    pl.set_defaults(func=cmd_links)

    # ---- Automation gegen bafoeg-digital.de ----

    plogin = sub.add_parser(
        "login",
        help=(
            "Login gegen BAföG Digital (via BundID). "
            "headless mit Benutzername+Passwort oder --headed für eID/ELSTER/2FA."
        ),
    )
    plogin.add_argument(
        "--method",
        choices=["password", "manual", "auto"],
        default="auto",
        help="Login-Methode (default: auto)",
    )
    plogin.add_argument(
        "--headed",
        action="store_true",
        help="Browser sichtbar starten (nötig für eID/ELSTER/2FA-Fallback)",
    )
    plogin.add_argument(
        "--manual-max-wait",
        type=int,
        default=300,
        help="Sekunden, die auf den manuellen Login gewartet wird",
    )
    plogin.add_argument("--json", action="store_true", help="Ausgabe als JSON")
    plogin.set_defaults(func=cmd_login)

    pstatus = sub.add_parser(
        "status",
        help="Antragsstatus + Postfachsnachrichten lesen (braucht gültige Session).",
    )
    pstatus.add_argument("--json", action="store_true", help="Ausgabe als JSON")
    pstatus.set_defaults(func=cmd_status)

    pa = sub.add_parser(
        "antrag",
        help="Antrags-Operationen gegen BAföG Digital.",
    )
    pa_sub = pa.add_subparsers(dest="antrag_befehl")
    pa_fill = pa_sub.add_parser(
        "fill",
        help="Formblatt 1 aus YAML-Datei laden und Entwurf speichern.",
    )
    pa_fill.add_argument("--daten", required=True, help="Pfad zur YAML-Datei (Formblatt 1)")
    pa_fill.add_argument(
        "--require-complete",
        action="store_true",
        help="Bei fehlenden Pflichtfeldern gar nicht erst speichern",
    )
    pa_fill.add_argument("--json", action="store_true", help="Ausgabe als JSON")
    pa_fill.set_defaults(func=cmd_antrag_fill)
    pa_submit = pa_sub.add_parser(
        "submit",
        help="Antrag ENDGÜLTIG einreichen (verlangt --confirm).",
    )
    pa_submit.add_argument("--daten", required=True, help="Pfad zur YAML-Datei (Formblatt 1)")
    pa_submit.add_argument(
        "--confirm",
        action="store_true",
        help="Explizit bestätigen, dass der Antrag endgültig eingereicht werden soll",
    )
    pa_submit.add_argument("--json", action="store_true", help="Ausgabe als JSON")
    pa_submit.set_defaults(func=cmd_antrag_submit)
    pa.set_defaults(func=lambda a: (pa.print_help() or 0))

    pdocs = sub.add_parser(
        "docs",
        help="Dokumenten-Operationen gegen BAföG Digital.",
    )
    pdocs_sub = pdocs.add_subparsers(dest="docs_befehl")
    pu = pdocs_sub.add_parser(
        "upload",
        help="Beleg/Immatrikulationsbescheinigung o.Ä. hochladen.",
    )
    pu.add_argument("--datei", required=True, help="Pfad zur Datei")
    pu.add_argument(
        "--typ",
        default="beleg",
        help="Dokumenttyp (z.B. immatrikulation, einkommensnachweis, ...)",
    )
    pu.add_argument("--beschreibung", default="", help="Kurzbeschreibung")
    pu.add_argument("--antrag-id", default="", help="Optionale Antrags-ID")
    pu.add_argument("--json", action="store_true", help="Ausgabe als JSON")
    pu.set_defaults(func=cmd_docs_upload)
    pdocs.set_defaults(func=lambda a: (pdocs.print_help() or 0))

    ptpl = sub.add_parser(
        "formblatt-template",
        help="YAML-Template für Formblatt 1 ausgeben.",
    )
    ptpl.add_argument(
        "--ausgeben", action="store_true",
        help="Template tatsächlich auf stdout drucken",
    )
    ptpl.set_defaults(func=cmd_formblatt_template)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if getattr(args, "version", False):
        from . import __version__

        print(f"bafoeg-cli {__version__}")
        return 0
    if not getattr(args, "befehl", None):
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
