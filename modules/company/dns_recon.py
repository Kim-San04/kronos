import socket
import requests
from rich.console import Console

console = Console()

class DnsRecon:
    def __init__(self, target):
        self.target = target

    def run(self):
        domain = self.target.domain

        try:
            ip = socket.gethostbyname(domain)
            if ip not in self.target.ips:
                self.target.ips.append(ip)
            console.print(f"    [cyan]IP : {ip}[/cyan]")
        except:
            pass

        self._get_dns_records(domain)
        self._whois(domain)
        self._enumerate_subdomains(domain)

    def _get_dns_records(self, domain):
        try:
            import dns.resolver
            record_types = ["A", "MX", "NS", "TXT", "CNAME", "SOA"]
            records = {}
            for rtype in record_types:
                try:
                    answers = dns.resolver.resolve(domain, rtype)
                    records[rtype] = [str(r) for r in answers]
                except:
                    pass
            self.target.dns_records = records
            console.print(
                f"    [cyan]{len(records)} types de records DNS[/cyan]"
            )
        except:
            pass

    def _whois(self, domain):
        try:
            r = requests.get(
                f"https://rdap.org/domain/{domain}",
                timeout=10
            )
            if r.status_code == 200:
                console.print("    [cyan]WHOIS récupéré[/cyan]")
        except:
            pass

    def _enumerate_subdomains(self, domain):
        COMMON_SUBS = [
            "www", "mail", "admin", "api", "dev",
            "staging", "test", "vpn", "ftp", "ssh",
            "portal", "app", "blog", "shop", "cdn",
            "static", "assets", "images", "media",
            "internal", "intranet", "remote", "git",
            "gitlab", "jenkins", "jira", "confluence",
        ]
        found = []
        for sub in COMMON_SUBS:
            subdomain = f"{sub}.{domain}"
            try:
                socket.gethostbyname(subdomain)
                found.append(subdomain)
                console.print(
                    f"    [green]Sous-domaine : {subdomain}[/green]"
                )
            except:
                pass

        self.target.subdomains.extend(found)
