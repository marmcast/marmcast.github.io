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

1. Open `index.html` in a text editor and fill in the two lines near the top:
   ```js
   const SUPABASE_URL = "https://abcdefgh.supabase.co";
   const SUPABASE_KEY = "sb_publishable_...";
   ```
2. Create a free account at **github.com**, then **New repository** (e.g. `race-ladder`), set it to **Public**.
3. **Add file → Upload files**: upload `index.html` and `marmcast.jpg` (the logo), plus the `.github` folder (it holds the keep-awake job). Commit.
   *Tip: if the browser won't upload the hidden `.github` folder, use **Add file → Create new file**, type the name `.github/workflows/keepalive.yml`, and paste in that file's contents.*
4. **Settings → Pages → Source: Deploy from a branch → `main` / root → Save.** After a minute your site is live at `https://YOUR-USERNAME.github.io/race-ladder/`.
5. Open the site, click **Admin sign in** at the bottom, sign in, and add your first races in the **Manage races** tab.

## 4. Keep the database awake

Free Supabase projects **pause after 7 days with no activity** (the data is kept, but the site stops working until you restore it in the dashboard). The included GitHub job pings the database every 3 days to prevent this.

1. In your GitHub repo: **Settings → Secrets and variables → Actions → New repository secret**. Add:
   - `SUPABASE_URL`: your Project URL
   - `SUPABASE_KEY`: your Publishable key
2. **Actions** tab → enable workflows if asked → **Keep Supabase awake → Run workflow** to test it. A green tick means it worked.

Two things to know:
- GitHub turns off scheduled jobs in a repo with **no commits for 60 days**. It emails you first, and re-enabling is one click (or just commit any small change every couple of months).
- If you ever see the site fail to load, log in to Supabase and click **Restore project**.

## How verification works

- **Admins** (people in the `admins` table) sign in and their scores go straight into the official results.
- **Public** visitors submit without an account. Behind the scenes they get an anonymous ID stored in their browser.
- The **database itself** rejects submissions that are all 1s or all 5s, scores outside 1–5, or a second score from the same person for the same race and year. These can't be bypassed by tampering with the web page.
- Public scores land as **pending**. Admins see them in the **Review queue**, with a warning when scores are 2+ points off the official average in two or more categories (Performance excluded), and approve or reject.
- The table shows **official only** by default; the toggle adds **verified public** scores.

**Known limit:** someone who clears their browser (or uses another device) gets a new anonymous ID and could submit again. Admin review is the safeguard. If abuse becomes a problem, Supabase supports adding a free CAPTCHA (Cloudflare Turnstile) or Google sign-in later.

## Keeping race names standard (worldwide)

- **Only admins create races.** The public pick from the list. If their race isn't there, they tap **Add your race**, enter the race details, and submit their score in the same step.
- The new race lands in **Manage races → Race suggestions** (with the number of scores waiting on it). The admin either:
  - **Adds it as a new race** (tidying the name first), or
  - picks **It's this existing race** if it's a duplicate, or
  - **Dismisses** it, which also deletes the scores attached to it.

  Once the race is added or linked, its scores appear in the **Review queue** for normal approval. A score can't be approved while its race is still a suggestion.
- **Naming rule:** the name the organisers use, **without the year or headline sponsor** ("London Marathon", not "TCS London Marathon 2026"). Sponsor names, translations and old names go in **Also known as**, so searches still find the race.
- **Country** is picked from a fixed list (stored as the standard 2-letter code, e.g. GB, FR, US), and **distance** from a fixed list, so they can't be spelled differently.
- **The database blocks exact duplicates:** the same name (ignoring capitals, accents, punctuation, "The" and any year) in the same country at the same distance.
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
