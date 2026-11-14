# MARMCast Race Ladder: free setup guide

Everything here runs on free tiers:

| Part | Service | Cost |
|---|---|---|
| Website | GitHub Pages | Free |
| Database, admin logins, public submissions | Supabase (Free plan) | Free |
| Keeping the database awake | GitHub Actions (scheduled job) | Free |

About 30–45 minutes the first time. You can do it all from a laptop browser; no coding tools needed.

---

## 1. Create the database (Supabase)

1. Sign up at **supabase.com** (GitHub login is easiest) and click **New project**. Pick a region near the UK (e.g. London or Ireland) and set a database password (store it somewhere safe).
2. When it's ready, open **SQL Editor → New query**, paste the whole of `supabase/schema.sql`, and click **Run**. You should see "Success".
3. Turn on accountless public submissions: **Authentication → Sign In / Providers → Allow anonymous sign-ins → On**, then Save.
4. Get your two values from **Project Settings → API Keys** (or the **Connect** button):
   - **Project URL**, like `https://abcdefgh.supabase.co`
   - **Publishable key** (older projects call it the `anon` `public` key)

   Both are safe to put in a public website; the database rules in `schema.sql` protect the data.
   **Never** use the `secret` / `service_role` key in the website.

## 2. Make yourself an admin

1. **Authentication → Users → Add user → Create new user.** Enter your email and a password, and tick **Auto Confirm User**. (No email is sent, so Supabase's free email limit doesn't matter.)
2. Copy the new user's **UID**.
3. In **SQL Editor**, run (with your UID):
   ```sql
   insert into public.admins (user_id) values ('PASTE-UID-HERE');
   ```
Repeat for each trusted admin. To remove one: `delete from public.admins where user_id = '...';`

## 3. Put the website online (GitHub Pages)

1. Create a free GitHub account, then a free organisation (e.g. `marmcast`), and in it a **Public** repository named `marmcast.github.io` (tick **Add a README file**).
2. **Add file → Upload files**: upload `index.html` and `marmcast.jpg`. Commit.
3. **Add file → Create new file**, name it `config.js`, and paste in (with your own values from Supabase):
   ```js
   window.MARM_CONFIG = {
     url: "https://yourproject.supabase.co",
     key: "sb_publishable_..."
   };
   ```
   Commit. (`config.example.js` in this folder is the same template.) Never put the secret key here.
4. **Add file → Create new file**, name it `.github/workflows/keepalive.yml`, paste in that file's contents, commit.
5. **Settings → Pages → Deploy from a branch → `main` / root → Save.** After a minute the site is live at `https://marmcast.github.io`.
6. Open the site, click **Admin sign in** at the bottom, and add your first races in **Manage races**.

## Updating the site later

Only `index.html` changes in normal updates. Your settings stay safe in `config.js`.
1. In the repository, **Add file → Upload files**, drag in the new `index.html` (it replaces the old one), **Commit changes**.
2. Wait a minute or two, then refresh the site (Ctrl+Shift+R / Cmd+Shift+R if it still looks old).
3. If an update also includes a new `supabase/schema.sql`, run it again in Supabase's SQL Editor (safe to re-run; it keeps your data).

## 4. Keep the database awake

Free Supabase projects **pause after 7 days with no activity** (the data is kept, but the site stops working until you restore it in the dashboard). The included GitHub job pings the database every 3 days to prevent this.

1. In your GitHub repo: **Settings → Secrets and variables → Actions → New repository secret**. Add:
   - `SUPABASE_URL`: your Project URL
   - `SUPABASE_KEY`: your Publishable key
2. **Actions** tab → enable workflows if asked → **Keep Supabase awake → Run workflow** to test it. A green tick means it worked.

Two things to know:
- GitHub turns off scheduled jobs in a repo with **no commits for 60 days**. It emails you first, and re-enabling is one click (or just commit any small change every couple of months).
- If you ever see the site fail to load, log in to Supabase and click **Restore project**.

## Staying on top of new entries

**On the site:** when you sign in as admin, a box at the top shows what's happened since your last visit (scores waiting, race suggestions, scores published), with links straight to them. New items get a green **New** badge. **Manage results** lists everything newest first and can be filtered to *Since my last visit*, the last 7 or 30 days, or all time. "Last visit" is remembered per device and browser.

**Email alerts (each admin chooses their own):** three emails, all sent privately from your Gmail:
- **Daily review alert:** every morning (07:07 UTC), only on days when scores or race suggestions are waiting. Lists what's waiting.
- **Weekly summary:** Fridays around noon (11:47 UTC): everything waiting, everything published that week with all the notes, new races and race suggestions.
- **Bug reports & suggestions:** checked every hour; sends only when a visitor has used **Report a bug / suggest a feature**. Each report is emailed once. Off until each admin switches it on.

Each admin signs in and taps **My notifications** (bottom of the page, or "Change" in the summary box) to set their email address and switch each one on or off. Until any admin has saved their choices, all three emails go to `SUMMARY_TO` or, if that isn't set, `GMAIL_ADDRESS`.

Files: `.github/workflows/daily-alert.yml`, `.github/workflows/weekly-summary.yml`, `.github/workflows/feedback-alert.yml` and `.github/scripts/weekly_digest.py` (one script does all three emails).

