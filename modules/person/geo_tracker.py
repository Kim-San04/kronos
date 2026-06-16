import requests
from rich.console import Console

console = Console()

class GeoTracker:
    def __init__(self, target):
        self.target = target

    def run(self):
        for platform, url in self.target.social_profiles.items():
            location = self._extract_location(platform, url)
            if location:
                self.target.locations.append({
                    "source": platform,
                    "location": location
                })
                console.print(
                    f"    [cyan]Localisation ({platform}) : {location}[/cyan]"
                )

        profile = self.target.github_data.get("profile", {})
        if profile.get("location"):
            self.target.locations.append({
                "source": "GitHub",
                "location": profile["location"]
            })
            console.print(
                f"    [cyan]Localisation GitHub : {profile['location']}[/cyan]"
            )

    def _extract_location(self, platform, url):
        return None
