import os
import requests
from rich.console import Console

console = Console()

class GitHubPerson:
    def __init__(self, target):
        self.target = target
        self.token = os.getenv("GITHUB_TOKEN")
        self.headers = {}
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"

    def run(self):
        username = (
            self.target.github_data.get("username")
            or self.target.username
        )

        if not username:
            username = self._search_by_name()

        if not username:
            console.print("    [dim]GitHub : aucun profil trouvé[/dim]")
            return

        repos = self._get_repos(username)
        console.print(f"    [cyan]{len(repos)} repos publics[/cyan]")

        commit_emails = self._scan_commits(username, repos[:10])
        for email in commit_emails:
            if email not in self.target.emails_found:
                self.target.emails_found.append(email)
                console.print(f"    [green]Email commit : {email}[/green]")

        self._analyze_activity(repos)
        langs = self._get_languages(repos)

        self.target.github_data.update({
            "username": username,
            "repos_count": len(repos),
            "languages": langs,
            "commit_emails": commit_emails,
        })

        if langs:
            console.print(
                f"    [cyan]Langages : {', '.join(langs[:3])}[/cyan]"
            )

    def _search_by_name(self) -> str:
        try:
            r = requests.get(
                f"https://api.github.com/search/users"
                f"?q={self.target.name}+type:user&per_page=5",
                headers=self.headers, timeout=10
            )
            if r.status_code == 200:
                items = r.json().get("items", [])
                for item in items:
                    profile = self._get_profile(item["login"])
                    if profile:
                        gh_name = (
                            profile.get("name", "") or ""
                        ).lower()
                        parts = [
                            p for p in
                            self.target.name.lower().split()
                            if len(p) > 2
                        ]
                        if any(p in gh_name for p in parts):
                            console.print(
                                f"    [green]GitHub trouvé : "
                                f"{item['login']} "
                                f"({profile.get('name')})[/green]"
                            )
                            self.target.github_data["profile"] = profile
                            return item["login"]
        except Exception:
            pass
        return None

    def _get_profile(self, username: str) -> dict:
        try:
            r = requests.get(
                f"https://api.github.com/users/{username}",
                headers=self.headers, timeout=5
            )
            return r.json() if r.status_code == 200 else {}
        except Exception:
            return {}

    def _get_repos(self, username: str) -> list:
        try:
            r = requests.get(
                f"https://api.github.com/users/{username}/repos"
                f"?per_page=100&sort=updated",
                headers=self.headers, timeout=10
            )
            return r.json() if r.status_code == 200 else []
        except Exception:
            return []

    def _scan_commits(self, username: str, repos: list) -> list:
        emails = set()
        for repo in repos:
            try:
                r = requests.get(
                    f"https://api.github.com/repos"
                    f"/{username}/{repo['name']}/commits?per_page=10",
                    headers=self.headers, timeout=8
                )
                if r.status_code == 200:
                    for commit in r.json():
                        author = (
                            commit.get("commit", {}).get("author", {})
                        )
                        email = author.get("email", "")
                        if (email
                                and "noreply" not in email
                                and "github" not in email):
                            emails.add(email)
            except Exception:
                pass
        return list(emails)

    def _get_languages(self, repos: list) -> list:
        langs = {}
        for repo in repos:
            lang = repo.get("language")
            if lang:
                langs[lang] = langs.get(lang, 0) + 1
        return sorted(langs, key=langs.get, reverse=True)[:5]

    def _analyze_activity(self, repos: list):
        hours = {}
        for repo in repos:
            updated = repo.get("updated_at", "")
            if updated and len(updated) >= 13:
                try:
                    hour = int(updated[11:13])
                    hours[hour] = hours.get(hour, 0) + 1
                except Exception:
                    pass
        if hours:
            peak = max(hours, key=hours.get)
            self.target.activity_hours = {
                "distribution": hours,
                "peak_hour": peak,
            }
            if 6 <= peak <= 12:
                period = "matin"
            elif 12 <= peak <= 18:
                period = "après-midi"
            elif 18 <= peak <= 22:
                period = "soirée"
            else:
                period = "nuit"
            console.print(
                f"    [cyan]Pic d'activité : {peak}h ({period})[/cyan]"
            )
