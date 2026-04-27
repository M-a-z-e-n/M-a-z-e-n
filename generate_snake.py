#!/usr/bin/env python3
"""
Custom GitHub Contribution Snake Generator
Fetches real contributions and draws a snake SVG without legend
Colors match M-a-z-e-n's README theme (#0D1117 background, #00C2FF accent)
"""

import requests
import json
import math
import random
import os
import sys
from datetime import datetime, timedelta

# ── Config ──────────────────────────────────────────────────────────────────
GITHUB_USER   = os.environ.get("GITHUB_USER", "M-a-z-e-n")
GITHUB_TOKEN  = os.environ.get("GITHUB_TOKEN", "")
OUTPUT_LIGHT  = os.environ.get("OUTPUT_LIGHT", "dist/github-contribution-grid-snake.svg")
OUTPUT_DARK   = os.environ.get("OUTPUT_DARK",  "dist/github-contribution-grid-snake-dark.svg")

# Grid dimensions (GitHub contribution graph: 53 weeks × 7 days)
COLS = 53
ROWS = 7
CELL = 12        # px per cell
GAP  = 3         # px gap between cells
PAD  = 20        # padding around grid

GRID_W = COLS * (CELL + GAP) - GAP + PAD * 2
GRID_H = ROWS * (CELL + GAP) - GAP + PAD * 2

# Theme
THEMES = {
    "dark": {
        "bg":           "#0D1117",
        "empty":        "#161B22",
        "empty_stroke": "#21262D",
        "dot_low":      "#0A3D62",
        "dot_mid":      "#0A6EBD",
        "dot_high":     "#00C2FF",
        "snake_body":   "#00C2FF",
        "snake_head":   "#FFFFFF",
        "snake_eye":    "#0D1117",
    },
    "light": {
        "bg":           "#FFFFFF",
        "empty":        "#EBEDF0",
        "empty_stroke": "#D0D7DE",
        "dot_low":      "#9BE9A8",
        "dot_mid":      "#40C463",
        "dot_high":     "#216E39",
        "snake_body":   "#00C2FF",
        "snake_head":   "#0A3D62",
        "snake_eye":    "#FFFFFF",
    },
}


# ── GitHub API ───────────────────────────────────────────────────────────────
def fetch_contributions():
    """Fetch contribution data via GitHub GraphQL API."""
    headers = {"Authorization": f"bearer {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
    query = """
    query($login: String!) {
      user(login: $login) {
        contributionsCollection {
          contributionCalendar {
            weeks {
              contributionDays {
                contributionCount
                date
              }
            }
          }
        }
      }
    }
    """
    try:
        r = requests.post(
            "https://api.github.com/graphql",
            json={"query": query, "variables": {"login": GITHUB_USER}},
            headers=headers,
            timeout=15
        )
        data = r.json()
        weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
        grid = []
        for week in weeks:
            col = []
            for day in week["contributionDays"]:
                col.append(day["contributionCount"])
            grid.append(col)
        return grid
    except Exception as e:
        print(f"⚠ Could not fetch contributions: {e}. Using demo grid.")
        return generate_demo_grid()


def generate_demo_grid():
    """Fallback demo grid if API is unavailable."""
    random.seed(42)
    grid = []
    for _ in range(COLS):
        col = []
        for _ in range(ROWS):
            r = random.random()
            if r < 0.6:
                col.append(0)
            elif r < 0.8:
                col.append(random.randint(1, 3))
            elif r < 0.95:
                col.append(random.randint(4, 8))
            else:
                col.append(random.randint(9, 20))
        grid.append(col)
    return grid


# ── Snake Path ───────────────────────────────────────────────────────────────
def generate_snake_path(grid):
    """
    Generate snake path that visits all non-zero cells first,
    then fills remaining cells, moving in a boustrophedon pattern.
    Returns list of (col, row) tuples.
    """
    cols = len(grid)
    rows = max(len(col) for col in grid)

    # Build full cell list in boustrophedon order (snake scan)
    path = []
    for c in range(cols):
        col_cells = [(c, r) for r in range(rows)] if c % 2 == 0 else [(c, r) for r in range(rows - 1, -1, -1)]
        path.extend(col_cells)

    return path


# ── SVG Generation ───────────────────────────────────────────────────────────
def cell_xy(col, row):
    """Top-left pixel of a grid cell."""
    x = PAD + col * (CELL + GAP)
    y = PAD + row * (CELL + GAP)
    return x, y


def dot_color(count, theme):
    t = THEMES[theme]
    if count == 0:
        return t["empty"], t["empty_stroke"]
    elif count <= 2:
        return t["dot_low"], t["dot_low"]
    elif count <= 6:
        return t["dot_mid"], t["dot_mid"]
    else:
        return t["dot_high"], t["dot_high"]


def build_svg(grid, theme, snake_path):
    t = THEMES[theme]
    cols = len(grid)
    rows = max(len(col) for col in grid)

    snake_set = set(snake_path)
    snake_index = {cell: i for i, cell in enumerate(snake_path)}
    snake_len = max(6, min(12, len([c for col in grid for c in col if c > 0]) // 10))

    # Head is last cell in path
    head = snake_path[-1]
    body_cells = set(snake_path[max(0, len(snake_path) - snake_len - 1):-1])

    lines = []
    lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{GRID_W}" height="{GRID_H}" viewBox="0 0 {GRID_W} {GRID_H}">')
    lines.append(f'  <rect width="{GRID_W}" height="{GRID_H}" fill="{t["bg"]}" rx="6"/>')

    # Draw all cells
    for c in range(cols):
        col_data = grid[c] if c < len(grid) else []
        for r in range(rows):
            count = col_data[r] if r < len(col_data) else 0
            x, y = cell_xy(c, r)
            cell = (c, r)

            if cell == head:
                # Snake head
                fill = t["snake_head"]
                lines.append(f'  <rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="3" fill="{fill}"/>')
                # Eyes
                ex1, ey1 = x + 3, y + 3
                ex2, ey2 = x + 8, y + 3
                lines.append(f'  <circle cx="{ex1}" cy="{ey1}" r="1.5" fill="{t["snake_eye"]}"/>')
                lines.append(f'  <circle cx="{ex2}" cy="{ey2}" r="1.5" fill="{t["snake_eye"]}"/>')
            elif cell in body_cells:
                # Snake body — slightly smaller for segment feel
                bx, by = x + 1, y + 1
                bw, bh = CELL - 2, CELL - 2
                lines.append(f'  <rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="2" fill="{t["snake_body"]}" opacity="0.85"/>')
            else:
                fill, stroke = dot_color(count, theme)
                lines.append(f'  <rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="{fill}" stroke="{stroke}" stroke-width="0.5"/>')

    lines.append('</svg>')
    return "\n".join(lines)


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    print(f"🐍 Generating snake for: {GITHUB_USER}")

    grid = fetch_contributions()
    print(f"✓ Grid loaded: {len(grid)} weeks")

    snake_path = generate_snake_path(grid)
    print(f"✓ Snake path: {len(snake_path)} cells")

    os.makedirs("dist", exist_ok=True)

    for theme, output in [("dark", OUTPUT_DARK), ("light", OUTPUT_LIGHT)]:
        svg = build_svg(grid, theme, snake_path)
        with open(output, "w") as f:
            f.write(svg)
        print(f"✓ Saved {theme}: {output}")

    print("🎉 Done!")


if __name__ == "__main__":
    main()
