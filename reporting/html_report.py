import os
import json
from dataclasses import asdict
from datetime import datetime

def generate_html(target, output_path: str):
    name = getattr(
        target, "domain",
        getattr(target, "name", "target")
    )
    data = asdict(target)
    score = target.risk_score
    score_color = (
        "#f44336" if score >= 70
        else "#ff9800" if score >= 40
        else "#4caf50"
    )

    sections = _build_sections(target)
    sections_html = "\n".join(sections)

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>KRONOS Report — {name}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: #0a0a0a; color: #e0e0e0; font-family: 'Courier New', monospace; }}
  .header {{ background: #111; border-bottom: 2px solid #00bcd4; padding: 20px 32px; }}
  .header h1 {{ color: #00bcd4; font-size: 20px; letter-spacing: 4px; }}
  .header p {{ color: #666; font-size: 12px; margin-top: 4px; }}
  .container {{ max-width: 1100px; margin: 0 auto; padding: 24px; }}
  .score-box {{ display: inline-block; background: {score_color}; color: white;
    font-size: 36px; font-weight: bold; padding: 16px 32px;
    border-radius: 4px; margin: 16px 0; }}
  .section {{ background: #111; border: 1px solid #1a3a40; border-radius: 4px;
    margin: 16px 0; padding: 20px; }}
  .section h2 {{ color: #00bcd4; font-size: 14px; letter-spacing: 2px;
    margin-bottom: 12px; text-transform: uppercase; }}
  .item {{ color: #b0b0b0; font-size: 12px; padding: 4px 0;
    border-bottom: 1px solid #1a1a1a; }}
  .tag {{ display: inline-block; background: #1a3a40; color: #00bcd4;
    padding: 2px 8px; border-radius: 2px; font-size: 11px; margin: 2px; }}
  .alert {{ color: #f44336; }}
  .ok {{ color: #4caf50; }}
  .summary {{ color: #b0b0b0; line-height: 1.6; font-size: 13px; }}
</style>
</head>
<body>
<div class="header">
  <h1>◆ KRONOS — OSINT INTELLIGENCE REPORT</h1>
  <p>Target: {name} | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Session: active</p>
</div>
<div class="container">
  <div class="section">
    <h2>Risk Score</h2>
    <div class="score-box">{score}/100</div>
  </div>
  {sections_html}
</div>
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    return output_path


def _build_sections(target):
    sections = []

    if target.ai_summary:
        sections.append(f"""
<div class="section">
  <h2>Executive Summary</h2>
  <p class="summary">{target.ai_summary}</p>
</div>""")

    if target.correlations:
        items = "".join(
            f'<div class="item">↔ {c}</div>'
            for c in target.correlations
        )
        sections.append(f"""
<div class="section">
  <h2>Key Correlations</h2>
  {items}
</div>""")

    # Person data
    if hasattr(target, "emails_found") and target.emails_found:
        items = "".join(
            f'<div class="item">{e}</div>'
            for e in target.emails_found
        )
        sections.append(f"""
<div class="section">
  <h2>Emails Found ({len(target.emails_found)})</h2>
  {items}
</div>""")

    if hasattr(target, "social_profiles") and target.social_profiles:
        items = "".join(
            f'<div class="item"><span class="tag">{p}</span> '
            f'<a href="{u}" style="color:#00bcd4">{u}</a></div>'
            for p, u in target.social_profiles.items()
        )
        sections.append(f"""
<div class="section">
  <h2>Social Profiles ({len(target.social_profiles)})</h2>
  {items}
</div>""")

    if hasattr(target, "breaches") and target.breaches:
        items = "".join(
            f'<div class="item alert">⚠ {b.get("Name","?")} '
            f'({b.get("BreachDate","")[:4]})</div>'
            for b in target.breaches
        )
        sections.append(f"""
<div class="section">
  <h2>Data Breaches ({len(target.breaches)})</h2>
  {items}
</div>""")

    # Company data
    if hasattr(target, "subdomains") and target.subdomains:
        items = "".join(
            f'<span class="tag">{s}</span>'
            for s in target.subdomains[:50]
        )
        sections.append(f"""
<div class="section">
  <h2>Subdomains ({len(target.subdomains)})</h2>
  {items}
</div>""")

    if hasattr(target, "cves") and target.cves:
        items = "".join(
            f'<div class="item alert">⚠ {cve}</div>'
            for cve in target.cves
        )
        sections.append(f"""
<div class="section">
  <h2>CVEs ({len(target.cves)})</h2>
  {items}
</div>""")

    if hasattr(target, "exposed_secrets") and target.exposed_secrets:
        items = "".join(
            f'<div class="item alert">⚠ [{s.get("type")}] '
            f'{s.get("repo")}/{s.get("file")}</div>'
            for s in target.exposed_secrets
        )
        sections.append(f"""
<div class="section">
  <h2>Exposed Secrets ({len(target.exposed_secrets)})</h2>
  {items}
</div>""")

    return sections
