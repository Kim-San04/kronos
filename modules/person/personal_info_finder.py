import requests
import re
import time
from rich.console import Console

console = Console()

PHONE_PATTERNS = [
    r'\+33\s?[67][\s\.\-]?\d{2}[\s\.\-]?\d{2}[\s\.\-]?\d{2}[\s\.\-]?\d{2}',
    r'0[67][\s\.\-]?\d{2}[\s\.\-]?\d{2}[\s\.\-]?\d{2}[\s\.\-]?\d{2}',
    r'\+\d{1,3}[\s\.\-]?\d{6,12}',
]

ADDRESS_PATTERNS = [
    r'\d{1,4}[,\s]+(?:rue|avenue|boulevard|allee|impasse|place|chemin)[^,\n]{5,50}',
    r'\d{5}\s+\w+',
]

SKIP_EMAIL_DOMAINS = [
    "example.com", "w3.org", "schema.org",
    "sentry.io", "cloudflare.com",
]

DIRECTORY_DOMAINS = [
    "pagesjaunes.fr", "118712.fr", "annuaire.com"
]

SOCIAL_PATTERNS = {
    "linkedin.com/in/": "LinkedIn",
    "twitter.com/": "Twitter",
    "instagram.com/": "Instagram",
}


class PersonalInfoFinder:
    """
    Cherche les informations personnelles exposées
    publiquement sur une personne.

    IMPORTANT : cherche UNIQUEMENT des infos
    que la personne a exposées publiquement.
    """

    def __init__(self, target):
        self.target = target

    def run(self):
        name = self.target.name
        console.print("    [dim]Recherche infos personnelles...[/dim]")

        self._search_french_directories(name)
        self._search_phone(name)
        self._search_address(name)
        self._extract_from_profiles()
        self._google_personal_info(name)

        personal = getattr(self.target, "personal_info", {})
        if personal:
            for key, value in personal.items():
                console.print(f"    [green]✓ {key} : {value}[/green]")
        else:
            console.print(
                "    [dim]Infos personnelles : non exposees publiquement[/dim]"
            )

    def _set_info(self, key: str, value: str):
        if not hasattr(self.target, "personal_info"):
            self.target.personal_info = {}
        if key not in self.target.personal_info:
            self.target.personal_info[key] = value

    def _search_french_directories(self, name: str):
        queries = [
            f'"{name}" site:pagesjaunes.fr',
            f'"{name}" site:118712.fr',
            f'"{name}" site:annuaire.com',
        ]
        for query in queries:
            for url in self._ddg_search(query):
                if any(d in url for d in DIRECTORY_DOMAINS):
                    self._set_info("Annuaire", url)
                    console.print(f"    [green]Annuaire : {url}[/green]")
                    return

    def _is_valid_french_phone(self, phone: str) -> bool:
        digits = re.sub(r'[\s\.\-\(\)]', '', phone)
        if digits.startswith("+33"):
            digits = "0" + digits[3:]
        if len(digits) != 10:
            return False
        if not digits.startswith("0"):
            return False
        valid_prefixes = ("06", "07", "01", "02", "03", "04", "05", "08", "09")
        return digits[:2] in valid_prefixes

    def _search_phone(self, name: str):
        queries = [
            f'"{name}" +33',
            f'"{name}" 06 OR 07',
            f'"{name}" telephone contact',
        ]
        for query in queries:
            for url in self._ddg_search(query):
                try:
                    r = requests.get(
                        url,
                        headers={"User-Agent": "Mozilla/5.0"},
                        timeout=5
                    )
                    for pattern in PHONE_PATTERNS:
                        for phone in re.findall(pattern, r.text):
                            clean = re.sub(r'[\s\.\-]', '', phone)
                            if self._is_valid_french_phone(clean):
                                self._set_info("Telephone", clean)
                                console.print(
                                    f"    [green]Tel : {clean}[/green]"
                                )
                                return
                except Exception:
                    pass
                time.sleep(0.3)

    def _search_address(self, name: str):
        queries = [
            f'"{name}" adresse',
            f'"{name}" rue OR avenue OR boulevard',
        ]
        first_name = name.split()[0].lower()

        for query in queries:
            for url in self._ddg_search(query):
                try:
                    r = requests.get(
                        url,
                        headers={"User-Agent": "Mozilla/5.0"},
                        timeout=5
                    )
                    for pattern in ADDRESS_PATTERNS:
                        for addr in re.findall(
                            pattern, r.text, re.IGNORECASE
                        )[:2]:
                            addr = addr.strip()
                            if (
                                len(addr) > 10
                                and first_name in r.text.lower()
                            ):
                                self._set_info("Adresse", addr)
                                return
                except Exception:
                    pass

    def _extract_from_profiles(self):
        for platform, url in self.target.social_profiles.items():
            try:
                r = requests.get(
                    url,
                    headers={"User-Agent": "Mozilla/5.0"},
                    timeout=5,
                    allow_redirects=True
                )
                if r.status_code != 200:
                    continue

                # Numéros de téléphone
                for pattern in PHONE_PATTERNS[:2]:
                    for phone in re.findall(pattern, r.text):
                        clean = re.sub(r'[\s\.\-]', '', phone)
                        if self._is_valid_french_phone(clean):
                            self._set_info("Telephone", clean)

                # Emails supplémentaires
                for email in re.findall(
                    r'[\w\.-]+@[\w\.-]+\.\w{2,}', r.text
                ):
                    if (
                        email not in self.target.emails_found
                        and not any(
                            d in email for d in SKIP_EMAIL_DOMAINS
                        )
                    ):
                        self.target.emails_found.append(email)

            except Exception:
                pass

    def _google_personal_info(self, name: str):
        queries = [
            f'"{name}" linkedin profil',
            f'"{name}" twitter',
            f'"{name}" instagram',
        ]
        for query in queries:
            for url in self._ddg_search(query):
                for pattern, platform in SOCIAL_PATTERNS.items():
                    if (
                        pattern in url
                        and platform not in self.target.social_profiles
                    ):
                        self.target.social_profiles[platform] = url
                        console.print(
                            f"    [green]✓ {platform} (Google) : {url}[/green]"
                        )

    def _ddg_search(self, query: str) -> list:
        try:
            r = requests.get(
                "https://html.duckduckgo.com/html/",
                params={"q": query},
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=10
            )
            urls = re.findall(r'href="(https?://[^"&]+)"', r.text)
            skip = ["duckduckgo.com", "w3.org", "schema.org"]
            return [u for u in urls[:10] if not any(s in u for s in skip)]
        except Exception:
            return []
