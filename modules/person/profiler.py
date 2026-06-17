import os
import json
from rich.console import Console

console = Console()

PROFILE_TYPES = {
    "developer": {
        "description": "Développeur / Ingénieur / Cybersec",
        "indicators": [
            "github", "gitlab", "informatique", "dev",
            "engineer", "code", "cyber", "security",
            "efrei", "epitech", "42", "polytech",
            "ingénieur", "développeur", "hack", "ctf"
        ],
        "primary_sources": [
            "GitHub", "GitLab", "HackTheBox", "TryHackMe",
            "Root-Me", "Stack Overflow", "LinkedIn",
            "Dev.to", "HackerNews", "CodeWars"
        ],
        "username_patterns": [
            "tech_pseudos",
            "initials_year",
            "name_variants",
        ],
        "search_queries": [
            '"{name}" github',
            '"{name}" cybersécurité OR security',
            '"{name}" {school} développeur',
            '"{name}" CTF OR hackthebox OR tryhackme',
            '"{username}" site:github.com',
        ]
    },
    "influencer": {
        "description": "Influenceur / Créateur / Artiste",
        "indicators": [
            "youtube", "instagram", "tiktok", "content",
            "créateur", "artiste", "musicien", "photographe",
            "blogueur", "streamer", "youtuber", "influencer"
        ],
        "primary_sources": [
            "Instagram", "TikTok", "YouTube", "Twitter",
            "Twitch", "Snapchat", "Pinterest",
            "SoundCloud", "Spotify", "Behance"
        ],
        "username_patterns": [
            "brand_name",
            "name_clean",
            "aesthetic",
        ],
        "search_queries": [
            '"{name}" instagram OR tiktok',
            '"{name}" youtube channel',
            '"{name}" créateur OR influencer',
            '"{name}" collaboration',
        ]
    },
    "business": {
        "description": "Entrepreneur / Manager / CEO",
        "indicators": [
            "ceo", "cto", "founder", "directeur", "manager",
            "entrepreneur", "startup", "société", "entreprise",
            "commercial", "consultant", "associé", "gérant"
        ],
        "primary_sources": [
            "LinkedIn", "Crunchbase", "Pappers.fr",
            "Twitter", "AngelList", "Malt",
            "SIRENE", "Infogreffe", "articles presse"
        ],
        "username_patterns": [
            "professional",
            "company_name",
            "linkedin_style",
        ],
        "search_queries": [
            '"{name}" linkedin',
            '"{name}" CEO OR fondateur OR directeur',
            '"{name}" site:pappers.fr OR site:societe.com',
            '"{name}" startup OR entreprise',
            '"{name}" interview OR article',
        ]
    },
    "regular": {
        "description": "Personne ordinaire",
        "indicators": [],
        "primary_sources": [
            "Facebook", "WhatsApp", "Instagram",
            "Pages Blanches", "Annuaires locaux",
            "LinkedIn", "Google Maps avis"
        ],
        "username_patterns": [
            "name_variants",
            "firstname_only",
        ],
        "search_queries": [
            '"{name}" facebook',
            '"{name}" site:pagesjaunes.fr OR site:118712.fr',
            '"{name}" avis OR review',
            '"{name}" {city}',
        ]
    },
    "public_figure": {
        "description": "Figure publique / Politique / Journaliste",
        "indicators": [
            "député", "sénateur", "maire", "ministre",
            "journaliste", "avocat", "médecin", "professeur",
            "celebrity", "acteur", "sportif", "coach"
        ],
        "primary_sources": [
            "Wikipedia", "Twitter", "LinkedIn",
            "Articles presse", "Site officiel",
            "Archives web", "YouTube"
        ],
        "username_patterns": [
            "official",
            "firstname_lastname",
        ],
        "search_queries": [
            '"{name}" wikipedia',
            '"{name}" site:twitter.com',
            '"{name}" interview OR biographie',
            '"{name}" site:lemonde.fr OR site:lefigaro.fr',
        ]
    },
    "gamer": {
        "description": "Gamer / Streamer",
        "indicators": [
            "gamer", "gaming", "steam", "twitch", "esport",
            "fortnite", "minecraft", "league", "valorant",
            "discord", "clan", "team", "streamer"
        ],
        "primary_sources": [
            "Steam", "Twitch", "Discord",
            "Xbox", "PSN", "Epic Games",
            "Battlenet", "Origin", "Riot Games"
        ],
        "username_patterns": [
            "gaming_tag",
            "numbers_heavy",
        ],
        "search_queries": [
            '"{name}" twitch OR steam',
            '"{username}" steam profile',
            '"{name}" gaming OR gamer',
            '"{username}" discord',
        ]
    },
    "academic": {
        "description": "Chercheur / Universitaire",
        "indicators": [
            "docteur", "professeur", "chercheur", "phd",
            "université", "laboratoire", "publication",
            "recherche", "thèse", "master", "doctorat"
        ],
        "primary_sources": [
            "Google Scholar", "ResearchGate",
            "Academia.edu", "ORCID", "HAL",
            "LinkedIn", "Site université"
        ],
        "username_patterns": [
            "academic_style",
            "firstname_lastname",
        ],
        "search_queries": [
            '"{name}" site:scholar.google.com',
            '"{name}" site:researchgate.net',
            '"{name}" publication OR article OR thèse',
            '"{name}" université OR laboratoire',
        ]
    }
}


