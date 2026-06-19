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
            console.print("    [dim]Aucun email a verifier[/dim]")
            return

        for email in emails:
            console.print(f"    [dim]Verif : {email}[/dim]")

            if self.hibp_key:
                self.target.breaches.extend(self._check_hibp(email))

            lc = self._check_leakcheck(email)
            if lc:
                self.target.breaches.extend(lc)

            sc = self._check_scylla(email)
            if sc:
                self.target.breaches.extend(sc)

            bd = self._check_breachdirectory(email)
            if bd:
                self.target.breaches.extend(bd)

        total = len(self.target.breaches)
        if total:
            console.print(f"    [red]{total} fuite(s) detectee(s)[/red]")
            for b in self.target.breaches[:5]:
                console.print(
                    f"    [dim]-> {b.get('Name', '?')} ({b.get('source', '?')})[/dim]"
                )
        else:
            console.print("    [green]Aucune fuite detectee[/green]")

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
                f"https://scylla.sh/search?q={email}&size=5",
                headers={"User-Agent": "KRONOS-OSINT/2.0"},
                timeout=10
            )
            if r.status_code == 200:
                data = r.json()
                results = []
                for item in data[:5]:
                    src = item.get("_source", {})
                    entry = {
                        "Name": src.get("database_name", "") or "Scylla",
                        "source": "Scylla.sh",
                        "email": email,
                        "date": src.get("created", ""),
                    }
                    password = src.get("password", "")
                    if password:
                        entry["password"] = password
                        console.print(
                            f"    [red]Scylla - password expose trouve ![/red]"
                        )
                    hash_val = src.get("hash", "") or src.get("password_hash", "")
                    if hash_val:
                        entry["hash"] = hash_val
                    database = src.get("database_name", "")
                    if database:
                        entry["database"] = database
                    results.append(entry)

                if results:
                    console.print(
                        f"    [red]Scylla : {len(results)} entree(s)[/red]"
                    )
                return results
        except Exception as e:
            console.print(f"    [dim]Scylla : {e}[/dim]")
        return []

    def _check_breachdirectory(self, email: str) -> list:
        api_key = os.getenv("BREACHDIRECTORY_API_KEY", "")
        if not api_key:
            return []

        try:
            r = requests.get(
                "https://breachdirectory.p.rapidapi.com/",
                params={"func": "auto", "term": email},
                headers={
                    "X-RapidAPI-Key": api_key,
                    "X-RapidAPI-Host": "breachdirectory.p.rapidapi.com"
                },
                timeout=10
            )
            if r.status_code == 200:
                data = r.json()
                if not data.get("success"):
                    return []

                results = []
                for item in data.get("result", [])[:10]:
                    entry = {
                        "Name": (item.get("sources", ["BreachDir"])[0]
                                 if item.get("sources") else "BreachDirectory"),
                        "source": "BreachDirectory",
                        "email": email,
                    }
                    pwd = item.get("password", "")
                    if pwd and pwd != "N/A":
                        entry["password"] = pwd
                        console.print(
                            f"    [red]BreachDirectory - password en clair : "
                            f"{pwd[:3]}***[/red]"
                        )
                    h = item.get("sha1", "")
                    if h:
                        entry["hash"] = h
                        entry["hash_type"] = "SHA1"
                    results.append(entry)

                if results:
                    console.print(
                        f"    [red]BreachDirectory : {len(results)} credential(s)[/red]"
                    )
                return results
        except Exception as e:
            console.print(f"    [dim]BreachDirectory : {e}[/dim]")
        return []
