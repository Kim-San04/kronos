import requests
import time
from rich.console import Console

console = Console()

PLATFORMS = {
    "GitHub": "https://github.com/{}",
    "Twitter": "https://twitter.com/{}",
    "Instagram": "https://www.instagram.com/{}",
    "LinkedIn": "https://www.linkedin.com/in/{}",
    "Reddit": "https://www.reddit.com/user/{}",
    "TikTok": "https://www.tiktok.com/@{}",
    "YouTube": "https://www.youtube.com/@{}",
    "Twitch": "https://www.twitch.tv/{}",
    "Pinterest": "https://www.pinterest.com/{}",
    "Snapchat": "https://www.snapchat.com/add/{}",
    "HackerNews": "https://news.ycombinator.com/user?id={}",
    "ProductHunt": "https://www.producthunt.com/@{}",
    "Medium": "https://medium.com/@{}",
    "Dev.to": "https://dev.to/{}",
    "Keybase": "https://keybase.io/{}",
    "GitLab": "https://gitlab.com/{}",
    "Bitbucket": "https://bitbucket.org/{}",
    "Steam": "https://steamcommunity.com/id/{}",
    "Spotify": "https://open.spotify.com/user/{}",
    "SoundCloud": "https://soundcloud.com/{}",
    "Behance": "https://www.behance.net/{}",
    "Dribbble": "https://dribbble.com/{}",
    "Fiverr": "https://www.fiverr.com/{}",
    "Etsy": "https://www.etsy.com/shop/{}",
    "Patreon": "https://www.patreon.com/{}",
    "Ko-fi": "https://ko-fi.com/{}",
    "DockerHub": "https://hub.docker.com/u/{}",
    "npm": "https://www.npmjs.com/~{}",
    "PyPI": "https://pypi.org/user/{}",
    "StackOverflow": "https://stackoverflow.com/users/{}",
}

class SocialScanner:
    def __init__(self, target):
        self.target = target

    def run(self):
        username = self.target.username or self._guess_username()
        if not username:
            return

        console.print(f"    [dim]Username testé : {username}[/dim]")

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36"
            )
        }

        found = 0
        for platform, url_template in PLATFORMS.items():
            url = url_template.format(username)
            try:
                r = requests.get(
                    url, headers=headers,
                    timeout=5, allow_redirects=True
                )
                if r.status_code == 200:
                    self.target.social_profiles[platform] = url
                    found += 1
                    console.print(
                        f"    [green]✓ {platform}[/green] — {url}"
                    )
            except:
                pass
            time.sleep(0.1)

        console.print(f"    [cyan]{found} profils trouvés[/cyan]")

    def _guess_username(self) -> str:
        name = self.target.name.lower()
        parts = name.split()
        if len(parts) >= 2:
            return f"{parts[0]}{parts[-1]}"
        return parts[0] if parts else ""
