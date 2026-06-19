from fpdf import FPDF
from datetime import datetime
import os, re, math


def safe(text) -> str:
    replacements = {
        "—": "-", "–": "-", "’": "'",
        "‘": "'", "“": '"', "”": '"',
        "…": "...", "é": "e", "è": "e",
        "ê": "e", "ë": "e", "à": "a",
        "â": "a", "ä": "a", "î": "i",
        "ï": "i", "ô": "o", "ö": "o",
        "ù": "u", "û": "u", "ü": "u",
        "ç": "c", "É": "E", "À": "A",
        "È": "E", "Ô": "O",
        "«": '"', "»": '"',
    }
    result = str(text or "")
    for c, r in replacements.items():
        result = result.replace(c, r)
    result = result.encode('latin-1', errors='replace').decode('latin-1')
    return result


def trunc(text: str, max_chars: int) -> str:
    t = safe(str(text or ""))
    if len(t) <= max_chars:
        return t
    return t[:max_chars - 3] + "..."


def deduplicate(profiles: dict) -> dict:
    seen_urls, seen_pl, result = set(), {}, {}
    for platform, url in profiles.items():
        pc = (platform.replace("Holehe_", "")
              .replace("Email_", "")
              .replace("_", " ").strip().lower())
        uc = url.lower().rstrip("/")
        if uc in seen_urls or pc in seen_pl:
            continue
        seen_urls.add(uc)
        seen_pl[pc] = True
        result[platform] = url
    return result


def get_account_details(platform, url, target) -> str:
    pl = platform.lower()
    ul = url.lower()
    gh = getattr(target, "github_data", {})
    dd = getattr(target, "deep_data", {})

    if "holehe_" in pl or "email_" in pl:
        site = platform.replace("Holehe_", "").replace("Email_", "")
        emails = getattr(target, "emails_found", [])
        em = emails[0] if emails else ""
        return f"Email {trunc(em, 30)} sur {site}"

    if "github" in pl or "github" in ul:
        parts = []
        if gh.get("repos_count"):
            parts.append(f"{gh['repos_count']} repos")
        if gh.get("languages"):
            parts.append(", ".join(gh["languages"][:3]))
        if dd.get("GitHub_Company"):
            parts.append(f"Org: {dd['GitHub_Company']}")
        if dd.get("GitHub_Orgs"):
            parts.append(f"Orgs: {', '.join(dd['GitHub_Orgs'][:2])}")
        return trunc(" | ".join(parts) or "Profil confirme", 85)

    if "linkedin" in pl or "linkedin" in ul:
        parts = []
        for key in ["LinkedIn_Titre", "LinkedIn_Ville", "LinkedIn_Formation"]:
            if dd.get(key):
                parts.append(trunc(dd[key], 30))
        return trunc(" | ".join(parts) or "Profil professionnel", 85)

    if any(k in pl or k in ul for k in ["root-me", "hackthebox", "tryhackme"]):
        parts = []
        if dd.get("RootMe_Score"):
            parts.append(dd["RootMe_Score"])
        if dd.get("RootMe_Rank"):
            parts.append(dd["RootMe_Rank"])
        return trunc(" | ".join(parts) or "CTF/Cybersec confirme", 85)

    if "twitter" in pl or "x.com" in ul:
        if dd.get("Twitter_Bio"):
            return trunc(dd["Twitter_Bio"], 85)
        emails = getattr(target, "emails_found", [])
        em = emails[0] if emails else ""
        return f"Email {trunc(em, 30)} detecte"

    if "instagram" in pl:
        parts = []
        if dd.get("Instagram_Bio"):
            parts.append(trunc(dd["Instagram_Bio"], 50))
        if dd.get("Instagram_Followers"):
            parts.append(f"{dd['Instagram_Followers']} followers")
        return trunc(" | ".join(parts) or "Compte detecte", 85)

    if "reddit" in pl:
        parts = []
        if dd.get("Reddit_Karma"):
            parts.append(f"Karma: {dd['Reddit_Karma']}")
        if dd.get("Reddit_Depuis"):
            parts.append(f"Depuis: {dd['Reddit_Depuis']}")
        return trunc(" | ".join(parts) or "Compte confirme", 85)

    if "@" in url or "detecte" in url.lower():
        return trunc(url, 85)

    return trunc("Compte detecte - " + url, 85)


