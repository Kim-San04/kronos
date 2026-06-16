import requests
import re
from rich.console import Console

console = Console()

class PhoneFinder:
    """
    Cherche le numéro de téléphone d'une personne.
    Sources : pages web publiques et mentions indexées.
    """

    def __init__(self, target):
        self.target = target

    def run(self):
        name = self.target.name
        console.print("    [dim]Recherche numéro de téléphone...[/dim]")

        phones_found = set()

        queries = [
            f'"{name}" "+33" OR "06" OR "07"',
            f'"{name}" téléphone contact',
            f'"{name}" phone number',
        ]

        for query in queries:
            phones = self._search_phones(query)
            phones_found.update(phones)

        if phones_found:
            for phone in phones_found:
                console.print(f"    [green]Téléphone : {phone}[/green]")
            self.target.correlations.append(
                f"Numéro(s) potentiel(s) : {', '.join(phones_found)}"
            )
        else:
            console.print(
                "    [dim]Numéro non trouvé publiquement[/dim]"
            )

    def _search_phones(self, query: str) -> set:
        phones = set()
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0)"
            }
            r = requests.get(
                "https://html.duckduckgo.com/html/",
                params={"q": query},
                headers=headers,
                timeout=10
            )

            patterns = [
                r'\+33\s?[67]\s?\d{2}\s?\d{2}\s?\d{2}\s?\d{2}',
                r'0[67]\s?\d{2}\s?\d{2}\s?\d{2}\s?\d{2}',
                r'\+\d{1,3}\s?\d{6,12}',
            ]

            for pattern in patterns:
                matches = re.findall(pattern, r.text)
                for match in matches:
                    clean = re.sub(r'\s', '', match)
                    if len(clean) >= 10:
                        phones.add(clean)

        except Exception:
            pass

        return phones
