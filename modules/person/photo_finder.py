import requests
import re
from rich.console import Console

console = Console()

class PhotoFinder:
    """
    Trouve des photos de la cible et génère des liens
    de recherche inversée d'image.
    """

    def __init__(self, target):
        self.target = target

    def run(self):
        name = self.target.name
        console.print("    [dim]Recherche de photos...[/dim]")

        search_urls = {
            "Google Images": (
                f"https://www.google.com/search?"
                f"q={name.replace(' ', '+')}&tbm=isch"
            ),
            "Yandex Images": (
                f"https://yandex.com/images/search?"
                f"text={name.replace(' ', '+')}"
            ),
            "Bing Images": (
                f"https://www.bing.com/images/search?"
                f"q={name.replace(' ', '+')}"
            ),
        }

        photo_sources = []

        # Avatar GitHub si disponible
        username = self.target.github_data.get("username", "")
        if username:
            avatar_url = (
                f"https://avatars.githubusercontent.com/{username}"
            )
            photo_sources.append({
                "source": "GitHub Avatar",
                "url": avatar_url
            })
            console.print(
                f"    [green]Photo GitHub : {avatar_url}[/green]"
            )

        for engine, url in search_urls.items():
            photo_sources.append({
                "source": engine,
                "url": url,
                "type": "search_link"
            })

        self.target.correlations.append(
            "Recherche photos : " + " | ".join(search_urls.keys())
        )

        console.print(
            f"    [cyan]{len(photo_sources)} source(s) photo identifiée(s)[/cyan]"
        )
        for p in photo_sources[:3]:
            console.print(
                f"    [dim]→ {p['source']} : {p['url'][:60]}[/dim]"
            )
