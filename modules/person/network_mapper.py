import requests
import os
from rich.console import Console

console = Console()

class NetworkMapper:
    def __init__(self, target):
        self.target = target
        self.token = os.getenv("GITHUB_TOKEN")
        self.headers = {}
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"

    def _add_connection(self, conn: dict):
        username = conn.get("username", "")
        platform = conn.get("platform", "")
        existing = [
            (c.get("username"), c.get("platform"))
            for c in self.target.connections
        ]
        if (username, platform) not in existing:
            self.target.connections.append(conn)

    def run(self):
        username = self.target.github_data.get("username")
        if not username:
            return

        followers = self._get_followers(username)
        for f in followers[:10]:
            self._add_connection({
                "platform": "GitHub",
                "type": "follower",
                "username": f.get("login"),
                "url": f.get("html_url")
            })

        console.print(
            f"    [cyan]{len(followers)} connexions GitHub identifiees[/cyan]"
        )

    def _get_followers(self, username):
        try:
            r = requests.get(
                f"https://api.github.com/users/{username}/followers?per_page=30",
                headers=self.headers, timeout=10
            )
            return r.json() if r.status_code == 200 else []
        except:
            return []
