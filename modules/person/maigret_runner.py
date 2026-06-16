import subprocess
import json
import os
from rich.console import Console

console = Console()

class MaigretRunner:
    """
    Maigret est encore plus puissant que Sherlock.
    Il récupère aussi les infos des profils trouvés.
    """

    def __init__(self, target):
        self.target = target

    def run(self):
        username = (
            self.target.username
            or self.target.name.lower().replace(" ", "")
        )

        console.print(
            f"    [dim]Maigret — analyse approfondie de '{username}'...[/dim]"
        )

        output_file = f"/tmp/maigret_{username}.json"

        try:
            subprocess.run(
                [
                    "maigret",
                    username,
                    "--json", output_file,
                    "--timeout", "15",
                    "--no-color",
                ],
                capture_output=True,
                text=True,
                timeout=180,
                env={**os.environ, "PATH": f"{os.path.expanduser('~')}/.local/bin:{os.environ.get('PATH', '')}"}
            )

            if not os.path.exists(output_file):
                console.print("    [dim]Maigret : aucun résultat[/dim]")
                return

            with open(output_file) as f:
                data = json.load(f)

            os.remove(output_file)

            claimed = 0
            for site, info in data.items():
                if info.get("status") == "Claimed":
                    url = info.get("url", "")
                    if url:
                        self.target.social_profiles[site] = url
                        claimed += 1

                    profile_data = info.get("parsed_data", {})

                    email = profile_data.get("email")
                    if email and email not in self.target.emails_found:
                        self.target.emails_found.append(email)
                        console.print(
                            f"    [green]Email : {email}[/green]"
                        )

                    location = profile_data.get("location")
                    if location:
                        self.target.locations.append({
                            "source": site,
                            "location": location
                        })

            total = len(self.target.social_profiles)
            console.print(
                f"    [cyan]{claimed} profils via Maigret "
                f"({total} total)[/cyan]"
            )

        except FileNotFoundError:
            console.print(
                "    [dim]Maigret non installé — "
                "pip install maigret[/dim]"
            )
        except Exception as e:
            console.print(f"    [dim]Maigret : {e}[/dim]")