Set up once:
1. Upload the four files, keeping their folders (open the folder on GitHub, then **Add file → Upload files**).
2. **Gmail app password:** the sending Gmail account needs 2-Step Verification on. Go to myaccount.google.com, search **App passwords**, create one called "MARMCast" and copy the 16-letter code.
3. **Supabase secret key:** **Project Settings → API Keys → Secret keys**, copy the `sb_secret_...` key (older projects: `service_role`). It can read everything, so it only ever goes in GitHub secrets, never in `config.js`.
4. Repository secrets (**Settings → Secrets and variables → Actions**): `SUPABASE_SECRET_KEY`, `GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD` (plus `SUPABASE_URL`, already there). Optional: `SUMMARY_TO`.
5. Test from **Actions → Weekly summary email → Run workflow** and **Actions → Daily review alert → Run workflow** (the daily one only sends if something is waiting). Check spam the first time.
Logs never show scores, notes or email addresses, as logs are public on a public repository.

## Bug reports and suggestions

Every visitor sees **Report a bug / suggest a feature** at the bottom of the page. It opens a short form (bug or idea, a message, and optional name or email for a reply). Reports go to the admin-only **Feedback** tab, where you can **Mark done**, **Reopen** or **Delete** them. Reports with possible swearing or web links get a red **Check this** tag. Each visitor can have at most 5 unread reports waiting.

Set up once: run `supabase/feedback.sql` in the SQL Editor (it's also in `schema.sql`), then upload `.github/workflows/feedback-alert.yml` and the updated `weekly_digest.py`.

## How verification works

- **Admins** (people in the `admins` table) sign in and their scores go straight into the official results.
- **Public** visitors submit without an account. Behind the scenes they get an anonymous ID stored in their browser.
- The **database itself** rejects submissions that are all 1s or all 5s, scores outside 1–5, or a second score from the same person for the same race and year. These can't be bypassed by tampering with the web page.
- Public scores land as **pending**. Admins see them in the **Review queue**, with a warning when scores are 2+ points off the official average in two or more categories (Performance excluded), and approve or reject.
- The table shows **official only** by default; the toggle adds **verified public** scores.

**Known limit:** someone who clears their browser (or uses another device) gets a new anonymous ID and could submit again. Admin review is the safeguard. If abuse becomes a problem, Supabase supports adding a free CAPTCHA (Cloudflare Turnstile) or Google sign-in later.

## Adding lots of races at once

- **Starter list:** `supabase/starter_races.sql` adds 47 well-known races (major UK marathons and halves, the World Marathon Majors and other big European and world races). Open it, delete any lines you don't want, then paste it into **SQL Editor** and **Run**. Races you've already added are skipped.
- **Your own list:** open `supabase/starter_races.csv` in Excel or Google Sheets, edit or add rows (country = 2-letter code such as GB, IE, FR, US; distance = one of 5K, 10K, 10 mile, Half marathon, Marathon, Ultra, Other; terrain = Road, Trail, Mixed or Fell; organiser optional; aliases like `{"Sponsor name","Other name"}` or `{}`), save as CSV, then in Supabase go to **Table Editor → races → Insert → Import data from CSV**. Leave the other columns (id, name_key, website, created_at) for Supabase to fill in. A row that duplicates an existing race makes the import fail, so remove races you already have first.

## Keeping race names standard (worldwide)

- **Only admins create races.** The public pick from the list. If their race isn't there, they tap **Add your race**, enter the race details, and submit their score in the same step.
- The new race lands in **Manage races → Race suggestions** (with the number of scores waiting on it). The admin either:
  - **Adds it as a new race** (tidying the name first), or
  - picks **It's this existing race** if it's a duplicate, or
  - **Dismisses** it, which also deletes the scores attached to it.

  Once the race is added or linked, its scores appear in the **Review queue** for normal approval. A score can't be approved while its race is still a suggestion.
- **Naming rule:** the name the organisers use, **without the year or headline sponsor** ("London Marathon", not "TCS London Marathon 2026"). Sponsor names, translations and old names go in **Also known as**, so searches still find the race.
- **Organiser (optional):** when different companies run a race with the same name at the same place (e.g. two Silverstone 10Ks), fill in the organiser and they're kept as separate races. If one company runs the same race more than once a year, put that in the name instead ("Silverstone Winter 10K").
- **Country** is picked from a fixed list (stored as the standard 2-letter code, e.g. GB, FR, US), and **distance** from a fixed list, so they can't be spelled differently.
- **The database blocks exact duplicates:** the same name (ignoring capitals, accents, punctuation, "The" and any year) in the same country, at the same distance, with the same organiser.
- **Near-duplicates are flagged** while typing, both when an admin adds a race and when the public suggests one: "Londn Marathon", "TCS London Marathon" or a matching website domain all trigger an "Is it one of these?" warning.
- **Merge:** if a duplicate slips through, **Manage races → Merge** moves all its scores onto the correct race, keeps the old name as an "also known as", and deletes the duplicate.

## Deleting results

Admins can delete any score: from the race's page (Delete button on each score), from the **Review queue**, or from **Manage results**, which lists every published and rejected score with a filter.

## Changing things later

- **Category names / descriptions:** (Performance is described as "How well you ran on the day") edit the `CATS` list near the top of the main script in `index.html` (labels only; the database column names stay `thunderboxes`, `scenery`, `swag`, `performance`).
- **Distances:** edit `DISTANCES` in the same place.
- **Custom domain** (optional, the only part that costs money): GitHub Pages supports one under Settings → Pages.
- **Backups:** the Free plan has no automatic backups. Every so often, use **Table Editor → scores → Export to CSV** (and the same for `races`).

## Free-tier headroom

Supabase Free gives 500 MB of database, which is millions of score rows at this size, and 50,000 monthly active users. GitHub Pages is free for public repos. You shouldn't hit any limits for a community site of this kind.
