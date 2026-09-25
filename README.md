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
data/members.js           ← member database + roles table. Synced from BNI, safe to hand-edit.
img/                      ← site images (logo, favicon, share image). See img/README.md.
img/members/              ← your own member photos. See img/members/README.md.
scripts/sync-bni.py       checks BNI against data/members.js and adds/fills in people
CNAME                     custom domain for GitHub Pages. Don't delete.
```

Everything in this repo is publicly reachable on the live site, so never
commit anything private (the weekly meeting email files `*.oft`/`*.eml`/`*.msg`
are already blocked by `.gitignore`).

## The member database (`data/members.js`)

Every person (members, leadership, and leadership-only people like the
Director Consultant) has one record in `data/members.js`, addressed by
their BNI member `id`:

```json
{
  "id": "Rag3V6j3CjTYuZwhSHWAqw==",
  "enabled": true,
  "trophyWinner": false,
  "roles": [],
  "name": "Adam Bortolussi",
  "firstName": "Adam",
  "lastName": "Bortolussi",
  "company": "Bortolussi Wealth Management",
  "companyUrl": "",
  "category": "Financial Advisor",
  "categoryPath": "Finance & Insurance > Financial Advisor > Financial Advisor",
  "phone": "5084163534",
  "email": "",
  "photo": "",
  "bniPhoto": "",
  "bniProfileUrl": "https://bninortheastma.com/en-US/memberdetails?...",
  "bniMessageUrl": "https://bninortheastma.com/en-US/sendmessage?..."
}
```

- **`enabled`** decides whether the person appears in the Members grid.
- **`trophyWinner`**: set `true` on this week's winner (and `false` on last
  week's). The This Week trophy card shows whoever is flagged. The
  congratulations line is `trophyNote` in `data/site-data.js`.
- **`roles`**: the leadership roles someone holds, e.g. `["President"]`.
  The Chapter Leadership tab lists everyone with at least one role,
  whether or not they're `enabled`. That's how the Regional Support Team
  (e.g. the Director Consultant, `enabled: false`) appears in Leadership
  but not in the Members grid.
- **`email`**, a missing **`companyUrl`**, or a corrected **`company`** /
  **`phone`**: just edit the record. The sync never overwrites a field that
  already has a value.
- **Photos:** `photo` is the image the site shows. Leave it `""` to use the
  BNI Connect photo (`bniPhoto`), or put your own file in `img/members/` and
  set `"photo": "img/members/adam-bortolussi.jpg"`. See
  `img/members/README.md`.
- Fields starting with **`bni`** mirror BNI and are refreshed on every sync.
  Don't edit those.

### The roles table

The `roles` list at the top of `data/members.js` defines every role:

```json
{ "role": "President", "section": "Executive Team", "max": 1 }
```

- **`section`** is the heading the role is listed under in Chapter
  Leadership. Sections appear in the order of their first role; within a
  section, people are ordered by their highest-listed role, then by name.
- **`max`** is how many people can hold the role (`null` = no limit).
  Every sync runs a **role cap check**: a capped role must be held by 1 to
  `max` people. When it fails (too many holders, or nobody), the live BNI
  page decides. If BNI lists a valid set of holders, the database is set to
  match; if BNI's own list breaks the cap too, nothing changes and the
  script tells you to fix it by hand. `--dry-run` shows what it would do.
- **`bniHolders`** is who BNI listed for the role at the last sync (member
  ids, refreshed every run; don't edit). If `data/members.js` is edited to
  break a cap before the next sync, the site still shows at most `max`
  people, preferring these, then alphabetical, and logs a browser-console
  warning naming whoever it left out.

The file must stay valid JSON after the `window.MEMBERS_DB = ` line: double
quotes, no trailing commas, no comments. The sync script stops with the line
number if it can't read it. And like everything in this repo, it's public, so
only add contact details members are happy to have online.

### Syncing with BNI

```bash
python3 scripts/sync-bni.py --dry-run
```

reads the chapter's public BNI page and reports, without changing anything:
who's new, which empty fields BNI could fill in, where BNI differs from your
values, and who's enabled here but no longer on BNI. Drop `--dry-run` to
apply it:

- **New on BNI** → added. Chapter members start `enabled: true`;
  leadership-only people start `enabled: false`.
- **Already in the database** → only empty fields are filled in. Where BNI
  has a different value, yours is kept and the difference is reported; add
  `--update` to take BNI's values instead.
- **No longer on BNI** → reported only. Set `"enabled": false` if they've
  left the chapter.
- **Roles** → follow the same rule as other fields: empty `roles` are filled
  in from BNI's leadership cards, differences are reported (`--update`
  takes BNI's). A role BNI shows that isn't in the roles table yet is added
  with `"max": null`.
- **Never touched:** `enabled`, `trophyWinner`, `email`, `photo`.

**Why a script instead of the page fetching BNI live:** BNI's server doesn't
send CORS headers, so a visitor's browser is blocked from reading that data
from a page on your own domain. Running the fetch here, from your machine,
sidesteps that, since CORS only restricts browsers. It also means the public
site never breaks just because BNI's page is slow or down.

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
- **BNI Connect member photos** — by default hot-linked directly from
  `bniconnectglobal.com` (`bniPhoto`). When a member updates their headshot
  in BNI Connect, it updates here too, next sync. If BNI ever blocks
  hotlinking, those photos would break; a photo stored in `img/members/`
  (`photo`) doesn't depend on BNI.
- **Google Maps** — the "View on Google Maps" button is a plain link
  (`goo.gl/maps/...`), not an embedded map, so no Google Maps API key is
  needed.
- **No contact form, no database, no auth** — matches the "view-only,
  I edit it myself" requirement. If a real contact form or admin login ever
  gets added later, that's the point where an actual backend (and real API
  keys) would come in — not needed for what's here now.

## Updating content week to week

Open `data/site-data.js` and edit the `thisWeek` block (trophy note,
speakers, quote, PALMS metrics) and the `rotation` array. Pick the trophy
winner by moving `"trophyWinner": true` in `data/members.js`. Full instructions
are in the comment block at the top of that file.

Rotation dates are written as "Month Day" (e.g. `"October 2"`). Dates before
today are hidden on the site automatically, so old rows can stay in the file
until you get around to deleting them.

For the speakers, you only need to type their `name` and
`company` — their photo and company link are looked up automatically by
matching the name against the member directory. If a speaker is a visitor
rather than a chapter member, add `photo` / `companyUrl` directly on that
entry and they'll be used as-is instead of an auto lookup.

Member and leadership changes (new member, title change, updated photo)
come from running `python3 scripts/sync-bni.py`; anything BNI doesn't have
goes straight into `data/members.js`. See "The member database" above.

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
