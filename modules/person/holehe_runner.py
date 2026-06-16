import subprocess
import os
from rich.console import Console

console = Console()

class HoleheRunner:
    """
    Holehe vérifie si un email est enregistré sur 120+ sites
    via la fonction "mot de passe oublié" (sans créer de compte).
    """

    def __init__(self, target):
        self.target = target

    def run(self):
        emails = []
        if self.target.email:
            emails.append(self.target.email)
        emails.extend([
            e for e in self.target.emails_found
            if e not in emails
        ][:3])

        if not emails:
            console.print("    [dim]Holehe : aucun email à tester[/dim]")
            return

        for email in emails:
            console.print(
                f"    [dim]Holehe — test de {email} sur 120+ sites...[/dim]"
            )
            self._run_holehe(email)

    def _run_holehe(self, email: str):
        try:
            result = subprocess.run(
                [
                    "holehe",
                    email,
                    "--only-used",
                    "--no-color",
                ],
                capture_output=True,
                text=True,
                timeout=120,
                env={**os.environ, "PATH": f"{os.path.expanduser('~')}/.local/bin:{os.environ.get('PATH', '')}"}
            )

            found_sites = []
            for line in result.stdout.splitlines():
                line_stripped = line.strip()
                if "[+]" in line_stripped or "✔" in line_stripped:
                    parts = line_stripped.split()
                    if len(parts) >= 2:
                        site = parts[-1].strip("[]✔✘ ")
                        if site and len(site) > 1:
                            found_sites.append(site)
                            self.target.social_profiles[f"Holehe_{site}"] = (
                                f"Compte détecté sur {site} avec {email}"
                            )

            if found_sites:
                console.print(
                    f"    [green]{email} utilisé sur : "
                    f"{', '.join(found_sites[:5])}[/green]"
                )
                if len(found_sites) > 5:
                    console.print(
                        f"    [dim]... et {len(found_sites) - 5} autres[/dim]"
                    )
            else:
                console.print(f"    [dim]{email} : non trouvé[/dim]")

        except FileNotFoundError:
            console.print(
                "    [dim]Holehe non installé — pip install holehe[/dim]"
            )
        except Exception as e:
            console.print(f"    [dim]Holehe : {e}[/dim]")