def get_status(platform, url) -> str:
    pl = platform.lower()
    confirmed = [
        "github", "root-me", "hackthebox", "tryhackme",
        "linkedin", "reddit", "hackernews", "gitlab", "codeberg"
    ]
    if any(k in pl for k in confirmed):
        return "CONFIRME"
    if any(k in pl for k in ["holehe_", "email_"]):
        return "VIA EMAIL"
    return "DETECTE"


def get_category(platform, url) -> str:
    c = platform.lower() + " " + url.lower()
    if any(k in c for k in ["linkedin", "viadeo", "malt", "behance"]):
        return "Pro"
    if any(k in c for k in [
        "github", "gitlab", "root-me", "hackthebox", "tryhackme",
        "stackoverflow", "codewars", "hackerone", "leetcode", "dev.to"
    ]):
        return "Dev/Cyber"
    if any(k in c for k in [
        "twitter", "instagram", "tiktok", "youtube", "snapchat",
        "reddit", "mastodon", "telegram", "discord", "twitch", "bluesky"
    ]):
        return "Social"
    if any(k in c for k in ["steam", "xbox", "chess", "osu", "warframe"]):
        return "Gaming"
    return "Autre"


def format_breach(breach: dict) -> dict:
    name = breach.get("Name") or breach.get("name", "")
    if isinstance(name, dict):
        name = name.get("name", "")
    name = (str(name).replace("{", "").replace("}", "")
            .replace("'name':", "").replace("'date':", "")
            .strip(" ,'"))
    if not name or name == "?":
        name = "Service non identifie"

    date = str(breach.get("date") or breach.get("BreachDate", "N/A"))[:10]
    source = str(breach.get("source", "N/A"))

    exposed_map = {
        "stealer": "Mots de passe, cookies, credentials",
        "linkedin": "Emails, mots de passe chiffres",
        "adobe": "Emails, mots de passe chiffres",
        "zynga": "Emails, mots de passe",
        "chegg": "Emails, mots de passe, noms",
        "000webhost": "Emails, mots de passe clairs",
    }
    exposed = "Donnees de compte"
    for k, v in exposed_map.items():
        if k in name.lower():
            exposed = v
            break

    password = breach.get("password", "")
    hash_val = breach.get("hash", "")
    hash_type = breach.get("hash_type", "")
    database = breach.get("database", "")
    email = breach.get("email", "")

    return {
        "name": safe(name),
        "date": safe(date),
        "source": safe(source),
        "exposed": safe(exposed),
        "email": safe(email),
        "password": safe(password),
        "hash": safe(hash_val[:40]) if hash_val else "",
        "hash_type": safe(hash_type),
        "database": safe(database),
    }


class KronosPDF(FPDF):
    _meta = ""

    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("Courier", "", 7)
        self.set_text_color(130, 130, 130)
        self.set_y(8)
        x_save = self.get_x()
        self.cell(90, 4, "KRONOS INTELLIGENCE SYSTEM",
                  align="L", new_x="RIGHT", new_y="LAST")
        self.cell(90, 4, self._meta,
                  align="R", new_x="LMARGIN", new_y="NEXT")
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


