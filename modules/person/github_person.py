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
        username = self.target.username or self._find_github_username()
        if not username:
            return

        profile = self._get_profile(username)
        if not profile:
            return

        if profile.get("email"):
            email = profile["email"]
            if email not in self.target.emails_found:
                self.target.emails_found.append(email)
                console.print(f"    [green]Email GitHub : {email}[/green]")

        repos = self._get_repos(username)
        commit_emails = self._scan_commits(username, repos[:5])
        for email in commit_emails:
            if email not in self.target.emails_found:
                self.target.emails_found.append(email)
                console.print(f"    [green]Email commit : {email}[/green]")

        self._analyze_activity(repos)

        self.target.github_data = {
            "username": username,
            "profile": profile,
            "repos_count": len(repos),
            "languages": self._get_languages(repos),
            "commit_emails": commit_emails,
        }

        console.print(
            f"    [cyan]{len(repos)} repos, "
            f"{len(commit_emails)} emails commits[/cyan]"
        )

    def _get_profile(self, username):
        try:
            r = requests.get(
                f"https://api.github.com/users/{username}",
                headers=self.headers, timeout=10
            )
            return r.json() if r.status_code == 200 else None
        except:
            return None

    def _get_repos(self, username):
        try:
            r = requests.get(
                f"https://api.github.com/users/{username}/repos?per_page=100",
                headers=self.headers, timeout=10
            )
            return r.json() if r.status_code == 200 else []
        except:
            return []

    def _scan_commits(self, username, repos):
        emails = set()
        for repo in repos:
            try:
                r = requests.get(
                    f"https://api.github.com/repos"
                    f"/{username}/{repo['name']}/commits?per_page=10",
                    headers=self.headers, timeout=10
                )
                if r.status_code == 200:
                    for commit in r.json():
                        author = (
                            commit.get("commit", {}).get("author", {})
                        )
                        email = author.get("email", "")
                        if email and "noreply" not in email:
                            emails.add(email)
            except:
                pass
        return list(emails)

    def _get_languages(self, repos):
        langs = {}
        for repo in repos:
            lang = repo.get("language")
            if lang:
                langs[lang] = langs.get(lang, 0) + 1
        return sorted(langs, key=langs.get, reverse=True)[:5]

    def _analyze_activity(self, repos):
        hours = {}
        for repo in repos:
            try:
                updated = repo.get("updated_at", "")
                if updated:
                    hour = int(updated[11:13])
                    hours[hour] = hours.get(hour, 0) + 1
            except:
                pass
        if hours:
            peak = max(hours, key=hours.get)
            self.target.activity_hours = {
                "distribution": hours,
                "peak_hour": peak
            }

    def _find_github_username(self):
        try:
            r = requests.get(
                f"https://api.github.com/search/users"
                f"?q={self.target.name}+type:user",
                headers=self.headers, timeout=10
            )
            if r.status_code == 200:
                items = r.json().get("items", [])
                if items:
                    return items[0]["login"]
        except:
            pass
        return None
