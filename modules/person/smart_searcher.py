import requests
import re
import time
from rich.console import Console

console = Console()

PLATFORM_URLS = {
    "GitHub": "https://api.github.com/users/{}",
    "GitLab": "https://gitlab.com/api/v4/users?username={}",
    "HackerNews": "https://hacker-news.firebaseio.com/v0/user/{}.json",
    "Reddit": "https://www.reddit.com/user/{}/about.json",
    "Stack Overflow": (
        "https://api.stackexchange.com/2.3/users"
        "?order=desc&sort=reputation&inname={}&site=stackoverflow"
    ),
    "Twitter": "https://twitter.com/{}",
    "Instagram": "https://www.instagram.com/{}/",
    "LinkedIn": "https://www.linkedin.com/in/{}",
    "TikTok": "https://www.tiktok.com/@{}",
    "Twitch": "https://www.twitch.tv/{}",
    "Steam": "https://steamcommunity.com/id/{}",
    "Spotify": "https://open.spotify.com/user/{}",
    "SoundCloud": "https://soundcloud.com/{}",
    "Behance": "https://www.behance.net/{}",
    "Dribbble": "https://dribbble.com/{}",
    "Medium": "https://medium.com/@{}",
    "Dev.to": "https://dev.to/{}",
}

NOT_FOUND_SIGNALS = {
    "Instagram": ["page not found", "this account doesn't exist"],
    "Twitter": ["this account doesn't exist", "page does not exist"],
    "TikTok": ["couldn't find this account"],
    "LinkedIn": ["page not found", "this profile doesn't exist"],
    "Twitch": ["sorry, unless you've been living"],
    "Steam": ["the specified profile could not be found"],
    "Medium": ["404", "page not found"],
    "Dev.to": ["404", "not found"],
    "Behance": ["404", "not found"],
    "Dribbble": ["404", "not found"],
    "SoundCloud": ["404", "not found"],
}

# URL propre à stocker dans social_profiles
CLEAN_URL = {
    "GitHub": "https://github.com/{}",
    "GitLab": "https://gitlab.com/{}",
    "Reddit": "https://www.reddit.com/u/{}",
    "TryHackMe": "https://tryhackme.com/p/{}",
}


