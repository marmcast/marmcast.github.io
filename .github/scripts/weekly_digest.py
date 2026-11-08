Claude
The email reads well. Let me check the database queries against a real PostgREST server, the same engine Supabase uses for this, since I can’t reach your live project from here.

There are now three ways to keep track of new entries, all free.

1. On the site, when you sign in

Summary box: a box at the top says what’s happened since your last visit: how many scores are waiting (and how many are new), race suggestions, and scores published. Each line has a link straight to the right tab.
New badges: new items get a green New badge in the review queue, race suggestions and results.
Recent approvals: in Manage results, newest first, you can filter to Since my last visit, the last 7 or 30 days, or all time. Each entry shows when it was published, whether you or another admin approved it, its total, and each category score.
“Last visit” is remembered separately on each device and browser.

2. Daily alert: every morning a GitHub job checks for anything waiting. If something is, it opens a short issue on your repository, e.g. “MARMCast: 2 scores to review, 1 race suggestion”, and GitHub emails it to you. Quiet days send nothing. Because issues are public, it only ever contains counts.

3. Weekly summary email: every Monday morning you get a private email from your own Gmail. It covers everything waiting for review and everything published that week, with each runner’s scores and notes, plus new races and race suggestions. weekly-summary-preview.png shows what it looks like with sample data.

I tested the summary box and results filter in a browser. I also tested the weekly email’s database queries and the daily count against a local copy of the database and PostgREST, the engine Supabase uses to serve data, and the public still can’t see unreviewed scores. Neither job prints any scores or notes in its logs, which are public on a public repository.

To set it up, using the new marmcast-race-ladder.zip:

In Supabase, run the new supabase/schema.sql. It adds the counts function and keeps your data.
On GitHub, upload the new index.html.
Add the three new files, keeping their folders: .github/workflows/daily-alert.yml, .github/workflows/weekly-summary.yml and .github/scripts/weekly_digest.py.
For the daily alert, click Watch → All Activity on your repository.
For the weekly email, add three secrets: your Supabase secret key, your Gmail address, and a Gmail app password. That needs 2-Step Verification on your Google account. The README has each step.
The secret key can read everything in the database, so it only ever goes in GitHub’s secrets, never in config.js. Run each job once from the Actions tab to check it works; the first email may land in spam.

The Claude-hosted prototype doesn’t have these admin extras. They’re only on the live site.

weekly-summary-preview.png
admin-summary-preview.png
Marmcast race ladder
ZIP
Change the weekly email to Friday at about noon UTC

Shared a file, ran a command
The weekly summary now goes out on Fridays at 11:47 UTC. That’s just before noon UK time in winter, or just before 1pm in summer. It still covers the previous 7 days, so a Friday email runs from last Friday to this one.

I set it slightly before the hour on purpose. GitHub’s scheduled jobs are busiest on the hour and can run late then, so this way it should arrive close to noon.

Two files changed: .github/workflows/weekly-summary.yml has the new schedule, and .github/scripts/weekly_digest.py now says “every Friday” at the bottom of the email. They’re in marmcast-race-ladder.zip.

If you’ve already uploaded them to GitHub, replace both. If not, upload these versions when you set up the weekly email.

Marmcast race ladder
ZIP
can't see settings - notifications in github

Locating the GitHub notification settings path.
Locating the GitHub notification settings path.
That page is in your account settings, not the repository’s Settings tab, which is probably why it’s not showing up.

Quickest: go straight to https://github.com/settings/notifications

Or by menu, in a browser:

Click your profile picture in the top-right corner of any GitHub page. Not the repository’s Settings tab.
Choose Settings.
In the left sidebar, click Notifications. On a phone the sidebar may be tucked behind a menu button at the top of the page.
Once you’re there:

At the top, check Default notifications email is the address you want the alerts sent to.
Under Subscriptions → Watching, make sure Email is ticked. GitHub may call it “Notify me: on GitHub, Email”.
Under Subscriptions → Participating, @mentions and custom, ticking Email is a good idea too.
Then watch the repository:

Open github.com/marmcast/marmcast.github.io.
Click Watch near the top right, next to Fork and Star. On a phone it may show as an eye icon.
Choose All Activity.
The GitHub phone app only controls push notifications, not emails, so use a browser for this. On a phone, Chrome or Safari’s “Desktop site” option makes the full menus appear.

To test it, go to Actions → Daily review alert → Run workflow. It only sends an email if something is waiting for review, so submit a test public score first, using preview mode.

