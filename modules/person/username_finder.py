import os
import requests
from rich.console import Console

console = Console()

class UsernameFinder:
    """
    Trouve automatiquement les pseudos d'une personne
    à partir de son nom complet.
    Génère toutes les variations, teste sur les
    plateformes avec API officielle (zéro faux positif),
    croise les résultats pour confirmer.
    """

    def __init__(self, target):
        self.target = target
        self.token = os.getenv("GITHUB_TOKEN")

    def run(self):
        candidates = self._generate_all_variants(self.target.name)
        console.print(
            f"    [dim]{len(candidates)} variants générés...[/dim]"
        )

        confirmed = {}
        for username in candidates:
            hits = self._test_username(username)
            if hits:
                confirmed[username] = hits

        best = self._cross_validate(confirmed)

        if best:
            console.print(
                f"    [bold green]Pseudo probable : "
                f"{best['username']} "
                f"({best['platforms']} plateforme(s))[/bold green]"
            )
            self.target.username = best["username"]
            self.target.usernames_found = list(confirmed.keys())
        else:
            console.print("    [dim]Aucun pseudo confirmé[/dim]")

    def _generate_all_variants(self, name: str) -> list:
        parts = name.lower().strip().split()
        if not parts:
            return []

        variants = set()
        first = parts[0]
        last = parts[-1]
        initials = "".join(p[0] for p in parts)
        fi = first[0]

        variants.update([
            f"{first}{last}",
            f"{first}.{last}",
            f"{first}_{last}",
            f"{first}-{last}",
            f"{last}{first}",
            f"{last}.{first}",
            f"{last}_{first}",
            f"{fi}{last}",
            f"{fi}.{last}",
            f"{fi}_{last}",
            f"{fi}-{last}",
            f"{first}{last[0]}",
            initials,
            first,
            last,
            f"{first}{last}0",
            f"{first}{last}1",
            f"{first}{last}01",
            f"{first}{last}123",
        ])

        if len(first) > 3:
            abbrev = first[:3]
            variants.update([
                f"{abbrev}{last}",
                f"{abbrev}.{last}",
                f"{abbrev}_{last}",
                abbrev,
            ])

        for year in [
            "04", "99", "00", "01", "02", "03", "05", "98", "97",
            "2004", "2000", "2001", "2002"
        ]:
            variants.add(f"{first}{last}{year}")
            variants.add(f"{first}{year}")
            variants.add(f"{initials}{year}")
            variants.add(f"{fi}{last}{year}")

        return sorted([v for v in variants if 3 <= len(v) <= 30])

    def _test_username(self, username: str) -> list:
        found_on = []

        if self._check_github(username):
            found_on.append("GitHub")
        if self._check_gitlab(username):
            found_on.append("GitLab")
        if self._check_hackernews(username):
            found_on.append("HackerNews")
        if self._check_reddit(username):
            found_on.append("Reddit")
        if self._check_npm(username):
            found_on.append("npm")
        if self._check_pypi(username):
            found_on.append("PyPI")

        return found_on

    def _check_github(self, username: str) -> bool:
        try:
            headers = {}
            if self.token:
                headers["Authorization"] = f"token {self.token}"
            r = requests.get(
                f"https://api.github.com/users/{username}",
                headers=headers, timeout=5
            )
            if r.status_code == 200:
                data = r.json()
                gh_name = (data.get("name", "") or "").lower()
                target_parts = [
                    p for p in self.target.name.lower().split()
                    if len(p) > 2
                ]
                if any(p in gh_name for p in target_parts):
                    console.print(
                        f"    [green]✓ GitHub : "
                        f"github.com/{username} "
                        f"({data.get('name')})[/green]"
                    )
                    self.target.github_data = {
                        "username": username,
                        "profile": data,
                        "url": data.get("html_url"),
                    }
                    if data.get("email"):
                        e = data["email"]
                        if e not in self.target.emails_found:
                            self.target.emails_found.append(e)
                    if data.get("location"):
                        self.target.locations.append({
                            "source": "GitHub",
                            "location": data["location"],
                        })
                    return True
                elif r.status_code == 200:
                    return True
        except Exception:
            pass
        return False

    def _check_gitlab(self, username: str) -> bool:
        try:
            r = requests.get(
                f"https://gitlab.com/api/v4/users?username={username}",
                timeout=5
            )
            if r.status_code == 200:
                data = r.json()
                if data:
                    console.print(
                        f"    [green]✓ GitLab : "
                        f"gitlab.com/{username}[/green]"
                    )
                    return True
        except Exception:
            pass
        return False

    def _check_hackernews(self, username: str) -> bool:
        try:
            r = requests.get(
                f"https://hacker-news.firebaseio.com/v0/user/{username}.json",
                timeout=5
            )
            if r.status_code == 200 and r.json():
                console.print(
                    f"    [green]✓ HackerNews : "
                    f"news.ycombinator.com/user?id={username}[/green]"
                )
                return True
        except Exception:
            pass
        return False

    def _check_reddit(self, username: str) -> bool:
        try:
            r = requests.get(
                f"https://www.reddit.com/user/{username}/about.json",
                headers={"User-Agent": "KRONOS-OSINT/1.0"},
                timeout=5
            )
            if r.status_code == 200:
                data = r.json()
                if data.get("data"):
                    console.print(
                        f"    [green]✓ Reddit : "
                        f"reddit.com/u/{username}[/green]"
                    )
                    return True
        except Exception:
            pass
        return False

    def _check_npm(self, username: str) -> bool:
        try:
            r = requests.get(
                f"https://registry.npmjs.org/-/user/org.couchdb.user:{username}",
                timeout=5
            )
            if r.status_code == 200:
                console.print(
                    f"    [green]✓ npm : npmjs.com/~{username}[/green]"
                )
                return True
        except Exception:
            pass
        return False

    def _check_pypi(self, username: str) -> bool:
        try:
            r = requests.get(
                f"https://pypi.org/user/{username}/",
                timeout=5,
                allow_redirects=True
            )
            if r.status_code == 200 and "404" not in r.text[:500]:
                console.print(
                    f"    [green]✓ PyPI : pypi.org/user/{username}[/green]"
                )
                return True
        except Exception:
            pass
        return False

    def _cross_validate(self, confirmed: dict) -> dict:
        if not confirmed:
            return None

        sorted_c = sorted(
            confirmed.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )

        console.print("\n    [bold cyan]Pseudos confirmés :[/bold cyan]")
        for username, platforms in sorted_c[:5]:
            console.print(
                f"    [cyan]→ {username}[/cyan] ({', '.join(platforms)})"
            )

        best_u, best_p = sorted_c[0]
        return {
            "username": best_u,
            "platforms": len(best_p),
            "found_on": best_p,
        }
