# BNI Winning Edge — chapter site

A one-page site for the chapter: this week's meeting (trophy winner, speakers,
quote, PALMS numbers), the upcoming speaker rotation, the leadership team, and
the full member directory. Plain HTML/CSS/JS — no build step, no server-side
code, no database.

Live at **https://bniwinningedge.com**, served by GitHub Pages from the `main`
branch.

## Project structure

```
index.html               the page shell (structure only — no content to edit here)
css/styles.css            theme: white background, #CF2030 (BNI red) accent
js/app.js                 renders the data files below into the page
data/site-data.js         ← chapter info + THIS WEEK + rotation. Edit weekly.
data/members-auto.js      ← member + leadership roster. AUTO-GENERATED, don't hand-edit.
data/overrides.js         ← manual fixes/additions on top of members-auto.js. Edit as needed.
img/                      ← site images (logo, favicon, share image). See img/README.md.
scripts/sync-bni.py       fetches the roster from BNI and regenerates members-auto.js
CNAME                     custom domain for GitHub Pages. Don't delete.
```

Everything in this repo is publicly reachable on the live site, so never
commit anything private (the weekly meeting email files `*.oft`/`*.eml`/`*.msg`
are already blocked by `.gitignore`).

## Where the member/leadership data comes from

The member directory and leadership team are fetched from the chapter's
public BNI page rather than typed in by hand — run:

```bash
python3 scripts/sync-bni.py
```

whenever the roster changes (new member, a title changes hands, someone
updates their BNI Connect photo). It takes a few seconds and rewrites
`data/members-auto.js`.

**Why a script instead of the page fetching this live, on every visit:** BNI's
server doesn't send CORS headers, so a visitor's browser is blocked from
reading that data directly from a script running on your own domain — that's
a restriction on BNI's end, not something client-side code can work around.
Running the fetch here, from your machine, sidesteps it, since CORS only
restricts browsers, not scripts you run yourself. The tradeoff is that "live"
becomes "re-run this when something changes" instead of "always current" —
appropriate for a roster that changes rarely, and it means the public site
never breaks just because BNI's page is slow or down.

### When BNI doesn't have something (e.g., no company link on file)

`sync-bni.py` only pulls what BNI publishes. When a member has no company
website on file, their name shows as **plain, unlinked text** instead of a
broken or guessed link — same idea for photos (falls back to BNI's default
silhouette) and for anything BNI simply doesn't expose at all, like email
addresses.

To fill in what's missing, or correct something, add it to
**`data/overrides.js`** instead of editing `members-auto.js` directly —
anything in `members-auto.js` gets overwritten the next time you run the
sync script, but `overrides.js` is untouched by it and always wins:

```js
window.SITE_OVERRIDES = {
  members: {
    "Christopher Mingace": { companyUrl: "https://www.hbmhlaw.com" }
  },
  leadership: {
    "Ian McCarthy": { companyUrl: "https://www.unitedhomeexperts.com" }
  }
};
```

Key each entry by the person's name exactly as it appears in
`members-auto.js`. Only include the fields you want to change — everything
else keeps whatever the sync fetched. Full explanation and more examples are
in the comment block at the top of `data/overrides.js`.

## Running it locally

You don't strictly need a local server — double-clicking `index.html` works
in most browsers because all data is loaded via `<script>` tags, not `fetch()`
(which browsers block on `file://` URLs). A local server just gives you
auto-reload while editing. Two easy options, neither requires installing a
runtime:

**Option A — VS Code Live Server extension (recommended)**
1. Install the extension: **Live Server** by Ritwick Dey
   (`ritwickdey.LiveServer`). This repo has a `.vscode/extensions.json` that
   will prompt you to install it automatically when you open the folder.
2. Right-click `index.html` → **Open with Live Server**.
3. It opens in your browser at `http://127.0.0.1:5500` and auto-refreshes
   whenever you save a file.

**Option B — Python's built-in server** (Python already on this machine)
```bash
python3 -m http.server 8000
```
then open `http://localhost:8000`. No auto-reload — refresh manually after
saving.

