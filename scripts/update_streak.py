"""Generate assets/streak.svg from the GitHub GraphQL API (stdlib only)."""
import datetime as dt
import json
import os
import urllib.request

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""


def fetch(login, token):
    body = json.dumps({"query": QUERY, "variables": {"login": login}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "streak-card",
        },
    )
    with urllib.request.urlopen(req) as resp:
        data = json.load(resp)
    cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    days = [d for w in cal["weeks"] for d in w["contributionDays"]]
    return cal["totalContributions"], days


def short(date_str):
    d = dt.date.fromisoformat(date_str)
    return f"{d.strftime('%b')} {d.day}"


def streaks(days, today=None):
    today = today or dt.date.today()
    days = sorted(
        (d for d in days if d["date"] <= today.isoformat()), key=lambda d: d["date"]
    )
    longest = (0, None, None)
    run, start = 0, None
    for d in days:
        if d["contributionCount"] > 0:
            if run == 0:
                start = d["date"]
            run += 1
            if run > longest[0]:
                longest = (run, start, d["date"])
        else:
            run = 0

    i = len(days) - 1
    if i >= 0 and days[i]["contributionCount"] == 0:
        i -= 1  # today may not have a contribution yet
    cur, cstart, cend = 0, None, None
    while i >= 0 and days[i]["contributionCount"] > 0:
        cur += 1
        cstart = days[i]["date"]
        if cend is None:
            cend = days[i]["date"]
        i -= 1
    return (cur, cstart, cend), longest


def rng(start, end):
    return f"{short(start)} - {short(end)}" if start and end else "-"


def render(total, current, longest, first_day, updated):
    cur, cs, ce = current
    lon, ls, le = longest
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="495" height="195" viewBox="0 0 495 195" role="img" aria-label="GitHub streak stats">
  <style>
    text {{ font-family: 'Segoe UI', Ubuntu, Helvetica, Arial, sans-serif; text-anchor: middle; }}
    .big {{ font-size: 28px; font-weight: 700; }}
    .lbl {{ font-size: 14px; }}
    .sub {{ font-size: 12px; fill: #2dba9a; }}
    .blue {{ fill: #70a5fd; }}
    .purple {{ fill: #bf91f3; }}
    .ring {{ animation: pop 0.8s ease-out both; transform-origin: 247.5px 70px; }}
    @keyframes pop {{ from {{ opacity: 0; transform: scale(0.85); }} to {{ opacity: 1; transform: scale(1); }} }}
  </style>
  <rect width="495" height="195" rx="10" fill="#0d1117"/>
  <line x1="165" y1="30" x2="165" y2="165" stroke="#30363d"/>
  <line x1="330" y1="30" x2="330" y2="165" stroke="#30363d"/>

  <text class="big blue" x="82" y="82">{total}</text>
  <text class="lbl blue" x="82" y="108">Total Contributions</text>
  <text class="sub" x="82" y="132">{short(first_day)} - Present</text>

  <g class="ring">
    <circle cx="247.5" cy="70" r="40" fill="none" stroke="#70a5fd" stroke-width="5"/>
    <text class="big purple" x="247.5" y="80">{cur}</text>
  </g>
  <text class="lbl purple" x="247.5" y="136" font-weight="700">Current Streak</text>
  <text class="sub" x="247.5" y="158">{rng(cs, ce)}</text>

  <text class="big blue" x="412" y="82">{lon}</text>
  <text class="lbl blue" x="412" y="108">Longest Streak</text>
  <text class="sub" x="412" y="132">{rng(ls, le)}</text>
  <text class="sub" x="247.5" y="185" opacity="0.5" font-size="10">updated {updated}</text>
</svg>
"""


def main():
    login = os.environ.get("GH_USER") or os.environ["GITHUB_REPOSITORY_OWNER"]
    token = os.environ["GH_TOKEN"]
    total, days = fetch(login, token)
    current, longest = streaks(days)
    first_day = min(d["date"] for d in days)
    updated = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    os.makedirs("assets", exist_ok=True)
    with open("assets/streak.svg", "w", encoding="utf-8") as f:
        f.write(render(total, current, longest, first_day, updated))
    print(f"total={total} current={current[0]} longest={longest[0]}")


if __name__ == "__main__":
    main()
