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
    busiest_day, _, busiest_count = max(days, key=lambda item: item[2])
    start = min(day for day, _, _ in days)
    levels = ["#102B37", "#087E83", "#08B9B1", "#35F0D0", "#A4FFE9"]
    max_count = max((count for _, _, count in days), default=1)
    bars: list[str] = []

    for day, level, count in days:
        offset = (day - start).days
        week, weekday = divmod(offset, 7)
        x = 285 + week * 15 + weekday * 10
        y = 340 + week * 3 - weekday * 7
        a = (x, y)
        b = (x + 15, y + 7)
        c = (x + 25, y)
        d = (x + 10, y - 7)
        tint = levels[min(max(level, 0), 4)]
        if count == 0:
            bars.append(polygon([a, b, c, d], "#0B202B", "#19414B", .72))
            continue
        height = min(70.0, 8.0 + 15.0 * (count / max_count) ** 0.55)
        at, bt, ct, dt = ((px, py - height) for px, py in (a, b, c, d))
        glow = f'<ellipse cx="{x + 12}" cy="{y - height / 2:.1f}" rx="11" ry="{height / 1.5:.1f}" fill="{tint}" opacity=".13" filter="url(#glow)"/>'
        bars.append(glow)
        bars.append(polygon([a, b, bt, at], "#075862", tint, .9))
        bars.append(polygon([b, c, ct, bt], "#06404B", tint, .95))
        bars.append(polygon([at, bt, ct, dt], tint, "#A8FFF0", .98))
        if count >= max(8, max_count * .55):
            bars.append(f'<circle cx="{x + 12}" cy="{y - height + 1:.1f}" r="1.6" fill="#D7FFF7" opacity=".9"/>')

    updated = datetime.now(timezone.utc).strftime("%d %b %Y · %H:%M UTC")
    best = busiest_day.strftime("%d %b")
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="590" viewBox="0 0 1200 590" role="img" aria-labelledby="title desc">
<title id="title">Live GitHub Contribution City for {USERNAME}</title>
<desc id="desc">An isometric neon city generated from {total:,} public GitHub contributions across {active} active days during the last year. Refreshed {updated}.</desc>
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1200" y2="590" gradientUnits="userSpaceOnUse"><stop stop-color="#06101A"/><stop offset=".58" stop-color="#0A1D29"/><stop offset="1" stop-color="#10241F"/></linearGradient>
  <linearGradient id="beam" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#4DE7F2"/><stop offset="1" stop-color="#70F0B0"/></linearGradient>
  <radialGradient id="aura"><stop stop-color="#12D5C8" stop-opacity=".24"/><stop offset="1" stop-color="#12D5C8" stop-opacity="0"/></radialGradient>
  <filter id="glow" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="5"/></filter>
  <pattern id="stars" width="137" height="97" patternUnits="userSpaceOnUse"><circle cx="13" cy="21" r="1" fill="#8FFFE6" opacity=".35"/><circle cx="91" cy="61" r=".8" fill="#63EAF2" opacity=".42"/><circle cx="57" cy="84" r=".7" fill="#B1FFD9" opacity=".28"/></pattern>
</defs>
<rect width="1200" height="590" rx="26" fill="url(#bg)"/>
<rect width="1200" height="590" rx="26" fill="url(#stars)"/>
<circle cx="840" cy="335" r="360" fill="url(#aura)"/>
<text x="58" y="68" fill="#70F0B0" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="13" letter-spacing="3.4">CONTRIBUTION CITY · LIVE DATA</text>
<text x="58" y="124" fill="#F2FBFF" font-family="Inter, ui-sans-serif, system-ui, sans-serif" font-size="37" font-weight="720">The year, built in neon.</text>
<g font-family="Inter, ui-sans-serif, system-ui, sans-serif">
 <text x="60" y="190" fill="#72A0AE" font-size="11" letter-spacing="1.8">CONTRIBUTIONS</text>
 <text x="58" y="238" fill="#D9FFF5" font-size="39" font-weight="700">{total:,}</text>
 <text x="60" y="272" fill="#72A0AE" font-size="11" letter-spacing="1.8">ACTIVE DAYS</text>
 <text x="58" y="306" fill="#F2FBFF" font-size="23" font-weight="650">{active}</text>
 <text x="60" y="349" fill="#72A0AE" font-size="11" letter-spacing="1.8">BUSIEST DAY</text>
 <text x="58" y="380" fill="#F2FBFF" font-size="19" font-weight="650">{best} · {busiest_count}</text>
</g>
<path d="M58 412h162" stroke="url(#beam)" stroke-width="2" stroke-linecap="round"/>
<text x="58" y="445" fill="#83A8B1" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="10" letter-spacing="1.3">HEIGHT = DAILY CONTRIBUTIONS</text>
<text x="58" y="466" fill="#63838D" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="10">Each tile maps to one day</text>
<g>{''.join(bars)}</g>
<path d="M276 502 1036 502" stroke="#62DCE2" stroke-opacity=".18"/>
<text x="58" y="552" fill="#6C8992" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="10" letter-spacing="1.2">SOURCE: PUBLIC GITHUB CONTRIBUTION CALENDAR · UPDATED {html.escape(updated)}</text>
</svg>
'''


def main() -> None:
    days = fetch_days()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render(days), encoding="utf-8")
    print(f"Wrote {OUTPUT}: {sum(x[2] for x in days):,} contributions / {len(days)} days")


if __name__ == "__main__":
    main()