class SmartSearcher:
    """
    Utilise la stratégie définie par TargetProfiler
    pour chercher sur les bonnes plateformes dans le bon ordre.
    """

    def __init__(self, target):
        self.target = target

    def run(self):
        strategy = getattr(self.target, "search_strategy", None)
        if not strategy:
            console.print("    [dim]Pas de stratégie définie — skip[/dim]")
            return

        profile_type = getattr(self.target, "profile_type", "regular")
        console.print(f"    [dim]Recherche ciblée ({profile_type})...[/dim]")

        # Requêtes DuckDuckGo adaptées au profil
        queries = getattr(self.target, "search_queries", [])
        for query in queries:
            if not query.strip():
                continue
            results = self._ddg_search(query)
            self._process_results(results)
            time.sleep(0.5)

        # Tester les pseudos suggérés sur les plateformes prioritaires
        suggested = getattr(self.target, "suggested_usernames", [])
        priority = strategy.get("primary_sources", [])

        if suggested and priority:
            console.print(
                f"    [dim]Test {len(suggested)} pseudos "
                f"sur sources prioritaires...[/dim]"
            )
            self._test_on_priority_platforms(suggested[:8], priority)

        # Sources spéciales selon le type
        self._run_special_sources(profile_type)

        found = len(self.target.social_profiles)
        console.print(f"    [cyan]{found} profils après recherche ciblée[/cyan]")

    def _test_on_priority_platforms(self, usernames: list, platforms: list):
        for username in usernames:
            for platform in platforms:
                if platform in self.target.social_profiles:
                    continue

                url_template = PLATFORM_URLS.get(platform)
                if not url_template:
                    continue

                url = url_template.format(username)

                try:
                    if self._verify_profile(platform, username, url):
                        clean_tpl = CLEAN_URL.get(platform, url_template)
                        self.target.social_profiles[platform] = (
                            clean_tpl.format(username)
                        )
                        console.print(
                            f"    [green]✓ {platform} ({username})[/green]"
                        )
                except Exception:
                    pass

                time.sleep(0.2)

    def _verify_profile(self, platform: str, username: str, url: str) -> bool:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36"
            )
        }

        if platform == "GitHub":
            r = requests.get(url, timeout=5)
            return r.status_code == 200

        if platform == "GitLab":
            r = requests.get(url, timeout=5)
            data = r.json() if r.status_code == 200 else []
            return bool(data) and any(
                u.get("username", "").lower() == username.lower()
                for u in data
            )

        if platform == "HackerNews":
            r = requests.get(url, timeout=5)
            return r.status_code == 200 and r.json() is not None

        if platform == "Reddit":
            r = requests.get(
                url,
                headers={"User-Agent": "KRONOS/1.0"},
                timeout=5
            )
            return (
                r.status_code == 200
                and r.json().get("data") is not None
            )

        if platform == "Stack Overflow":
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                return len(r.json().get("items", [])) > 0
            return False

        # Plateformes sans API — vérification contenu
        not_found = NOT_FOUND_SIGNALS.get(platform, [])

        r = requests.get(
            url, headers=headers, timeout=8, allow_redirects=True
        )

        if r.status_code == 404:
            return False
        if r.status_code != 200:
            return False
        if len(r.text) < 800:
            return False

        content_lower = r.text.lower()
        return not any(s in content_lower for s in not_found)

    def _run_special_sources(self, profile_type: str):
        username = self.target.username or ""
        name = self.target.name

        if profile_type == "developer":
            self._check_hackthebox(username)
            self._check_tryhackme(username)
            self._check_rootme(username)

        elif profile_type == "business":
            self._check_pappers(name)
            self._check_crunchbase(name)

        elif profile_type == "academic":
            self._check_google_scholar(name)
            self._check_researchgate(name)

        elif profile_type == "gamer":
            self._check_steam(username)

    def _check_hackthebox(self, username: str):
        if not username:
            return
        try:
            r = requests.get(
                f"https://www.hackthebox.com/api/v4/search/fetch"
                f"?query={username}&tags[]=user",
                timeout=8
            )
            if r.status_code == 200:
                for user in r.json().get("users", []):
                    if user.get("name", "").lower() == username.lower():
                        url = (
                            f"https://www.hackthebox.com"
                            f"/profile/{user['id']}"
                        )
                        self.target.social_profiles["HackTheBox"] = url
                        console.print(
                            f"    [green]✓ HackTheBox : {url}[/green]"
                        )
                        break
        except Exception:
            pass

    def _check_tryhackme(self, username: str):
        if not username:
            return
        try:
            r = requests.get(
                f"https://tryhackme.com/api/user/exist/{username}",
                timeout=8
            )
            if r.status_code == 200 and r.json().get("success"):
                url = f"https://tryhackme.com/p/{username}"
                self.target.social_profiles["TryHackMe"] = url
                console.print(f"    [green]✓ TryHackMe : {url}[/green]")
        except Exception:
            pass

    def _check_rootme(self, username: str):
        if not username:
            return
        try:
            url = f"https://www.root-me.org/{username}"
            r = requests.get(url, timeout=8)
            if r.status_code == 200 and "404" not in r.text[:500]:
                self.target.social_profiles["Root-Me"] = url
                console.print(f"    [green]✓ Root-Me : {url}[/green]")
        except Exception:
            pass

    def _check_pappers(self, name: str):
        try:
            for url in self._ddg_search(f'"{name}" site:pappers.fr'):
                if "pappers.fr" in url:
                    self.target.social_profiles["Pappers"] = url
                    console.print(f"    [green]✓ Pappers : {url}[/green]")
                    break
        except Exception:
            pass

    def _check_crunchbase(self, name: str):
        try:
            for url in self._ddg_search(f'"{name}" site:crunchbase.com'):
                if "crunchbase.com/person" in url:
                    self.target.social_profiles["Crunchbase"] = url
                    console.print(f"    [green]✓ Crunchbase : {url}[/green]")
                    break
        except Exception:
            pass

    def _check_google_scholar(self, name: str):
        try:
            for url in self._ddg_search(
                f'"{name}" site:scholar.google.com'
            ):
                if "scholar.google.com" in url:
                    self.target.social_profiles["Google Scholar"] = url
                    console.print(
                        f"    [green]✓ Google Scholar : {url}[/green]"
                    )
                    break
        except Exception:
            pass

    def _check_researchgate(self, name: str):
        try:
            clean = name.replace(" ", "_")
            url = f"https://www.researchgate.net/profile/{clean}"
            r = requests.get(url, timeout=8)
            if r.status_code == 200 and "not found" not in r.text.lower():
                self.target.social_profiles["ResearchGate"] = url
                console.print(f"    [green]✓ ResearchGate : {url}[/green]")
        except Exception:
            pass

    def _check_steam(self, username: str):
        if not username:
            return
        try:
            url = f"https://steamcommunity.com/id/{username}"
            r = requests.get(url, timeout=8)
            if (
                r.status_code == 200
                and "The specified profile" not in r.text
            ):
                self.target.social_profiles["Steam"] = url
                console.print(f"    [green]✓ Steam : {url}[/green]")
        except Exception:
            pass

    def _ddg_search(self, query: str) -> list:
        try:
            r = requests.get(
                "https://html.duckduckgo.com/html/",
                params={"q": query},
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0)"},
                timeout=10
            )
            urls = re.findall(r'href="(https?://[^"&]+)"', r.text)
            skip = ["duckduckgo.com", "w3.org", "schema.org", "google.com"]
            return [u for u in urls[:15] if not any(s in u for s in skip)]
        except Exception:
            return []

    def _process_results(self, results: list):
        platform_patterns = {
            "linkedin.com/in/": "LinkedIn",
            "twitter.com/": "Twitter/X",
            "x.com/": "Twitter/X",
            "instagram.com/": "Instagram",
            "github.com/": "GitHub",
            "t.me/": "Telegram",
            "tiktok.com/@": "TikTok",
            "youtube.com/": "YouTube",
            "discord.com/": "Discord",
        }

        for url in results:
            for pattern, platform in platform_patterns.items():
                if pattern in url and platform not in self.target.social_profiles:
                    self.target.social_profiles[platform] = url
                    console.print(
                        f"    [green]✓ {platform} (via recherche) : {url}[/green]"
                    )
