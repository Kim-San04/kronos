import os
import requests
import re
from rich.console import Console

console = Console()

SECRET_PATTERNS = {
    "AWS Key": r"AKIA[0-9A-Z]{16}",
    "AWS Secret": r"[0-9a-zA-Z/+]{40}",
    "GitHub Token": r"ghp_[0-9a-zA-Z]{36}",
    "Private Key": r"-----BEGIN (RSA|EC|DSA) PRIVATE KEY-----",
    "Password": r"password\s*=\s*['\"][^'\"]+['\"]",
    "API Key": r"api[_-]?key\s*=\s*['\"][^'\"]+['\"]",
    "DB URL": r"(mysql|postgresql|mongodb)://[^\s]+",
}

class SecretScanner:
    def __init__(self, target):
        self.target = target
        self.token = os.getenv("GITHUB_TOKEN")
        self.headers = {}
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"

    def run(self):
        domain = self.target.domain
        company = domain.split(".")[0]

        org = self._find_org(company)
        if not org:
            return

        repos = self._get_repos(org)

        secrets_found = 0
        for repo in repos[:20]:
            secrets = self._scan_repo(org, repo)
            if secrets:
                secrets_found += len(secrets)
                self.target.exposed_secrets.extend(secrets)

        if secrets_found:
            console.print(
                f"    [red]⚠ {secrets_found} secrets potentiels trouvés ![/red]"
            )
        else:
            console.print("    [green]Aucun secret évident détecté[/green]")

    def _find_org(self, company):
        try:
            r = requests.get(
                f"https://api.github.com/search/users?q={company}+type:org",
                headers=self.headers, timeout=10
            )
            if r.status_code == 200:
                items = r.json().get("items", [])
                if items:
                    return items[0]["login"]
        except:
            pass
        return None

    def _get_repos(self, org):
        try:
            r = requests.get(
                f"https://api.github.com/orgs/{org}/repos?per_page=50",
                headers=self.headers, timeout=10
            )
            return r.json() if r.status_code == 200 else []
        except:
            return []

    def _scan_repo(self, org, repo):
        secrets = []
        repo_name = repo.get("name", "")

        try:
            r = requests.get(
                f"https://raw.githubusercontent.com"
                f"/{org}/{repo_name}/main/README.md",
                timeout=5
            )
            if r.status_code == 200:
                for secret_type, pattern in SECRET_PATTERNS.items():
                    matches = re.findall(pattern, r.text, re.IGNORECASE)
                    if matches:
                        secrets.append({
                            "repo": repo_name,
                            "type": secret_type,
                            "file": "README.md",
                            "count": len(matches)
                        })
                        console.print(
                            f"    [red]{secret_type} dans {repo_name}/README.md[/red]"
                        )
        except:
            pass

        return secrets
