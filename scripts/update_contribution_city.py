#!/usr/bin/env python3
"""Render a neon isometric city from a public GitHub contribution calendar."""

from __future__ import annotations

import html
import re
import sys
import urllib.request
from datetime import date, datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

USERNAME = "tanishqnarula12"
OUTPUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("assets/contribution-city.svg")


class CalendarParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.days: list[tuple[date, int, int]] = []
        self.pending: tuple[date, int] | None = None
        self.in_tooltip = False
        self.tooltip = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs = dict(attrs)
        if tag == "td" and "ContributionCalendar-day" in (attrs.get("class") or ""):
            try:
                self.pending = (date.fromisoformat(attrs["data-date"] or ""), int(attrs["data-level"] or "0"))
            except (KeyError, ValueError):
                self.pending = None
        elif tag == "tool-tip" and self.pending:
            self.in_tooltip = True
            self.tooltip = ""

    def handle_data(self, data: str) -> None:
        if self.in_tooltip:
            self.tooltip += data

    def handle_endtag(self, tag: str) -> None:
        if tag == "tool-tip" and self.in_tooltip:
            if self.pending:
                count_match = re.search(r"([\d,]+)\s+contributions?\b", self.tooltip, re.I)
                count = int(count_match.group(1).replace(",", "")) if count_match else 0
                self.days.append((self.pending[0], self.pending[1], count))
            self.pending = None
            self.in_tooltip = False


def fetch_days() -> list[tuple[date, int, int]]:
    url = f"https://github.com/users/{USERNAME}/contributions"
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; ContributionCity/1.0)", "Accept": "text/html"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        source = response.read().decode("utf-8", "replace")
    parser = CalendarParser()
    parser.feed(source)
    if len(parser.days) < 300:
        raise RuntimeError(f"Expected a full contribution year, received {len(parser.days)} days")
    return parser.days


def polygon(points: list[tuple[float, float]], fill: str, stroke: str, opacity: float = 1) -> str:
    points_attr = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    return f'<polygon points="{points_attr}" fill="{fill}" stroke="{stroke}" stroke-width=".8" opacity="{opacity:.2f}"/>'


def render(days: list[tuple[date, int, int]]) -> str:
    total = sum(count for _, _, count in days)
    active = sum(count > 0 for _, _, count in days)
    start = min(day for day, _, _ in days)
    levels = ["#10271D", "#168447", "#25B65D", "#45DB78", "#9AF2A8"]
    max_count = max((count for _, _, count in days), default=1)
    floors: list[str] = []
    towers: list[tuple[float, str]] = []

    for day, level, count in days:
        offset = (day - start).days
        week, weekday = divmod(offset, 7)
        # Use the same two isometric vectors for both the tile edges and cell
        # spacing. This keeps the calendar as one clean, non-overlapping plane.
        x = 43 + week * 17.5 + weekday * 17.5
        y = 240 + week * 6 - weekday * 10
        a = (x, y)
        b = (x + 17.5, y + 6)
        c = (x + 35, y - 4)
        d = (x + 17.5, y - 10)
        tint = levels[min(max(level, 0), 4)]
        if count == 0:
            floors.append(polygon([a, b, c, d], "#0D2118", "#274532", .95))
            continue
        height = min(108.0, 14.0 + 94.0 * (count / max_count) ** 0.55)
        at, bt, ct, dt = ((px, py - height) for px, py in (a, b, c, d))
        floors.append(polygon([a, b, c, d], "#163821", "#3A7046", .98))
        block = [
            f'<ellipse cx="{x + 14}" cy="{y - height / 2:.1f}" rx="14" ry="{height / 1.5:.1f}" fill="{tint}" opacity=".18" filter="url(#glow)"/>',
            polygon([a, b, bt, at], "#126539", tint, .98),
            polygon([b, c, ct, bt], "#0A4B2A", tint, 1),
            polygon([at, bt, ct, dt], tint, "#B8FFC4", 1),
        ]
        if count >= max(8, max_count * .55):
            block.append(f'<path d="M{x + 10:.1f} {y - height + 3:.1f}h9" stroke="#D9FFE0" stroke-width="1.5" opacity=".9"/>')
        towers.append((y, "".join(block)))
    bars = floors + [markup for _, markup in sorted(towers, key=lambda item: item[0])]

    updated = datetime.now(timezone.utc).strftime("%d %b %Y · %H:%M UTC")
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="640" viewBox="0 0 1200 640" role="img" aria-labelledby="title desc">
<title id="title">Live GitHub Contribution City for {USERNAME}</title>
<desc id="desc">A large isometric emerald contribution grid generated from {total:,} public GitHub contributions across {active} active days during the last year. Each building height reflects that day’s contribution count. Refreshed {updated}.</desc>
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1200" y2="640" gradientUnits="userSpaceOnUse"><stop stop-color="#07120D"/><stop offset=".58" stop-color="#0A1D12"/><stop offset="1" stop-color="#102018"/></linearGradient>
  <linearGradient id="beam" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#62F08B"/><stop offset="1" stop-color="#B6FFB6"/></linearGradient>
  <radialGradient id="aura"><stop stop-color="#31E970" stop-opacity=".24"/><stop offset="1" stop-color="#31E970" stop-opacity="0"/></radialGradient>
  <filter id="glow" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="5"/></filter>
  <pattern id="stars" width="137" height="97" patternUnits="userSpaceOnUse"><circle cx="13" cy="21" r="1" fill="#9AFFB4" opacity=".32"/><circle cx="91" cy="61" r=".8" fill="#5DEB81" opacity=".38"/><circle cx="57" cy="84" r=".7" fill="#D0FFD6" opacity=".24"/></pattern>
