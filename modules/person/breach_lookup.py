import os
import requests
from rich.console import Console

console = Console()

class BreachLookup:
    def __init__(self, target):
        self.target = target
        self.hibp_key = os.getenv("HIBP_API_KEY")

    def run(self):
        emails = []
        if self.target.email:
            emails.append(self.target.email)
        emails.extend(self.target.emails_found[:3])

        for email in emails:
            breaches = self._check_hibp(email)
            if breaches:
                self.target.breaches.extend(breaches)
                console.print(
                    f"    [red]⚠ {email} trouvé "
                    f"dans {len(breaches)} fuite(s)[/red]"
                )
                for b in breaches[:3]:
                    console.print(
                        f"      [dim]→ {b.get('Name')} "
                        f"({b.get('BreachDate', '')[:4]})[/dim]"
                    )

    def _check_hibp(self, email: str) -> list:
        if not self.hibp_key:
            return []
        try:
            r = requests.get(
                f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}",
                headers={
                    "hibp-api-key": self.hibp_key,
                    "User-Agent": "KRONOS-OSINT"
                },
                timeout=10
            )
            return r.json() if r.status_code == 200 else []
        except:
            return []
