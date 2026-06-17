from fpdf import FPDF
from datetime import datetime

def generate_pdf(target, output_path: str):
    name = getattr(target, "name", getattr(target, "domain", "Target"))
    date = datetime.now().strftime("%d %B %Y")
    profiles = getattr(target, "social_profiles", {})
    emails = getattr(target, "emails_found", [])
    breaches = getattr(target, "breaches", [])
    locations = getattr(target, "locations", [])
    correlations = getattr(target, "correlations", [])
    risk_score = getattr(target, "risk_score", 0)
    ai_summary = getattr(target, "ai_summary", "")
    usernames = getattr(target, "usernames_found", [])

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.set_margins(20, 20, 20)

    # ─────────────────────────────
    # PAGE DE GARDE
    # ─────────────────────────────
    pdf.add_page()

    # Dégradé simulé avec rectangles
    for i in range(100):
        gray = int(255 - (i * 0.6))
        pdf.set_fill_color(gray, gray, gray)
        pdf.rect(0, i * 2.97, 210, 2.97, "F")

    cx = 105
    pdf.set_draw_color(20, 20, 20)
    pdf.set_fill_color(20, 20, 20)
    pdf.set_line_width(0.5)

    # Tête de lance
    pdf.polygon([
        [cx - 8, 60], [cx + 8, 60],
        [cx + 4, 40], [cx - 4, 40],
    ], style="F")
    pdf.polygon([
        [cx - 4, 40], [cx + 4, 40], [cx, 25],
    ], style="F")

    # Manche
    pdf.set_line_width(3)
    pdf.line(cx, 60, cx, 200)

    # Garde
    pdf.set_line_width(1.5)
    pdf.line(cx - 15, 110, cx + 15, 110)
    pdf.line(cx - 10, 120, cx + 10, 120)

    # Embout
    pdf.set_fill_color(20, 20, 20)
    pdf.polygon([
        [cx - 3, 200], [cx + 3, 200], [cx, 215],
    ], style="F")

    # KRONOS
    pdf.set_font("Courier", "B", 52)
    pdf.set_text_color(20, 20, 20)
    pdf.set_y(225)
    pdf.cell(0, 20, "KRONOS", align="C", new_x="LMARGIN", new_y="NEXT")

    # Trait
    pdf.set_draw_color(80, 80, 80)
    pdf.set_line_width(0.3)
    pdf.line(60, 248, 150, 248)

    # Sous-titre
    pdf.set_font("Courier", "", 8)
    pdf.set_text_color(100, 100, 100)
    pdf.set_y(252)
    pdf.cell(0, 6, "OSINT INTELLIGENCE SYSTEM", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_y(275)
    pdf.set_font("Courier", "", 7)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 5, "CONFIDENTIEL — USAGE RESTREINT", align="C", new_x="LMARGIN", new_y="NEXT")

    # ─────────────────────────────
    # FONCTIONS UTILITAIRES
    # ─────────────────────────────
    def page_header():
        pdf.set_font("Courier", "", 7)
        pdf.set_text_color(150, 150, 150)
        pdf.set_y(12)
        pdf.cell(0, 4, "KRONOS — OSINT INTELLIGENCE REPORT", align="L", new_x="RIGHT", new_y="LAST")
        pdf.cell(0, 4, f"{name} · {date}", align="R", new_x="LMARGIN", new_y="NEXT")
        pdf.set_draw_color(200, 200, 200)
        pdf.set_line_width(0.2)
        pdf.line(20, 18, 190, 18)
        pdf.set_text_color(20, 20, 20)
        pdf.set_y(24)

    def section_title(num: str, title: str):
        pdf.ln(6)
        pdf.set_font("Courier", "", 7)
        pdf.set_text_color(150, 150, 150)
        pdf.cell(0, 4, num, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(20, 20, 20)
        pdf.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        pdf.set_draw_color(20, 20, 20)
        pdf.set_line_width(0.5)
        pdf.line(20, pdf.get_y(), 190, pdf.get_y())
        pdf.ln(6)

    def add_footer():
        pdf.set_y(-15)
        pdf.set_font("Courier", "", 8)
        pdf.set_text_color(150, 150, 150)
        pdf.cell(0, 4, f"— {pdf.page_no()} —", align="C")

    # ─────────────────────────────
    # PAGE 2 — RÉSUMÉ
    # ─────────────────────────────
    pdf.add_page()
    page_header()

    # Métriques
    metrics = [
        ("PROFILS", str(len(profiles))),
        ("EMAILS", str(len(emails))),
        ("FUITES", str(len(breaches))),
        ("SCORE", f"{risk_score}/100"),
    ]

    col_w = 42
    y_metrics = pdf.get_y()
    for i, (label, value) in enumerate(metrics):
        x = 20 + i * col_w
        pdf.set_draw_color(200, 200, 200)
        pdf.set_line_width(0.3)
        pdf.rect(x, y_metrics, col_w - 2, 20)

        pdf.set_font("Courier", "B", 16)
        pdf.set_text_color(20, 20, 20)
        pdf.set_xy(x, y_metrics + 2)
        pdf.cell(col_w - 2, 8, value, align="C")

        pdf.set_font("Courier", "", 7)
        pdf.set_text_color(120, 120, 120)
        pdf.set_xy(x, y_metrics + 12)
        pdf.cell(col_w - 2, 5, label, align="C")

    pdf.set_y(y_metrics + 28)

    section_title("01", "Résumé exécutif")

    if ai_summary:
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(50, 50, 50)
        pdf.multi_cell(0, 6, ai_summary)

    pdf.ln(4)
    for label, value in [
        ("Cible", name),
        ("Date", date),
        ("Pseudos détectés", ", ".join(usernames[:5]) or "—"),
    ]:
        pdf.set_font("Courier", "", 8)
        pdf.set_text_color(120, 120, 120)
        pdf.cell(50, 6, label.upper(), new_x="RIGHT", new_y="LAST")
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(20, 20, 20)
        pdf.cell(0, 6, str(value), new_x="LMARGIN", new_y="NEXT")

    add_footer()

    # ─────────────────────────────
    # EMAILS
    # ─────────────────────────────
    if emails:
        pdf.add_page()
        page_header()
        section_title("02", f"Emails identifiés ({len(emails)})")

        for email in emails:
            pdf.set_font("Courier", "", 10)
            pdf.set_text_color(20, 20, 20)
            pdf.cell(8, 7, "-", new_x="RIGHT", new_y="LAST")
            pdf.cell(0, 7, email, new_x="LMARGIN", new_y="NEXT")
            pdf.set_draw_color(230, 230, 230)
            pdf.set_line_width(0.2)
            pdf.line(20, pdf.get_y(), 190, pdf.get_y())

        add_footer()

    # ─────────────────────────────
    # PROFILS SOCIAUX
    # ─────────────────────────────
    if profiles:
        categories = {
            "Réseaux sociaux": [],
            "Gaming": [],
            "Développement": [],
            "Autre": [],
        }
        social_kw = [
            "twitter", "instagram", "linkedin", "facebook",
            "tiktok", "youtube", "snapchat", "bsky", "mastodon",
            "discord", "clubhouse", "holehe_twitter",
            "holehe_instagram", "holehe_facebook"
        ]
        gaming_kw = [
            "steam", "chess", "osu", "pokemon", "warframe",
            "runescape", "smule", "twitch", "xbox", "playstation"
        ]
        dev_kw = [
            "github", "gitlab", "codeberg", "hackerone", "bugcrowd",
            "codewars", "codeforces", "hackmd", "gitea", "stackoverflow"
        ]

        for platform, url in profiles.items():
            pl = platform.lower()
            if any(k in pl for k in social_kw):
                categories["Réseaux sociaux"].append((platform, url))
            elif any(k in pl for k in gaming_kw):
                categories["Gaming"].append((platform, url))
            elif any(k in pl for k in dev_kw):
                categories["Développement"].append((platform, url))
            else:
                categories["Autre"].append((platform, url))

        sec_num = 3
        for cat, items in categories.items():
            if not items:
                continue
            pdf.add_page()
            page_header()
            section_title(f"0{sec_num}", f"{cat} ({len(items)})")
            sec_num += 1

            for platform, url in items:
                clean = platform.replace("Holehe_", "").replace("_", " ")
                pdf.set_font("Helvetica", "B", 9)
                pdf.set_text_color(20, 20, 20)
                pdf.cell(45, 6, clean[:22], new_x="RIGHT", new_y="LAST")
                pdf.set_font("Courier", "", 8)
                pdf.set_text_color(80, 80, 80)
                url_short = url[:62] + "..." if len(url) > 62 else url
                pdf.cell(0, 6, url_short, new_x="LMARGIN", new_y="NEXT")
                pdf.set_draw_color(230, 230, 230)
                pdf.set_line_width(0.1)
                pdf.line(20, pdf.get_y(), 190, pdf.get_y())

            add_footer()

    # ─────────────────────────────
    # FUITES
    # ─────────────────────────────
    if breaches:
        pdf.add_page()
        page_header()
        section_title("0X", f"Fuites de données ({len(breaches)})")

        for breach in breaches:
            n = breach.get("Name", breach.get("name", "?"))
            d = breach.get("date", breach.get("BreachDate", "?"))
            if isinstance(d, str):
                d = d[:4]
            src = breach.get("source", "")

            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(20, 20, 20)
            pdf.cell(0, 6, f"!  {n}", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Courier", "", 8)
            pdf.set_text_color(120, 120, 120)
            pdf.cell(0, 5, f"   {d}  —  {src}", new_x="LMARGIN", new_y="NEXT")
            pdf.set_draw_color(200, 200, 200)
            pdf.set_line_width(0.2)
            pdf.line(20, pdf.get_y(), 190, pdf.get_y())
            pdf.ln(2)

        add_footer()

    # ─────────────────────────────
    # CORRÉLATIONS
    # ─────────────────────────────
    if correlations:
        pdf.add_page()
        page_header()
        section_title("0X", "Analyse & Corrélations")

        for c in correlations:
            pdf.set_draw_color(20, 20, 20)
            pdf.set_line_width(1)
            pdf.line(20, pdf.get_y() + 3, 22, pdf.get_y() + 3)
            pdf.set_line_width(0.2)
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(50, 50, 50)
            pdf.set_x(26)
            pdf.multi_cell(0, 6, c)
            pdf.ln(4)

        add_footer()

    try:
        pdf.output(output_path)
        print(f"[KRONOS] PDF généré : {output_path}")
    except Exception as e:
        print(f"[KRONOS] Erreur PDF save : {e}")