class Table:
    def __init__(self, pdf, col_widths, row_h=6, font_size=9):
        self.pdf = pdf
        self.widths = col_widths
        self.row_h = row_h
        self.font_size = font_size
        self.x0 = 15

    def header(self, labels):
        self.pdf.set_fill_color(235, 235, 235)
        self.pdf.set_font("Courier", "", 7)
        self.pdf.set_text_color(90, 90, 90)
        self.pdf.set_draw_color(170, 170, 170)
        self.pdf.set_line_width(0.2)
        y = self.pdf.get_y()

        if y + 7 > self.pdf.h - 20:
            self.pdf.add_page()
            y = self.pdf.get_y()

        for i, (label, w) in enumerate(zip(labels, self.widths)):
            x = self.x0 + sum(self.widths[:i])
            self.pdf.set_xy(x, y)
            self.pdf.cell(w, 7, safe(label.upper())[:18],
                          border=1, fill=True,
                          new_x="RIGHT", new_y="LAST")
        self.pdf.set_xy(self.x0, y + 7)

    def row(self, cells, bold=False):
        self.pdf.set_font("Helvetica", "B" if bold else "", self.font_size)

        char_limits = []
        for w in self.widths:
            chars = max(8, int((w - 3) / 1.85))
            char_limits.append(chars)

        max_lines = 1
        for cell, limit in zip(cells, char_limits):
            txt = safe(str(cell or ""))
            lines = math.ceil(len(txt) / limit) if limit > 0 and txt else 1
            lines = min(lines, 2)
            max_lines = max(max_lines, lines)

        row_h = max_lines * self.row_h + 2

        if self.pdf.get_y() + row_h > self.pdf.h - 20:
            self.pdf.add_page()

        y = self.pdf.get_y()

        for i, (cell, w, limit) in enumerate(zip(cells, self.widths, char_limits)):
            x = self.x0 + sum(self.widths[:i])
            txt = safe(str(cell or "N/A"))

            if len(txt) > limit * max_lines:
                max_chars = limit * max_lines - 3
                txt = txt[:max_chars] + "..."

            lines_txt = []
            while len(txt) > limit:
                cut = txt[:limit].rfind(" ")
                if cut <= 0:
                    cut = limit
                lines_txt.append(txt[:cut])
                txt = txt[cut:].lstrip()
            lines_txt.append(txt)
            lines_txt = lines_txt[:2]

            self.pdf.set_draw_color(200, 200, 200)
            self.pdf.set_line_width(0.1)
            self.pdf.rect(x, y, w, row_h)

            self.pdf.set_font(
                "Helvetica",
                "B" if (bold and i == 0) else "",
                self.font_size
            )
            self.pdf.set_text_color(20, 20, 20)
            for li, line_txt in enumerate(lines_txt):
                self.pdf.set_xy(x + 1.5, y + 1 + li * self.row_h)
                self.pdf.cell(w - 3, self.row_h, line_txt, border=0)

        self.pdf.set_xy(self.x0, y + row_h)


