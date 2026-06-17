from fpdf import FPDF
from datetime import datetime
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
    for char, replacement in replacements.items():
        result = result.replace(char, replacement)
    return result


def deduplicate_profiles(profiles: dict) -> dict:
    seen_urls = set()
    seen_platforms = {}
    result = {}

    for platform, url in profiles.items():
        platform_clean = (
            platform
            .replace("Holehe_", "")
            .replace("_", " ")
            .strip()
            .lower()
        )
        url_clean = url.lower().rstrip("/")

        if url_clean in seen_urls:
            continue
        if platform_clean in seen_platforms:
            continue

        seen_urls.add(url_clean)
        seen_platforms[platform_clean] = True
        result[platform] = url

    return result


def categorize_profiles(profiles: dict) -> dict:
    categories = {
        "Reseaux sociaux": {},
        "Plateformes pro": {},
        "Developpement": {},
        "Jeux video et loisirs": {},
        "Autres comptes": {},
    }

    social = [
        "twitter", "instagram", "facebook",
        "tiktok", "youtube", "snapchat",
        "pinterest", "mastodon", "bluesky",
        "bsky", "threads", "discord",
        "telegram", "whatsapp", "reddit",
        "clubhouse"
    ]
    pro = [
        "linkedin", "viadeo", "malt",
        "crunchbase", "pappers", "wellfound"
    ]
    dev = [
        "github", "gitlab", "codeberg",
        "hackthebox", "tryhackme", "root-me",
        "stackoverflow", "hackerearth",
        "hackerone", "bugcrowd", "codewars",
        "codeforces", "leetcode", "dev.to",
        "hackmd", "gitea"
    ]
    gaming = [
        "steam", "twitch", "xbox", "playstation",
        "chess", "osu", "pokemon", "warframe",
        "runescape", "battlenet", "epic"
    ]

    for platform, url in profiles.items():
        pl = platform.lower()
        url_l = url.lower()
        combined = pl + " " + url_l

        if any(k in combined for k in pro):
            categories["Plateformes pro"][platform] = url
        elif any(k in combined for k in dev):
            categories["Developpement"][platform] = url
        elif any(k in combined for k in gaming):
            categories["Jeux video et loisirs"][platform] = url
        elif any(k in combined for k in social):
            categories["Reseaux sociaux"][platform] = url
        else:
            categories["Autres comptes"][platform] = url

    return {k: v for k, v in categories.items() if v}


def format_breach(breach: dict) -> str:
    name = breach.get("Name") or breach.get("name", "Service inconnu")
    date = breach.get("date") or breach.get("BreachDate", "")

    if isinstance(name, dict):
        name = str(name)

    desc = "Votre compte a ete detecte dans une fuite de donnees"
    if name and name not in ["?", "{}", "Service inconnu"]:
        desc = f"Fuite detectee : {safe(name)}"

    if date and len(str(date)) >= 4:
        desc += f" (en {str(date)[:4]})"

    return desc


def format_holehe(platform: str, value: str) -> tuple:
    site = platform.replace("Holehe_", "").replace("Email_", "")
    email = ""
    if "avec " in value:
        email = value.split("avec ")[-1]
    elif "@" in value:
        match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', value)
        if match:
            email = match.group(0)
    return site, email


