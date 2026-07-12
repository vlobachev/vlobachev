#!/usr/bin/env python3
"""Generate Precision Dark stats/language SVG cards from the GitHub API.

Runs in CI with the built-in GITHUB_TOKEN (no PAT required) and writes
assets/stats.svg and assets/langs.svg, replacing the external
github-readme-stats dependency.
"""
import json
import os
import urllib.request
from collections import Counter

USER = "vlobachev"
API = "https://api.github.com"
TOKEN = os.environ.get("GITHUB_TOKEN", "")

BG, BORDER, TEXT, MUTED, ACCENT = "#0d1117", "#30363d", "#e6edf3", "#8b949e", "#3fb950"
MONO = 'ui-monospace, "SF Mono", Menlo, Consolas, monospace'

LANG_COLORS = {
    "Python": "#3572A5", "HCL": "#844FBA", "Shell": "#89e051", "Go": "#00ADD8",
    "TypeScript": "#3178c6", "JavaScript": "#f1e05a", "Ruby": "#701516",
    "Dockerfile": "#384d54", "Smarty": "#f0c040", "HTML": "#e34c26",
    "CSS": "#663399", "Makefile": "#427819", "Jinja": "#a52a22", "Mustache": "#724b3b",
}


def api(path):
    req = urllib.request.Request(API + path, headers={
        "Accept": "application/vnd.github+json",
        **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}),
    })
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def fetch():
    user = api(f"/users/{USER}")
    repos, page = [], 1
    while True:
        batch = api(f"/users/{USER}/repos?per_page=100&page={page}&type=owner")
        repos += batch
        if len(batch) < 100:
            break
        page += 1
    own = [r for r in repos if not r["fork"]]
    langs = Counter()
    for r in own:
        try:
            for lang, size in api(f"/repos/{USER}/{r['name']}/languages").items():
                langs[lang] += size
        except Exception:
            pass
    stats = {
        "Public repos": user["public_repos"],
        "Followers": user["followers"],
        "Stars earned": sum(r["stargazers_count"] for r in own),
        "Forks of my work": sum(r["forks_count"] for r in own),
    }
    return stats, langs


def card(width, height, title, body):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" role="img" aria-label="{title}">
  <style>.mono{{font-family:{MONO};}}.t{{font-size:13px;fill:{ACCENT};font-weight:600;letter-spacing:.4px;}}
  .k{{font-size:12.5px;fill:{MUTED};}}.v{{font-size:12.5px;fill:{TEXT};font-weight:600;}}</style>
  <rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="8" fill="{BG}" stroke="{BORDER}"/>
  <text x="20" y="28" class="mono t">▸ {title}</text>
{body}</svg>'''


def stats_svg(stats):
    rows = ""
    y = 58
    for k, v in stats.items():
        rows += f'  <text x="20" y="{y}" class="mono k">{k}</text>\n'
        rows += f'  <text x="315" y="{y}" text-anchor="end" class="mono v">{v}</text>\n'
        y += 26
    return card(335, 165, f"{USER} — github stats", rows)


def langs_svg(langs):
    total = sum(langs.values()) or 1
    top = langs.most_common(6)
    body, x = "", 20
    # stacked bar
    for lang, size in top:
        w = max(3, round(size / total * 380))
        body += f'  <rect x="{x}" y="44" width="{w}" height="9" rx="2" fill="{LANG_COLORS.get(lang, MUTED)}"/>\n'
        x += w + 2
    # legend, two columns
    for i, (lang, size) in enumerate(top):
        cx, cy = 20 + (i % 2) * 210, 78 + (i // 2) * 26
        pct = size / total * 100
        body += f'  <circle cx="{cx + 5}" cy="{cy - 4}" r="5" fill="{LANG_COLORS.get(lang, MUTED)}"/>\n'
        body += f'  <text x="{cx + 18}" y="{cy}" class="mono k">{lang} <tspan class="v">{pct:.1f}%</tspan></text>\n'
    return card(440, 165, "most used languages", body)


def main():
    stats, langs = fetch()
    os.makedirs("assets", exist_ok=True)
    with open("assets/stats.svg", "w") as f:
        f.write(stats_svg(stats))
    with open("assets/langs.svg", "w") as f:
        f.write(langs_svg(langs))
    print("wrote assets/stats.svg, assets/langs.svg")


if __name__ == "__main__":
    main()
