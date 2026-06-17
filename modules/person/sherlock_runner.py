import subprocess
import json
import os
import re
from rich.console import Console

console = Console()

class SherlockRunner:
    """
    Lance Sherlock pour trouver tous les comptes
    d'une personne sur 300+ plateformes.
    """

    def __init__(self, target):
        self.target = target

    def run(self):
        all_usernames = self._generate_usernames()

        # Le username fourni explicitement est toujours pertinent
        provided = self.target.username
        relevant = [
            u for u in all_usernames
            if u == provided or self._is_relevant_username(u)
        ]

        if not relevant:
            console.print(
                "    [dim]Sherlock : aucun username pertinent à tester[/dim]"
            )
            return

        console.print(
            f"    [dim]Sherlock — test de "
            f"{len(relevant)} username(s) pertinent(s) sur 300+ sites...[/dim]"
        )

        all_found = {}

        for username in relevant[:4]:
            found = self._run_sherlock(username)
            if found:
                all_found[username] = found
                console.print(
                    f"    [green]✓ '{username}' : "
                    f"{len(found)} compte(s) trouvé(s)[/green]"
                )
                for platform, url in list(found.items())[:5]:
                    console.print(
                        f"      [dim]→ {platform} : {url}[/dim]"
                    )

        for username, profiles in all_found.items():
            self.target.social_profiles.update(profiles)
            if username not in self.target.usernames_found:
                self.target.usernames_found.append(username)

        total = len(self.target.social_profiles)
        console.print(
            f"    [bold cyan]{total} comptes confirmés sur internet[/bold cyan]"
        )

        if all_found:
            best = max(all_found, key=lambda k: len(all_found[k]))
            self.target.username = best

    def _is_relevant_username(self, username: str) -> bool:
        name_parts = [
            p.lower() for p in self.target.name.split()
            if len(p) > 2
        ]
        return any(part in username.lower() for part in name_parts)

    def _run_sherlock(self, username: str) -> dict:
        output_file = f"/tmp/sherlock_{username}.txt"

        try:
            result = subprocess.run(
                [
                    "sherlock",
                    username,
                    "--output", output_file,
                    "--timeout", "10",
                    "--print-found",
                ],
                capture_output=True,
                text=True,
                timeout=120,
                env={**os.environ, "PATH": f"{os.path.expanduser('~')}/.local/bin:{os.environ.get('PATH', '')}"}
            )

            found = {}

            if os.path.exists(output_file):
                with open(output_file) as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("http"):
                            url = line
                            platform = self._extract_platform(url)
                            found[platform] = url
                os.remove(output_file)

            for line in result.stdout.splitlines():
                if "[+]" in line:
                    url_match = re.search(r'https?://[^\s]+', line)
                    platform_match = re.search(r'\[\+\]\s+(\w[\w\s]+):', line)
                    if url_match:
                        url = url_match.group(0)
                        platform = (
                            platform_match.group(1).strip()
                            if platform_match
                            else self._extract_platform(url)
                        )
                        found[platform] = url

            return found

        except subprocess.TimeoutExpired:
            console.print("    [dim]Sherlock timeout[/dim]")
            return {}
        except FileNotFoundError:
            console.print(
                "    [red]Sherlock non installé : "
                "pip install sherlock-project[/red]"
            )
            return {}
        except Exception as e:
            console.print(f"    [dim]Sherlock erreur : {e}[/dim]")
            return {}

    def _extract_platform(self, url: str) -> str:
        match = re.search(r'https?://(?:www\.)?([^/\.]+)', url)
        return match.group(1).title() if match else url

    def _generate_usernames(self) -> list:
        if self.target.username:
            base = [self.target.username]
        else:
            name = self.target.name.lower().split()
            if len(name) >= 2:
                f, l = name[0], name[-1]
                base = [
                    f"{f}{l}",
                    f"{f}.{l}",
                    f"{f}_{l}",
                    f"{f[0]}{l}",
                    f,
                ]
            else:
                base = [name[0]]

        extras = []
        for u in base[:2]:
            for year in ["04", "2004", "00", "99"]:
                extras.append(f"{u}{year}")

        return list(dict.fromkeys(base + extras))[:6]
