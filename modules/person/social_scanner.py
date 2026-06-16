import time
import requests
from rich.console import Console

console = Console()

PLATFORMS = {
    "Twitter": {
        "url": "https://twitter.com/{}",
        "not_found": [
            "this account doesn't exist",
            "page does not exist",
            "sorry, that page doesn't exist",
        ],
    },
    "Instagram": {
        "url": "https://www.instagram.com/{}/",
        "not_found": [
            "page not found",
            "sorry, this page",
            "isn't available",
        ],
    },
    "TikTok": {
        "url": "https://www.tiktok.com/@{}",
        "not_found": [
            "couldn't find this account",
            "no videos yet",
        ],
    },
    "YouTube": {
        "url": "https://www.youtube.com/@{}",
        "not_found": [
            "this page isn't available",
            "404",
        ],
    },
    "LinkedIn": {
        "url": "https://www.linkedin.com/in/{}",
        "not_found": [
            "page not found",
            "this profile doesn't exist",
            "sign in",
        ],
    },
    "Pinterest": {
        "url": "https://www.pinterest.com/{}/",
        "not_found": [
            "sorry! we couldn't find that page",
            "404",
        ],
    },
    "Twitch": {
        "url": "https://www.twitch.tv/{}",
        "not_found": [
            "sorry. unless you've been",
            "404",
        ],
    },
    "Medium": {
        "url": "https://medium.com/@{}",
        "not_found": ["404", "page not found"],
    },
    "Dev.to": {
        "url": "https://dev.to/{}",
        "not_found": ["404", "not found"],
    },
    "Behance": {
        "url": "https://www.behance.net/{}",
        "not_found": ["404", "not found"],
    },
    "Dribbble": {
        "url": "https://dribbble.com/{}",
        "not_found": ["404", "not found"],
    },
    "SoundCloud": {
        "url": "https://soundcloud.com/{}",
        "not_found": ["404", "not found"],
    },
    "Steam": {
        "url": "https://steamcommunity.com/id/{}",
        "not_found": [
            "the specified profile could not be found",
            "error",
        ],
    },
    "Patreon": {
        "url": "https://www.patreon.com/{}",
        "not_found": ["404", "not found"],
    },
}

class SocialScanner:
    def __init__(self, target):
        self.target = target

    def run(self):
        usernames = self._get_usernames_to_test()

        console.print(
            f"    [dim]Test sur {len(PLATFORMS)} plateformes...[/dim]"
        )

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
            )
        }

        for username in usernames[:3]:
            for platform, config in PLATFORMS.items():
                if platform in self.target.social_profiles:
                    continue

                url = config["url"].format(username)
                try:
                    r = requests.get(
                        url, headers=headers,
                        timeout=8, allow_redirects=True
                    )

                    if r.status_code == 404:
                        continue
                    if r.status_code != 200:
                        continue

                    content = r.text.lower()
                    not_found = any(
                        nf.lower() in content
                        for nf in config.get("not_found", [])
                    )
                    if not_found:
                        continue

                    if len(r.text) < 800:
                        continue

                    self.target.social_profiles[platform] = url
                    console.print(
                        f"    [green]✓ {platform} : {url}[/green]"
                    )

                except Exception:
                    pass

                time.sleep(0.3)

        total = len(self.target.social_profiles)
        console.print(f"    [cyan]{total} profils confirmés[/cyan]")

    def _get_usernames_to_test(self) -> list:
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
                ]
            else:
                base = [name[0]]

        base.extend(self.target.usernames_found[:3])
        return list(dict.fromkeys(base))
