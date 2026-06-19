from fpdf import FPDF
from datetime import datetime
import math
import os
import re


def safe(text) -> str:
    replacements = {
        "—": "-", "–": "-",
        "’": "'", "‘": "'",
        "“": '"', "”": '"',
        "…": "...", "é": "e",
        "è": "e", "ê": "e",
        "ë": "e", "à": "a",
        "â": "a", "ä": "a",
        "î": "i", "ï": "i",
        "ô": "o", "ö": "o",
        "ù": "u", "û": "u",
        "ü": "u", "ç": "c",
        "É": "E", "À": "A",
        "È": "E", "Ô": "O",
        "«": '"', "»": '"',
    }
    result = str(text or "")
    for char, rep in replacements.items():
        result = result.replace(char, rep)
    result = result.encode('latin-1', errors='replace').decode('latin-1')
    return result


def deduplicate(profiles: dict) -> dict:
    seen_urls = set()
    seen_platforms = {}
    result = {}
    for platform, url in profiles.items():
        pc = (platform
              .replace("Holehe_", "")
              .replace("Email_", "")
              .replace("_", " ")
              .strip().lower())
        uc = url.lower().rstrip("/")
        if uc in seen_urls or pc in seen_platforms:
            continue
        seen_urls.add(uc)
        seen_platforms[pc] = True
        result[platform] = url
    return result


def get_account_details(platform: str, url: str, target) -> str:
    pl = platform.lower()
    ul = url.lower()
    github_data = getattr(target, "github_data", {})
    langs = github_data.get("languages", [])
    repos = github_data.get("repos_count", 0)
    commit_emails = github_data.get("commit_emails", [])
    activity = getattr(target, "activity_hours", {})
    peak = activity.get("peak_hour", None)

    if "holehe_" in pl or "email_" in pl:
        site = platform.replace("Holehe_", "").replace("Email_", "")
        email_used = ""
        if "avec " in url:
            email_used = url.split("avec ")[-1]
        elif "@" in url:
            m = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', url)
            if m:
                email_used = m.group(0)
        return safe(
            f"Email {email_used} enregistre sur {site} — detecte par Holehe"
        )

    if "github" in pl or "github" in ul:
        details = []
        if repos:
            details.append(f"{repos} repos publics")
        if langs:
            details.append("Langages : " + ", ".join(langs[:4]))
        if commit_emails:
            details.append("Email commits : " + commit_emails[0])
        if peak is not None:
            details.append(f"Pic activite : {peak}h")
        return safe(" · ".join(details) if details else "Profil public confirme")

    if "linkedin" in pl or "linkedin" in ul:
        details = ["Profil professionnel"]
        notes = getattr(target, "notes", "") or ""
        if "efrei" in notes.lower():
            details.append("Formation : EFREI")
        locs = getattr(target, "locations", [])
        if locs:
            details.append("Localisation : " + locs[0].get("location", ""))
        details.append("Source : README GitHub (pivot)")
        return safe(" · ".join(details))

    if any(k in pl or k in ul for k in [
        "root-me", "hackthebox", "tryhackme", "root_me"
    ]):
        username = getattr(target, "username", "") or ""
        return safe(
            f"Alias {username} confirme · "
            f"Plateforme cybersecurite / CTF · Expertise hacking ethique"
        )

    if "youtube" in pl or "youtube" in ul:
        username = getattr(target, "username", "") or ""
        return safe(f"Chaine YouTube @{username} · Detecte via Sherlock")

    if "twitter" in pl or "x.com" in ul:
        emails = getattr(target, "emails_found", [])
        email_str = emails[0] if emails else ""
        return safe(f"Email {email_str} enregistre · Detecte via Holehe")

    if "instagram" in pl or "instagram" in ul:
        return safe("Compte detecte · Contenu accessible sur profil public")

    if "telegram" in pl or "t.me" in ul:
        return safe("Presence Telegram confirmee")

    if "reddit" in pl or "reddit" in ul:
        return safe("Compte Reddit confirme via API officielle")

    if "hackernews" in pl or "ycombinator" in ul:
        return safe("Compte HackerNews confirme · Communaute tech")

    if "@" in url or "detecte" in url.lower():
        return safe(url[:80])

    return safe("Compte confirme · " + url[:60])


