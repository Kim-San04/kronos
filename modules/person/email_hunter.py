import os
import re
import requests
import smtplib
import socket
from rich.console import Console

console = Console()

class EmailHunter:
    def __init__(self, target):
        self.target = target
        self.hunter_key = os.getenv("HUNTER_API_KEY")

    def run(self):
        name = self.target.name
        parts = name.lower().split()
        if len(parts) < 2:
            return

        first, last = parts[0], parts[-1]

        patterns = [
            f"{first}.{last}",
            f"{first[0]}{last}",
            f"{first}_{last}",
            f"{first}",
            f"{last}",
            f"{first}{last}",
            f"{last}.{first}",
            f"{first[0]}.{last}",
        ]

        domains = [
            "gmail.com", "yahoo.fr", "outlook.com",
            "hotmail.com", "protonmail.com", "icloud.com",
        ]

        if self.hunter_key and hasattr(self.target, "domain"):
            self._hunter_search()

        found = []
        for domain in domains[:3]:
            for pattern in patterns[:4]:
                email = f"{pattern}@{domain}"
                if self._verify_smtp(email):
                    found.append(email)
                    console.print(
                        f"    [green]Email trouvé : {email}[/green]"
                    )

        self.target.emails_found.extend(found)

    def _verify_smtp(self, email: str) -> bool:
        domain = email.split("@")[1]
        try:
            mx = self._get_mx(domain)
            if not mx:
                return False
            server = smtplib.SMTP(timeout=5)
            server.connect(mx)
            server.helo("check.com")
            server.mail("test@check.com")
            code, _ = server.rcpt(email)
            server.quit()
            return code == 250
        except:
            return False

    def _get_mx(self, domain: str) -> str:
        try:
            import dns.resolver
            mx = dns.resolver.resolve(domain, "MX")
            return str(mx[0].exchange)
        except:
            return ""

    def _hunter_search(self):
        try:
            r = requests.get(
                "https://api.hunter.io/v2/email-finder",
                params={
                    "domain": self.target.domain,
                    "first_name": self.target.name.split()[0],
                    "last_name": self.target.name.split()[-1],
                    "api_key": self.hunter_key
                },
                timeout=10
            )
            data = r.json()
            if data.get("data", {}).get("email"):
                email = data["data"]["email"]
                self.target.emails_found.append(email)
        except:
            pass
