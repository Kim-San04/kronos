import os
import re
import requests
import subprocess
from rich.console import Console

console = Console()

SOCIAL_PATTERNS = {
    r'https?://t\.me/[\w]+': "Telegram",
    r'https?://twitter\.com/[\w]+': "Twitter",
    r'https?://instagram\.com/[\w.]+': "Instagram",
    r'https?://linkedin\.com/in/[\w-]+': "LinkedIn",
    r'https?://github\.com/[\w-]+': "GitHub",
    r'https?://tiktok\.com/@[\w.]+': "TikTok",
    r'https?://youtube\.com/[\w@/-]+': "YouTube",
    r'https?://discord\.gg/[\w]+': "Discord",
}

README_PLATFORMS = {
    "instagram.com": "Instagram",
    "twitter.com": "Twitter",
    "t.me/": "Telegram",
    "tiktok.com": "TikTok",
    "linkedin.com": "LinkedIn",
    "youtube.com": "YouTube",
    "discord.gg": "Discord",
}

SKIP_EMAIL_DOMAINS = [
    "example.com", "w3.org", "schema.org",
    "sentry.io", "githubusercontent.com",
]


class RecursivePivot:
    """
    Chaque découverte devient une nouvelle ancre.

    Email trouvé → Holehe
    Profil GitHub trouvé → lire bio, README, Twitter
    Tout profil → extraire liens sociaux et emails
    """

    def __init__(self, target):
        self.target = target
        self._already_pivoted = set()

    def run(self):
        console.print("    [dim]Pivot recursif...[/dim]")

        max_iterations = 3
        iteration = 0

        while iteration < max_iterations:
            iteration += 1
            new_found = 0

            for email in self.target.emails_found[:5]:
                key = f"email:{email}"
                if key not in self._already_pivoted:
                    self._already_pivoted.add(key)
                    new_found += self._pivot_from_email(email)

            for platform, url in list(
                self.target.social_profiles.items()
            )[:15]:
                key = f"profile:{url}"
                if key not in self._already_pivoted:
                    self._already_pivoted.add(key)
                    new_found += self._pivot_from_profile(platform, url)

            if new_found == 0:
                break

            console.print(
                f"    [cyan]Iteration {iteration} : "
                f"{new_found} nouvelle(s) decouverte(s)[/cyan]"
            )

            from modules.person.deep_crawler import DeepCrawler
            DeepCrawler(self.target).run()

        total = len(self.target.social_profiles)
        console.print(
            f"    [bold cyan]{total} comptes apres pivot recursif[/bold cyan]"
        )

    def _pivot_from_email(self, email: str) -> int:
        new_found = 0

        try:
            result = subprocess.run(
                ["holehe", email, "--only-used", "--no-color"],
                capture_output=True,
                text=True,
                timeout=60
            )
            for line in result.stdout.splitlines():
                if "[+]" in line or "✔" in line:
                    parts = line.strip().split()
                    if parts:
                        site = parts[-1].strip()
                        key = f"Holehe_{site}"
                        if key not in self.target.social_profiles:
                            self.target.social_profiles[key] = (
                                f"{email} utilisé sur {site}"
                            )
                            console.print(
                                f"    [green]✓ {site} via {email}[/green]"
                            )
                            new_found += 1
        except Exception:
            pass

        return new_found

    def _pivot_from_profile(self, platform: str, url: str) -> int:
        new_found = 0

        try:
            if "github.com" in url:
                return self._read_github_bio(url)

            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36"
                )
            }
            r = requests.get(
                url, headers=headers, timeout=8, allow_redirects=True
            )
            if r.status_code != 200:
                return 0

            # Liens vers d'autres profils sociaux
            for pattern, found_platform in SOCIAL_PATTERNS.items():
                for match in re.findall(pattern, r.text):
                    if found_platform not in self.target.social_profiles:
                        self.target.social_profiles[found_platform] = match
                        console.print(
                            f"    [green]✓ {found_platform} "
                            f"depuis {platform} : {match}[/green]"
                        )
                        new_found += 1

            # Emails dans la page
            for email in re.findall(
                r'[\w\.-]+@[\w\.-]+\.\w{2,}', r.text
            ):
                if (
                    email not in self.target.emails_found
                    and not any(d in email for d in SKIP_EMAIL_DOMAINS)
                ):
                    self.target.emails_found.append(email)
                    console.print(
                        f"    [green]Email depuis {platform} : {email}[/green]"
                    )
                    new_found += 1

        except Exception:
            pass

        return new_found

    def _read_github_bio(self, github_url: str) -> int:
        new_found = 0

        try:
            username = github_url.rstrip("/").split("/")[-1]
            token = os.getenv("GITHUB_TOKEN")
            headers = {}
            if token:
                headers["Authorization"] = f"token {token}"

            r = requests.get(
                f"https://api.github.com/users/{username}",
                headers=headers,
                timeout=8
            )
            if r.status_code != 200:
                return 0

            data = r.json()

            # Twitter dans le profil GitHub
            twitter = data.get("twitter_username")
            if twitter and "Twitter" not in self.target.social_profiles:
                self.target.social_profiles["Twitter"] = (
                    f"https://twitter.com/{twitter}"
                )
                console.print(
                    f"    [green]Twitter depuis GitHub : @{twitter}[/green]"
                )
                new_found += 1

            # Site personnel / blog
            blog = data.get("blog", "")
            if blog and blog.startswith("http"):
                self.target.social_profiles["Site personnel"] = blog
                console.print(f"    [green]Site web : {blog}[/green]")
                new_found += 1

            # Email public (déjà validé par github_person,
            # ici c'est depuis le pivot donc on accepte)
            email = data.get("email")
            if email and email not in self.target.emails_found:
                self.target.emails_found.append(email)
                console.print(
                    f"    [green]Email GitHub : {email}[/green]"
                )
                new_found += 1

            # Localisation
            location = data.get("location")
            if location:
                existing = [l.get("location") for l in self.target.locations]
                if location not in existing:
                    self.target.locations.append({
                        "source": "GitHub",
                        "location": location
                    })
                    console.print(
                        f"    [cyan]Localisation : {location}[/cyan]"
                    )

            # README du profil
            for branch in ["main", "master"]:
                try:
                    r2 = requests.get(
                        f"https://raw.githubusercontent.com"
                        f"/{username}/{username}/{branch}/README.md",
                        headers=headers,
                        timeout=5
                    )
                    if r2.status_code == 200:
                        for url in re.findall(
                            r'https?://[^\s\)\]\"\'<>]+', r2.text
                        ):
                            for domain, pname in README_PLATFORMS.items():
                                if (
                                    domain in url
                                    and pname not in self.target.social_profiles
                                ):
                                    self.target.social_profiles[pname] = url
                                    console.print(
                                        f"    [green]{pname} dans README : "
                                        f"{url}[/green]"
                                    )
                                    new_found += 1
                        break
                except Exception:
                    pass

        except Exception:
            pass

        return new_found
