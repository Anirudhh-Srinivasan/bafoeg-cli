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
import sys
from typing import Any

from . import fristen, links, rechner, unterlagen, werte


def _out(data: Any, as_json: bool, pretty: bool = True) -> None:
    """Ausgabe als JSON (für Agenten) oder als lesbarer Text."""
    if as_json:
        if pretty:
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            print(json.dumps(data, ensure_ascii=False))
        return
    # Plaintext – einfache, menschliche Darstellung
    print(json.dumps(data, ensure_ascii=False, indent=2))


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
        "--einkommen-vater", type=float, default=0.0, help="Monatliches Nettoeinkommen Vater"
    )
    pr.add_argument(
        "--einkommen-mutter", type=float, default=0.0, help="Monatliches Nettoeinkommen Mutter"
    )
    pr.add_argument(
        "--weitere-kinder",
        type=int,
        default=0,
        help="Weitere unterhaltsberechtigte Kinder im Haushalt",
    )
    pr.add_argument(
        "--eigen-einkommen", type=float, default=0.0, help="Eigenes Bruttoeinkommen im Bewilligungszeitraum"
    )
    pr.add_argument(
        "--ehegatte-einkommen",
        type=float,
        default=0.0,
        help="Einkommen Ehegatte/eingetr. Lebenspartner (Monat)",
    )
    pr.add_argument(
        "--eigene-kinder", type=int, default=0, help="Eigene Kinder ohne Ausbildung"
    )
    pr.add_argument(
        "--vermoegen", type=float, default=0.0, help="Eigenes Vermögen (§29)"
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