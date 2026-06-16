from datetime import datetime

CATEGORIES = {
    "Réseaux sociaux": [
        "twitter", "instagram", "linkedin", "facebook",
        "tiktok", "youtube", "snapchat", "pinterest",
        "mastodon", "bluesky", "bsky", "threads"
    ],
    "Gaming": [
        "steam", "xbox", "playstation", "twitch",
        "discord", "chess", "osu", "pokemon",
        "warframe", "runescape", "roblox"
    ],
    "Développement": [
        "github", "gitlab", "codeberg", "gitea",
        "stackoverflow", "hackerrank", "codeforces",
        "hackerearth", "leetcode", "codewars",
        "hackerone", "bugcrowd"
    ],
    "Créatif": [
        "behance", "dribbble", "deviantart",
        "soundcloud", "mixcloud", "spotify",
        "vimeo", "dailymotion", "medium", "dev.to"
    ],
    "Autre": []
}

def categorize_profiles(profiles: dict) -> dict:
    categorized = {cat: {} for cat in CATEGORIES}

    for platform, url in profiles.items():
        platform_lower = platform.lower()
        assigned = False

        for category, keywords in CATEGORIES.items():
            if category == "Autre":
                continue
            if any(kw in platform_lower for kw in keywords):
                categorized[category][platform] = url
                assigned = True
                break

        if not assigned:
            categorized["Autre"][platform] = url

    return {k: v for k, v in categorized.items() if v}


def generate_pdf(target, output_path: str):
    try:
        from weasyprint import HTML
    except ImportError:
        _fallback_txt(target, output_path)
        return

    name = getattr(target, "name", getattr(target, "domain", "Target"))
    date = datetime.now().strftime("%d %B %Y")

    profiles = getattr(target, "social_profiles", {})
    emails = getattr(target, "emails_found", [])
    breaches = getattr(target, "breaches", [])
    locations = getattr(target, "locations", [])
    correlations = getattr(target, "correlations", [])
    risk_score = getattr(target, "risk_score", 0)
    ai_summary = getattr(target, "ai_summary", "")

    categorized = categorize_profiles(profiles)

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  @page {{
    size: A4;
    margin: 20mm 22mm 22mm 22mm;
  }}
  body {{
    font-family: Georgia, serif;
    color: #111;
    font-size: 11pt;
    line-height: 1.7;
  }}
  .cover {{
    text-align: center;
    padding: 60px 0;
    border-bottom: 2px solid #111;
    margin-bottom: 40px;
  }}
  .cover h1 {{
    font-family: 'Courier New', monospace;
    font-size: 36pt;
    font-weight: 900;
    letter-spacing: 12px;
    margin: 0 0 8px;
    text-indent: 12px;
  }}
  .cover .subtitle {{
    font-family: 'Courier New', monospace;
    font-size: 8pt;
    letter-spacing: 4px;
    color: #666;
    text-transform: uppercase;
    margin: 0 0 40px;
  }}
  .cover .meta {{
    display: inline-block;
    border: 0.5px solid #ccc;
    padding: 16px 32px;
    text-align: left;
  }}
  .cover .meta-row {{
    display: flex;
    gap: 16px;
    margin: 4px 0;
  }}
  .cover .meta-label {{
    font-family: 'Courier New', monospace;
    font-size: 8pt;
    letter-spacing: 2px;
    color: #999;
    min-width: 80px;
    text-transform: uppercase;
  }}
  .cover .meta-value {{
    font-family: 'Courier New', monospace;
    font-size: 10pt;
    color: #111;
  }}
  .section-num {{
    font-family: 'Courier New', monospace;
    font-size: 8pt;
    letter-spacing: 5px;
    color: #aaa;
    margin-bottom: 4px;
    text-transform: uppercase;
  }}
  h2 {{
    font-size: 18pt;
    font-weight: bold;
    border-bottom: 1px solid #111;
    padding-bottom: 8px;
    margin: 32px 0 16px;
  }}
  h3 {{
    font-size: 12pt;
    font-weight: bold;
    margin: 20px 0 8px;
    color: #333;
  }}
  .metrics {{
    display: flex;
    gap: 0;
    border: 0.5px solid #ddd;
    margin: 20px 0;
  }}
  .metric {{
    flex: 1;
    padding: 16px;
    text-align: center;
    border-right: 0.5px solid #ddd;
  }}
  .metric:last-child {{ border-right: none; }}
  .metric-value {{
    font-family: 'Courier New', monospace;
    font-size: 22pt;
    font-weight: bold;
  }}
  .metric-label {{
    font-family: 'Courier New', monospace;
    font-size: 8pt;
    letter-spacing: 2px;
    color: #999;
    margin-top: 4px;
    text-transform: uppercase;
  }}
  .profile-url {{
    font-family: 'Courier New', monospace;
    font-size: 9pt;
    color: #444;
    padding: 4px 0;
    border-bottom: 0.5px solid #f0f0f0;
    word-break: break-all;
  }}
  .profile-platform {{
    font-weight: bold;
    color: #111;
    min-width: 140px;
    display: inline-block;
  }}
  .email-item {{
    font-family: 'Courier New', monospace;
    font-size: 10pt;
    padding: 6px 0;
    border-bottom: 0.5px solid #eee;
  }}
  .breach-item {{
    padding: 8px 0;
    border-bottom: 0.5px solid #eee;
    font-size: 10pt;
  }}
  .breach-name {{ font-weight: bold; }}
  .breach-meta {{
    font-family: 'Courier New', monospace;
    font-size: 9pt;
    color: #888;
    margin-left: 8px;
  }}
  .correlation-item {{
    padding: 6px 0 6px 16px;
    border-left: 2px solid #111;
    margin-bottom: 8px;
    font-size: 10pt;
  }}
  .summary {{
    background: #f9f9f9;
    border: 0.5px solid #eee;
    padding: 16px 20px;
    margin: 16px 0;
    font-size: 11pt;
    line-height: 1.8;
  }}
  .location-item {{
    font-family: 'Courier New', monospace;
    font-size: 10pt;
    padding: 4px 0;
  }}
  .confidential {{
    text-align: center;
    font-family: 'Courier New', monospace;
    font-size: 8pt;
    letter-spacing: 3px;
    color: #bbb;
    text-transform: uppercase;
    margin-top: 40px;
  }}