def get_status_label(platform: str, url: str) -> str:
    pl = platform.lower()
    if any(k in pl for k in [
        "github", "root-me", "hackthebox",
        "tryhackme", "linkedin", "reddit",
        "hackernews", "gitlab"
    ]):
        return "CONFIRME"
    if any(k in pl for k in ["holehe_", "email_"]):
        return "VIA EMAIL"
    return "DETECTE"


def get_category(platform: str, url: str) -> str:
    combined = platform.lower() + " " + url.lower()
    if any(k in combined for k in [
        "linkedin", "viadeo", "malt", "behance", "dribbble"
    ]):
        return "Professionnel"
    if any(k in combined for k in [
        "github", "gitlab", "codeberg", "root-me",
        "hackthebox", "tryhackme", "stackoverflow",
        "hackerearth", "codewars", "dev.to", "hackmd", "kaggle"
    ]):
        return "Dev / Cybersec"
    if any(k in combined for k in [
        "twitter", "instagram", "facebook", "tiktok",
        "youtube", "snapchat", "reddit", "mastodon",
        "bluesky", "telegram", "discord", "twitch"
    ]):
        return "Reseau social"
    if any(k in combined for k in [
        "steam", "xbox", "chess", "osu", "pokemon", "warframe", "epic"
    ]):
        return "Gaming"
    return "Autre"


def format_breach(breach: dict) -> dict:
    name_raw = breach.get("Name") or breach.get("name", "")
    if isinstance(name_raw, dict):
        name_raw = name_raw.get("name", "") or name_raw.get("Name", "")
    name = (str(name_raw)
            .replace("{", "").replace("}", "")
            .replace("'name':", "").replace("'Name':", "")
            .replace("'date':", "").replace("''", "")
            .strip(" ,"))
    if not name or name in ["?", "None", ""]:
        name = "Service non identifie"

    date_raw = breach.get("date") or breach.get("BreachDate", "")
    date_str = str(date_raw)[:10] if date_raw else "N/A"
    source = breach.get("source", "N/A")

    exposed_map = {
        "stealer": (
            "Mots de passe · Cookies de session · "
            "Donnees de navigation · Credentials"
        ),
        "linkedin": "Emails · Mots de passe chiffres · Noms d'utilisateur",
        "adobe": "Emails · Mots de passe chiffres · Questions de securite",
        "zynga": "Emails · Mots de passe · Donnees de compte",
        "chegg": "Emails · Mots de passe · Noms · Dates de naissance",
        "000webhost": "Emails · Mots de passe en clair · Adresses IP",
    }
    data_exposed = "Donnees de compte"
    for key, val in exposed_map.items():
        if key in name.lower():
            data_exposed = val
            break

    return {
        "name": safe(name),
        "date": safe(date_str),
        "source": safe(source),
        "exposed": safe(data_exposed),
    }


class KronosPDF(FPDF):
    _meta = ""

    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("Courier", "", 7)
        self.set_text_color(130, 130, 130)
        self.set_y(8)
        self.cell(
            90, 4,
            "KRONOS INTELLIGENCE SYSTEM",
            align="L", new_x="RIGHT", new_y="LAST"
        )
        self.cell(
            90, 4, self._meta,
            align="R", new_x="LMARGIN", new_y="NEXT"
        )
        self.set_draw_color(180, 180, 180)
        self.set_line_width(0.3)
        self.line(15, 14, 195, 14)
        self.set_text_color(20, 20, 20)
        self.ln(2)

    def footer(self):
        if self.page_no() == 1:
            return
        self.set_y(-12)
        self.set_font("Courier", "", 7)
        self.set_text_color(150, 150, 150)
        self.cell(0, 4, f"- {self.page_no() - 1} -", align="C")