Run python3 .github/scripts/weekly_digest.py
python3: can't open file '/home/runner/work/marmcast.github.io/marmcast.github.io/.github/scripts/weekly_digest.py': [Errno 2] No such file or directory
Error: Process completed with exit code 2.

Weighing two ways to fix the script's location
GitHub ran the job but couldn’t find the script, so weekly_digest.py isn’t where the job expects it. It needs to sit in a scripts folder inside the .github folder. Usually it has ended up somewhere else, for example at the top level next to index.html or inside the workflows folder, or the name differs slightly, such as weekly_digest (1).py or .txt on the end.

Check where it is: on the repository’s Code tab, open the .github folder. You should see two folders, workflows and scripts, with weekly_digest.py inside scripts.

To put it in the right place:

Add file → Create new file.
In the name box, type exactly .github/scripts/weekly_digest.py. Each / turns into a folder as you type.
Open weekly_digest.py from the zip in Notepad or TextEdit, copy everything, and paste it into the big box.
Click Commit changes.
If a copy exists in the wrong place, open it and delete it: use the ⋯ menu → Delete file, then commit.
Then rerun Actions → Weekly summary email → Run workflow.

I’ll also make the job find the script wherever it sits in the repository, so this can’t trip it up again.

Shared 2 files, ran a command
The new weekly-summary.yml searches the whole repository for the script, including copies with a “(1)” added to the name, and the log says which file it used. If the script is missing altogether, the log now says so in plain English.

The quickest fix right now is to replace the workflow file:

On GitHub, open .github/workflows/weekly-summary.yml and click the pencil icon.
Select everything in the edit box and delete it.
Paste in the full contents of the new weekly-summary.yml, then click Commit changes.
Run it again from Actions → Weekly summary email → Run workflow.
If it still fails:

“Can’t find weekly_digest.py”: the script isn’t in the repository at all. Add it as shown in the steps above.
Anything about Supabase or Gmail: that’s the next setup step, the secrets. Tell me what the message says.
Weekly summary
YML
Marmcast race ladder
ZIP
send
Node.js 20 is deprecated. The following actions target Node.js 20 but are being forced to run on Node.js 24: actions/checkout@v4. For more information see: https://github.blog/changelog/2025-09-19-deprecation-of-node-20-on-github-actions-runners/

Checking a deprecation warning in the workflow annotation.
Checking a deprecation warning in the workflow annotation.
That’s only a warning, not an error. GitHub is phasing out an older version of the tool that downloads your repository files at the start of the job. It ran on the newer version automatically, so it doesn’t stop anything working.

Did it work? If the run has a green tick, it did, and your summary email should arrive within a minute or two. Check spam the first time. If the run has a red cross, the real error is further down: click into the run, open the Build and send the summary step, and tell me what it says.

To get rid of the warning, I’ve switched the file to the newer version of that tool:

Shared a file, ran a command
To stop the warning, there’s a one-word edit on GitHub. You don’t need the whole file again:

Open .github/workflows/weekly-summary.yml and click the pencil icon.
Find actions/checkout@v4 and change v4 to v5.
Click Commit changes.
The updated weekly-summary.yml is attached if you’d rather paste the whole thing, and it’s in the zip too. The other two jobs, keep-awake and the daily alert, don’t use that tool, so they won’t show the warning.

Weekly summary
YML
How is Claude doing this session?



Claude is AI and can make mistakes.
Weekly summary · YML
# Emails a readable summary of the last 7 days every Friday around noon, privately via Gmail.
# Needs secrets: SUPABASE_URL, SUPABASE_SECRET_KEY, GMAIL_ADDRESS, GMAIL_APP_PASSWORD (see README).
name: Weekly summary email
 
on:
  schedule:
    - cron: "47 11 * * 5"   # Fridays 11:47 UTC (about noon)
  workflow_dispatch:
 
jobs:
  send:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - name: Build and send the summary
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_SECRET_KEY: ${{ secrets.SUPABASE_SECRET_KEY }}
          GMAIL_ADDRESS: ${{ secrets.GMAIL_ADDRESS }}
          GMAIL_APP_PASSWORD: ${{ secrets.GMAIL_APP_PASSWORD }}
          SUMMARY_TO: ${{ secrets.SUMMARY_TO }}
          SITE: https://${{ github.repository_owner }}.github.io
        run: |
          script=$(find . -name 'weekly_digest*.py' -not -path './.git/*' | head -1)
          if [ -z "$script" ]; then
            echo "Can't find weekly_digest.py in the repository. Add it as .github/scripts/weekly_digest.py (see README)."
            exit 1
          fi
          echo "Using $script"
          python3 "$script"
 
Claude finished the response