</style>
</head>
<body>

<div class="cover">
  <h1>KRONOS</h1>
  <div class="subtitle">OSINT Intelligence Report</div>
  <div class="meta">
    <div class="meta-row">
      <span class="meta-label">Cible</span>
      <span class="meta-value">{name}</span>
    </div>
    <div class="meta-row">
      <span class="meta-label">Date</span>
      <span class="meta-value">{date}</span>
    </div>
    <div class="meta-row">
      <span class="meta-label">Score</span>
      <span class="meta-value">{risk_score}/100</span>
    </div>
    <div class="meta-row">
      <span class="meta-label">Profils</span>
      <span class="meta-value">{len(profiles)}</span>
    </div>
  </div>
  <div class="confidential">Confidentiel — Usage restreint</div>
</div>

<div class="section-num">01</div>
<h2>Résumé exécutif</h2>
<div class="summary">{ai_summary or f"Analyse OSINT de {name}. {len(profiles)} profil(s) trouvé(s) sur {len(categorized)} catégorie(s). Score de risque : {risk_score}/100."}</div>

<div class="metrics">
  <div class="metric">
    <div class="metric-value">{len(profiles)}</div>
    <div class="metric-label">Profils</div>
  </div>
  <div class="metric">
    <div class="metric-value">{len(emails)}</div>
    <div class="metric-label">Emails</div>
  </div>
  <div class="metric">
    <div class="metric-value">{len(breaches)}</div>
    <div class="metric-label">Fuites</div>
  </div>
  <div class="metric">
    <div class="metric-value">{risk_score}</div>
    <div class="metric-label">Score</div>
  </div>
</div>
"""

    if emails:
        html += "\n<div class=\"section-num\">02</div>\n<h2>Emails identifiés</h2>\n"
        for email in emails:
            html += f'<div class="email-item">✉ {email}</div>\n'

    if categorized:
        html += "\n<div class=\"section-num\">03</div>\n<h2>Profils en ligne</h2>\n"
        for category, profs in categorized.items():
            html += f"<h3>{category} ({len(profs)})</h3>\n"
            for platform, url in profs.items():
                clean = platform.replace("Holehe_", "").replace("_", " ")
                html += (
                    f'<div class="profile-url">'
                    f'<span class="profile-platform">{clean}</span>'
                    f'{url}</div>\n'
                )

    if breaches:
        html += "\n<div class=\"section-num\">04</div>\n<h2>Fuites de données</h2>\n"
        for b in breaches:
            bname = b.get("Name", b.get("name", "?"))
            bdate = b.get("BreachDate", b.get("date", ""))[:4]
            bsrc = b.get("source", "")
            html += (
                f'<div class="breach-item">'
                f'<span class="breach-name">⚠ {bname}</span>'
                f'<span class="breach-meta">{bdate}</span>'
                f'<span class="breach-meta">via {bsrc}</span>'
                f'</div>\n'
            )

    if locations:
        html += "\n<div class=\"section-num\">05</div>\n<h2>Localisations</h2>\n"
        for loc in locations:
            html += (
                f'<div class="location-item">'
                f'📍 {loc.get("location", "?")} '
                f'<span style="color:#999;font-size:9pt">'
                f'({loc.get("source", "?")})</span>'
                f'</div>\n'
            )

    if correlations:
        html += "\n<div class=\"section-num\">06</div>\n<h2>Corrélations &amp; Analyse</h2>\n"
        for corr in correlations:
            html += f'<div class="correlation-item">{corr}</div>\n'

    html += "\n</body>\n</html>"

    HTML(string=html).write_pdf(output_path)
    print(f"[KRONOS] Rapport PDF : {output_path}")


def _fallback_txt(target, output_path: str):
    txt_path = output_path.replace(".pdf", ".txt")
    name = getattr(target, "name", getattr(target, "domain", "target"))
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"KRONOS Report — {name}\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n")
        f.write(f"Risk Score: {target.risk_score}/100\n\n")
        if target.ai_summary:
            f.write(f"Summary:\n{target.ai_summary}\n\n")
        for c in target.correlations:
            f.write(f"- {c}\n")