No Node.js, npm, or other runtime is required for either option — `sync-bni.py`
needs Python (already present), everything else is browser-native.

## APIs / external services

There isn't really an "API" here for the page itself — it's a static site —
but a few external things it depends on:

- **BNI's chapter-detail endpoint** — `scripts/sync-bni.py` fetches from
  `bninortheastma.com/bnicms/v3/frontend/chapterdetail/display`. This is
  BNI's own internal (undocumented, no key/auth) endpoint that their public
  chapter page itself calls — not a stable public API, so if BNI redesigns
  that page, this script may need its parsing patterns updated. It'll tell
  you clearly (and not overwrite existing data) if it parses zero members.
- **BNI Connect member photos** — hot-linked directly from
  `bniconnectglobal.com` instead of being downloaded and stored in this repo.
  When a member updates their headshot in BNI Connect, it updates here too,
  next sync. No key or account needed — it's a public image URL — but if BNI
  ever blocks hotlinking, those photos would break.
- **Google Maps** — the "View on Google Maps" button is a plain link
  (`goo.gl/maps/...`), not an embedded map, so no Google Maps API key is
  needed.
- **No contact form, no database, no auth** — matches the "view-only,
  I edit it myself" requirement. If a real contact form or admin login ever
  gets added later, that's the point where an actual backend (and real API
  keys) would come in — not needed for what's here now.

## Updating content week to week

Open `data/site-data.js` and edit the `thisWeek` block (trophy winner,
speakers, quote, PALMS metrics) and the `rotation` array. Full instructions
are in the comment block at the top of that file.

Rotation dates are written as "Month Day" (e.g. `"October 2"`). Dates before
today are hidden on the site automatically, so old rows can stay in the file
until you get around to deleting them.

For the trophy winner and speakers, you only need to type their `name` and
`company` — their photo and company link are looked up automatically by
matching the name against the member directory. If a speaker is a visitor
rather than a chapter member, add `photo` / `companyUrl` directly on that
entry and they'll be used as-is instead of an auto lookup.

Member and leadership roster changes (new member, title change, updated
photo) aren't edited by hand — run `python3 scripts/sync-bni.py` to pull the
latest from BNI, or add an entry to `data/overrides.js` for anything BNI
doesn't have on file. See "Where the member/leadership data comes from" above.

## Images

Site images live in `img/` and are served from the site itself. `img/README.md`
lists the expected files (logo, favicon, Apple touch icon, share image) and
their sizes. The header logo is still hot-linked from an email CDN until a
local `img/bni-logo.png` (or `.svg`) is added.

## Deploying

The site deploys with **GitHub Pages** ("Deploy from a branch", `main`, `/`),
with the custom domain set by the `CNAME` file. There's no build step: pushing
to `main` publishes.

1. Preview locally (see "Running it locally" above).
2. Commit and push to `main`. Larger changes are built on a separate branch
   and merged into `main` when ready.
3. Pages rebuilds in about a minute. To check from the command line:
   `gh api repos/Ikonera-Dev/site_bniwinningedge/pages/builds/latest --jq '.status + " " + .commit[0:7]'`
4. Check the live site.

**Cloudflare** sits in front of GitHub Pages (DNS, TLS, and caching; `www`
redirects to the bare domain). It caches CSS, JS and data files for about 10
minutes, so an update can take up to 10 minutes to appear even after the
Pages build finishes. HTML isn't cached. To see the fresh copy of a file right
away, add any query string, e.g.
`https://bniwinningedge.com/data/site-data.js?x=123`.

Re-run `python3 scripts/sync-bni.py` locally before a deploy if you want the
roster refreshed; the script doesn't run on the host.

## A note on the seed data

The member/leadership data in `data/members-auto.js` and the This Week
content in `data/site-data.js` were pulled from the chapter's public BNI page
and this week's meeting recap email as a starting point, so the site isn't
empty on first run. Double-check it before publishing — especially anyone
whose photo is still the default silhouette or whose company shows as
unlinked text — and add anything missing to `data/overrides.js`.
