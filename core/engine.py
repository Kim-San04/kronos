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
            ("Recherche de pseudos",
             "modules.person.username_finder",
             "UsernameFinder"),
            ("Email Hunter",
             "modules.person.email_hunter",
             "EmailHunter"),
            ("Réseaux sociaux",
             "modules.person.social_scanner",
             "SocialScanner"),
            ("GitHub — profil, commits, emails",
             "modules.person.github_person",
             "GitHubPerson"),
            ("Fuites de données",
             "modules.person.breach_lookup",
             "BreachLookup"),
            ("Analyse comportementale",
             "modules.person.behavior_analyzer",
             "BehaviorAnalyzer"),
            ("Géolocalisation",
             "modules.person.geo_tracker",
             "GeoTracker"),
            ("Réseau de relations",
             "modules.person.network_mapper",
             "NetworkMapper"),
            ("Analyse IA",
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
        os.makedirs(self.args.output, exist_ok=True)

        from export.kronos_export import KronosExport
        export = KronosExport(target, self.session_id)
        json_path = export.save(self.args.output)
        console.print(f"  [cyan]✓[/cyan] Export JSON : {json_path}")

        from reporting.graph_builder import GraphBuilder
        graph = GraphBuilder(target, self.session_id)
        graph_path = graph.build(self.args.output)
        console.print(f"  [cyan]✓[/cyan] Graphe : {graph_path}")

        if not self.args.no_pdf:
            from reporting.pdf_report import generate_pdf
            name = getattr(
                target, "domain",
                getattr(target, "name", "target")
            ).replace(" ", "_")
            pdf_path = (
                f"{self.args.output}/"
                f"kronos_{name}_{self.session_id}.pdf"
            )
            generate_pdf(target, pdf_path)
            console.print(
                f"  [cyan]✓[/cyan] Rapport PDF : {pdf_path}"
            )
