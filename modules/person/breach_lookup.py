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
        emails.extend([
            e for e in self.target.emails_found
            if e not in emails
        ][:5])

        if not emails:
            console.print("    [dim]Aucun email à vérifier[/dim]")
            return

        for email in emails:
            console.print(f"    [dim]Vérification : {email}[/dim]")

            if self.hibp_key:
                breaches = self._check_hibp(email)
                if breaches:
                    self.target.breaches.extend(breaches)

            leaks = self._check_leakcheck(email)
            if leaks:
                self.target.breaches.extend(leaks)

            scylla = self._check_scylla(email)
            if scylla:
                self.target.breaches.extend(scylla)

        total = len(self.target.breaches)
        if total:
            console.print(
                f"    [red]⚠ {total} fuite(s) détectée(s)[/red]"
            )
            for b in self.target.breaches[:5]:
                console.print(
                    f"    [dim]→ {b.get('Name', '?')} "
                    f"({b.get('source', '?')})[/dim]"
                )
        else:
            console.print("    [green]Aucune fuite détectée[/green]")

    def _check_hibp(self, email: str) -> list:
        try:
            r = requests.get(
                f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}",
                headers={
                    "hibp-api-key": self.hibp_key,
                    "User-Agent": "KRONOS-OSINT"
                },
                timeout=10
            )
            if r.status_code == 200:
                return [{**b, "source": "HIBP"} for b in r.json()]
        except Exception:
            pass
        return []

    def _check_leakcheck(self, email: str) -> list:
        try:
            r = requests.get(
                f"https://leakcheck.io/api/public?check={email}",
                timeout=10
            )
            if r.status_code == 200:
                data = r.json()
                if data.get("success") and data.get("found"):
                    return [
                        {
                            "Name": src,
                            "source": "LeakCheck",
                            "email": email,
                        }
                        for src in data.get("sources", [])
                    ]
        except Exception:
            pass
        return []

    def _check_scylla(self, email: str) -> list:
        try:
            r = requests.get(
                f"https://scylla.sh/search?q={email}",
                headers={"User-Agent": "KRONOS-OSINT/1.0"},
                timeout=10
            )
            if r.status_code == 200:
                data = r.json()
                if data and len(data) > 0:
                    return [{
                        "Name": "Scylla Database",
                        "source": "Scylla",
                        "email": email,
                        "count": len(data),
                    }]
        except Exception:
            pass
        return []
