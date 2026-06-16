import requests
from rich.console import Console

console = Console()

class EmployeeFinder:
    def __init__(self, target):
        self.target = target

    def run(self):
        patterns = self._detect_email_pattern()

        if patterns:
            console.print(
                f"    [cyan]Pattern email détecté : {patterns[0]}[/cyan]"
            )
            self.target.employees.append({
                "pattern": patterns[0],
                "source": "pattern_detection"
            })

        console.print(
            f"    [cyan]{len(self.target.employees)} employés identifiés[/cyan]"
        )

    def _detect_email_pattern(self):
        patterns = []
        domain = self.target.domain

        if self.target.emails:
            email = self.target.emails[0]
            local = email.split("@")[0]
            if "." in local:
                patterns.append("{first}.{last}@" + domain)
            elif "_" in local:
                patterns.append("{first}_{last}@" + domain)
            else:
                patterns.append("{first}{last}@" + domain)

        return patterns
