"""MARMCast Race Ladder: admin emails (weekly summary and daily review alert).

  python3 weekly_digest.py           -> weekly summary   (weekly-summary.yml, Fridays)
  python3 weekly_digest.py daily     -> daily review alert (daily-alert.yml, every morning; only sends if something is waiting)

Each admin chooses which emails they get on the site (footer > My notifications).
If no admin has saved their choices yet, both emails go to SUMMARY_TO, or else GMAIL_ADDRESS.

Secrets (GitHub > Settings > Secrets and variables > Actions):
  SUPABASE_URL, SUPABASE_SECRET_KEY (sb_secret_...), GMAIL_ADDRESS, GMAIL_APP_PASSWORD; optional SUMMARY_TO.
Nothing from the database (and no email address) is printed to the log, which is public on a public repository.
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
        try: why = json.loads(e.read()).get("message", "")   # Supabase's own error text (never contains data)
        except Exception: why = ""
        sys.exit(f"Supabase refused the request for {path}: HTTP {e.code}. {why}\n"
                 "401 = wrong key (use the sb_secret_ key). 403 'permission denied' = run the service_role grant lines from schema.sql.")

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

def recipients(kind):
    """Admins who switched this email on. Falls back to SUMMARY_TO / GMAIL_ADDRESS if nobody has saved choices yet."""
    admins = {a["user_id"] for a in fetch("admins", {"select": "user_id"})}
    prefs = [p for p in fetch("admin_prefs", {"select": "user_id,email,daily,weekly"}) if p["user_id"] in admins]
    if prefs:
        return sorted({p["email"] for p in prefs if p.get(kind)})
    fallback = os.environ.get("SUMMARY_TO") or os.environ.get("GMAIL_ADDRESS") or ""
    return [a.strip() for a in fallback.split(",") if a.strip()]

def build_daily(pending, requests, site):
    def line(o):
        race = o.get("races") or o.get("race_requests")
        total = sum(o.get(k) or 0 for k, _ in CATS)
        new = ' <span style="background:#fef3c7;color:#92400e;border-radius:10px;padding:1px 7px;font-size:12px">new race</span>' if not o.get("races") else ""
        who = esc(o.get("display_name") or "Runner")
        return f'<li style="margin:6px 0">{race_label(race)}{new}<br><span style="color:#555;font-size:13px">{esc(o.get("year"))} · {who} · overall {total}/20 · sent {when(o.get("created_at"))}</span></li>'
    parts = [
        '<div style="font-family:Arial,Helvetica,sans-serif;max-width:640px;margin:auto;color:#111">',
        '<div style="background:#000;color:#fff;padding:14px 16px;border-radius:10px"><div style="font-size:20px;font-weight:900">MARMCAST <span style="color:#5ddb56">RACE LADDER</span></div>'
        '<div style="color:#ccc;font-size:13px">Daily review alert</div></div>',
        f'<p style="font-size:15px">Waiting for an admin: <b>{len(pending)}</b> score(s) to review and <b>{len(requests)}</b> race suggestion(s).</p>']
    if pending: parts.append('<h2 style="font-size:17px;border-bottom:2px solid #5ddb56;padding-bottom:4px">Scores to review</h2><ul style="padding-left:18px">' + "".join(line(o) for o in pending) + '</ul>')
    if requests: parts.append('<h2 style="font-size:17px;border-bottom:2px solid #5ddb56;padding-bottom:4px">Race suggestions</h2><ul style="padding-left:18px">' + "".join(f'<li>{race_label(q)} · suggested {when(q.get("created_at"))}</li>' for q in requests) + '</ul>')
    parts.append(f'<p style="margin-top:20px"><a href="{esc(site)}" style="background:#5ddb56;color:#061006;padding:10px 16px;border-radius:8px;text-decoration:none;font-weight:bold">Review them now</a></p>'
                 '<p style="color:#888;font-size:12px">You get this because the daily alert is switched on in My notifications on the site.</p></div>')
    return f"MARMCast: {len(pending)} score(s) to review, {len(requests)} race suggestion(s)", "".join(parts)

def send(to, subject, body):
    sender = os.environ["GMAIL_ADDRESS"]
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ssl.create_default_context()) as s:
        s.login(sender, os.environ["GMAIL_APP_PASSWORD"].replace(" ", ""))
        for addr in to:   # one email each, so admins don't see each other's addresses
            msg = EmailMessage(); msg["Subject"] = subject; msg["From"] = f"MARMCast Race Ladder <{sender}>"; msg["To"] = addr
            msg.set_content("MARMCast Race Ladder update. Open this email in an app that shows HTML.")
            msg.add_alternative(body, subtype="html")
            s.send_message(msg)

def main():
    mode = (sys.argv[1] if len(sys.argv) > 1 else "weekly").lower()
    kind = "daily" if mode == "daily" else "weekly"
    need = ("SUPABASE_URL", "SUPABASE_SECRET_KEY") + (() if os.environ.get("DRY_RUN") else ("GMAIL_ADDRESS", "GMAIL_APP_PASSWORD"))
    missing = [k for k in need if not os.environ.get(k)]
    if missing:
        sys.exit("Missing GitHub secret(s): " + ", ".join(missing) + ". Add them under Settings > Secrets and variables > Actions.")
    site = os.environ.get("SITE", "")
    sel = "*,races(name,city,country,distance,organiser),race_requests(name,city,country,distance,organiser)"

    if kind == "daily":
        pending = fetch("scores", {"select": sel, "status": "eq.pending", "order": "created_at.asc"})
        requests = fetch("race_requests", {"select": "name,city,country,distance,organiser,created_at", "order": "created_at.asc"})
        if not pending and not requests:
            print("Nothing waiting for review today, so no email."); return
        subject, body = build_daily(pending, requests, site)
    else:
        since = datetime.now(timezone.utc) - timedelta(days=DAYS)
        iso = since.strftime("%Y-%m-%dT%H:%M:%SZ")
        scores = fetch("scores", {"select": sel, "or": f'(created_at.gte."{iso}",reviewed_at.gte."{iso}")', "order": "created_at.desc"})
        races = fetch("races", {"select": "name,city,country,distance,organiser,created_at", "created_at": f"gte.{iso}", "order": "created_at.desc"})
        requests = fetch("race_requests", {"select": "name,city,country,distance,organiser,created_at", "order": "created_at.desc"})
        subject, body = build(scores, races, requests, site, since)

    to = recipients(kind)
    if os.environ.get("DRY_RUN"):
        open(f"{kind}_preview.html", "w").write(body); print(f"Dry run: wrote {kind}_preview.html for {len(to)} recipient(s)"); return
    if not to:
        print(f"No admin has the {kind} email switched on, so nothing was sent."); return
    send(to, subject, body)
    print(f"{kind.capitalize()} email sent to {len(to)} admin(s).")

if __name__ == "__main__":
    main()
