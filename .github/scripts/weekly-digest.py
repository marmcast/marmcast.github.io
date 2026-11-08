"""MARMCast Race Ladder: weekly summary email.

Run by .github/workflows/weekly-summary.yml every Friday. It reads the last 7 days of
activity from Supabase and emails a readable summary to you through Gmail.

Secrets it needs (GitHub > Settings > Secrets and variables > Actions):
  SUPABASE_URL          your project URL
  SUPABASE_SECRET_KEY   Supabase "secret" key (sb_secret_...). Only ever stored here, never on the website.
  GMAIL_ADDRESS         the Gmail address that sends (and receives) the summary
  GMAIL_APP_PASSWORD    a Gmail app password (not your normal password)
Optional:
  SUMMARY_TO            send to a different address (comma-separate several)
Nothing from the database is printed to the log (the log is public on a public repository).
"""
import os, sys, json, ssl, smtplib, urllib.request, urllib.parse, html
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage

CATS = [("thunderboxes", "Thunderboxes"), ("scenery", "Scenery"), ("swag", "Swag Bag"), ("performance", "Performance")]
DAYS = 7

def fetch(path, params):
    url = os.environ["SUPABASE_URL"].rstrip("/").removesuffix("/rest/v1") + "/rest/v1/" + path + "?" + urllib.parse.urlencode(params, safe="(),.*:")
    req = urllib.request.Request(url, headers={"apikey": os.environ["SUPABASE_SECRET_KEY"], "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"Supabase refused the request for {path}: HTTP {e.code}. Check SUPABASE_URL and SUPABASE_SECRET_KEY.")

def esc(x): return html.escape(str(x if x is not None else ""))

def race_label(r):
    if not r: return "Unknown race"
    bits = [r.get("distance"), r.get("city"), r.get("country")]
    s = f'{esc(r.get("name"))} <span style="color:#666">({", ".join(esc(b) for b in bits if b)}'
    if r.get("organiser"): s += f' · {esc(r["organiser"])}'
    return s + ")</span>"

def when(ts):
    try: return datetime.fromisoformat(ts.replace("Z", "+00:00")).strftime("%a %d %b")
    except Exception: return ""

def score_card(o):
    race = o.get("races") or o.get("race_requests")
    total = sum(o.get(k) or 0 for k, _ in CATS)
    who = o.get("display_name") or ("Admin" if o.get("source") == "admin" else "Runner")
    kind = "Official" if o.get("source") == "admin" else ("Public (entered by admin)" if o.get("on_behalf") else "Public")
    newrace = ' <span style="background:#fef3c7;color:#92400e;border-radius:10px;padding:1px 7px;font-size:12px">new race</span>' if not o.get("races") and o.get("race_requests") else ""
    rows = "".join(
        f'<tr><td style="padding:3px 10px 3px 0;color:#444">{label}</td><td style="padding:3px 10px 3px 0;font-weight:bold">{esc(o.get(k))}</td>'
        f'<td style="padding:3px 0;color:#555;font-style:italic">{esc(o.get(k + "_note") or "")}</td></tr>'
        for k, label in CATS)
    return f'''<div style="border:1px solid #ddd;border-left:4px solid #5ddb56;border-radius:8px;padding:10px 12px;margin:10px 0">
  <div style="font-weight:bold">{race_label(race)}{newrace}</div>
  <div style="color:#555;font-size:13px;margin:2px 0 6px">{esc(o.get("year"))} · {esc(who)} · {kind} · added {when(o.get("created_at"))} · <b>overall {total}/20</b></div>
  <table style="border-collapse:collapse;font-size:14px">{rows}</table></div>'''

def section(title, items, empty):
    body = "".join(items) if items else f'<p style="color:#777">{empty}</p>'
    return f'<h2 style="font-size:17px;margin:22px 0 4px;border-bottom:2px solid #5ddb56;padding-bottom:4px">{title} ({len(items)})</h2>{body}'

def build(scores, races, requests, site, since):
    pending = [o for o in scores if o["status"] == "pending"]
    published = [o for o in scores if o["status"] == "approved"]
    rejected = [o for o in scores if o["status"] == "rejected"]
    race_items = [f'<li>{race_label(r)} · added {when(r.get("created_at"))}</li>' for r in races]
    req_items = [f'<li>{race_label(q)} · suggested {when(q.get("created_at"))}</li>' for q in requests]
    parts = [
        f'<div style="font-family:Arial,Helvetica,sans-serif;max-width:640px;margin:auto;color:#111">',
        f'<div style="background:#000;color:#fff;padding:14px 16px;border-radius:10px"><div style="font-size:20px;font-weight:900">MARMCAST <span style="color:#5ddb56">RACE LADDER</span></div>'
        f'<div style="color:#ccc;font-size:13px">Weekly summary: {since:%a %d %b} to {datetime.now(timezone.utc):%a %d %b %Y}</div></div>',
        f'<p style="font-size:15px">This week: <b>{len(pending)}</b> waiting for review · <b>{len(published)}</b> published · '
        f'<b>{len(races)}</b> new race(s) · <b>{len(requests)}</b> race suggestion(s) waiting.</p>',
        section("Waiting for review", [score_card(o) for o in pending], "Nothing waiting."),
        section("Published this week", [score_card(o) for o in published], "Nothing published this week."),
    ]
    if rejected: parts.append(section("Rejected this week", [score_card(o) for o in rejected], ""))
    parts.append(f'<h2 style="font-size:17px;margin:22px 0 4px;border-bottom:2px solid #5ddb56;padding-bottom:4px">New races added ({len(races)})</h2>'
                 + (f'<ul>{"".join(race_items)}</ul>' if race_items else '<p style="color:#777">None.</p>'))
    parts.append(f'<h2 style="font-size:17px;margin:22px 0 4px;border-bottom:2px solid #5ddb56;padding-bottom:4px">Race suggestions waiting ({len(requests)})</h2>'
                 + (f'<ul>{"".join(req_items)}</ul>' if req_items else '<p style="color:#777">None.</p>'))
    parts.append(f'<p style="margin-top:24px"><a href="{esc(site)}" style="background:#5ddb56;color:#061006;padding:10px 16px;border-radius:8px;text-decoration:none;font-weight:bold">Open the Race Ladder</a></p>'
                 '<p style="color:#888;font-size:12px">Sent automatically every Friday by your GitHub repository.</p></div>')
    subject = f"MARMCast weekly: {len(pending)} to review, {len(published)} published, {len(races)} new race(s)"
    return subject, "".join(parts)

def main():
    since = datetime.now(timezone.utc) - timedelta(days=DAYS)
    iso = since.strftime("%Y-%m-%dT%H:%M:%SZ")
    sel = "*,races(name,city,country,distance,organiser),race_requests(name,city,country,distance,organiser)"
    scores = fetch("scores", {"select": sel, "or": f'(created_at.gte."{iso}",reviewed_at.gte."{iso}")', "order": "created_at.desc"})
    races = fetch("races", {"select": "name,city,country,distance,organiser,created_at", "created_at": f"gte.{iso}", "order": "created_at.desc"})
    requests = fetch("race_requests", {"select": "name,city,country,distance,organiser,created_at", "order": "created_at.desc"})
    subject, body = build(scores, races, requests, os.environ.get("SITE", ""), since)

    if os.environ.get("DRY_RUN"):
        open("weekly_summary_preview.html", "w").write(body); print("Dry run: wrote weekly_summary_preview.html"); return
    sender = os.environ["GMAIL_ADDRESS"]
    to = [a.strip() for a in (os.environ.get("SUMMARY_TO") or sender).split(",") if a.strip()]
    msg = EmailMessage(); msg["Subject"] = subject; msg["From"] = f"MARMCast Race Ladder <{sender}>"; msg["To"] = ", ".join(to)
    msg.set_content("Your weekly MARMCast Race Ladder summary. Open this email in an app that shows HTML.")
    msg.add_alternative(body, subtype="html")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ssl.create_default_context()) as s:
        s.login(sender, os.environ["GMAIL_APP_PASSWORD"].replace(" ", ""))
        s.send_message(msg)
    print(f"Weekly summary sent to {len(to)} address(es).")

if __name__ == "__main__":
    main()
