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
                    f"    [red]⚠ {email} — "
                    f"{total} fuite(s) détectée(s)[/red]"
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

    def _check_leakcheck(self, email: str) -> list:
        try:
            r = requests.get(
                f"https://leakcheck.io/api/public?check={email}",
                timeout=10
            )
            if r.status_code == 200:
                data = r.json()
                if data.get("success") and data.get("found"):
                    return [{
                        "Name": src,
                        "source": "LeakCheck",
                        "email": email
                    } for src in data.get("sources", [])]
        except:
            pass
        return []

    def _check_scylla(self, email: str) -> list:
        try:
            r = requests.get(
                f"https://scylla.sh/search?q={email}",
                headers={"User-Agent": "KRONOS-OSINT"},
                timeout=10
            )
            if r.status_code == 200:
                data = r.json()
                if data:
                    return [{
                        "Name": "Scylla Database",
                        "source": "Scylla",
                        "email": email,
                        "count": len(data)
                    }]
        except:
            pass
        return []
