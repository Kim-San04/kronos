import os
from rich.console import Console

console = Console()

class ShodanScan:
    def __init__(self, target):
        self.target = target
        self.api_key = os.getenv("SHODAN_API_KEY")

    def run(self):
        if not self.api_key:
            console.print("    [dim]Shodan : clé API manquante[/dim]")
            return

        try:
            import shodan
            api = shodan.Shodan(self.api_key)
            domain = self.target.domain

            results = api.search(f"hostname:{domain}")

            for result in results.get("matches", []):
                ip = result.get("ip_str")
                if ip and ip not in self.target.ips:
                    self.target.ips.append(ip)

                port = result.get("port")
                if port and port not in self.target.open_ports:
                    self.target.open_ports.append(port)

                vulns = result.get("vulns", {})
                for cve in vulns.keys():
                    if cve not in self.target.cves:
                        self.target.cves.append(cve)
                        console.print(f"    [red]CVE : {cve}[/red]")

                product = result.get("product", "")
                if product and product not in self.target.technologies:
                    self.target.technologies.append(product)

            console.print(
                f"    [cyan]{len(self.target.ips)} IPs, "
                f"{len(self.target.open_ports)} ports, "
                f"{len(self.target.cves)} CVEs[/cyan]"
            )

        except Exception as e:
            console.print(f"    [dim]Shodan erreur : {e}[/dim]")