class TargetProfiler:
    """
    Cerveau de KRONOS.

    Avant de chercher quoi que ce soit,
    analyser les indices disponibles sur la cible
    et décider :
    1. Quel type de profil (développeur, artiste, etc.)
    2. Où chercher en priorité
    3. Quels pseudos tester
    4. Dans quel ordre lancer les modules
    """

    def __init__(self, target):
        self.target = target
        self.api_key = os.getenv("GROQ_API_KEY")
        self.profile_type = None
        self.strategy = None

    def run(self):
        console.print("    [dim]Profilage de la cible...[/dim]")

        if self.api_key:
            self.profile_type = self._ai_profiling()

        if not self.profile_type:
            self.profile_type = self._keyword_profiling()

        self.strategy = PROFILE_TYPES.get(
            self.profile_type, PROFILE_TYPES["regular"]
        )

        console.print(
            f"    [bold cyan]Type détecté : "
            f"{self.strategy['description']}[/bold cyan]"
        )
        console.print(
            f"    [cyan]Sources prioritaires : "
            f"{', '.join(self.strategy['primary_sources'][:5])}[/cyan]"
        )

        self.target.profile_type = self.profile_type
        self.target.search_strategy = self.strategy
        self.target.priority_sources = self.strategy["primary_sources"]
        self.target.search_queries = [
            q.format(
                name=self.target.name,
                username=self.target.username or "",
                school=self._detect_school(),
                city=self._detect_city()
            )
            for q in self.strategy["search_queries"]
        ]

        self._generate_profile_usernames()

        return self.profile_type

    def _ai_profiling(self) -> str:
        try:
            from groq import Groq
            client = Groq(api_key=self.api_key)

            context = {
                "name": self.target.name,
                "username": self.target.username,
                "email": self.target.email,
                "location": (
                    self.target.locations[0]["location"]
                    if self.target.locations else None
                ),
                "company": getattr(self.target, "company", None),
                "notes": getattr(self.target, "notes", None)
            }

            prompt = f"""Tu es un expert OSINT.
Analyse ces informations sur une cible et détermine son type de profil.

Informations disponibles :
{json.dumps(context, ensure_ascii=False, indent=2)}

Types possibles :
- developer (dev, ingénieur, cybersec, étudiant IT)
- influencer (youtuber, instagrammer, artiste, créateur)
- business (CEO, manager, entrepreneur, commercial)
- regular (personne ordinaire sans profil tech)
- public_figure (politique, journaliste, celebrity)
- gamer (streamer, joueur professionnel)
- academic (chercheur, universitaire, professeur)

Réponds UNIQUEMENT avec le type en JSON :
{{
    "type": "developer",
    "confidence": 85,
    "reasoning": "Présence GitHub, nom d'école IT détecté",
    "likely_platforms": ["GitHub", "LinkedIn", "Discord"],
    "likely_username_style": "initiales + année (ex: hs04)"
}}"""

            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                timeout=15
            )

            text = response.choices[0].message.content.strip()
            if "```" in text:
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            text = text.strip()

            result = json.loads(text)
            profile_type = result.get("type", "regular")
            reasoning = result.get("reasoning", "")
            likely_username = result.get("likely_username_style", "")

            if reasoning:
                console.print(f"    [dim]IA : {reasoning}[/dim]")
            if likely_username:
                console.print(
                    f"    [dim]Style pseudo probable : {likely_username}[/dim]"
                )

            ai_platforms = result.get("likely_platforms", [])
            if ai_platforms:
                if not hasattr(self.target, "ai_suggested_platforms"):
                    self.target.ai_suggested_platforms = []
                existing = self.target.priority_sources if self.strategy else []
                for p in ai_platforms:
                    if p not in existing:
                        self.target.ai_suggested_platforms.append(p)

            return profile_type if profile_type in PROFILE_TYPES else "regular"

        except Exception as e:
            console.print(
                f"    [dim]AI profiling : {e} — fallback keywords[/dim]"
            )
            return None

    def _keyword_profiling(self) -> str:
        text = " ".join(filter(None, [
            self.target.name.lower(),
            (self.target.username or "").lower(),
            (self.target.email or "").lower(),
            getattr(self.target, "notes", "") or "",
            " ".join([
                loc.get("location", "")
                for loc in self.target.locations
            ])
        ]))

        scores = {}
        for ptype, config in PROFILE_TYPES.items():
            score = sum(
                1 for indicator in config["indicators"]
                if indicator in text
            )
            scores[ptype] = score

        best = max(scores, key=scores.get)
        return best if scores[best] > 0 else "regular"

    def _generate_profile_usernames(self):
        if self.target.username:
            return

        name = self.target.name.lower().split()
        if len(name) < 2:
            return

        first, last = name[0], name[-1]
        fi = first[0]
        initials = fi + last[0]

        variants = set()

        if self.profile_type == "developer":
            variants.update([
                f"{fi}{last}",
                f"{fi}-{last}",
                f"{fi}_{last}",
                f"{initials}04",
                f"{initials}99",
                f"{initials}00",
                f"{first}-san",
                f"{first}dev",
                f"{last}dev",
                f"{first}hack",
                f"0x{fi}{last}",
            ])

        elif self.profile_type == "influencer":
            variants.update([
                first,
                f"{first}.{last}",
                f"by{first}",
                f"its{first}",
                f"the{first}",
                f"{first}official",
                f"{first}_{last}",
                f"{first}real",
            ])

        elif self.profile_type == "business":
            variants.update([
                f"{first}.{last}",
                f"{first}-{last}",
                f"{first}{last}",
                f"{fi}.{last}",
                f"{first}_{last}",
            ])

        elif self.profile_type == "gamer":
            variants.update([
                f"x{first}x",
                f"{first}gaming",
                f"{first}gamer",
                f"{first}666",
                f"{first}gg",
                f"{first}pro",
                f"{first}yt",
                f"_{first}_",
                f"the{first}",
            ])

        elif self.profile_type == "academic":
            variants.update([
                f"{first}.{last}",
                f"{fi}.{last}",
                f"{first}_{last}",
                f"{fi}{last}",
            ])

        else:
            variants.update([
                f"{first}{last}",
                f"{first}.{last}",
                f"{fi}{last}",
                first,
                last,
            ])

        self.target.suggested_usernames = list(variants)

        console.print(
            f"    [dim]{len(variants)} pseudos générés "
            f"(style {self.profile_type})[/dim]"
        )

    def _detect_school(self) -> str:
        text = " ".join([
            self.target.name,
            self.target.username or "",
            self.target.email or "",
            getattr(self.target, "notes", "") or "",
        ]).lower()
        schools = {
            "efrei": "EFREI",
            "epitech": "Epitech",
            "42": "42",
            "centrale": "Centrale",
            "polytechnique": "Polytechnique",
            "hec": "HEC",
        }
        for key, name in schools.items():
            if key in text:
                return name
        return ""

    def _detect_city(self) -> str:
        if self.target.locations:
            return self.target.locations[0].get("location", "")
        return ""
