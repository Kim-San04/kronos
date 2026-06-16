from rich.console import Console

console = Console()

class Correlator:
    def __init__(self, target):
        self.target = target

    def run(self):
        findings = []

        # Email présent dans fuites et profils sociaux
        if hasattr(self.target, "emails_found") and hasattr(self.target, "breaches"):
            leaked_emails = {
                b.get("email", "") for b in self.target.breaches
            }
            overlap = [
                e for e in self.target.emails_found
                if e in leaked_emails
            ]
            if overlap:
                findings.append(
                    f"Emails en fuite également présents dans les profils : "
                    f"{', '.join(overlap)}"
                )

        # Localisation cohérente entre sources
        if hasattr(self.target, "locations") and len(self.target.locations) > 1:
            locs = [l.get("location", "") for l in self.target.locations]
            unique = set(locs)
            if len(unique) == 1:
                findings.append(
                    f"Localisation confirmée par plusieurs sources : {locs[0]}"
                )
            elif len(unique) > 1:
                findings.append(
                    f"Localisations multiples détectées : {', '.join(unique)}"
                )

        # Technologie + CVE
        if (hasattr(self.target, "technologies") and
                hasattr(self.target, "cves") and
                self.target.technologies and self.target.cves):
            findings.append(
                f"Technologies exposées avec {len(self.target.cves)} CVE(s) connue(s)"
            )

        for f in findings:
            self.target.correlations.append(f)
            console.print(f"    [yellow]↔ {f}[/yellow]")

        if not findings:
            console.print("    [dim]Aucune corrélation supplémentaire[/dim]")