</defs>
<rect width="1200" height="640" rx="26" fill="url(#bg)"/>
<rect width="1200" height="640" rx="26" fill="url(#stars)"/>
<circle cx="775" cy="340" r="430" fill="url(#aura)"/>
<text x="58" y="58" fill="#80F39A" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="12" letter-spacing="3.1">LIVE CONTRIBUTION CITY  /  BUILDER MODE</text>
<text x="55" y="108" fill="#F2FFF4" font-family="Inter, ui-sans-serif, system-ui, sans-serif" font-size="32" font-weight="720">Building ideas into real products.</text>
<g>{''.join(bars)}</g>
<rect x="790" y="28" width="365" height="112" rx="15" fill="#0D2118" stroke="#315A3B" stroke-width="1.2"/>
<path d="M972 45v78" stroke="#315A3B"/>
<text x="816" y="58" fill="#86A994" font-family="Inter, ui-sans-serif, system-ui, sans-serif" font-size="10" letter-spacing="1.8">CONTRIBUTIONS</text>
<text x="814" y="102" fill="#9AF2A8" font-family="Inter, ui-sans-serif, system-ui, sans-serif" font-size="34" font-weight="700">{total:,}</text>
<text x="997" y="58" fill="#86A994" font-family="Inter, ui-sans-serif, system-ui, sans-serif" font-size="10" letter-spacing="1.8">ACTIVE DAYS</text>
<text x="995" y="102" fill="#F2FFF4" font-family="Inter, ui-sans-serif, system-ui, sans-serif" font-size="34" font-weight="700">{active}</text>
<path d="M55 582 1100 582" stroke="url(#beam)" stroke-opacity=".25"/>
<text x="58" y="612" fill="#91B39A" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="10" letter-spacing="1.2">DAILY CONTRIBUTIONS  ·  TALLER BLOCKS = MORE ACTIVITY</text>
<g transform="translate(927 606)" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="9" fill="#91B39A">
 <text x="-73" y="4">LESS</text><rect x="-42" y="-7" width="12" height="12" rx="2" fill="#10271D" stroke="#274532"/><rect x="-24" y="-7" width="12" height="12" rx="2" fill="#168447"/><rect x="-6" y="-7" width="12" height="12" rx="2" fill="#25B65D"/><rect x="12" y="-7" width="12" height="12" rx="2" fill="#45DB78"/><rect x="30" y="-7" width="12" height="12" rx="2" fill="#9AF2A8"/><text x="53" y="4">MORE</text>
</g>
<text x="58" y="632" fill="#6F9079" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="9" letter-spacing="1.1">PUBLIC GITHUB CONTRIBUTION CALENDAR  ·  REFRESHED {html.escape(updated)}</text>
</svg>
'''


def main() -> None:
    days = fetch_days()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render(days), encoding="utf-8")
    print(f"Wrote {OUTPUT}: {sum(x[2] for x in days):,} contributions / {len(days)} days")


if __name__ == "__main__":
    main()
