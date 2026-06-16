import requests
from rich.console import Console

console = Console()

class SSLCerts:
    def __init__(self, target):
        self.target = target

    def run(self):
        domain = self.target.domain
        subdomains = self._crtsh(domain)

        new = [s for s in subdomains if s not in self.target.subdomains]
        self.target.subdomains.extend(new)
        self.target.ssl_certs = [{"subdomain": s} for s in subdomains]

        console.print(
            f"    [cyan]{len(subdomains)} sous-domaines via certificats SSL[/cyan]"
        )

    def _crtsh(self, domain: str) -> list:
        try:
            r = requests.get(
                f"https://crt.sh/?q=%.{domain}&output=json",
                timeout=15
            )
            if r.status_code == 200:
                data = r.json()
                subs = set()
                for cert in data:
                    name = cert.get("name_value", "")
                    for sub in name.split("\n"):
                        sub = sub.strip().lstrip("*.")
                        if (sub and domain in sub and
                                not sub.startswith(".")):
                            subs.add(sub)
                return list(subs)
        except:
            pass
        return []
