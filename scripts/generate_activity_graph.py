#!/usr/bin/env python3
"""Generate a self-hosted GitHub contribution activity graph (last 31 days)."""
import json
import math
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import Request, urlopen

USERNAME = os.environ.get("PROFILE_USER", "vikassharma270907-alt")
TOKEN = os.environ["GITHUB_TOKEN"]
QUERY = """query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}"""

request = Request(
    "https://api.github.com/graphql",
    data=json.dumps({"query": QUERY, "variables": {"login": USERNAME}}).encode("utf-8"),
    headers={
        "Authorization": "Bearer " + TOKEN,
        "Content-Type": "application/json",
        "Accept": "application/vnd.github+json",
        "User-Agent": "github-profile-activity-svg",
    },
    method="POST",
)
with urlopen(request, timeout=35) as response:
    payload = json.load(response)

if payload.get("errors"):
    raise RuntimeError("GitHub GraphQL returned errors: " + str(payload["errors"]))
user = (payload.get("data") or {}).get("user")
if not user:
    raise RuntimeError("GitHub GraphQL did not return a user; refusing to publish fake data")

weeks = user["contributionsCollection"]["contributionCalendar"]["weeks"]
counts = {
    day["date"]: day["contributionCount"]
    for week in weeks
    for day in week["contributionDays"]
}
today = datetime.now(timezone.utc).date()
dates = [today - timedelta(days=30 - i) for i in range(31)]
values = [counts.get(day.isoformat(), 0) for day in dates]
total = sum(values)
active = sum(value > 0 for value in values)
highest = max(values)
ceiling = max(4, math.ceil(highest / 4) * 4)

W, H = 960, 360
left, right, top, bottom = 62, 32, 105, 295
plot_width, plot_height = W - left - right, bottom - top

def x_at(index):
    return left + plot_width * index / 30

def y_at(value):
    return bottom - plot_height * value / ceiling

def f(number):
    return f"{number:.1f}"

coordinates = [(x_at(i), y_at(value)) for i, value in enumerate(values)]
polyline = " ".join(f"{f(x)},{f(y)}" for x, y in coordinates)
area_path = (
    f"M {f(left)} {f(bottom)} "
    + " ".join(f"L {f(x)} {f(y)}" for x, y in coordinates)
    + f" L {f(x_at(30))} {f(bottom)} Z"
)
parts = [
    '<svg xmlns="http://www.w3.org/2000/svg" width="960" height="360" '
    'viewBox="0 0 960 360" role="img" aria-label="GitHub contribution activity graph">',
    '<title>GitHub Contribution Activity</title>',
    f'<desc>{total} public contributions across the past 31 days, '
    f'{active} active days, for {USERNAME}.</desc>',
    '<defs><linearGradient id="purple-fill" x1="0" y1="0" x2="0" y2="1">'
    '<stop offset="0%" stop-color="#7C3AED" stop-opacity=".42"/>'
    '<stop offset="100%" stop-color="#7C3AED" stop-opacity=".025"/>'
    '</linearGradient></defs>',
    '<rect width="960" height="360" rx="18" fill="#0D1117" stroke="#30363D"/>',
    '<text x="32" y="42" font-family="system-ui,Segoe UI,sans-serif" '
    'font-weight="700" font-size="22" fill="#E6EDF3">Contribution Activity</text>',
    f'<text x="32" y="68" font-family="system-ui,Segoe UI,sans-serif" '
    f'font-size="13" fill="#A78BFA">Last 31 days  ·  {total} contributions  ·  {active} active days</text>',
]
for n in range(5):
    value = ceiling * n / 4
    y = y_at(value)
    parts.append(
        f'<line x1="{left}" y1="{f(y)}" x2="{W - right}" y2="{f(y)}" '
        'stroke="#30363D" stroke-width="1" stroke-dasharray="4 5"/>'
    )
    parts.append(
        f'<text x="{left - 11}" y="{f(y + 4)}" text-anchor="end" '
        'font-size="12" font-family="system-ui,Segoe UI,sans-serif" '
        f'fill="#8B949E">{round(value)}</text>'
    )
for index in (0, 7, 14, 21, 30):
    parts.append(
        f'<text x="{f(x_at(index))}" y="{bottom + 30}" '
        f'text-anchor="middle" font-size="12" '
        'font-family="system-ui,Segoe UI,sans-serif" fill="#8B949E">'
        f'{dates[index].strftime("%d %b")}</text>'
    )
parts.extend([
    f'<path d="{area_path}" fill="url(#purple-fill)"/>',
    f'<polyline points="{polyline}" fill="none" stroke="#A78BFA" '
    'stroke-width="3" stroke-linejoin="round" stroke-linecap="round"/>',
])
for i, (x, y) in enumerate(coordinates):
    if values[i]:
        parts.append(
            f'<circle cx="{f(x)}" cy="{f(y)}" r="3.2" '
            'fill="#E9D5FF" stroke="#7C3AED" stroke-width="1.2"/>'
        )
parts.extend([
    '<text x="928" y="344" text-anchor="end" font-size="10" '
    'font-family="system-ui,Segoe UI,sans-serif" fill="#8B949E">'
    'Powered by GitHub GraphQL · Updated automatically</text>',
    '</svg>',
])
dest = Path("dist/activity-graph.svg")
dest.parent.mkdir(parents=True, exist_ok=True)
dest.write_text("\n".join(parts) + "\n", encoding="utf-8")
print(f"Generated {dest}: {total} contributions, {active} active days")
