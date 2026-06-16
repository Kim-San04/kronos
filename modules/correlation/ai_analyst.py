import os
import json
from rich.console import Console

console = Console()

class AIAnalyst:
    def __init__(self, target):
        self.target = target
        self.api_key = os.getenv("GROQ_API_KEY")

    def run(self):
        if not self.api_key:
            self._rule_based_analysis()
            return

        try:
            from groq import Groq
            client = Groq(api_key=self.api_key)

            data = self._prepare_summary()

            prompt = f"""Tu es un expert OSINT.
Analyse ces données collectées sur une cible
et fournis une analyse en JSON.

Données collectées :
{json.dumps(data, indent=2, ensure_ascii=False)}

Réponds UNIQUEMENT en JSON valide :
{{
    "summary": "résumé exécutif en 3 phrases",
    "correlations": [
        "corrélation importante 1",
        "corrélation importante 2"
    ],
    "risks": [
        "risque identifié 1",
        "risque identifié 2"
    ],
    "risk_score": 75,
    "recommendations": [
        "recommandation 1"
    ]
}}"""

            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                timeout=30
            )

            text = response.choices[0].message.content.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            text = text.strip()

            result = json.loads(text)

            self.target.ai_summary = result.get("summary", "")
            self.target.correlations = result.get("correlations", [])
            self.target.risk_score = int(result.get("risk_score", 0))

            console.print(
                f"    [cyan]Score de risque : "
                f"{self.target.risk_score}/100[/cyan]"
            )
            for c in self.target.correlations[:3]:
                console.print(f"    [yellow]→ {c}[/yellow]")

        except Exception as e:
            console.print(
                f"    [dim]AI erreur : {e} — fallback règles[/dim]"
            )
            self._rule_based_analysis()

    def _prepare_summary(self) -> dict:
        target_type = type(self.target).__name__

        if target_type == "PersonTarget":
            return {
                "type": "personne",
                "nom": self.target.name,
                "emails": self.target.emails_found,
                "pseudos": self.target.usernames_found,
                "profils_sociaux": list(
                    self.target.social_profiles.keys()
                ),
                "github": bool(self.target.github_data),
                "fuites": len(self.target.breaches),
                "localisations": self.target.locations,
                "connexions": len(self.target.connections),
                "pic_activite": self.target.activity_hours.get(
                    "peak_hour"
                ),
                "langages_github": self.target.github_data.get(
                    "languages", []
                ),
            }
        else:
            return {
                "type": "entreprise",
                "domaine": self.target.domain,
                "ips": self.target.ips,
                "sous_domaines": len(self.target.subdomains),
                "ports_ouverts": self.target.open_ports,
                "cves": self.target.cves,
                "technologies": self.target.technologies,
                "employes": len(self.target.employees),
                "emails": self.target.emails,
                "secrets_exposes": len(self.target.exposed_secrets),
                "cloud_assets": len(self.target.cloud_assets),
                "darkweb": len(self.target.darkweb_mentions),
            }

    def _rule_based_analysis(self):
        score = 0
        correlations = []

        if hasattr(self.target, "breaches"):
            n = len(self.target.breaches)
            if n > 0:
                score += n * 15
                correlations.append(
                    f"{n} fuite(s) de données détectée(s)"
                )

        if hasattr(self.target, "exposed_secrets"):
            n = len(self.target.exposed_secrets)
            if n > 0:
                score += n * 25
                correlations.append(
                    f"{n} secret(s) exposé(s) sur GitHub"
                )

        if hasattr(self.target, "cves"):
            n = len(self.target.cves)
            if n > 0:
                score += n * 10
                correlations.append(f"{n} CVE(s) identifiée(s)")

        if hasattr(self.target, "darkweb_mentions"):
            n = len(self.target.darkweb_mentions)
            if n > 0:
                score += n * 20
                correlations.append(f"{n} mention(s) darkweb")

        if hasattr(self.target, "social_profiles"):
            n = len(self.target.social_profiles)
            if n > 0:
                score += n * 3
                correlations.append(
                    f"{n} profil(s) social(aux) confirmé(s)"
                )

        if hasattr(self.target, "emails_found"):
            emails = self.target.emails_found
            if emails:
                score += len(emails) * 5
                correlations.append(
                    f"{len(emails)} email(s) trouvé(s) : "
                    f"{', '.join(emails[:2])}"
                )

        self.target.risk_score = min(score, 100)
        self.target.correlations = correlations

        if not self.target.ai_summary:
            name = getattr(
                self.target, "name",
                getattr(self.target, "domain", "Cible")
            )
            self.target.ai_summary = (
                f"Analyse KRONOS de {name}. "
                f"Score de risque : {self.target.risk_score}/100. "
                f"{len(correlations)} corrélation(s) identifiée(s)."
            )

        console.print(
            f"    [cyan]Score de risque : "
            f"{self.target.risk_score}/100[/cyan]"
        )
