#!/usr/bin/env python3
"""
KRONOS — OSINT Intelligence System
"""

import argparse
import sys
import os
from dotenv import load_dotenv

load_dotenv()

def parse_args():
    parser = argparse.ArgumentParser(
        prog="kronos",
        description="KRONOS — OSINT Intelligence System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --person "John Doe" --username johndoe
  python main.py --person "Jane Smith" --email jane@example.com
  python main.py --company example.com --org example-org
  python main.py --company tesla.com --no-pdf --output ./results
        """
    )

    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument(
        "--person", "-p",
        metavar="NAME",
        help="Nom complet de la cible (personne)"
    )
    target.add_argument(
        "--company", "-c",
        metavar="DOMAIN",
        help="Domaine de la cible (entreprise)"
    )

    parser.add_argument(
        "--username", "-u",
        metavar="USERNAME",
        help="Username connu de la cible"
    )
    parser.add_argument(
        "--email", "-e",
        metavar="EMAIL",
        help="Email connu de la cible"
    )
    parser.add_argument(
        "--phone",
        metavar="PHONE",
        help="Numéro de téléphone de la cible"
    )
    parser.add_argument(
        "--org",
        metavar="ORG",
        help="Nom de l'organisation GitHub"
    )
    parser.add_argument(
        "--notes",
        metavar="TEXT",
        help=(
            "Contexte supplémentaire sur la cible "
            "(ex: 'étudiant EFREI Bordeaux cybersec')"
        )
    )
    parser.add_argument(
        "--employer",
        metavar="COMPANY",
        help="Entreprise connue de la cible (personne)"
    )
    parser.add_argument(
        "--output", "-o",
        metavar="DIR",
        default="./output",
        help="Dossier de sortie (défaut: ./output)"
    )
    parser.add_argument(
        "--no-pdf",
        action="store_true",
        help="Désactiver la génération PDF"
    )
    parser.add_argument(
        "--monitor", "-m",
        action="store_true",
        help="Activer la surveillance continue après le scan"
    )
    parser.add_argument(
        "--monitor-interval",
        type=int,
        default=3600,
        metavar="SECONDS",
        help="Intervalle de surveillance en secondes (défaut: 3600)"
    )
    parser.add_argument(
        "--no-intro",
        action="store_true",
        help="Désactiver l'animation d'intro"
    )

    return parser.parse_args()


def main():
    args = parse_args()

    target_name = args.person or args.company
    mode = "PERSON" if args.person else "COMPANY"

    if not args.no_intro:
        from ui.intro import show_intro
        show_intro(target_name, mode)

    from core.engine import KronosEngine
    engine = KronosEngine(args)

    if args.person:
        engine.run_person_scan()
    else:
        engine.run_company_scan()

    if args.monitor:
        from monitor.watcher import Watcher
        from core.target import PersonTarget, CompanyTarget
        # Watcher utilise la cible du moteur
        # reconstruite depuis le dernier export
        pass


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[KRONOS] Interrupted.")
        sys.exit(0)
