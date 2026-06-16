import requests
from rich.console import Console

console = Console()

class DarkwebMonitor:
    def __init__(self, target):
        self.target = target

    def run(self):
        domain = self.target.domain

        self._check_dehashed(domain)
        self._check_intelligencex(domain)

        if self.target.darkweb_mentions:
            console.print(
                f"    [red]⚠ {len(self.target.darkweb_mentions)} "
                f"mention(s) darkweb[/red]"
            )
        else:
            console.print("    [green]Aucune mention darkweb trouvée[/green]")

    def _check_dehashed(self, domain):
        # Nécessite un compte DeHashed
        pass

    def _check_intelligencex(self, domain):
        # Nécessite une clé API IntelX
        pass
