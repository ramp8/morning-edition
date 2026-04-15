#!/usr/bin/env python3
"""
Morning Edition — Daily HN Magazine Generator
Fetches Hacker News front page, curates top 10 stories, renders as editorial HTML magazine.
"""

from __future__ import annotations

import json
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

HERMES_HOME = Path.home() / ".hermes"
OUTPUT_DIR = HERMES_HOME / "scripts" / "magazines"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Curation keywords ──────────────────────────────────────────────
LEAN_IN = {
    "ai",
    "artificial intelligence",
    "llm",
    "gpt",
    "claude",
    "gemini",
    "openai",
    "anthropic",
    "machine learning",
    "ml",
    "deep learning",
    "neural",
    "creative",
    "design",
    "3d",
    "blender",
    "figma",
    "photoshop",
    "illustration",
    "music",
    "audio",
    "video",
    "animation",
    "generative",
    "dev tools",
    "developer",
    "cli",
    "terminal",
    "editor",
    "ide",
    "vim",
    "neovim",
    "emacs",
    "vscode",
    "language server",
    "compiler",
    "debugger",
    "linter",
    "open source",
    "self-host",
    "self-hosted",
    "privacy",
    "encryption",
    "vpn",
    "tor",
    "surveillance",
    "tracking",
    "ad blocker",
    "decentralized",
    "weird",
    "strange",
    "unusual",
    "surprising",
    "counterintuitive",
    "science",
    "physics",
    "quantum",
    "biology",
    "neuroscience",
    "space",
    "actionable",
    "how i",
    "how to",
    "guide",
    "tutorial",
    "workflow",
    "automation",
    "script",
    "tool",
    "framework",
    "library",
    "api",
    "rust",
    "go",
    "python",
    "zig",
    "swift",
    "kotlin",
    "typescript",
    "postgres",
    "sqlite",
    "redis",
    "database",
    "homelab",
    "raspberry pi",
    "sbc",
    "nix",
    "nixos",
    "indie",
    "solo",
    "bootstrapped",
    "side project",
    "productivity",
    "note-taking",
    "obsidian",
    "knowledge management",
    "reverse engineering",
    "exploit",
    "security",
    "hacking",
    "alternative",
    "minimalist",
    "lightweight",
    "fast",
}

SKIP = {
    "crypto",
    "cryptocurrency",
    "bitcoin",
    "ethereum",
    "nft",
    "web3",
    "defi",
    "coinbase",
    "binance",
    "blockchain",
    "token",
    "y combinator",
    "yc",
    "startup fundraising",
    "series a",
    "series b",
    "valuation",
    "vc",
    "venture capital",
    "ipo",
    "politics",
    "election",
    "congress",
    "senate",
    "trump",
    "biden",
    "legislation",
    "regulation",
    "policy",
    "remote work debate",
    "return to office",
    "rto",
}

FLAG_FOR_USER = {
    "ai tool",
    "ai agent",
    "llm tool",
    "coding assistant",
    "copilot",
    "devtool",
    "cli tool",
    "terminal tool",
    "homelab",
    "self-hosted",
    "privacy tool",
    "automation",
    "workflow",
    "note-taking",
    "obsidian",
    "nixos",
    "nix",
    "raspberry pi",
}