def generate_pdf(target, output_path: str):
    name = getattr(target, "name", getattr(target, "domain", "Cible"))
    date = datetime.now().strftime("%d %B %Y")
    date_safe = safe(date)

    raw_profiles = getattr(target, "social_profiles", {})
    profiles = deduplicate_profiles(raw_profiles)

    emails = list(dict.fromkeys(getattr(target, "emails_found", [])))
    breaches = getattr(target, "breaches", [])
    locations = getattr(target, "locations", [])
    correlations = getattr(target, "correlations", [])
    risk_score = getattr(target, "risk_score", 0)
    ai_summary = getattr(target, "ai_summary", "")
    usernames = list(dict.fromkeys(
        getattr(target, "usernames_found", [])
        + ([target.username] if getattr(target, "username", None) else [])
    ))
    github_data = getattr(target, "github_data", {})
    langs = github_data.get("languages", [])
    profile_type = getattr(target, "profile_type", "")
    categorized = categorize_profiles(profiles)

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.set_margins(20, 20, 20)

    def page_header():
        pdf.set_font("Courier", "", 7)
        pdf.set_text_color(160, 160, 160)
        pdf.set_y(12)
        pdf.cell(
            0, 4,
            "KRONOS - OSINT INTELLIGENCE REPORT",
            align="L", new_x="RIGHT", new_y="LAST"
        )
        pdf.cell(
            0, 4,
            f"{safe(name)} . {date_safe}",
            align="R", new_x="LMARGIN", new_y="NEXT"
        )
        pdf.set_draw_color(210, 210, 210)
        pdf.set_line_width(0.2)
        pdf.line(20, 18, 190, 18)
        pdf.set_text_color(20, 20, 20)
        pdf.set_y(24)

    def page_footer(num: int):
        pdf.set_y(-14)
        pdf.set_font("Courier", "", 8)
        pdf.set_text_color(180, 180, 180)
        pdf.cell(0, 4, f"- {num} -", align="C")

    def section_title(num: int, title: str):
        pdf.ln(4)
        pdf.set_font("Courier", "", 8)
        pdf.set_text_color(160, 160, 160)
        pdf.cell(
            0, 5,
            f"0{num}" if num < 10 else str(num),
            new_x="LMARGIN", new_y="NEXT"
        )
        pdf.set_font("Helvetica", "B", 15)
        pdf.set_text_color(20, 20, 20)
        pdf.cell(0, 8, safe(title), new_x="LMARGIN", new_y="NEXT")
        pdf.set_draw_color(20, 20, 20)
        pdf.set_line_width(0.5)
        pdf.line(20, pdf.get_y(), 190, pdf.get_y())
        pdf.ln(6)

    def label_value(label: str, value: str):
        pdf.set_font("Courier", "", 8)
        pdf.set_text_color(140, 140, 140)
        pdf.cell(55, 6, safe(label).upper(), new_x="RIGHT", new_y="LAST")
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(20, 20, 20)
        pdf.multi_cell(0, 6, safe(value), new_x="LMARGIN", new_y="NEXT")

    def profile_row(platform: str, url: str, note: str = ""):
        clean = (
            platform
            .replace("Holehe_", "")
            .replace("Email_", "")
            .replace("_", " ")
            .strip()
        )
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(20, 20, 20)
        pdf.cell(45, 6, safe(clean[:22]), new_x="RIGHT", new_y="LAST")

        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(60, 60, 60)

        display = url
        if "Compte detecte sur" in url or (
            "avec" in url and "@" in url
        ):
            site, email = format_holehe(platform, url)
            display = f"Compte detecte avec l'email {safe(email)}"
        elif len(url) > 70:
            display = url[:67] + "..."

        pdf.cell(0, 6, safe(display), new_x="LMARGIN", new_y="NEXT")

        if note:
            pdf.set_font("Helvetica", "I", 8)
            pdf.set_text_color(120, 120, 120)
            pdf.set_x(65)
            pdf.cell(0, 5, safe(note), new_x="LMARGIN", new_y="NEXT")

        pdf.set_draw_color(235, 235, 235)
        pdf.set_line_width(0.1)
        pdf.line(20, pdf.get_y(), 190, pdf.get_y())

    # ─────────────────────────────
    # PAGE DE GARDE
    # ─────────────────────────────
    pdf.add_page()

    for i in range(100):
        gray = int(255 - i * 0.7)
        pdf.set_fill_color(gray, gray, gray)
        pdf.rect(0, i * 2.97, 210, 2.97, "F")

    cx = 105
    pdf.set_fill_color(30, 30, 30)
    pdf.set_draw_color(30, 30, 30)
    pdf.set_line_width(0.5)

    pdf.polygon([
        [cx, 22], [cx + 6, 48],
        [cx + 2, 46], [cx, 40],
        [cx - 2, 46], [cx - 6, 48]
    ], style="F")

    pdf.set_line_width(2.5)
    pdf.line(cx, 48, cx, 200)

    pdf.set_line_width(1.5)
    pdf.line(cx - 14, 108, cx + 14, 108)
    pdf.set_line_width(1.0)
    pdf.line(cx - 9, 118, cx + 9, 118)

    pdf.set_line_width(2.5)
    pdf.line(cx, 200, cx, 210)
    pdf.set_fill_color(30, 30, 30)
    pdf.polygon([[cx - 4, 210], [cx + 4, 210], [cx, 220]], style="F")

    pdf.set_font("Courier", "B", 50)
    pdf.set_text_color(20, 20, 20)
    pdf.set_y(228)
    pdf.cell(0, 18, "KRONOS", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_draw_color(100, 100, 100)
    pdf.set_line_width(0.3)
    pdf.line(70, 249, 140, 249)

    pdf.set_font("Courier", "", 8)
    pdf.set_text_color(100, 100, 100)
    pdf.set_y(252)
    pdf.cell(
        0, 5, "OSINT INTELLIGENCE SYSTEM",
        align="C", new_x="LMARGIN", new_y="NEXT"
    )

    pdf.set_y(272)
    pdf.set_font("Courier", "", 7)
    pdf.set_text_color(160, 160, 160)
    pdf.cell(
        0, 4, "CONFIDENTIEL - USAGE RESTREINT",
        align="C", new_x="LMARGIN", new_y="NEXT"
    )

    page_num = 2

    # ─────────────────────────────
    # PAGE RÉSUMÉ
    # ─────────────────────────────
    pdf.add_page()
    page_header()
    section_title(1, "Resume de l'enquete")

    metrics = [
        ("Comptes trouves", str(len(profiles))),
        ("Emails trouves", str(len(emails))),
        ("Fuites de donnees", str(len(breaches))),
        ("Score de risque", f"{risk_score}/100"),
    ]

    col_w = 42
    y_start = pdf.get_y()
    for i, (label, value) in enumerate(metrics):
        x = 20 + i * col_w
        pdf.set_draw_color(200, 200, 200)
        pdf.set_line_width(0.3)
        pdf.rect(x, y_start, col_w - 2, 22)
        pdf.set_font("Courier", "B", 18)
        pdf.set_text_color(20, 20, 20)
        pdf.set_xy(x, y_start + 2)
        pdf.cell(col_w - 2, 9, value, align="C")
        pdf.set_font("Courier", "", 7)
        pdf.set_text_color(120, 120, 120)
        pdf.set_xy(x, y_start + 12)
        pdf.cell(col_w - 2, 5, label, align="C")

    pdf.set_y(y_start + 30)

    if ai_summary:
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(50, 50, 50)
        pdf.multi_cell(0, 6, safe(ai_summary))
        pdf.ln(4)

    pdf.ln(4)
    label_value("Personne ciblee", name)

    if usernames:
        label_value("Pseudos utilises", ", ".join(usernames[:5]))

    if profile_type:
        type_labels = {
            "developer": "Informaticien / Cybersecurite",
            "influencer": "Createur de contenu",
            "business": "Professionnel / Entrepreneur",
            "gamer": "Gamer / Streamer",
            "academic": "Chercheur / Etudiant",
            "regular": "Particulier",
            "public_figure": "Figure publique",
        }
        label_value(
            "Profil detecte",
            type_labels.get(profile_type, profile_type)
        )

    if langs:
        label_value("Langages code GitHub", ", ".join(langs[:5]))

    if locations:
        locs = ", ".join([
            l.get("location", "")
            for l in locations[:3]
            if l.get("location")
        ])
        if locs:
            label_value("Localisation", locs)

    page_footer(page_num)
    page_num += 2

    section_num = 2

    # ─────────────────────────────
    # PAGE EMAILS
    # ─────────────────────────────
    if emails:
        pdf.add_page()
        page_header()
        section_title(
            section_num,
            f"Adresses email trouvees ({len(emails)})"
        )
        section_num += 1

        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(50, 50, 50)
        pdf.multi_cell(
            0, 6,
            "Les adresses email suivantes ont ete "
            "identifiees comme appartenant a la cible :"
        )
        pdf.ln(6)

        for email in emails:
            pdf.set_font("Courier", "B", 10)
            pdf.set_text_color(20, 20, 20)
            pdf.cell(8, 7, ">", new_x="RIGHT", new_y="LAST")
            pdf.set_font("Courier", "", 10)
            pdf.cell(0, 7, safe(email), new_x="LMARGIN", new_y="NEXT")
            pdf.set_draw_color(230, 230, 230)
            pdf.line(20, pdf.get_y(), 190, pdf.get_y())

        page_footer(page_num)
        page_num += 2

    # ─────────────────────────────
    # PAGES PROFILS PAR CATÉGORIE
    # ─────────────────────────────
    cat_descriptions = {
        "Reseaux sociaux": (
            "Comptes sur les reseaux sociaux confirmes pour cette personne."
        ),
        "Plateformes pro": (
            "Presence professionnelle en ligne."
        ),
        "Developpement": (
            "Comptes sur des plateformes de programmation "
            "et de cybersecurite."
        ),
        "Jeux video et loisirs": (
            "Comptes sur des plateformes de gaming et de loisirs."
        ),
        "Autres comptes": (
            "Autres comptes identifies."
        ),
    }

    for cat, profs in categorized.items():
        if not profs:
            continue

        pdf.add_page()
        page_header()
        section_title(
            section_num,
            f"{safe(cat)} ({len(profs)} compte(s))"
        )
        section_num += 1

        desc = cat_descriptions.get(cat, "")
        if desc:
            pdf.set_font("Helvetica", "I", 9)
            pdf.set_text_color(100, 100, 100)
            pdf.multi_cell(0, 5, safe(desc))
            pdf.ln(4)

        for platform, url in profs.items():
            profile_row(platform, url)

        page_footer(page_num)
        page_num += 2

    # ─────────────────────────────
    # PAGE FUITES DE DONNÉES
    # ─────────────────────────────
    if breaches:
        pdf.add_page()
        page_header()
        section_title(
            section_num,
            f"Fuites de donnees ({len(breaches)})"
        )
        section_num += 1

        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(50, 50, 50)
        pdf.multi_cell(
            0, 6,
            "Les informations suivantes indiquent que des donnees "
            "associees a cette personne ont ete exposees lors de "
            "cyberattaques sur des services en ligne. "
            "Il est recommande de changer les mots de passe associes."
        )
        pdf.ln(6)

        for breach in breaches:
            desc = format_breach(breach)
            source = breach.get("source", "")

            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(20, 20, 20)
            pdf.cell(8, 7, "!", new_x="RIGHT", new_y="LAST")
            pdf.set_font("Helvetica", "", 10)
            pdf.cell(0, 7, safe(desc), new_x="LMARGIN", new_y="NEXT")

            if source:
                pdf.set_font("Helvetica", "I", 8)
                pdf.set_text_color(130, 130, 130)
                pdf.set_x(28)
                pdf.cell(
                    0, 5,
                    f"Source : {safe(source)}",
                    new_x="LMARGIN", new_y="NEXT"
                )

            pdf.set_draw_color(220, 220, 220)
            pdf.line(20, pdf.get_y(), 190, pdf.get_y())
            pdf.ln(2)

        page_footer(page_num)
        page_num += 2

    # ─────────────────────────────
    # PAGE LOCALISATIONS
    # ─────────────────────────────
    if locations:
        pdf.add_page()
        page_header()
        section_title(section_num, "Localisations identifiees")
        section_num += 1

        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(50, 50, 50)
        pdf.multi_cell(
            0, 6,
            "Les localisations suivantes ont ete "
            "trouvees sur les profils de la cible :"
        )
        pdf.ln(6)

        for loc in locations:
            location = loc.get("location", "")
            source = loc.get("source", "")
            if not location:
                continue

            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(20, 20, 20)
            pdf.cell(8, 7, ">", new_x="RIGHT", new_y="LAST")
            pdf.cell(0, 7, safe(location), new_x="LMARGIN", new_y="NEXT")

            if source:
                pdf.set_font("Helvetica", "I", 8)
                pdf.set_text_color(130, 130, 130)
                pdf.set_x(28)
                pdf.cell(
                    0, 5,
                    f"trouve sur : {safe(source)}",
                    new_x="LMARGIN", new_y="NEXT"
                )

        page_footer(page_num)
        page_num += 2

    # ─────────────────────────────
    # PAGE ANALYSE & CONCLUSIONS
    # ─────────────────────────────
    if correlations or ai_summary:
        pdf.add_page()
        page_header()
        section_title(section_num, "Analyse et conclusions")

        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(50, 50, 50)
        pdf.multi_cell(
            0, 6,
            "Sur la base des informations collectees, "
            "voici les conclusions principales :"
        )
        pdf.ln(6)

        for corr in correlations:
            if not corr.strip():
                continue
            pdf.set_draw_color(20, 20, 20)
            pdf.set_line_width(1.5)
            pdf.line(20, pdf.get_y() + 3, 22, pdf.get_y() + 3)
            pdf.set_line_width(0.2)
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(40, 40, 40)
            pdf.set_x(26)
            pdf.multi_cell(0, 6, safe(corr))
            pdf.ln(3)

        page_footer(page_num)

    try:
        pdf.output(output_path)
        print(f"[KRONOS] PDF genere : {output_path}")
    except Exception as e:
        print(f"[KRONOS] Erreur PDF : {e}")
        raise
