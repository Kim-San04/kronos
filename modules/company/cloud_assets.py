import requests
from rich.console import Console

console = Console()

class CloudAssets:
    def __init__(self, target):
        self.target = target

    def run(self):
        domain = self.target.domain
        company = domain.split(".")[0]

        found = []

        s3_names = [
            company,
            f"{company}-backup",
            f"{company}-assets",
            f"{company}-static",
            f"{company}-media",
            f"{company}-uploads",
            f"{company}-dev",
            f"{company}-staging",
            f"{company}-prod",
            f"{company}-data",
            f"backup-{company}",
            f"assets-{company}",
        ]

        for name in s3_names:
            url = f"https://{name}.s3.amazonaws.com"
            try:
                r = requests.get(url, timeout=5)
                if r.status_code in [200, 403]:
                    status = (
                        "PUBLIC" if r.status_code == 200
                        else "PRIVATE (existe)"
                    )
                    found.append({
                        "type": "S3",
                        "name": name,
                        "url": url,
                        "status": status
                    })
                    color = "red" if r.status_code == 200 else "yellow"
                    console.print(
                        f"    [{color}]S3 bucket : {name} — {status}[/{color}]"
                    )
            except:
                pass

        self.target.cloud_assets.extend(found)
        self.target.s3_buckets = [f.get("name") for f in found]

        if not found:
            console.print("    [dim]Aucun cloud asset trouvé[/dim]")
