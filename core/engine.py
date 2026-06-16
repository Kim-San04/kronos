import os
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

console = Console()

class KronosEngine:
    def __init__(self, args):
        self.args = args
        self.target_name = args.person or args.company
        self.target_type = "person" if args.person else "company"
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    def run_person_scan(self):
        from core.target import PersonTarget
        target = PersonTarget(
            name=self.args.person,
            email=getattr(self.args, "email", None),
            username=getattr(self.args, "username", None),
            phone=getattr(self.args, "phone", None),
        )

        steps = [
            ("Username finder",
             "modules.person.username_finder",
             "UsernameFinder"),
            ("Sherlock — 300+ plateformes",
             "modules.person.sherlock_runner",
             "SherlockRunner"),
            ("Maigret — analyse approfondie",
             "modules.person.maigret_runner",
             "MaigretRunner"),
            ("GitHub — commits, emails",
             "modules.person.github_person",
             "GitHubPerson"),
            ("Email Hunter",
             "modules.person.email_hunter",
             "EmailHunter"),
            ("Holehe — email sur 120+ sites",
             "modules.person.holehe_runner",
             "HoleheRunner"),
            ("Fuites de données",
             "modules.person.breach_lookup",
             "BreachLookup"),
            ("Google Dorking",
             "modules.person.google_dorker",
             "GoogleDorker"),
            ("Recherche numéro",
             "modules.person.phone_finder",
             "PhoneFinder"),
            ("Recherche photos",
             "modules.person.photo_finder",
             "PhotoFinder"),
            ("Analyse comportementale",
             "modules.person.behavior_analyzer",
             "BehaviorAnalyzer"),
            ("Réseau de relations",
             "modules.person.network_mapper",
             "NetworkMapper"),
            ("Validation des résultats",
             "modules.person.result_validator",
             "ResultValidator"),
            ("Analyse IA — corrélations",
             "modules.correlation.ai_analyst",
             "AIAnalyst"),
        ]

        self._run_steps(steps, target)
        self._show_summary(target)
        self._generate_outputs(target)

    def run_company_scan(self):
        from core.target import CompanyTarget
        target = CompanyTarget(
            domain=self.args.company,
            org=getattr(self.args, "org", None),
        )

        steps = [
            ("DNS & WHOIS & ASN",
             "modules.company.dns_recon",
             "DnsRecon"),
            ("Sous-domaines — brute force + crt.sh",
             "modules.company.ssl_certs",
             "SSLCerts"),
            ("Shodan — ports, CVEs, services",
             "modules.company.shodan_scan",
             "ShodanScan"),
            ("Cloud assets — S3, Azure, GCP",
             "modules.company.cloud_assets",
             "CloudAssets"),
            ("Secrets exposés — GitHub, GitLab",
             "modules.company.secret_scanner",
             "SecretScanner"),
            ("GitHub Organisation",
             "modules.company.github_org",
             "GitHubOrg"),
            ("Employés — LinkedIn, emails",
             "modules.company.employee_finder",
             "EmployeeFinder"),
            ("Darkweb — mentions, fuites",
             "modules.company.darkweb_monitor",
             "DarkwebMonitor"),
            ("Analyse IA — corrélation",
             "modules.correlation.ai_analyst",
             "AIAnalyst"),
        ]

        self._run_steps(steps, target)
        self._show_summary(target)
        self._generate_outputs(target)

    def _run_steps(self, steps, target):
        import importlib
        total = len(steps)
        for i, (name, module_path, class_name) in enumerate(steps, 1):
            console.print(
                f"  [dim][{i}/{total}][/dim] "
                f"[cyan]▶[/cyan] {name}..."
            )
            try:
                mod = importlib.import_module(module_path)
                cls = getattr(mod, class_name)
                cls(target).run()
                console.print(
                    f"  [dim][{i}/{total}][/dim] "
                    f"[green]✓[/green] {name}"
                )
            except Exception as e:
                console.print(
                    f"  [dim][{i}/{total}][/dim] "
                    f"[red]✗[/red] {name}: {e}"
                )

    def _show_summary(self, target):
        console.print()

        table = Table(
            box=box.SIMPLE_HEAVY,
            show_header=False,
            border_style="cyan",
            padding=(0, 2)
        )
        table.add_column(style="dim", width=24)
        table.add_column(style="bold white")

        if hasattr(target, "emails_found"):
            table.add_row(
                "Emails trouvés",
                str(len(target.emails_found))
            )
            table.add_row(
                "Profils sociaux",
                str(len(target.social_profiles))
            )
            table.add_row(
                "Fuites de données",
                str(len(target.breaches))
            )
            table.add_row(
                "Localisations",
                str(len(target.locations))
            )
            table.add_row(
                "Connexions identifiées",
                str(len(target.connections))
            )
        else:
            table.add_row(
                "Sous-domaines",
                str(len(target.subdomains))
            )
            table.add_row(
                "IPs découvertes",
                str(len(target.ips))
            )
            table.add_row(
                "Secrets exposés",
                str(len(target.exposed_secrets))
            )
            table.add_row(
                "Employés identifiés",
                str(len(target.employees))
            )
            table.add_row(
                "Mentions darkweb",
                str(len(target.darkweb_mentions))
            )

        table.add_row(
            "Score de risque",
            f"[bold red]{target.risk_score}/100[/bold red]"
        )

        console.print(Panel(
            table,
            title="[bold cyan]◆ RÉSULTATS KRONOS[/bold cyan]",
            border_style="cyan",
            box=box.HEAVY
        ))

    def _generate_outputs(self, target):
        name = getattr(
            target, "name",
            getattr(target, "domain", "target")
        ).replace(" ", "_")

        session_dir = f"{self.args.output}/{name}_{self.session_id}"
        raw_dir = f"{session_dir}/raw"
        os.makedirs(session_dir, exist_ok=True)
        os.makedirs(raw_dir, exist_ok=True)

        from export.kronos_export import KronosExport
        export = KronosExport(target, self.session_id)
        export.save_to_path(f"{session_dir}/data.json")

        from reporting.graph_builder import GraphBuilder
        graph = GraphBuilder(target, self.session_id)
        graph.build_to_path(f"{session_dir}/graph.html")

        if not self.args.no_pdf:
            from reporting.pdf_report import generate_pdf
            generate_pdf(target, f"{session_dir}/report.pdf")

        console.print(
            f"\n  [bold cyan]✓ Résultats dans : "
            f"{session_dir}[/bold cyan]"
        )
        console.print(f"  [dim]  ├── report.pdf[/dim]")
        console.print(f"  [dim]  ├── graph.html[/dim]")
        console.print(f"  [dim]  └── data.json[/dim]")