def th(pdf, headers, widths):
    pdf.set_fill_color(235, 235, 235)
    pdf.set_font("Courier", "", 7)
    pdf.set_text_color(90, 90, 90)
    pdf.set_draw_color(180, 180, 180)
    pdf.set_line_width(0.2)
    y = pdf.get_y()
    x_start = 15
    for i, (h, w) in enumerate(zip(headers, widths)):
        x = x_start + sum(widths[:i])
        pdf.set_xy(x, y)
        pdf.cell(
            w, 7,
            safe(h.upper())[:20],
            border=1, fill=True, align="L",
            new_x="RIGHT", new_y="LAST"
        )
    pdf.set_xy(x_start, y + 7)


def tr(pdf, cells, widths, bold=False, line_h=5):
    font_style = "B" if bold else ""
    pdf.set_font("Helvetica", font_style, 9)
    max_lines = 1
    for cell, w in zip(cells, widths):
        txt = safe(str(cell or ""))
        chars_per_line = max(1, int((w - 2) / 1.9))
        lines = math.ceil(len(txt) / chars_per_line) if txt else 1
        max_lines = max(max_lines, min(lines, 5))
    row_h = max_lines * line_h + 2

    if pdf.get_y() + row_h > pdf.h - 20:
        pdf.add_page()

    y_start = pdf.get_y()
    x_start = 15

    for i, (cell, w) in enumerate(zip(cells, widths)):
        txt = safe(str(cell or "N/A"))
        x = x_start + sum(widths[:i])
        pdf.set_draw_color(200, 200, 200)
        pdf.set_line_width(0.1)
        pdf.rect(x, y_start, w, row_h)
        pdf.set_font("Helvetica", font_style, 9)
        pdf.set_text_color(20, 20, 20)
        pdf.set_xy(x + 1, y_start + 1)
        pdf.multi_cell(w - 2, line_h, txt[:200], border=0)
        pdf.set_xy(x_start + sum(widths[:i + 1]), y_start)

    pdf.set_xy(x_start, y_start + row_h)


