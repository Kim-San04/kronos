import os
import json
from dataclasses import asdict
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

            data = asdict(self.target)
            summary = json.dumps(data, indent=2)[:3000]

            prompt = f"""
Tu es un expert en OSINT et threat intelligence.
Analyse ces données collectées sur une cible et fournis :
1. Un résumé exécutif (3-5 phrases)
2. Les corrélations importantes entre les données
3. Les risques identifiés
4. Un score de risque global de 0 à 100

Données :
{summary}

Réponds en JSON :
{{
    "summary": "résumé...",
    "correlations": ["corrélation 1", ...],
    "risks": ["risque 1", ...],
    "risk_score": 75
}}
"""
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000
            )

            text = response.choices[0].message.content

            # Extraire le JSON de la réponse
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                text = text[start:end]

            result = json.loads(text)

            self.target.ai_summary = result.get("summary", "")
            self.target.correlations = result.get("correlations", [])
            self.target.risk_score = int(result.get("risk_score", 0))

            risks = result.get("risks", [])
            console.print(
                f"    [cyan]IA : score {self.target.risk_score}/100, "
                f"{len(risks)} risques identifiés[/cyan]"
            )

        except Exception as e:
            console.print(f"    [dim]Groq IA erreur : {e}[/dim]")
            self._rule_based_analysis()

    def _rule_based_analysis(self):
        score = 0
        correlations = []

        if hasattr(self.target, "breaches") and self.target.breaches:
            score += min(len(self.target.breaches) * 10, 30)
            correlations.append(
                f"{len(self.target.breaches)} fuite(s) de données détectée(s)"
            )

        if hasattr(self.target, "exposed_secrets") and self.target.exposed_secrets:
            score += min(len(self.target.exposed_secrets) * 15, 40)
            correlations.append(
                f"{len(self.target.exposed_secrets)} secret(s) exposé(s)"
            )

        if hasattr(self.target, "cves") and self.target.cves:
            score += min(len(self.target.cves) * 5, 20)
            correlations.append(
                f"{len(self.target.cves)} CVE(s) identifiée(s)"
            )

        if hasattr(self.target, "darkweb_mentions") and self.target.darkweb_mentions:
            score += min(len(self.target.darkweb_mentions) * 10, 20)
            correlations.append("Présence sur le darkweb détectée")

        if hasattr(self.target, "social_profiles") and self.target.social_profiles:
            score += min(len(self.target.social_profiles) * 2, 10)
            correlations.append(
                f"{len(self.target.social_profiles)} profil(s) social(aux) identifié(s)"
            )

        self.target.risk_score = min(score, 100)
        self.target.correlations = correlations
        self.target.ai_summary = (
            "Analyse basée sur les règles (Groq non disponible). "
            f"Score de risque calculé : {self.target.risk_score}/100."
        )

        console.print(
            f"    [cyan]Analyse règles : score {self.target.risk_score}/100[/cyan]"
        )