def fetch_json(url: str) -> dict | list:
    req = urllib.request.Request(url, headers={"User-Agent": "MorningEdition/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())


def get_hn_stories(limit: int = 50) -> list[dict]:
    """Fetch top HN stories with metadata."""
    ids = fetch_json("https://hacker-news.firebaseio.com/v0/topstories.json")[:limit]
    stories = []
    for sid in ids:
        try:
            item = fetch_json(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json")
            if item and item.get("type") == "story" and not item.get("deleted"):
                stories.append(item)
        except Exception:
            continue
    return stories


def score_story(story: dict) -> tuple[int, int]:
    """Returns (lean_score, skip_penalty). Higher lean = more relevant. skip > 0 = filtered out."""
    title = (story.get("title") or "").lower()
    lean_hits = sum(1 for kw in LEAN_IN if kw in title)
    skip_hits = sum(1 for kw in SKIP if kw in title)
    return lean_hits, skip_hits


def flag_story(story: dict) -> bool:
    title = (story.get("title") or "").lower()
    return any(kw in title for kw in FLAG_FOR_USER)


def curate(stories: list[dict], count: int = 10) -> list[dict]:
    """Pick top stories: prefer high lean_score, penalize skip, break ties by HN score."""
    scored = []
    for s in stories:
        lean, skip = score_story(s)
        if skip >= 2:
            continue  # hard skip
        hn_score = s.get("score", 0) or 0
        curated = {
            **s,
            "_lean": lean,
            "_skip": skip,
            "_flag": flag_story(s),
            "_final_score": (lean * 1000) - (skip * 500) + min(hn_score, 999),
        }
        scored.append(curated)

    scored.sort(key=lambda x: x["_final_score"], reverse=True)
    return scored[:count]


# ── Magazine Spreads ───────────────────────────────────────────────

SPREAD_STYLES = [
    # 1. HERO — warm off-white opener with bold orange
    {
        "name": "hero",
        "bg": "#faf5ef",
        "fg": "#1a1a1a",
        "accent": "#e85d26",
        "num_size": "14rem",
        "num_color": "#e85d26",
        "num_opacity": "0.12",
        "num_pos": "top-left",
        "layout": "center",
    },
    # 2. SKY — soft blue editorial
    {
        "name": "sky",
        "bg": "#e8f0fe",
        "fg": "#1a2a3a",
        "accent": "#1565c0",
        "num_size": "12rem",
        "num_color": "#1565c0",
        "num_opacity": "0.1",
        "num_pos": "bottom-right",
        "layout": "left",
    },
    # 3. ROSE ALERT — urgent stamp feel
    {
        "name": "rose-alert",
        "bg": "#fce4ec",
        "fg": "#1a1a1a",
        "accent": "#c62828",
        "num_size": "10rem",
        "num_color": "#c62828",
        "num_opacity": "0.9",
        "num_pos": "top-right",
        "layout": "left",
    },
    # 4. TERMINAL — retro green on cream
    {
        "name": "terminal",
        "bg": "#f0f5e8",
        "fg": "#2e4a1e",
        "accent": "#33691e",
        "num_size": "8rem",
        "num_color": "#33691e",
        "num_opacity": "0.15",
        "num_pos": "top-left",
        "layout": "left",
    },
    # 5. ACADEMIC — drop-cap scholarly
    {
        "name": "academic",
        "bg": "#faf8f5",
        "fg": "#2c2c2c",
        "accent": "#1a5276",
        "num_size": "9rem",
        "num_color": "#1a5276",
        "num_opacity": "0.12",
        "num_pos": "left-center",
        "layout": "right-of-num",
    },
    # 6. SUNSET — warm coral energy
    {
        "name": "sunset",
        "bg": "#fff3e0",
        "fg": "#3e2723",
        "accent": "#e65100",
        "num_size": "11rem",
        "num_color": "#e65100",
        "num_opacity": "0.12",
        "num_pos": "bottom-left",
        "layout": "center",
    },
    # 7. SAGE — muted green calm
    {
        "name": "sage",
        "bg": "#e8f5e9",
        "fg": "#1b3a1f",
        "accent": "#2e7d32",
        "num_size": "10rem",
        "num_color": "#2e7d32",
        "num_opacity": "0.1",
        "num_pos": "top-right",
        "layout": "left",
    },
    # 8. DATA — amber blueprint
    {
        "name": "data",
        "bg": "#fff8e1",
        "fg": "#3e2723",
        "accent": "#f57f17",
        "num_size": "7rem",
        "num_color": "#f57f17",
        "num_opacity": "0.15",
        "num_pos": "bottom-left",
        "layout": "left",
    },
    # 9. LAVENDER — soft creative
    {
        "name": "lavender",
        "bg": "#ede7f6",
        "fg": "#311b5e",
        "accent": "#6a1b9a",
        "num_size": "9rem",
        "num_color": "#6a1b9a",
        "num_opacity": "0.1",
        "num_pos": "top-left",
        "layout": "center",
    },
    # 10. BIG STAT — number IS the story
    {
        "name": "big-stat",
        "bg": "#f5f0eb",
        "fg": "#1a1a1a",
        "accent": "#e85d26",
        "num_size": "16rem",
        "num_color": "#e85d26",
        "num_opacity": "0.08",
        "num_pos": "center",
        "layout": "over-num",
    },
]


def render_spread(story: dict, index: int) -> str:
    s = SPREAD_STYLES[index]
    num = index + 1
    title = story.get("title", "Untitled")
    url = story.get("url", f"https://news.ycombinator.com/item?id={story.get('id')}")
    hn_score = story.get("score", 0)
    by = story.get("by", "anon")
    descendants = story.get("descendants", 0)
    flag = story.get("_flag", False)

    # Position the big numeral
    num_styles = {
        "top-left": "top: -2rem; left: -1rem;",
        "bottom-right": "bottom: -2rem; right: -1rem;",
        "top-right": "top: -2rem; right: -1rem;",
        "left-center": "top: 50%; left: -1rem; transform: translateY(-50%);",
        "bottom-left": "bottom: -2rem; left: -1rem;",
        "center": "top: 50%; left: 50%; transform: translate(-50%, -50%);",
    }
    num_pos = num_styles.get(s["num_pos"], "top: -2rem; left: -1rem;")

    # Layout variations
    if s["layout"] == "center":
        content_style = "text-align: center; max-width: 700px; margin: 0 auto; position: relative; z-index: 2;"
    elif s["layout"] == "right-of-num":
        content_style = "margin-left: 5rem; position: relative; z-index: 2;"
    elif s["layout"] == "over-num":
        content_style = "position: relative; z-index: 2; text-align: center;"
    else:
        content_style = "max-width: 650px; position: relative; z-index: 2;"

    # Terminal-style prefix
    prefix = ""
    if s["name"] == "terminal":
        prefix = '<div style="font-size:1.1rem;opacity:0.5;margin-bottom:0.5rem;">$ cat story.md</div>'
    elif s["name"] == "academic":
        prefix = (
            '<div style="font-size:1rem;letter-spacing:0.15em;text-transform:uppercase;opacity:0.5;margin-bottom:0.5rem;">Vol. CMXCVIII · No. '
            + str(num)
            + "</div>"
        )

    flag_html = ""
    if flag:
        flag_html = f"""<div style="
            display:inline-block;
            background:{s["accent"]};
            color:{s["bg"]};
            font-family:'Inter',sans-serif;
            font-weight:800;
            font-size:0.85rem;
            letter-spacing:0.08em;
            text-transform:uppercase;
            padding:0.35rem 0.9rem;
            border-radius:3px;
            margin-bottom:1.2rem;
        ">⚑ For You</div><br>"""

    return f'''
    <section style="
        background: {s["bg"]};
        color: {s["fg"]};
        min-height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 6rem 4rem;
        position: relative;
        overflow: hidden;
        page-break-after: always;
    ">
        <!-- Giant Numeral -->
        <div style="
            position: absolute;
            font-family: 'Fraunces', serif;
            font-size: {s["num_size"]};
            font-weight: 900;
            color: {s["num_color"]};
            opacity: {s["num_opacity"]};
            line-height: 1;
            {num_pos}
            user-select: none;
            pointer-events: none;
        ">{num:02d}</div>

        <div style="{content_style}">
            {prefix}
            {flag_html}
            <h2 style="
                font-family: 'Fraunces', serif;
                font-size: 3.2rem;
                font-weight: 700;
                line-height: 1.15;
                margin-bottom: 1.5rem;
                color: {s["fg"]};
            "><a href="{url}" style="color:inherit;text-decoration:none;border-bottom:2px solid {s["accent"]}40;" target="_blank">{title}</a></h2>

            <div style="
                font-family: 'Inter', sans-serif;
                font-size: 1.15rem;
                line-height: 1.6;
                opacity: 0.7;
                margin-bottom: 2rem;
            ">
                by <strong>{by}</strong> · {hn_score:,} points · {descendants} comments
            </div>

            <a href="{url}" style="
                font-family: 'Inter', sans-serif;
                font-weight: 600;
                font-size: 1.1rem;
                color: {s["accent"]};
                text-decoration: none;
                border-bottom: 2px solid {s["accent"]};
                padding-bottom: 2px;
            ">Read →</a>
        </div>
    </section>'''


def render_magazine(stories: list[dict], date_str: str) -> str:
    spreads = "\n".join(render_spread(s, i) for i, s in enumerate(stories))

    # Story titles for table of contents
    toc_items = ""
    for i, s in enumerate(stories):
        flag = " ⚑" if s.get("_flag") else ""
        toc_items += f"""<div style="
            font-family: 'Inter', sans-serif;
            font-size: 1.2rem;
            padding: 0.6rem 0;
            border-bottom: 1px solid #1a1a1a10;
            color: #555;
        "><span style="color:#ff6b35;font-weight:700;font-family:'Fraunces',serif;margin-right:1rem;">{i + 1:02d}</span>{s.get("title", "Untitled")}{flag}</div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Morning Edition — {date_str}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300..900;1,9..144,300..900&family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        html {{ scroll-behavior: smooth; }}
        body {{ background: #f5f0eb; }}
        a {{ transition: opacity 0.2s; }}
        a:hover {{ opacity: 0.8; }}
        @media (max-width: 768px) {{
            section {{ padding: 4rem 2rem !important; }}
            h2 {{ font-size: 2.2rem !important; }}
        }}
    </style>
</head>
<body>
    <!-- COVER -->
    <section style="
        background: #faf5ef;
        color: #1a1a1a;
        min-height: 100vh;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
        padding: 4rem;
    ">
        <div style="font-family:'Inter',sans-serif;font-size:1rem;letter-spacing:0.3em;text-transform:uppercase;opacity:0.4;margin-bottom:2rem;">Daily Digest</div>
        <h1 style="font-family:'Fraunces',serif;font-size:6rem;font-weight:900;line-height:1;margin-bottom:1rem;color:#e85d26;">Morning<br>Edition</h1>
        <div style="font-family:'Inter',sans-serif;font-size:1.4rem;font-weight:300;opacity:0.5;margin-bottom:4rem;">{date_str}</div>
        <div style="width:400px;max-width:100%;text-align:left;">
            {toc_items}
        </div>
        <div style="font-family:'Inter',sans-serif;font-size:0.85rem;opacity:0.25;margin-top:4rem;">Curated from Hacker News · 10 stories that matter</div>
    </section>

    {spreads}

    <!-- BACK COVER -->
    <section style="
        background: #faf5ef;
        color: #1a1a1a;
        min-height: 60vh;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
        padding: 4rem;
    ">
        <div style="font-family:'Fraunces',serif;font-size:3rem;font-weight:700;opacity:0.2;">∎</div>
        <div style="font-family:'Inter',sans-serif;font-size:1rem;opacity:0.3;margin-top:2rem;">
            Morning Edition · {date_str}<br>
            Hacker News × Your Taste Profile
        </div>
    </section>
</body>
</html>"""


def main():
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")

    print("Fetching HN stories...")
    stories = get_hn_stories(limit=50)
    print(f"Got {len(stories)} stories, curating...")

    curated = curate(stories, count=10)
    print(f"Selected {len(curated)} stories")

    html = render_magazine(curated, date_str)

    out_path = OUTPUT_DIR / f"{date_str}.html"
    out_path.write_text(html, encoding="utf-8")
    print(f"MAGAZINE_SAVED={out_path}")
    return str(out_path)


if __name__ == "__main__":
    main()