def generate_pdf(target, output_path: str):
    name = getattr(target, "name", getattr(target, "domain", "Cible"))
    parts = name.strip().split()
    if len(parts) >= 2:
        name_display = f"{parts[-1].upper()}, {' '.join(parts[:-1])}"
    else:
        name_display = name.upper()

    date_safe = safe(datetime.now().strftime("%d %B %Y"))

    raw_profiles = getattr(target, "social_profiles", {})
    profiles = deduplicate(raw_profiles)
    emails = list(dict.fromkeys(getattr(target, "emails_found", [])))
    breaches = getattr(target, "breaches", [])
    locations = getattr(target, "locations", [])
    correlations = getattr(target, "correlations", [])
    risk_score = getattr(target, "risk_score", 0)
    username = getattr(target, "username", "") or ""
    usernames = list(dict.fromkeys(filter(None, [
        username
    ] + getattr(target, "usernames_found", []))))
    github_data = getattr(target, "github_data", {})
    langs = github_data.get("languages", [])
    repos_count = github_data.get("repos_count", 0)
    commit_emails = github_data.get("commit_emails", [])
    profile_type = getattr(target, "profile_type", "")
    personal_info = getattr(target, "personal_info", {})
    deep_data = getattr(target, "deep_data", {})
    activity = getattr(target, "activity_hours", {})
    peak = activity.get("peak_hour", None)
    connections = getattr(target, "connections", [])
    notes = getattr(target, "notes", "") or ""

    type_labels = {
        "developer": "Informaticien / Cybersecurite",
        "influencer": "Createur de contenu",
        "business": "Professionnel / Entrepreneur",
        "gamer": "Gamer / Streamer",
        "academic": "Chercheur / Etudiant",
        "regular": "Particulier",
        "public_figure": "Figure publique",
    }
    profile_label = type_labels.get(profile_type, profile_type or "N/A")

    if peak is not None:
        if 6 <= peak <= 12:
            period = f"{peak}h00 (matin)"
        elif 12 <= peak <= 18:
            period = f"{peak}h00 (apres-midi)"
        elif 18 <= peak <= 22:
            period = f"{peak}h00 (soir)"
        else:
            period = f"{peak}h00 (nuit)"
    else:
        period = "N/A"

    pdf = KronosPDF()
    pdf._meta = safe(f"DOSSIER : {name} · {date_safe}")
    pdf.set_margins(15, 18, 15)
    pdf.set_auto_page_break(auto=True, margin=16)

    # ─────────────────────────────
    # PAGE DE GARDE
    # ─────────────────────────────
    pdf.add_page()

    # Dégradé blanc → gris clair
    for i in range(100):
        gray = int(255 - i * 0.7)
        pdf.set_fill_color(gray, gray, gray)
        pdf.rect(0, i * 2.97, 210, 2.97, "F")

    # Bandeau noir en haut
    pdf.set_fill_color(17, 17, 17)
    pdf.rect(0, 0, 210, 14, "F")
    pdf.set_font("Courier", "", 7)
    pdf.set_text_color(200, 200, 200)
    pdf.set_y(5)
    pdf.cell(
        60, 4,
        "KRONOS INTELLIGENCE SYSTEM",
        align="L", new_x="RIGHT", new_y="LAST"
    )
    pdf.set_text_color(150, 150, 150)
    pdf.cell(
        60, 4,
        safe("DOSSIER D'ENQUETE - CONFIDENTIEL"),
        align="C", new_x="RIGHT", new_y="LAST"
    )
    pdf.cell(
        60, 4,
        safe(f"REF: KRN-{datetime.now().strftime('%Y-%m%d')}-001"),
        align="R", new_x="LMARGIN", new_y="NEXT"
    )

    # Sous-titre
    pdf.set_y(30)
    pdf.set_font("Courier", "", 8)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(
        0, 5,
        "FICHE SUJET - RAPPORT D'INVESTIGATION OSINT",
        align="C", new_x="LMARGIN", new_y="NEXT"
    )
    pdf.ln(8)

    # Photo + identité
    photo_x = 20
    photo_y = pdf.get_y()
    photo_w = 42
    photo_h = 54

    # Cadre photo
    pdf.set_draw_color(150, 150, 150)
    pdf.set_fill_color(245, 245, 245)
    pdf.set_line_width(0.5)
    pdf.rect(photo_x, photo_y, photo_w, photo_h, "FD")
    pdf.set_font("Courier", "", 7)
    pdf.set_text_color(160, 160, 160)
    pdf.set_xy(photo_x, photo_y + photo_h / 2 - 4)
    pdf.cell(
        photo_w, 4, "PHOTO",
        align="C", new_x="LMARGIN", new_y="NEXT"
    )
    gh_user = github_data.get("username", username)
    if gh_user:
        pdf.set_xy(photo_x, photo_y + photo_h / 2 + 2)
        pdf.set_font("Courier", "", 6)
        pdf.cell(
            photo_w, 4,
            safe(f"github/{gh_user}"),
            align="C", new_x="LMARGIN", new_y="NEXT"
        )

    # Nom & infos à droite de la photo
    info_x = photo_x + photo_w + 10
    info_w = 195 - info_x
    pdf.set_xy(info_x, photo_y)

    name_parts = name.strip().split()
    if len(name_parts) >= 2:
        pdf.set_font("Helvetica", "B", 24)
        pdf.set_text_color(20, 20, 20)
        pdf.cell(
            info_w, 12,
            safe(name_parts[-1].upper()),
            new_x="LMARGIN", new_y="NEXT"
        )
        pdf.set_x(info_x)
        pdf.set_font("Helvetica", "B", 18)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(
            info_w, 10,
            safe(" ".join(name_parts[:-1])),
            new_x="LMARGIN", new_y="NEXT"
        )
    else:
        pdf.set_font("Helvetica", "B", 24)
        pdf.set_text_color(20, 20, 20)
        pdf.cell(
            info_w, 12,
            safe(name.upper()),
            new_x="LMARGIN", new_y="NEXT"
        )

    if usernames:
        pdf.set_x(info_x)
        pdf.set_font("Courier", "", 9)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(
            info_w, 6,
            safe("ALIAS : " + " · ".join(usernames[:3])),
            new_x="LMARGIN", new_y="NEXT"
        )

    pdf.ln(4)

    # Tableau d'identité
    fields = [
        ("STATUT", profile_label),
        ("LOCALISATION", locations[0]["location"] if locations else "N/A"),
        ("SCORE EXPOSITION", f"{risk_score}/100"),
        ("DATE ENQUETE", date_safe),
        ("COMPTES DETECTES", str(len(profiles))),
        ("EMAILS IDENTIFIES", str(len(emails))),
        ("FUITES DETECTEES", str(len(breaches))),
        ("SOURCES ANALYSEES", "GitHub · Sherlock · Holehe · LeakCheck"),
    ]

    col1_w = 55
    col2_w = info_w - col1_w
    row_h = 7

    for i, (label, value) in enumerate(fields):
        y_row = pdf.get_y()
        if i == 0:
            y_row = photo_y + 38
        pdf.set_xy(info_x, y_row)
        bg = 250 if i % 2 == 0 else 255
        pdf.set_fill_color(bg, bg, bg)
        pdf.set_draw_color(200, 200, 200)
        pdf.set_line_width(0.2)
        pdf.set_font("Courier", "", 7)
        pdf.set_text_color(120, 120, 120)
        pdf.cell(
            col1_w, row_h,
            safe(label),
            border=1, fill=True,
            new_x="RIGHT", new_y="LAST"
        )
        pdf.set_font("Courier", "", 8)
        pdf.set_text_color(20, 20, 20)
        pdf.cell(
            col2_w, row_h,
            safe(str(value)[:50]),
            border=1, fill=False,
            new_x="LMARGIN", new_y="NEXT"
        )

    # Silhouette KRONOS centrée
    cx = 105
    cy = 185
    pdf.set_fill_color(30, 30, 30)
    pdf.set_draw_color(30, 30, 30)
    pdf.polygon(
        [[cx, cy], [cx + 5, cy + 22],
         [cx + 2, cy + 20], [cx, cy + 16],
         [cx - 2, cy + 20], [cx - 5, cy + 22]],
        style="F"
    )
    pdf.set_line_width(2)
    pdf.line(cx, cy + 22, cx, cy + 65)
    pdf.set_line_width(1.2)
    pdf.line(cx - 10, cy + 40, cx + 10, cy + 40)
    pdf.set_line_width(0.8)
    pdf.line(cx - 7, cy + 47, cx + 7, cy + 47)
    pdf.set_line_width(2)
    pdf.line(cx, cy + 65, cx, cy + 72)
    pdf.polygon(
        [[cx - 3, cy + 72],
         [cx + 3, cy + 72],
         [cx, cy + 78]],
        style="F"
    )

    pdf.set_font("Courier", "B", 36)
    pdf.set_text_color(20, 20, 20)
    pdf.set_y(cy + 80)
    pdf.cell(0, 14, "KRONOS", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_draw_color(120, 120, 120)
    pdf.set_line_width(0.3)
    pdf.line(70, pdf.get_y(), 140, pdf.get_y())
    pdf.ln(2)
    pdf.set_font("Courier", "", 7)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(
        0, 5, "OSINT INTELLIGENCE SYSTEM",
        align="C", new_x="LMARGIN", new_y="NEXT"
    )

    pdf.set_y(277)
    pdf.set_font("Courier", "", 7)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(
        0, 4,
        "USAGE STRICTEMENT RESTREINT - NE PAS DIFFUSER",
        align="C", new_x="LMARGIN", new_y="NEXT"
    )

    # ─────────────────────────────
    # PAGES CONTENU
    # ─────────────────────────────
    pdf.add_page()
    sec = 1

    def section(num: int, title: str):
        pdf.ln(3)
        pdf.set_fill_color(17, 17, 17)
        pdf.set_font("Courier", "B", 8)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(
            12, 6,
            f"0{num}" if num < 10 else str(num),
            fill=True, align="C",
            new_x="RIGHT", new_y="LAST"
        )
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(20, 20, 20)
        pdf.set_x(pdf.get_x() + 4)
        pdf.cell(0, 6, safe(title), new_x="LMARGIN", new_y="NEXT")
        pdf.set_draw_color(20, 20, 20)
        pdf.set_line_width(0.4)
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        pdf.ln(4)

    # ─── SECTION 1 : IDENTIFIANTS ───
    section(sec, "IDENTIFIANTS ET CONTACTS")
    sec += 1

    th(pdf, ["TYPE", "VALEUR", "SOURCE", "FIABILITE"], [38, 70, 52, 20])

    id_rows = []
    for email in emails:
        if email in commit_emails:
            src = "GitHub commits"
        elif "efrei" in email.lower():
            src = "Pivot RecursivePivot"
        else:
            src = "Holehe / pivot"
        id_rows.append(("EMAIL", email, src, "HAUTE"))

    for u in usernames:
        id_rows.append(("ALIAS", u, "GitHub API + Sherlock", "CERTAINE"))

    if langs:
        id_rows.append((
            "LANGAGES CODE",
            " · ".join(langs[:5]),
            f"Analyse {repos_count} repos GitHub",
            "CERTAINE"
        ))
    if repos_count:
        id_rows.append(("REPOS PUBLICS", str(repos_count), "GitHub API", "CERTAINE"))
    if peak is not None:
        id_rows.append(("PIC D'ACTIVITE", period, "Horodatages GitHub commits", "ESTIMEE"))
    if locations:
        for loc in locations:
            id_rows.append((
                "LOCALISATION",
                loc.get("location", ""),
                f"Profil {loc.get('source', '')}",
                "PROBABLE"
            ))
    if notes:
        id_rows.append(("CONTEXTE CONNU", notes[:80], "Fourni par l'operateur", "INFO"))

    for row in id_rows:
        tr(pdf, list(row), [38, 70, 52, 20])

    # ─── SECTION 2 : COMPTES ───
    section(sec, "COMPTES EN LIGNE - DETAIL")
    sec += 1

    th(pdf,
       ["PLATEFORME", "URL / IDENTIFIANT", "DONNEES TROUVEES", "CATEGORIE", "STATUT"],
       [28, 42, 62, 24, 24])

    for platform, url in profiles.items():
        clean = (platform
                 .replace("Holehe_", "")
                 .replace("Email_", "")
                 .replace("_", " ")
                 .strip())
        details = get_account_details(platform, url, target)
        category = get_category(platform, url)
        status = get_status_label(platform, url)

        display_url = url
        if "avec " in url:
            display_url = url.split("avec ")[1][:35]
        elif len(url) > 40:
            display_url = url[:37] + "..."

        tr(pdf,
           [clean[:16], display_url[:38], details[:90], category[:20], status],
           [28, 42, 62, 24, 24])

    # ─── SECTION 3 : FUITES ───
    if breaches:
        section(sec, f"INCIDENTS DE SECURITE ({len(breaches)} DETECTE(S))")
        sec += 1

        th(pdf,
           ["INCIDENT", "DATE", "DONNEES EXPOSEES", "SOURCE"],
           [32, 20, 80, 48])
        for breach in breaches:
            bd = format_breach(breach)
            tr(pdf,
               [bd["name"], bd["date"], bd["exposed"], bd["source"]],
               [32, 20, 80, 48])

    # ─── SECTION 4 : PROFIL COMPORTEMENTAL ───
    section(sec, "PROFIL COMPORTEMENTAL")
    sec += 1

    behavior_rows = []
    if peak is not None:
        behavior_rows.append((
            "PERIODE D'ACTIVITE", period,
            "Analyse horodatages GitHub commits"
        ))
    if langs:
        behavior_rows.append((
            "COMPETENCES TECHNIQUES",
            " · ".join(langs[:6]),
            f"{repos_count} repos analyses"
        ))
    if profile_type:
        behavior_rows.append((
            "PROFIL DETECTE PAR IA", profile_label, "Groq llama-3.3-70b"
        ))

    interests = []
    for platform, _ in profiles.items():
        pl = platform.lower()
        if any(k in pl for k in ["root-me", "hackthebox", "tryhackme"]):
            if "Cybersecurite / CTF" not in interests:
                interests.append("Cybersecurite / CTF")
        if "spotify" in pl or "soundcloud" in pl:
            if "Musique" not in interests:
                interests.append("Musique")
        if "youtube" in pl:
            if "Video / Streaming" not in interests:
                interests.append("Video / Streaming")
    if interests:
        behavior_rows.append((
            "CENTRES D'INTERET",
            " · ".join(interests),
            "Analyse comptes detectes"
        ))
    if username:
        behavior_rows.append((
            "STYLE DE PSEUDO", username,
            "Meme alias sur toutes les plateformes techniques"
        ))

    if behavior_rows:
        th(pdf, ["CRITERE", "VALEUR", "SOURCE / METHODE"], [42, 72, 66])
        for row in behavior_rows:
            tr(pdf, list(row), [42, 72, 66])

    # ─── SECTION 5 : CONNEXIONS ───
    if connections:
        section(sec, f"RESEAU DE RELATIONS ({len(connections)} CONNEXION(S))")
        sec += 1

        th(pdf, ["USERNAME", "PLATEFORME", "TYPE DE LIEN", "URL"], [40, 30, 30, 80])
        for conn in connections[:20]:
            tr(pdf,
               [conn.get("username", "N/A")[:18],
                conn.get("platform", "N/A")[:14],
                conn.get("type", "N/A")[:14],
                conn.get("url", "N/A")[:50]],
               [40, 30, 30, 80])

    # ─── SECTION 6 : CORRELATIONS IA ───
    if correlations:
        section(sec, f"CORRELATIONS IDENTIFIEES ({len(correlations)})")
        sec += 1

        th(pdf, ["N", "CORRELATION", "ELEMENTS RELIES"], [10, 100, 70])
        for i, corr in enumerate(correlations, 1):
            if not corr.strip():
                continue
            elements = re.findall(r'`([^`]+)`|"([^"]+)"', corr)
            elem_str = " · ".join([
                e[0] or e[1] for e in elements[:3]
            ]) if elements else ""
            tr(pdf,
               [str(i), safe(corr[:95]), safe(elem_str[:65])],
               [10, 100, 70])

    # ─── SECTION 7 : DONNEES EXTRAITES EN PROFONDEUR ───
    if deep_data:
        section(sec, f"DONNEES EXTRAITES EN PROFONDEUR ({len(deep_data)})")
        sec += 1

        th(pdf, ["SOURCE", "TYPE", "VALEUR"], [40, 40, 100])
        for key, value in deep_data.items():
            parts = key.split("_", 1)
            source = parts[0] if parts else key
            dtype = parts[1].replace("_", " ") if len(parts) > 1 else ""
            if isinstance(value, list):
                value = ", ".join(str(v) for v in value[:5])
            tr(pdf,
               [source[:18], dtype[:18], str(value)[:90]],
               [40, 40, 100])

    # ─── SECTION 8 : INFORMATIONS PERSONNELLES ───
    if personal_info:
        section(sec, "INFORMATIONS PERSONNELLES")
        sec += 1

        th(pdf, ["TYPE", "VALEUR", "SOURCE", "FIABILITE"], [38, 70, 52, 20])
        for key, value in personal_info.items():
            tr(pdf,
               [key.upper(), str(value)[:60], "Annuaire / Web", "A VERIFIER"],
               [38, 70, 52, 20])

    try:
        pdf.output(output_path)
        print(f"[KRONOS] PDF : {output_path}")
    except Exception as e:
        print(f"[KRONOS] Erreur PDF : {e}")
        raise
