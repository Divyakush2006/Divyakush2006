#!/usr/bin/env python3
"""
Self-hosted GitHub stat cards for Divyakush Punjabi.

Fetches live stats from the GitHub API and renders animated SVG cards that are
committed straight into this repository — no third-party image service, so the
profile can never show a broken card.

Outputs (light + dark variants):
    assets/stats-<theme>.svg   — headline credibility metrics
    assets/langs-<theme>.svg   — most-used languages by bytes of code

Usage:  GITHUB_TOKEN=<token> python scripts/generate_stats.py
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request
from collections import defaultdict

USER = os.environ.get("GH_USER", "divyakush2006")
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
OUT_DIR = "assets"

THEMES = {
    "dark":  {"bg": "#0d1117", "border": "#30363d", "title": "#58a6ff",
              "text": "#c9d1d9", "muted": "#8b949e", "icon": "#58a6ff"},
    "light": {"bg": "#ffffff", "border": "#d0d7de", "title": "#0969da",
              "text": "#1f2328", "muted": "#59636e", "icon": "#0969da"},
}

# Stable colour per language so both cards agree.
LANG_COLORS = {
    "TypeScript": "#3178c6", "JavaScript": "#f1e05a", "Python": "#3572A5",
    "HTML": "#e34c26", "CSS": "#563d7c", "Java": "#b07219", "C++": "#f34b7d",
    "C": "#555555", "Jupyter Notebook": "#DA5B0B", "Verilog": "#b2b7f8",
    "Shell": "#89e051", "Dockerfile": "#384d54", "Vue": "#41b883",
}
FALLBACK_COLORS = ["#58a6ff", "#3fb950", "#d29922", "#f85149", "#a371f7", "#db61a2"]


def gh_json(url: str) -> object:
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "netra-stats-generator",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def gh_graphql(query: str) -> dict:
    body = json.dumps({"query": query}).encode()
    req = urllib.request.Request("https://api.github.com/graphql", data=body, headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "netra-stats-generator",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)["data"]


def collect() -> tuple[list[tuple[str, str]], list[tuple[str, float, str]]]:
    """Return (stat rows, language slices)."""
    data = gh_graphql("""
    {
      user(login: "%s") {
        repositories(first: 100, ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC) {
          totalCount
          nodes { stargazerCount languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
            edges { size node { name } } } }
        }
        contributionsCollection {
          totalCommitContributions
          totalRepositoriesWithContributedCommits
          contributionCalendar { totalContributions }
        }
      }
    }""" % USER)["user"]

    repos = data["repositories"]
    stars = sum(r["stargazerCount"] for r in repos["nodes"])
    c = data["contributionsCollection"]

    # Deliberately surfaces breadth + consistency. PR/issue counts are omitted:
    # they measure open-source tenure, not engineering capability.
    rows = [
        ("commit", "Total Commits (past year)", f"{c['totalCommitContributions']:,}"),
        ("graph",  "Total Contributions",       f"{c['contributionCalendar']['totalContributions']:,}"),
        ("repo",   "Repositories Contributed To", f"{c['totalRepositoriesWithContributedCommits']:,}"),
        ("book",   "Public Repositories",       f"{repos['totalCount']:,}"),
        ("star",   "Total Stars Earned",        f"{stars:,}"),
    ]

    totals: dict[str, int] = defaultdict(int)
    for r in repos["nodes"]:
        for e in r["languages"]["edges"]:
            totals[e["node"]["name"]] += e["size"]

    grand = sum(totals.values()) or 1
    top = sorted(totals.items(), key=lambda kv: -kv[1])[:6]
    langs = []
    for i, (name, size) in enumerate(top):
        colour = LANG_COLORS.get(name, FALLBACK_COLORS[i % len(FALLBACK_COLORS)])
        langs.append((name, size * 100.0 / grand, colour))
    return rows, langs


ICONS = {  # 16x16 octicon paths
    "star": "M8 .25a.75.75 0 0 1 .673.418l1.882 3.815 4.21.612a.75.75 0 0 1 .416 1.279l-3.046 2.97.719 4.192a.75.75 0 0 1-1.088.791L8 12.347l-3.766 1.98a.75.75 0 0 1-1.088-.79l.72-4.194L.818 6.374a.75.75 0 0 1 .416-1.28l4.21-.611L7.327.668A.75.75 0 0 1 8 .25Z",
    "commit": "M11.93 8.5a4.002 4.002 0 0 1-7.86 0H.75a.75.75 0 0 1 0-1.5h3.32a4.002 4.002 0 0 1 7.86 0h3.32a.75.75 0 0 1 0 1.5Zm-1.43-.75a2.5 2.5 0 1 0-5 0 2.5 2.5 0 0 0 5 0Z",
    "repo": "M2 2.5A2.5 2.5 0 0 1 4.5 0h8.75a.75.75 0 0 1 .75.75v12.5a.75.75 0 0 1-.75.75h-2.5a.75.75 0 0 1 0-1.5h1.75v-2h-8a1 1 0 0 0-.714 1.7.75.75 0 1 1-1.072 1.05A2.495 2.495 0 0 1 2 11.5Zm10.5-1h-8a1 1 0 0 0-1 1v6.708A2.486 2.486 0 0 1 4.5 9h8Z",
    "book": "M0 1.75A.75.75 0 0 1 .75 1h4.253c1.227 0 2.317.59 3 1.501A3.743 3.743 0 0 1 11.006 1h4.245a.75.75 0 0 1 .75.75v10.5a.75.75 0 0 1-.75.75h-4.507a2.25 2.25 0 0 0-1.591.659l-.622.621a.75.75 0 0 1-1.06 0l-.622-.621A2.25 2.25 0 0 0 5.258 13H.75a.75.75 0 0 1-.75-.75Z",
    "graph": "M1.5 1.75V13.5h13.75a.75.75 0 0 1 0 1.5H.75a.75.75 0 0 1-.75-.75V1.75a.75.75 0 0 1 1.5 0Zm14.28 2.53-5.25 5.25a.75.75 0 0 1-1.06 0L7 7.06 4.28 9.78a.751.751 0 0 1-1.042-.018.751.751 0 0 1-.018-1.042l3.25-3.25a.75.75 0 0 1 1.06 0L9 7.94l4.72-4.72a.751.751 0 0 1 1.042.018.751.751 0 0 1 .018 1.042Z",
}


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render_stats(rows, t: dict) -> str:
    w, h = 500, 60 + len(rows) * 30
    parts = [
        f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" fill="none" '
        f'xmlns="http://www.w3.org/2000/svg" role="img" aria-label="GitHub statistics">',
        '<style>'
        '.t{font:600 18px "Segoe UI",Ubuntu,sans-serif;fill:%s}'
        '.l{font:400 14px "Segoe UI",Ubuntu,sans-serif;fill:%s}'
        '.v{font:700 14px "Segoe UI",Ubuntu,sans-serif;fill:%s}'
        '.r{opacity:0;animation:f .5s ease-in-out forwards}'
        '@keyframes f{to{opacity:1;transform:translateX(0)}}'
        '</style>' % (t["title"], t["text"], t["text"]),
        f'<rect x=".5" y=".5" rx="6" width="{w-1}" height="{h-1}" fill="{t["bg"]}" stroke="{t["border"]}"/>',
        f'<text x="25" y="35" class="t">Divyakush\'s GitHub Stats</text>',
    ]
    for i, (icon, label, value) in enumerate(rows):
        y = 62 + i * 30
        delay = 0.15 + i * 0.12
        parts.append(f'<g class="r" style="animation-delay:{delay}s">')
        parts.append(f'<g transform="translate(25,{y-12})"><svg width="16" height="16" viewBox="0 0 16 16" '
                     f'fill="{t["icon"]}"><path d="{ICONS[icon]}"/></svg></g>')
        parts.append(f'<text x="52" y="{y}" class="l">{esc(label)}:</text>')
        parts.append(f'<text x="{w-25}" y="{y}" class="v" text-anchor="end">{esc(value)}</text></g>')
    parts.append("</svg>")
    return "".join(parts)


def render_langs(langs, t: dict) -> str:
    w = 500
    rows = (len(langs) + 1) // 2
    h = 92 + rows * 24
    bar_w, bar_x, bar_y = w - 50, 25, 52
    parts = [
        f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" fill="none" '
        f'xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Most used languages">',
        '<style>'
        '.t{font:600 18px "Segoe UI",Ubuntu,sans-serif;fill:%s}'
        '.n{font:400 13px "Segoe UI",Ubuntu,sans-serif;fill:%s}'
        '.g{opacity:0;animation:f .5s ease-in-out forwards}'
        '@keyframes f{to{opacity:1}}'
        '</style>' % (t["title"], t["text"]),
        f'<rect x=".5" y=".5" rx="6" width="{w-1}" height="{h-1}" fill="{t["bg"]}" stroke="{t["border"]}"/>',
        '<text x="25" y="35" class="t">Most Used Languages</text>',
        f'<mask id="m"><rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="10" rx="5" fill="#fff"/></mask>',
        '<g mask="url(#m)">',
    ]
    off = 0.0
    for _, pct, colour in langs:
        seg = bar_w * pct / 100.0
        parts.append(f'<rect x="{bar_x+off:.2f}" y="{bar_y}" width="{seg:.2f}" height="10" fill="{colour}"/>')
        off += seg
    if off < bar_w:  # remainder ("Other")
        parts.append(f'<rect x="{bar_x+off:.2f}" y="{bar_y}" width="{bar_w-off:.2f}" height="10" fill="{t["muted"]}"/>')
    parts.append("</g>")

    for i, (name, pct, colour) in enumerate(langs):
        col, row = i % 2, i // 2
        x = 25 + col * 235
        y = 92 + row * 24
        parts.append(f'<g class="g" style="animation-delay:{0.2+i*0.1}s">')
        parts.append(f'<circle cx="{x+5}" cy="{y-4}" r="5" fill="{colour}"/>')
        parts.append(f'<text x="{x+18}" y="{y}" class="n">{esc(name)} {pct:.2f}%</text></g>')
    parts.append("</svg>")
    return "".join(parts)


def main() -> int:
    if not TOKEN:
        print("error: GITHUB_TOKEN is required", file=sys.stderr)
        return 1
    os.makedirs(OUT_DIR, exist_ok=True)
    rows, langs = collect()
    for theme, palette in THEMES.items():
        for name, svg in (("stats", render_stats(rows, palette)),
                          ("langs", render_langs(langs, palette))):
            path = os.path.join(OUT_DIR, f"{name}-{theme}.svg")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(svg)
            print(f"wrote {path}")
    print("\nstats:", {label: value for _, label, value in rows})
    print("langs:", [(n, round(p, 2)) for n, p, _ in langs])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