def generate_pdf(target, output_path: str):
    name = getattr(target, "name", getattr(target, "domain", "Cible"))
    ds = safe(datetime.now().strftime("%d %B %Y"))

    profiles = deduplicate(getattr(target, "social_profiles", {}))
    emails = list(dict.fromkeys(getattr(target, "emails_found", [])))
    breaches = getattr(target, "breaches", [])
    locations = getattr(target, "locations", [])
    correlations = getattr(target, "correlations", [])
    risk_score = getattr(target, "risk_score", 0)
    username = getattr(target, "username", "") or ""
    usernames = list(dict.fromkeys(filter(None,
        [username] + getattr(target, "usernames_found", []))))
    gh = getattr(target, "github_data", {})
    langs = gh.get("languages", [])
    repos = gh.get("repos_count", 0)
    profile_type = getattr(target, "profile_type", "")
    personal = getattr(target, "personal_info", {})
    activity = getattr(target, "activity_hours", {})
    peak = activity.get("peak_hour", None)
    connections = getattr(target, "connections", [])
    notes = getattr(target, "notes", "") or ""
    deep = getattr(target, "deep_data", {})

    type_labels = {
        "developer": "Informaticien/Cybersecurite",
        "influencer": "Createur de contenu",
        "business": "Professionnel/Entrepreneur",
        "gamer": "Gamer/Streamer",
        "academic": "Chercheur/Etudiant",
        "regular": "Particulier",
        "public_figure": "Figure publique",
    }
    profile_label = type_labels.get(profile_type, "N/A")

    if peak is not None:
        period = (
            f"{peak}h (matin)" if 6 <= peak < 12 else
            f"{peak}h (apres-midi)" if 12 <= peak < 18 else
            f"{peak}h (soir)" if 18 <= peak < 22 else
            f"{peak}h (nuit)"
        )
    else:
        period = "N/A"

    loc_str = locations[0]["location"] if locations else "N/A"

    pdf = KronosPDF()
    pdf._meta = safe(f"DOSSIER: {name} - {ds}")
    pdf.set_margins(15, 18, 15)
    pdf.set_auto_page_break(True, 16)

    # ─────── PAGE DE GARDE ───────
    pdf.add_page()

    for i in range(100):
        g = int(255 - i * 0.7)
        pdf.set_fill_color(g, g, g)
        pdf.rect(0, i * 2.97, 210, 2.97, "F")

    pdf.set_fill_color(17, 17, 17)
    pdf.rect(0, 0, 210, 14, "F")
    pdf.set_font("Courier", "", 7)
    pdf.set_text_color(200, 200, 200)
    pdf.set_y(5)
    pdf.cell(60, 4, "KRONOS INTELLIGENCE SYSTEM",
             align="L", new_x="RIGHT", new_y="LAST")
    pdf.set_text_color(150, 150, 150)
    pdf.cell(60, 4, safe("DOSSIER D'ENQUETE - CONFIDENTIEL"),
             align="C", new_x="RIGHT", new_y="LAST")
    pdf.cell(60, 4, safe(f"REF: KRN-{datetime.now().strftime('%Y%m%d')}"),
             align="R", new_x="LMARGIN", new_y="NEXT")

    pdf.set_y(28)
    pdf.set_font("Courier", "", 8)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, safe("FICHE SUJET - RAPPORT D'INVESTIGATION OSINT"),
             align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    px, py, pw, ph = 20, pdf.get_y(), 42, 54
    pdf.set_draw_color(150, 150, 150)
    pdf.set_fill_color(245, 245, 245)
    pdf.rect(px, py, pw, ph, "FD")
    pdf.set_font("Courier", "", 7)
    pdf.set_text_color(160, 160, 160)
    pdf.set_xy(px, py + ph / 2 - 5)
    pdf.cell(pw, 4, "PHOTO", align="C", new_x="LMARGIN", new_y="NEXT")
    if username:
        pdf.set_font("Courier", "", 6)
        pdf.set_xy(px, py + ph / 2)
        pdf.cell(pw, 4, safe(f"github/{username}")[:20],
                 align="C", new_x="LMARGIN", new_y="NEXT")

    ix = px + pw + 10
    iw = 195 - ix
    pdf.set_xy(ix, py)
    parts = name.strip().split()
    if len(parts) >= 2:
        pdf.set_font("Helvetica", "B", 22)
        pdf.set_text_color(20, 20, 20)
        pdf.cell(iw, 11, safe(parts[-1].upper()),
                 new_x="LMARGIN", new_y="NEXT")
        pdf.set_x(ix)
        pdf.set_font("Helvetica", "B", 16)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(iw, 9, safe(" ".join(parts[:-1])),
                 new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.set_font("Helvetica", "B", 22)
        pdf.set_text_color(20, 20, 20)
        pdf.cell(iw, 11, safe(name.upper()),
                 new_x="LMARGIN", new_y="NEXT")

    if usernames:
        pdf.set_x(ix)
        pdf.set_font("Courier", "", 9)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(iw, 6, safe("ALIAS : " + " - ".join(usernames[:3])),
                 new_x="LMARGIN", new_y="NEXT")

    pdf.ln(3)

    fy = max(py + 38, pdf.get_y())
    fields = [
        ("STATUT", profile_label),
        ("LOCALISATION", loc_str),
        ("SCORE", f"{risk_score}/100"),
        ("DATE", ds),
        ("COMPTES", str(len(profiles))),
        ("EMAILS", str(len(emails))),
        ("FUITES", str(len(breaches))),
        ("SOURCES", "GitHub,Sherlock,Holehe,LeakCheck"),
    ]
    c1, c2 = 42, iw - 42
    for i, (label, value) in enumerate(fields):
        yy = fy + i * 7
        pdf.set_xy(ix, yy)
        bg = 250 if i % 2 == 0 else 255
        pdf.set_fill_color(bg, bg, bg)
        pdf.set_draw_color(200, 200, 200)
        pdf.set_line_width(0.2)
        pdf.set_font("Courier", "", 7)
        pdf.set_text_color(120, 120, 120)
        pdf.cell(c1, 7, safe(label), border=1, fill=True,
                 new_x="RIGHT", new_y="LAST")
        pdf.set_font("Courier", "", 8)
        pdf.set_text_color(20, 20, 20)
        pdf.cell(c2, 7, trunc(value, int(c2 / 1.9)), border=1,
                 new_x="LMARGIN", new_y="NEXT")

    cx, cy = 105, 190
    pdf.set_fill_color(30, 30, 30)
    pdf.set_draw_color(30, 30, 30)
    pdf.polygon([[cx, cy], [cx + 5, cy + 20], [cx + 2, cy + 18],
                 [cx, cy + 14], [cx - 2, cy + 18], [cx - 5, cy + 20]], style="F")
    pdf.set_line_width(2)
    pdf.line(cx, cy + 20, cx, cy + 60)
    pdf.set_line_width(1.2)
    pdf.line(cx - 10, cy + 35, cx + 10, cy + 35)
    pdf.set_line_width(0.8)
    pdf.line(cx - 7, cy + 42, cx + 7, cy + 42)
    pdf.set_line_width(2)
    pdf.line(cx, cy + 60, cx, cy + 68)
    pdf.polygon([[cx - 3, cy + 68], [cx + 3, cy + 68], [cx, cy + 75]], style="F")

    pdf.set_font("Courier", "B", 38)
    pdf.set_text_color(20, 20, 20)
    pdf.set_y(cy + 78)
    pdf.cell(0, 14, "KRONOS", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(120, 120, 120)
    pdf.set_line_width(0.3)
    pdf.line(75, pdf.get_y(), 135, pdf.get_y())
    pdf.ln(2)
    pdf.set_font("Courier", "", 7)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, "OSINT INTELLIGENCE SYSTEM",
             align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_y(274)
    pdf.set_font("Courier", "", 7)
    pdf.set_text_color(160, 160, 160)
    pdf.cell(0, 4, "USAGE STRICTEMENT RESTREINT",
             align="C", new_x="LMARGIN", new_y="NEXT")

    # ─────── CONTENU ───────
    pdf.add_page()
    sec = 1

    def section(num, title):
        if pdf.get_y() > pdf.h - 40:
            pdf.add_page()
        pdf.ln(4)
        pdf.set_fill_color(17, 17, 17)
        pdf.set_font("Courier", "B", 8)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(14, 7, f"0{num}" if num < 10 else str(num),
                 fill=True, align="C", new_x="RIGHT", new_y="LAST")
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(20, 20, 20)
        pdf.set_x(pdf.get_x() + 3)
        pdf.cell(0, 7, safe(title), new_x="LMARGIN", new_y="NEXT")
        pdf.set_draw_color(20, 20, 20)
        pdf.set_line_width(0.4)
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        pdf.ln(4)

    # ─── 01 IDENTIFIANTS ───
    section(sec, "IDENTIFIANTS ET CONTACTS")
    sec += 1

    t = Table(pdf, [40, 70, 50, 20])
    t.header(["TYPE", "VALEUR", "SOURCE", "FIABILITE"])

    for em in emails:
        src = "GitHub commits" if em in gh.get("commit_emails", []) else "Holehe / pivot"
        if "efrei" in em.lower():
            src = "Pivot recursif"
        t.row(("EMAIL", em, src, "HAUTE"))

    for u in usernames:
        t.row(("ALIAS", u, "GitHub+Sherlock", "CERTAINE"))

    if langs:
        t.row(("LANGAGES", ", ".join(langs[:4]), f"{repos} repos GitHub", "CERTAINE"))
    if repos:
        t.row(("REPOS PUBLICS", str(repos), "GitHub API", "CERTAINE"))
    if peak is not None:
        t.row(("PIC ACTIVITE", period, "Commits GitHub", "ESTIMEE"))
    for loc in locations:
        t.row(("LOCALISATION", loc.get("location", ""),
               f"Profil {loc.get('source', '')}", "PROBABLE"))
    if notes:
        t.row(("CONTEXTE", notes[:50], "Operateur", "INFO"))

    # ─── 02 COMPTES ───
    section(sec, "COMPTES EN LIGNE")
    sec += 1

    t2 = Table(pdf, [28, 45, 67, 22, 18])
    t2.header(["PLATEFORME", "URL", "DONNEES TROUVEES", "CATEGORIE", "STATUT"])
    for platform, url in profiles.items():
        clean = (platform.replace("Holehe_", "").replace("Email_", "")
                 .replace("_", " ").strip())
        display = url
        if "avec " in url:
            display = url.split("avec ")[-1]
        t2.row([clean, display,
                get_account_details(platform, url, target),
                get_category(platform, url),
                get_status(platform, url)])

    # ─── 03 DONNEES LINKEDIN ───
    linkedin_keys = {k: v for k, v in deep.items()
                     if "linkedin" in k.lower() or "LinkedIn" in k}
    if linkedin_keys:
        section(sec, f"DONNEES LINKEDIN EXTRAITES ({len(linkedin_keys)})")
        sec += 1
        t3 = Table(pdf, [55, 125])
        t3.header(["CHAMP", "VALEUR"])
        for k, v in linkedin_keys.items():
            field_name = k.replace("LinkedIn_", "").replace("_", " ")
            if isinstance(v, list):
                v = ", ".join(str(x) for x in v)
            t3.row([field_name, str(v)])

    # ─── 04 DONNEES GITHUB ───
    github_keys = {k: v for k, v in deep.items()
                   if "github" in k.lower() or "GitHub" in k}
    if github_keys:
        section(sec, f"DONNEES GITHUB EXTRAITES ({len(github_keys)})")
        sec += 1
        t_gh = Table(pdf, [55, 125])
        t_gh.header(["CHAMP", "VALEUR"])
        for k, v in github_keys.items():
            field_name = k.replace("GitHub_", "").replace("_", " ")
            if isinstance(v, list):
                v = ", ".join(str(x) for x in v)
            t_gh.row([field_name, str(v)])

    # ─── 05 AUTRES DONNEES PROFONDES ───
    other_deep = {k: v for k, v in deep.items()
                  if "linkedin" not in k.lower() and "github" not in k.lower()
                  and "LinkedIn" not in k and "GitHub" not in k}
    if other_deep:
        section(sec, f"DONNEES EXTRAITES ({len(other_deep)})")
        sec += 1
        t_od = Table(pdf, [45, 25, 110])
        t_od.header(["SOURCE", "CHAMP", "VALEUR"])
        for k, v in other_deep.items():
            ps = k.split("_", 1)
            src = ps[0]
            field = ps[1].replace("_", " ") if len(ps) > 1 else k
            if isinstance(v, list):
                v = ", ".join(str(x) for x in v)
            t_od.row([src, field, str(v)])

    # ─── 06 INCIDENTS ───
    if breaches:
        section(sec, f"INCIDENTS DE SECURITE ({len(breaches)})")
        sec += 1

        for b in breaches:
            bd = format_breach(b)
            t_b = Table(pdf, [55, 125])
            t_b.header(["CHAMP", "DETAIL"])
            t_b.row(["INCIDENT", bd["name"]], bold=True)
            t_b.row(["DATE", bd["date"]])
            if bd["email"]:
                t_b.row(["EMAIL COMPROMIS", bd["email"]])
            if bd["database"]:
                t_b.row(["BASE DE DONNEES", bd["database"]])
            t_b.row(["DONNEES EXPOSEES", bd["exposed"]])
            if bd["password"]:
                t_b.row(["MOT DE PASSE EXPOSE", bd["password"]])
            if bd["hash"]:
                ht = bd["hash_type"] or "INCONNU"
                t_b.row([f"HASH ({ht})", bd["hash"]])
            t_b.row(["SOURCE DETECTION", bd["source"]])
            pdf.ln(2)

    # ─── 07 COMPORTEMENT ───
    section(sec, "PROFIL COMPORTEMENTAL")
    sec += 1

    beh_rows = []
    if peak is not None:
        beh_rows.append(("PERIODE ACTIVITE", period, "Horodatages commits GitHub"))
    if langs:
        beh_rows.append(("COMPETENCES TECH", ", ".join(langs[:5]), f"{repos} repos"))
    if profile_type:
        beh_rows.append(("PROFIL IA", profile_label, "Groq llama-3.3-70b"))

    interests = []
    for pl_name in profiles:
        pll = pl_name.lower()
        if any(k in pll for k in ["root-me", "hackthebox", "tryhackme"]):
            if "CTF/Cybersec" not in interests:
                interests.append("CTF/Cybersec")
        if "spotify" in pll or "soundcloud" in pll:
            if "Musique" not in interests:
                interests.append("Musique")
        if "eventbrite" in pll:
            if "Evenements" not in interests:
                interests.append("Evenements")
        if "youtube" in pll:
            if "Video" not in interests:
                interests.append("Video")
    if interests:
        beh_rows.append(("CENTRES INTERET", " - ".join(interests), "Analyse comptes"))
    if username:
        beh_rows.append(("STYLE PSEUDO", username, "Meme alias toutes plateformes"))

    if beh_rows:
        t5 = Table(pdf, [42, 70, 68])
        t5.header(["CRITERE", "VALEUR", "SOURCE"])
        for row in beh_rows:
            t5.row(row)

    # ─── 08 CONNEXIONS ───
    dedup_conns = []
    seen_conns = set()
    for c in connections:
        key = (c.get("username", ""), c.get("platform", ""))
        if key not in seen_conns:
            seen_conns.add(key)
            dedup_conns.append(c)

    if dedup_conns:
        section(sec, f"RESEAU ({len(dedup_conns)} connexions)")
        sec += 1
        t6 = Table(pdf, [45, 28, 28, 79])
        t6.header(["USERNAME", "PLATEFORME", "TYPE", "URL"])
        for c in dedup_conns[:20]:
            t6.row([c.get("username", "")[:22],
                    c.get("platform", "")[:14],
                    c.get("type", "")[:14],
                    c.get("url", "")[:45]])

    # ─── 09 CORRELATIONS ───
    if correlations:
        section(sec, f"CORRELATIONS ({len(correlations)})")
        sec += 1
        t7 = Table(pdf, [10, 170])
        t7.header(["N", "CORRELATION"])
        for i, c in enumerate(correlations, 1):
            if c.strip():
                t7.row([str(i), c])

    # ─── 10 INFOS PERSONNELLES ───
    if personal:
        section(sec, "INFORMATIONS PERSONNELLES")
        sec += 1
        t8 = Table(pdf, [40, 70, 50, 20])
        t8.header(["TYPE", "VALEUR", "SOURCE", "FIABILITE"])
        for k, v in personal.items():
            t8.row([k.upper(), str(v), "Annuaire/Web", "A VERIFIER"])

    try:
        pdf.output(output_path)
        print(f"[KRONOS] PDF : {output_path}")
    except Exception as e:
        print(f"[KRONOS] Erreur PDF : {e}")
        raise
