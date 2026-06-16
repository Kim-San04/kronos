import os
import requests
from rich.console import Console

console = Console()

class GitHubOrg:
    def __init__(self, target):
        self.target = target
        self.token = os.getenv("GITHUB_TOKEN")
        self.headers = {}
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"

    def run(self):
        org = self.target.org or self.target.domain.split(".")[0]

        try:
            r = requests.get(
                f"https://api.github.com/orgs/{org}/members?per_page=50",
                headers=self.headers, timeout=10
            )
            if r.status_code == 200:
                members = r.json()
                for member in members:
                    email = self._get_email(member["login"])
                    employee = {
                        "username": member["login"],
                        "github_url": member["html_url"],
                        "email": email,
                        "source": "GitHub"
                    }
                    self.target.employees.append(employee)
                    if email:
                        self.target.emails.append(email)

                console.print(
                    f"    [cyan]{len(members)} membres GitHub org[/cyan]"
                )
        except Exception as e:
            console.print(f"    [dim]GitHub Org : {e}[/dim]")

    def _get_email(self, username):
        try:
            r = requests.get(
                f"https://api.github.com/users/{username}",
                headers=self.headers, timeout=5
            )
            if r.status_code == 200:
                return r.json().get("email")
        except:
            pass
        return None
