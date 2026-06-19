import os
import re
import time
import requests
import subprocess
from collections import deque
from rich.console import Console
from bs4 import BeautifulSoup

console = Console()


class IntelEngine:
    """
    Moteur d'intelligence recursif.
    Chaque decouverte genere de nouvelles taches.
    Le systeme creuse jusqu'a epuisement des pistes
    ou profondeur max.
    """

    MAX_DEPTH = 4
    MAX_TASKS = 80

    def __init__(self, target):
        self.target = target
        self.queue = deque()
        self.visited = set()
        self.tasks_done = 0

        self.gh_token = os.getenv("GITHUB_TOKEN", "")
        self.gh_headers = (
            {"Authorization": f"token {self.gh_token}"}
            if self.gh_token else {}
        )
        self.web_headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64) "
                "AppleWebKit/537.36 Chrome/120.0.0.0"
            )
        }

    def add_task(self, task_type, value, depth=0, source=""):
        if not value or not value.strip():
            return
        key = f"{task_type}:{value.strip().lower()}"
        if (key in self.visited
                or self.tasks_done >= self.MAX_TASKS
                or depth >= self.MAX_DEPTH):
            return
        self.visited.add(key)
        self.queue.append({
            "type": task_type,
            "value": value.strip(),
            "depth": depth,
            "source": source
        })

    def seed(self):
        d = 0
        if self.target.email:
            self.add_task("email", self.target.email, d, "initial")
        for e in self.target.emails_found:
            self.add_task("email", e, d, "initial")
        if self.target.username:
            self.add_task("username", self.target.username, d, "initial")
        for platform, url in self.target.social_profiles.items():
            self.add_task("url", url, d, f"initial_{platform}")
            pl = platform.lower()
            if "github" in pl:
                u = url.rstrip("/").split("/")[-1]
                self.add_task("github", u, d, "initial")
            elif "linkedin" in pl:
                self.add_task("linkedin", url, d, "initial")
        self.add_task("name", self.target.name, d, "initial")

    def run(self):
        self.seed()
        console.print(
            f"    [cyan]{len(self.queue)} taches initiales "
            f"- pivot recursif...[/cyan]"
        )

        while self.queue and self.tasks_done < self.MAX_TASKS:
            task = self.queue.popleft()
            self.tasks_done += 1
            t, v, d = task["type"], task["value"], task["depth"]

            console.print(
                f"    [dim][{self.tasks_done}] {t}: {v[:40]} (depth {d})[/dim]"
            )

            new_info = []
            if t == "email":
                new_info = self._pivot_email(v, d)
            elif t == "username":
                new_info = self._pivot_username(v, d)
            elif t == "github":
                new_info = self._pivot_github(v, d)
            elif t == "linkedin":
                new_info = self._pivot_linkedin(v, d)
            elif t == "url":
                new_info = self._pivot_url(v, d)
            elif t == "name":
                new_info = self._pivot_name(v, d)
            elif t == "phone":
                new_info = self._pivot_phone(v, d)

            for info in new_info:
                self.add_task(info["type"], info["value"], d + 1, f"{t}:{v[:20]}")

            if self.tasks_done % 10 == 0:
                console.print(
                    f"    [cyan]{self.tasks_done} taches, "
                    f"{len(self.queue)} en attente[/cyan]"
                )

        console.print(
            f"    [bold cyan]Pivot termine : {self.tasks_done} taches, "
            f"{len(self.target.social_profiles)} profils, "
            f"{len(self.target.emails_found)} emails[/bold cyan]"
        )

    # ──────────────────────────────
    # PIVOTS
    # ──────────────────────────────

    def _pivot_email(self, email, depth):
        new = []

        # Holehe
        try:
            result = subprocess.run(
                ["holehe", email, "--only-used", "--no-color"],
                capture_output=True, text=True, timeout=60
            )
            for line in result.stdout.splitlines():
                if "[+]" in line:
                    parts = line.strip().split()
                    if parts:
                        site = parts[-1].strip()
                        key = f"Holehe_{site}"
                        if key not in self.target.social_profiles:
                            self.target.social_profiles[key] = (
                                f"{email} utilise sur {site}"
                            )
                            console.print(f"    [green]Holehe: {site}[/green]")
        except Exception:
            pass

        # LeakCheck
        try:
            r = requests.get(
                f"https://leakcheck.io/api/public?check={email}",
                timeout=10
            )
            if r.status_code == 200:
                data = r.json()
                if data.get("success") and data.get("found"):
                    for src in data.get("sources", []):
                        breach = {"Name": src, "source": "LeakCheck", "email": email}
                        if breach not in self.target.breaches:
                            self.target.breaches.append(breach)
        except Exception:
            pass

        # Scylla
        try:
            r = requests.get(
                f"https://scylla.sh/search?q={email}&size=10",
                headers={"User-Agent": "KRONOS/2.0"}, timeout=10
            )
            if r.status_code == 200:
                data = r.json()
                for item in data[:5]:
                    src = item.get("_source", {})
                    breach = {
                        "Name": src.get("database_name", "Scylla"),
                        "source": "Scylla.sh", "email": email,
                    }
                    pwd = src.get("password", "")
                    if pwd:
                        breach["password"] = pwd
                    h = src.get("hash", "")
                    if h:
                        breach["hash"] = h
                    if breach not in self.target.breaches:
                        self.target.breaches.append(breach)
                        if pwd:
                            console.print("    [red]Scylla: password expose![/red]")
        except Exception:
            pass

        # BreachDirectory
        bd_key = os.getenv("BREACHDIRECTORY_API_KEY", "")
        if bd_key:
            try:
                r = requests.get(
                    "https://breachdirectory.p.rapidapi.com/",
                    params={"func": "auto", "term": email},
                    headers={
                        "X-RapidAPI-Key": bd_key,
                        "X-RapidAPI-Host": "breachdirectory.p.rapidapi.com"
                    }, timeout=10
                )
                if r.status_code == 200:
                    data = r.json()
                    if data.get("success"):
                        for item in data.get("result", [])[:10]:
                            entry = {
                                "Name": (item.get("sources", ["BreachDir"])[0]
                                         if item.get("sources") else "BreachDirectory"),
                                "source": "BreachDirectory", "email": email,
                            }
                            pwd = item.get("password", "")
                            if pwd and pwd != "N/A":
                                entry["password"] = pwd
                                console.print(
                                    f"    [red]BreachDir: password {pwd[:3]}***[/red]"
                                )
                            h = item.get("sha1", "")
                            if h:
                                entry["hash"] = h
                                entry["hash_type"] = "SHA1"
                            if entry not in self.target.breaches:
                                self.target.breaches.append(entry)
            except Exception:
                pass

        # Pivot: username from email local part
        local = email.split("@")[0]
        if local and local != (self.target.username or "").lower():
            new.append({"type": "username", "value": local})

        return new

    def _pivot_username(self, username, depth):
        new = []

        # Sherlock
        try:
            output_file = f"/tmp/sherlock_{username}.txt"
            result = subprocess.run(
                ["sherlock", username, "--output", output_file,
                 "--timeout", "8", "--print-found"],
                capture_output=True, text=True, timeout=180
            )

            found_urls = []
            if os.path.exists(output_file):
                with open(output_file) as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("http"):
                            found_urls.append(line)
                os.remove(output_file)

            for line in result.stdout.splitlines():
                m = re.search(r'https?://[^\s]+', line)
                if m and "[+]" in line:
                    found_urls.append(m.group(0))

            skip = [
                "discord.com", "smule.com", "boardgamegeek.com",
                "chess.com", "anilist", "aparat.com", "myanimelist"
            ]
            for url in set(found_urls):
                if any(s in url for s in skip):
                    continue
                platform = self._url_to_platform(url)
                if platform and platform not in self.target.social_profiles:
                    if self._verify_url(url, username):
                        self.target.social_profiles[platform] = url
                        console.print(f"    [green]{platform}: {url[:40]}[/green]")
                        new.append({"type": "url", "value": url})
                        if "github" in url.lower():
                            new.append({"type": "github", "value": username})
        except Exception:
            pass

        if depth < 2:
            for v in self._username_variants(username)[:5]:
                new.append({"type": "username", "value": v})

        return new

    def _pivot_github(self, username, depth):
        new = []

        # Profil
        try:
            r = requests.get(
                f"https://api.github.com/users/{username}",
                headers=self.gh_headers, timeout=8
            )
            if r.status_code == 200:
                data = r.json()

                if data.get("email"):
                    e = data["email"]
                    if e not in self.target.emails_found:
                        self.target.emails_found.append(e)
                        console.print(f"    [green]GitHub email: {e}[/green]")
                        new.append({"type": "email", "value": e})

                tw = data.get("twitter_username", "")
                if tw and "Twitter" not in self.target.social_profiles:
                    self.target.social_profiles["Twitter"] = f"https://twitter.com/{tw}"
                    new.append({"type": "url", "value": f"https://twitter.com/{tw}"})

                blog = data.get("blog", "") or ""
                if blog.startswith("http") and "Site_web" not in self.target.social_profiles:
                    self.target.social_profiles["Site_web"] = blog
                    new.append({"type": "url", "value": blog})

                loc = data.get("location", "") or ""
                if loc:
                    existing = [l.get("location") for l in self.target.locations]
                    if loc not in existing:
                        self.target.locations.append({"source": "GitHub", "location": loc})

                company = data.get("company", "") or ""
                if company:
                    self.target.deep_data["GitHub_Entreprise"] = company.strip("@")

                bio = data.get("bio", "") or ""
                if bio:
                    self.target.deep_data["GitHub_Bio"] = bio
                    for u in re.findall(r'https?://[^\s]+', bio):
                        new.append({"type": "url", "value": u})
        except Exception:
            pass

        # README
        for branch in ["main", "master"]:
            try:
                r = requests.get(
                    f"https://raw.githubusercontent.com"
                    f"/{username}/{username}/{branch}/README.md",
                    headers=self.gh_headers, timeout=5
                )
                if r.status_code == 200:
                    readme = r.text
                    for u in re.findall(r'https?://[^\s\)\]\"\'<>]+', readme):
                        pl = self._url_to_platform(u)
                        if pl and pl not in self.target.social_profiles:
                            self.target.social_profiles[pl] = u
                            console.print(f"    [green]README: {pl}[/green]")
                            new.append({"type": "url", "value": u})

                    skip_dom = ["example.com", "w3.org", "github.com", "noreply"]
                    for e in re.findall(r'[\w\.\-]+@[\w\.\-]+\.\w{2,}', readme):
                        if not any(s in e for s in skip_dom):
                            if e not in self.target.emails_found:
                                self.target.emails_found.append(e)
                                console.print(f"    [green]README email: {e}[/green]")
                                new.append({"type": "email", "value": e})
                    break
            except Exception:
                pass

        # Repos + commits
        try:
            r = requests.get(
                f"https://api.github.com/users/{username}/repos"
                f"?per_page=30&sort=updated",
                headers=self.gh_headers, timeout=8
            )
            if r.status_code == 200:
                repos = r.json()
                self.target.deep_data["GitHub_Repos"] = str(len(repos))

                langs = []
                for repo in repos:
                    lang = repo.get("language", "")
                    if lang and lang not in langs:
                        langs.append(lang)
                if langs:
                    self.target.deep_data["GitHub_Langages"] = ", ".join(langs[:8])
                    if not self.target.github_data.get("languages"):
                        self.target.github_data["languages"] = langs[:5]
                    if not self.target.github_data.get("repos_count"):
                        self.target.github_data["repos_count"] = len(repos)
                        self.target.github_data["username"] = username

                for repo in repos[:8]:
                    try:
                        r2 = requests.get(
                            f"https://api.github.com/repos/{username}"
                            f"/{repo['name']}/commits?per_page=15",
                            headers=self.gh_headers, timeout=5
                        )
                        if r2.status_code == 200:
                            for c in r2.json():
                                a = c.get("commit", {}).get("author", {})
                                e = a.get("email", "")
                                if (e and "noreply" not in e
                                        and "github" not in e
                                        and e not in self.target.emails_found):
                                    self.target.emails_found.append(e)
                                    console.print(
                                        f"    [green]Commit email ({repo['name']}): {e}[/green]"
                                    )
                                    new.append({"type": "email", "value": e})
                        time.sleep(0.1)
                    except Exception:
                        pass
        except Exception:
            pass

        # Orgs
        try:
            r = requests.get(
                f"https://api.github.com/users/{username}/orgs",
                headers=self.gh_headers, timeout=8
            )
            if r.status_code == 200:
                orgs = r.json()
                if orgs:
                    org_names = [o.get("login", "") for o in orgs if o.get("login")]
                    if org_names:
                        self.target.deep_data["GitHub_Orgs"] = " - ".join(org_names)
                        console.print(f"    [cyan]GitHub orgs: {', '.join(org_names[:3])}[/cyan]")
        except Exception:
            pass

        # Followers
        try:
            r = requests.get(
                f"https://api.github.com/users/{username}/followers?per_page=20",
                headers=self.gh_headers, timeout=8
            )
            if r.status_code == 200:
                followers = r.json()
                seen = set(c.get("username", "") for c in self.target.connections)
                for f in followers:
                    login = f.get("login", "")
                    if login and login not in seen:
                        self.target.connections.append({
                            "username": login, "platform": "GitHub",
                            "type": "follower", "url": f.get("html_url", "")
                        })
                        seen.add(login)
                if followers:
                    console.print(f"    [cyan]{len(followers)} followers GitHub[/cyan]")
        except Exception:
            pass

        # Activity hours
        try:
            r = requests.get(
                f"https://api.github.com/users/{username}/repos"
                f"?per_page=100&sort=updated",
                headers=self.gh_headers, timeout=8
            )
            if r.status_code == 200:
                hours = {}
                for repo in r.json():
                    updated = repo.get("updated_at", "")
                    if updated and len(updated) >= 13:
                        try:
                            hour = int(updated[11:13])
                            hours[hour] = hours.get(hour, 0) + 1
                        except Exception:
                            pass
                if hours:
                    peak = max(hours, key=hours.get)
                    self.target.activity_hours = {
                        "distribution": hours, "peak_hour": peak
                    }
        except Exception:
            pass

        return new

    def _pivot_linkedin(self, url, depth):
        new = []
        li_cookie = (
            os.getenv("LINKEDIN_SESSION_COOKIE", "")
            or getattr(self.target, "linkedin_cookie", "")
        )

        base_headers = {
            **self.web_headers,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
        }

        if li_cookie:
            base_headers["Cookie"] = f"li_at={li_cookie}; lang=v=2&lang=fr-fr"
            console.print("    [cyan]LinkedIn avec session cookie...[/cyan]")
        else:
            console.print("    [yellow]LinkedIn sans authentification[/yellow]")

        try:
            session = requests.Session()
            session.headers.update(base_headers)

            if li_cookie:
                session.get("https://www.linkedin.com", timeout=8)
                time.sleep(0.5)

            r = session.get(url, timeout=15, allow_redirects=True)
            if r.status_code == 200:
                text = r.text

                patterns = {
                    "LinkedIn_Titre": [r'"headline":"([^"]{5,200})"'],
                    "LinkedIn_About": [
                        r'"summary":"([^"]{20,1000})"',
                        r'"description":"([^"]{20,500})"',
                    ],
                    "LinkedIn_Ville": [
                        r'"locationName":"([^"]{3,100})"',
                        r'"geoLocationName":"([^"]{3,100})"',
                    ],
                    "LinkedIn_Ecoles": [r'"schoolName":"([^"]{2,100})"'],
                    "LinkedIn_Diplomes": [r'"degreeName":"([^"]{2,100})"'],
                    "LinkedIn_Domaines": [r'"fieldOfStudy":"([^"]{2,100})"'],
                    "LinkedIn_Entreprises": [r'"companyName":"([^"]{2,100})"'],
                    "LinkedIn_Postes": [r'"title":"([^"]{3,150})"'],
                    "LinkedIn_Connexions": [
                        r'"connectionsCount":(\d+)',
                        r'"followerCount":(\d+)',
                    ],
                }

                for key, pats in patterns.items():
                    if key in self.target.deep_data:
                        continue
                    all_vals = []
                    for pat in pats:
                        for m in re.findall(pat, text, re.I)[:5]:
                            v = m.strip()
                            if (v and len(v) > 1
                                    and v not in all_vals
                                    and "linkedin" not in v.lower()
                                    and "http" not in v.lower()):
                                all_vals.append(v)
                    if all_vals:
                        unique = list(dict.fromkeys(all_vals))[:5]
                        self.target.deep_data[key] = " | ".join(unique)[:300]
                        console.print(
                            f"    [green]LinkedIn "
                            f"{key.replace('LinkedIn_','')}: {unique[0][:50]}[/green]"
                        )

                # Location → target.locations
                ville = self.target.deep_data.get("LinkedIn_Ville", "")
                if ville:
                    first_loc = ville.split("|")[0].strip()
                    existing = [l.get("location") for l in self.target.locations]
                    if first_loc and first_loc not in existing:
                        self.target.locations.append(
                            {"source": "LinkedIn", "location": first_loc}
                        )

                # Emails in HTML
                skip_dom = ["linkedin.com", "example.com", "w3.org", "sentry.io"]
                for e in re.findall(r'[\w\.\-]+@[\w\.\-]+\.\w{2,}', text):
                    if not any(s in e for s in skip_dom):
                        if e not in self.target.emails_found:
                            self.target.emails_found.append(e)
                            console.print(f"    [green]LinkedIn email: {e}[/green]")
                            new.append({"type": "email", "value": e})

                # Skills
                skills = re.findall(r'"name":"([A-Z][a-zA-Z\s\+\#]{2,40})"', text)
                if skills:
                    filtered = [s for s in skills if len(s) > 2
                                and not any(x in s.lower() for x in
                                            ["linkedin", "http", "json", "null", "true", "false"])]
                    unique = list(dict.fromkeys(filtered))[:15]
                    if unique:
                        self.target.deep_data["LinkedIn_Competences"] = " - ".join(unique)
                        console.print(
                            f"    [green]LinkedIn competences: {', '.join(unique[:4])}[/green]"
                        )
        except Exception as e:
            console.print(f"    [dim]LinkedIn: {e}[/dim]")

        # DDG fallback
        name = self.target.name
        name_parts = name.lower().split()
        for query in [
            f'site:linkedin.com/in "{name}"',
            f'"{name}" linkedin formation OR entreprise',
        ]:
            try:
                r = requests.get(
                    "https://html.duckduckgo.com/html/",
                    params={"q": query},
                    headers=self.web_headers, timeout=10
                )
                soup = BeautifulSoup(r.text, "html.parser")
                for el in soup.find_all(class_=re.compile("result__snippet"))[:4]:
                    snippet = el.get_text(" ", strip=True)
                    if snippet and len(snippet) > 30 and any(
                        p in snippet.lower() for p in name_parts
                    ):
                        key = f"LinkedIn_Web_{len(self.target.deep_data)}"
                        self.target.deep_data[key] = snippet[:250]
                        console.print(f"    [cyan]LinkedIn DDG: {snippet[:50]}...[/cyan]")
                time.sleep(0.5)
            except Exception:
                pass

        return new

    def _pivot_url(self, url, depth):
        new = []
        skip = [
            "google.com", "duckduckgo.com", "facebook.com",
            "wikipedia.org", "amazon.com", "w3.org", "schema.org",
            "cdnjs.cloudflare.com", "bing.com",
            "discord.com", "discord.gg",
        ]
        if any(s in url for s in skip):
            return new

        try:
            r = requests.get(
                url, headers=self.web_headers,
                timeout=8, allow_redirects=True
            )
            if r.status_code != 200:
                return new

            text = r.text

            # Emails
            skip_dom = ["example.com", "w3.org", "sentry.io", "cloudflare.com", "noreply"]
            for e in re.findall(r'[\w\.\-]+@[\w\.\-]+\.\w{2,}', text):
                if not any(s in e for s in skip_dom):
                    if e not in self.target.emails_found:
                        self.target.emails_found.append(e)
                        console.print(f"    [green]Email ({url[:30]}): {e}[/green]")
                        new.append({"type": "email", "value": e})

            # Phones
            for phone in re.findall(
                r'0[67][\s\.\-]?\d{2}[\s\.\-]?\d{2}[\s\.\-]?\d{2}[\s\.\-]?\d{2}', text
            ):
                clean = re.sub(r'[\s\.\-]', '', phone)
                if len(clean) == 10 and len(set(clean)) > 3:
                    if "Telephone" not in self.target.personal_info:
                        self.target.personal_info["Telephone"] = clean
                        console.print(f"    [green]Tel: {clean}[/green]")
                        new.append({"type": "phone", "value": clean})

            # Social links
            social_patterns = {
                r'https?://(?:www\.)?twitter\.com/([\w]+)': "Twitter",
                r'https?://(?:www\.)?instagram\.com/([\w\.]+)': "Instagram",
                r'https?://(?:www\.)?linkedin\.com/in/([\w\-]+)': "LinkedIn",
                r'https?://t\.me/([\w]+)': "Telegram",
                r'https?://(?:www\.)?tiktok\.com/@([\w\.]+)': "TikTok",
                r'https?://(?:www\.)?github\.com/([\w\-]+)': "GitHub",
                r'https?://(?:www\.)?youtube\.com/(@[\w\-]+)': "YouTube",
            }
            bases = {
                "Twitter": "https://twitter.com/",
                "Instagram": "https://instagram.com/",
                "LinkedIn": "https://linkedin.com/in/",
                "Telegram": "https://t.me/",
                "TikTok": "https://tiktok.com/@",
                "GitHub": "https://github.com/",
                "YouTube": "https://youtube.com/",
            }
            for pattern, platform in social_patterns.items():
                for m in re.findall(pattern, text):
                    full_url = bases.get(platform, "") + m
                    if platform not in self.target.social_profiles:
                        self.target.social_profiles[platform] = full_url
                        console.print(f"    [green]{platform} via {url[:30]}: {m}[/green]")
                        new.append({"type": "url", "value": full_url})
                        if platform == "GitHub":
                            new.append({"type": "github", "value": m})
                        elif platform == "LinkedIn":
                            new.append({"type": "linkedin", "value": full_url})
        except Exception:
            pass

        return new

    def _pivot_name(self, name, depth):
        new = []
        if depth > 2:
            return new

        queries = [
            f'"{name}"',
            f'"{name}" site:linkedin.com',
            f'"{name}" github OR gitlab',
        ]

        for query in queries[:3]:
            try:
                r = requests.get(
                    "https://html.duckduckgo.com/html/",
                    params={"q": query},
                    headers=self.web_headers, timeout=10
                )
                soup = BeautifulSoup(r.text, "html.parser")
                for el in soup.find_all(class_=re.compile(r"result__url|result__a"))[:5]:
                    href = el.get("href", "") or el.get_text(strip=True)
                    if href.startswith("http"):
                        platform = self._url_to_platform(href)
                        if platform and platform not in self.target.social_profiles:
                            new.append({"type": "url", "value": href})
                            if "linkedin" in href:
                                new.append({"type": "linkedin", "value": href})
                            elif "github" in href:
                                u = href.rstrip("/").split("/")[-1]
                                new.append({"type": "github", "value": u})
                time.sleep(0.4)
            except Exception:
                pass

        return new

    def _pivot_phone(self, phone, depth):
        new = []
        for query in [f'"{phone}"', f'"{phone}" site:pagesjaunes.fr']:
            try:
                r = requests.get(
                    "https://html.duckduckgo.com/html/",
                    params={"q": query},
                    headers=self.web_headers, timeout=10
                )
                soup = BeautifulSoup(r.text, "html.parser")
                for el in soup.find_all(class_=re.compile("result__snippet"))[:3]:
                    text = el.get_text(" ", strip=True)
                    if text and len(text) > 20:
                        self.target.deep_data[f"Phone_Info_{phone}"] = text[:200]
                        console.print(f"    [cyan]Tel {phone}: {text[:40]}[/cyan]")
                time.sleep(0.3)
            except Exception:
                pass
        return new

    # ──────────────────────────────
    # HELPERS
    # ──────────────────────────────

    def _url_to_platform(self, url):
        mapping = {
            "twitter.com": "Twitter", "x.com": "Twitter",
            "instagram.com": "Instagram", "linkedin.com": "LinkedIn",
            "github.com": "GitHub", "gitlab.com": "GitLab",
            "tiktok.com": "TikTok", "youtube.com": "YouTube",
            "t.me": "Telegram", "discord.gg": "Discord",
            "reddit.com": "Reddit", "twitch.tv": "Twitch",
            "medium.com": "Medium", "dev.to": "Dev.to",
            "hackthebox.com": "HackTheBox", "tryhackme.com": "TryHackMe",
            "root-me.org": "Root-Me", "spotify.com": "Spotify",
        }
        url_lower = url.lower()
        for domain, name in mapping.items():
            if domain in url_lower:
                return name
        return ""

    def _username_variants(self, username):
        variants = []
        u = username.lower()
        base = re.sub(r'\d+$', '', u)
        if base and base != u:
            variants.append(base)
        clean = re.sub(r'[-_]', '', u)
        if clean and clean != u:
            variants.append(clean)
        return variants

    def _verify_url(self, url, username):
        skip_verify = ["discord", "tiktok", "instagram", "twitter", "snapchat"]
        if any(u in url.lower() for u in skip_verify):
            return True

        try:
            if "github.com" in url:
                r = requests.get(
                    f"https://api.github.com/users/{username}",
                    headers=self.gh_headers, timeout=5
                )
                return r.status_code == 200

            if "reddit.com" in url:
                r = requests.get(
                    f"https://www.reddit.com/user/{username}/about.json",
                    headers={"User-Agent": "KRONOS/2.0"}, timeout=5
                )
                return r.status_code == 200 and r.json().get("data") is not None

            r = requests.get(url, headers=self.web_headers, timeout=5, allow_redirects=True)
            return r.status_code == 200
        except Exception:
            return False
