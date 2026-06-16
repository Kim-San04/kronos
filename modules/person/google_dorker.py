import requests
import re
from rich.console import Console

console = Console()

class GoogleDorker:
    """
    Cherche des infos via Google Dorking sur DuckDuckGo.
    Trouve LinkedIn, profils, mentions, images.
    """

    def __init__(self, target):
        self.target = target

    def run(self):
        name = self.target.name
        console.print(f"    [dim]Google Dorking : '{name}'...[/dim]")

        dorks = [
            f'"{name}" site:linkedin.com',
            f'"{name}" site:twitter.com',
            f'"{name}" email OR mail OR contact',
            f'"{name}" site:github.com',
            f'"{name}" téléphone OR phone OR tel',
            f'"{name}" filetype:pdf',
        ]

        results = []
        for dork in dorks:
            hits = self._search(dork)
            results.extend(hits)
            if hits:
                console.print(
                    f"    [cyan]Dork : {dork[:55]}...[/cyan]"
                )
                for hit in hits[:2]:
                    console.print(
                        f"    [dim]→ {hit['url'][:70]}[/dim]"
                    )

        self._analyze_results(results)

        self.target.correlations.append(
            f"Google Dorks : {len(results)} résultats pour '{name}'"
        )

    def _search(self, query: str) -> list:
        try:
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36"
                )
            }
            r = requests.get(
                "https://html.duckduckgo.com/html/",
                params={"q": query},
                headers=headers,
                timeout=10
            )

            urls = re.findall(r'href="(https?://[^"&]+)"', r.text)

            skip = ["duckduckgo.com", "w3.org", "schema.org"]
            results = []
            for url in urls[:10]:
                if not any(s in url for s in skip):
                    results.append({"url": url, "query": query})

            return results[:5]

        except Exception:
            return []

    def _analyze_results(self, results: list):
        for r in results:
            url = r["url"]

            if "linkedin.com/in/" in url:
                if "LinkedIn" not in self.target.social_profiles:
                    self.target.social_profiles["LinkedIn"] = url
                    console.print(
                        f"    [green]LinkedIn : {url}[/green]"
                    )

            elif "twitter.com/" in url or "x.com/" in url:
                if "Twitter" not in self.target.social_profiles:
                    self.target.social_profiles["Twitter"] = url

            elif "github.com/" in url and "/issues/" not in url:
                if "GitHub_Dork" not in self.target.social_profiles:
                    self.target.social_profiles["GitHub_Dork"] = url
