import requests
import re
import time
import os
import datetime
from rich.console import Console
from bs4 import BeautifulSoup

console = Console()


class DeepCrawler:
    """
    Pour chaque compte trouvé, creuse en profondeur
    pour extraire le maximum d'informations.

    GitHub    → followers, orgs, gists,
                emails dans commits, liens README
    LinkedIn  → formation, entreprise, localisation
    Root-Me   → score, rang
    Twitter   → bio, liens
    Instagram → bio, followers, liens
    Reddit    → karma, ancienneté
    """

    def __init__(self, target):
        self.target = target
        self.token = os.getenv("GITHUB_TOKEN")
        self.headers_gh = {}
        if self.token:
            self.headers_gh["Authorization"] = f"token {self.token}"
        self.headers_web = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
            )
        }

    def run(self):
        console.print("    [dim]Crawling profond...[/dim]")
        discoveries = 0

        for platform, url in list(self.target.social_profiles.items()):
            pl = platform.lower()

            if "github" in pl or "github.com" in url:
                discoveries += self._deep_github(url)
            elif "linkedin" in pl or "linkedin.com" in url:
                discoveries += self._deep_linkedin(url)
            elif "root-me" in pl or "root-me.org" in url:
                discoveries += self._deep_rootme(url)
            elif "twitter" in pl or "x.com" in url:
                discoveries += self._deep_twitter(url)
            elif "instagram" in pl or "instagram.com" in url:
                discoveries += self._deep_instagram(url)
            elif "reddit" in pl or "reddit.com" in url:
                discoveries += self._deep_reddit(url)

            time.sleep(0.3)

        if discoveries:
            console.print(
                f"    [cyan]{discoveries} information(s) "
                f"supplementaire(s) extraites[/cyan]"
            )

    def _deep_github(self, url: str) -> int:
        found = 0
        username = url.rstrip("/").split("/")[-1]
        if not username or username == "github.com":
            return 0

        console.print(f"    [dim]GitHub deep : {username}...[/dim]")

        # 1. Profil complet
        try:
            r = requests.get(
                f"https://api.github.com/users/{username}",
                headers=self.headers_gh, timeout=8
            )
            if r.status_code == 200:
                data = r.json()

                if data.get("email"):
                    email = data["email"]
                    if email not in self.target.emails_found:
                        self.target.emails_found.append(email)
                        console.print(
                            f"    [green]Email GitHub profile : {email}[/green]"
                        )
                        found += 1

                bio = data.get("bio", "") or ""
                for link in re.findall(r'https?://[^\s]+', bio):
                    platform = self._id_platform(link)
                    if platform and platform not in self.target.social_profiles:
                        self.target.social_profiles[platform] = link
                        console.print(
                            f"    [green]{platform} dans bio GitHub : {link}[/green]"
                        )
                        found += 1

                tw = data.get("twitter_username")
                if tw and "Twitter" not in self.target.social_profiles:
                    self.target.social_profiles["Twitter"] = (
                        f"https://twitter.com/{tw}"
                    )
                    console.print(f"    [green]Twitter GitHub : @{tw}[/green]")
                    found += 1

                blog = data.get("blog", "") or ""
                if blog.startswith("http") and "Site web" not in self.target.social_profiles:
                    self.target.social_profiles["Site web"] = blog
                    console.print(f"    [green]Site web : {blog}[/green]")
                    found += 1

                loc = data.get("location") or ""
                if loc:
                    existing = [l.get("location") for l in self.target.locations]
                    if loc not in existing:
                        self.target.locations.append({
                            "source": "GitHub",
                            "location": loc
                        })
                        console.print(f"    [cyan]Ville : {loc}[/cyan]")
                        found += 1

                company = data.get("company") or ""
                if company:
                    if not isinstance(self.target.deep_data, dict):
                        self.target.deep_data = {}
                    self.target.deep_data["GitHub_Company"] = company.strip("@")
                    console.print(f"    [cyan]Entreprise : {company}[/cyan]")
                    found += 1
        except Exception:
            pass

        # 2. README du profil
        for branch in ["main", "master"]:
            try:
                r = requests.get(
                    f"https://raw.githubusercontent.com"
                    f"/{username}/{username}/{branch}/README.md",
                    headers=self.headers_gh, timeout=5
                )
                if r.status_code == 200:
                    readme = r.text
                    social_patterns = {
                        r'https?://(?:www\.)?instagram\.com/[\w\.]+': "Instagram",
                        r'https?://(?:www\.)?twitter\.com/[\w]+': "Twitter",
                        r'https?://t\.me/[\w]+': "Telegram",
                        r'https?://(?:www\.)?linkedin\.com/in/[\w\-]+': "LinkedIn",
                        r'https?://(?:www\.)?tiktok\.com/@[\w\.]+': "TikTok",
                        r'https?://(?:www\.)?youtube\.com/[\w@\-/]+': "YouTube",
                        r'https?://discord\.gg/[\w]+': "Discord",
                        r'https?://(?:www\.)?reddit\.com/u/[\w]+': "Reddit",
                    }
                    for pattern, pname in social_patterns.items():
                        for match in re.findall(pattern, readme):
                            if pname not in self.target.social_profiles:
                                self.target.social_profiles[pname] = match
                                console.print(
                                    f"    [green]{pname} dans README : {match}[/green]"
                                )
                                found += 1

                    skip = ["example.com", "w3.org", "schema.org", "noreply", "github.com"]
                    for email in re.findall(r'[\w\.\-]+@[\w\.\-]+\.\w{2,}', readme):
                        if (email not in self.target.emails_found
                                and not any(s in email for s in skip)):
                            self.target.emails_found.append(email)
                            console.print(
                                f"    [green]Email README : {email}[/green]"
                            )
                            found += 1
                    break
            except Exception:
                pass

        # 3. Organisations
        try:
            r = requests.get(
                f"https://api.github.com/users/{username}/orgs",
                headers=self.headers_gh, timeout=8
            )
            if r.status_code == 200:
                orgs = r.json()
                org_names = [o.get("login", "") for o in orgs if o.get("login")]
                if org_names:
                    if not isinstance(self.target.deep_data, dict):
                        self.target.deep_data = {}
                    self.target.deep_data["GitHub_Orgs"] = org_names
                    console.print(
                        f"    [cyan]{len(org_names)} organisation(s) GitHub : "
                        f"{', '.join(org_names[:3])}[/cyan]"
                    )
                    found += len(org_names)
        except Exception:
            pass

        # 4. Followers (connexions)
        try:
            r = requests.get(
                f"https://api.github.com/users/{username}/followers?per_page=30",
                headers=self.headers_gh, timeout=8
            )
            if r.status_code == 200:
                followers = r.json()
                for follower in followers[:10]:
                    conn = {
                        "username": follower.get("login"),
                        "platform": "GitHub",
                        "type": "follower",
                        "url": follower.get("html_url", "")
                    }
                    self._add_connection(conn)
                if followers:
                    console.print(
                        f"    [cyan]{len(followers)} followers GitHub[/cyan]"
                    )
                    found += len(followers[:10])
        except Exception:
            pass

        # 5. Commits récents → emails
        try:
            r = requests.get(
                f"https://api.github.com/users/{username}/repos"
                f"?per_page=30&sort=updated",
                headers=self.headers_gh, timeout=8
            )
            if r.status_code == 200:
                repos = r.json()
                for repo in repos[:5]:
                    r2 = requests.get(
                        f"https://api.github.com/repos"
                        f"/{username}/{repo['name']}/commits?per_page=20",
                        headers=self.headers_gh, timeout=8
                    )
                    if r2.status_code == 200:
                        for commit in r2.json():
                            author = commit.get("commit", {}).get("author", {})
                            email = author.get("email", "")
                            if (email
                                    and "noreply" not in email
                                    and "github" not in email
                                    and email not in self.target.emails_found):
                                self.target.emails_found.append(email)
                                console.print(
                                    f"    [green]Email commit "
                                    f"({repo['name']}) : {email}[/green]"
                                )
                                found += 1
                    time.sleep(0.2)
        except Exception:
            pass

        return found

    def _deep_linkedin(self, url: str) -> int:
        found = 0
        name = self.target.name
        name_parts = name.lower().split()

        if not isinstance(self.target.deep_data, dict):
            self.target.deep_data = {}

        console.print("    [dim]LinkedIn deep crawl...[/dim]")

        # METHODE 1 : Lire la page LinkedIn directement
        try:
            r = requests.get(
                url,
                headers={**self.headers_web, "Accept-Language": "fr-FR,fr;q=0.9"},
                timeout=12
            )
            if r.status_code == 200:
                text = r.text

                for pattern in [
                    r'<title>([^<]+)\s*\|',
                    r'"name":\s*"([^"]+)"',
                    r'og:title.*?content="([^"]+)"',
                ]:
                    m = re.search(pattern, text)
                    if m:
                        val = m.group(1).strip()
                        if any(p in val.lower() for p in name_parts):
                            self.target.deep_data["LinkedIn_Nom"] = val
                            found += 1
                            break

                for pattern in [
                    r'"headline":\s*"([^"]+)"',
                    r'class="top-card-layout__headline[^"]*">([^<]+)<',
                    r'"title":\s*"([^"]+)"',
                ]:
                    m = re.search(pattern, text)
                    if m:
                        val = m.group(1).strip()
                        if val and len(val) > 3:
                            self.target.deep_data["LinkedIn_Titre"] = val[:100]
                            console.print(
                                f"    [green]LinkedIn titre : {val[:50]}[/green]"
                            )
                            found += 1
                            break

                for pattern in [
                    r'"summary":\s*"([^"]+)"',
                    r'"description":\s*"([^"]{20,})"',
                ]:
                    m = re.search(pattern, text)
                    if m:
                        val = m.group(1).strip()
                        if val and len(val) > 20 and any(
                            p in val.lower() for p in name_parts
                        ):
                            self.target.deep_data["LinkedIn_Bio"] = val[:300]
                            found += 1
                            break

                for pattern in [
                    r'"locationName":\s*"([^"]+)"',
                    r'"geoLocationName":\s*"([^"]+)"',
                    r'class="top-card-layout__location[^"]*">([^<]+)<',
                ]:
                    m = re.search(pattern, text)
                    if m:
                        loc = m.group(1).strip()
                        if loc and len(loc) > 2:
                            existing = [
                                l.get("location") for l in self.target.locations
                            ]
                            if loc not in existing:
                                self.target.locations.append({
                                    "source": "LinkedIn", "location": loc
                                })
                                self.target.deep_data["LinkedIn_Ville"] = loc
                                console.print(
                                    f"    [green]LinkedIn ville : {loc}[/green]"
                                )
                                found += 1
                            break

                for pattern in [
                    r'"schoolName":\s*"([^"]+)"',
                    r'"degreeName":\s*"([^"]+)"',
                    r'"fieldOfStudy":\s*"([^"]+)"',
                ]:
                    matches = re.findall(pattern, text)
                    for m in matches[:3]:
                        key = f"LinkedIn_Formation_{found}"
                        self.target.deep_data[key] = m
                        console.print(f"    [green]Formation : {m}[/green]")
                        found += 1

                for pattern in [
                    r'"companyName":\s*"([^"]+)"',
                ]:
                    matches = re.findall(pattern, text)
                    companies = list(dict.fromkeys([
                        m for m in matches if len(m) > 2
                    ]))[:5]
                    if companies:
                        self.target.deep_data["LinkedIn_Experiences"] = (
                            " · ".join(companies)
                        )
                        console.print(
                            f"    [green]Experiences : "
                            f"{', '.join(companies[:3])}[/green]"
                        )
                        found += len(companies)
                        break

                for pattern in [
                    r'"connectionsCount":(\d+)',
                    r'(\d+)\s*connexions?',
                ]:
                    m = re.search(pattern, text, re.I)
                    if m:
                        self.target.deep_data["LinkedIn_Connexions"] = m.group(1)
                        found += 1
                        break
        except Exception as e:
            console.print(f"    [dim]LinkedIn direct : {e}[/dim]")

        # METHODE 2 : Google Cache
        try:
            cache_url = (
                f"https://webcache.googleusercontent.com"
                f"/search?q=cache:{url}"
            )
            r = requests.get(cache_url, headers=self.headers_web, timeout=10)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, "html.parser")
                for tag in soup(["script", "style"]):
                    tag.decompose()
                text = soup.get_text(" ", strip=True)
                if any(p in text.lower() for p in name_parts):
                    sentences = [
                        s.strip() for s in text.split(".")
                        if any(p in s.lower() for p in name_parts)
                        and 10 < len(s) < 200
                    ]
                    if sentences:
                        self.target.deep_data["LinkedIn_Cache"] = (
                            ". ".join(sentences[:3])
                        )
                        console.print(
                            f"    [green]LinkedIn cache : "
                            f"{sentences[0][:50]}...[/green]"
                        )
                        found += 1
        except Exception:
            pass

        # METHODE 3 : DuckDuckGo cible
        try:
            queries = [
                f'site:linkedin.com "{name}" formation',
                f'"{name}" linkedin "EFREI" OR "Bordeaux"',
            ]
            for query in queries:
                r = requests.get(
                    "https://html.duckduckgo.com/html/",
                    params={"q": query},
                    headers=self.headers_web,
                    timeout=10
                )
                soup = BeautifulSoup(r.text, "html.parser")
                for el in soup.find_all(
                    class_=re.compile("result__snippet")
                )[:3]:
                    snippet = el.get_text(" ", strip=True)
                    if (snippet
                            and any(p in snippet.lower() for p in name_parts)
                            and len(snippet) > 30):
                        key = f"LinkedIn_DDG_{found}"
                        self.target.deep_data[key] = snippet[:200]
                        console.print(
                            f"    [cyan]LinkedIn DDG : {snippet[:50]}...[/cyan]"
                        )
                        found += 1
                time.sleep(0.5)
        except Exception:
            pass

        if found == 0:
            console.print(
                "    [dim]LinkedIn : contenu protege par authentification[/dim]"
            )

        return found

    def _deep_rootme(self, url: str) -> int:
        found = 0
        try:
            r = requests.get(url, headers=self.headers_web, timeout=10)
            if r.status_code == 200:
                text = r.text
                if not isinstance(self.target.deep_data, dict):
                    self.target.deep_data = {}

                score = re.search(r'(\d+)\s*(?:points?|pts)', text)
                if score:
                    self.target.deep_data["RootMe_Score"] = score.group(1) + " points"
                    console.print(
                        f"    [green]Root-Me score : {score.group(1)} pts[/green]"
                    )
                    found += 1

                rank = re.search(r'rang\s*:?\s*(\d+)', text, re.IGNORECASE)
                if rank:
                    self.target.deep_data["RootMe_Rank"] = f"Rang #{rank.group(1)}"
                    found += 1
        except Exception:
            pass
        return found

    def _deep_twitter(self, url: str) -> int:
        found = 0
        username = url.rstrip("/").split("/")[-1]
        if not username:
            return 0

        nitter_instances = [
            f"https://nitter.net/{username}",
            f"https://nitter.privacydev.net/{username}",
        ]

        for nitter_url in nitter_instances:
            try:
                r = requests.get(nitter_url, headers=self.headers_web, timeout=8)
                if r.status_code == 200:
                    soup = BeautifulSoup(r.text, "html.parser")

                    bio_el = soup.find(class_="profile-bio")
                    if bio_el:
                        bio_text = bio_el.get_text(" ", strip=True)
                        if not isinstance(self.target.deep_data, dict):
                            self.target.deep_data = {}
                        self.target.deep_data["Twitter_Bio"] = bio_text[:200]
                        console.print(
                            f"    [green]Twitter bio : {bio_text[:50]}...[/green]"
                        )
                        found += 1

                        for link in re.findall(r'https?://[^\s]+', bio_text):
                            platform = self._id_platform(link)
                            if platform and platform not in self.target.social_profiles:
                                self.target.social_profiles[platform] = link
                                found += 1

                    stats = soup.find_all(class_=re.compile("profile-stat"))
                    for stat in stats:
                        val = stat.find(class_=re.compile("profile-stat-num"))
                        label = stat.find(class_=re.compile("profile-stat-header"))
                        if val and label:
                            key = "Twitter_" + label.get_text(strip=True)
                            if not isinstance(self.target.deep_data, dict):
                                self.target.deep_data = {}
                            self.target.deep_data[key] = val.get_text(strip=True)
                    break
            except Exception:
                pass

        return found

    def _deep_instagram(self, url: str) -> int:
        found = 0
        try:
            r = requests.get(url, headers=self.headers_web, timeout=8)
            if r.status_code == 200:
                text = r.text
                if not isinstance(self.target.deep_data, dict):
                    self.target.deep_data = {}

                bio = re.search(r'"biography":"([^"]+)"', text)
                if bio:
                    bio_text = bio.group(1)
                    self.target.deep_data["Instagram_Bio"] = bio_text
                    console.print(
                        f"    [green]Instagram bio : {bio_text[:50]}[/green]"
                    )
                    found += 1

                    for link in re.findall(r'https?://[^\s"\\]+', bio_text):
                        platform = self._id_platform(link)
                        if platform and platform not in self.target.social_profiles:
                            self.target.social_profiles[platform] = link
                            found += 1

                followers = re.search(
                    r'"edge_followed_by":\{"count":(\d+)\}', text
                )
                if followers:
                    self.target.deep_data["Instagram_Followers"] = followers.group(1)
                    found += 1
        except Exception:
            pass
        return found

    def _deep_reddit(self, url: str) -> int:
        found = 0
        username = url.rstrip("/").split("/")[-1]
        try:
            r = requests.get(
                f"https://www.reddit.com/user/{username}/about.json",
                headers={"User-Agent": "KRONOS-OSINT/2.0"},
                timeout=8
            )
            if r.status_code == 200:
                data = r.json().get("data", {})
                if not isinstance(self.target.deep_data, dict):
                    self.target.deep_data = {}

                karma = data.get("total_karma", 0)
                created = data.get("created_utc", 0)

                if karma:
                    self.target.deep_data["Reddit_Karma"] = str(karma)
                    found += 1
                if created:
                    date = datetime.datetime.fromtimestamp(
                        created
                    ).strftime("%Y-%m-%d")
                    self.target.deep_data["Reddit_Depuis"] = date
                    found += 1

                console.print(f"    [cyan]Reddit karma : {karma}[/cyan]")
        except Exception:
            pass
        return found

    def _add_connection(self, conn: dict):
        username = conn.get("username", "")
        platform = conn.get("platform", "")
        existing = [
            (c.get("username"), c.get("platform"))
            for c in self.target.connections
        ]
        if (username, platform) not in existing:
            self.target.connections.append(conn)

    def _id_platform(self, url: str) -> str:
        mapping = {
            "instagram.com": "Instagram",
            "twitter.com": "Twitter",
            "x.com": "Twitter",
            "linkedin.com": "LinkedIn",
            "tiktok.com": "TikTok",
            "t.me": "Telegram",
            "youtube.com": "YouTube",
            "twitch.tv": "Twitch",
            "reddit.com": "Reddit",
            "discord.gg": "Discord",
            "discord.com": "Discord",
            "github.com": "GitHub",
            "gitlab.com": "GitLab",
            "medium.com": "Medium",
            "dev.to": "Dev.to",
            "soundcloud.com": "SoundCloud",
            "spotify.com": "Spotify",
            "behance.net": "Behance",
        }
        url_lower = url.lower()
        for domain, name in mapping.items():
            if domain in url_lower:
                return name
        return ""
