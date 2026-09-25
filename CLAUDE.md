# CLAUDE.md — BNI Winning Edge chapter site

Handoff notes for Claude Code sessions. Read README.md for the full content-editing guide.

## What this is
Static one-page chapter site (plain HTML/CSS/JS, no build step, no backend).
- Repo: `Ikonera-Dev/site_bniwinningedge` (public), branch `main`
- Live: https://bniwinningedge.com, deployed with GitHub Pages ("deploy from branch", `main`, `/`)
- Commit author: `mouraotech <apps@mourao.tech>`, set per clone with `git config user.name/user.email`

## Files
- `data/site-data.js`: `thisWeek` (date, `trophyNote`, speakers), `quote` {text, author}, `palms` {asOf YYYY-MM-DD, ytdSince, metrics keyed by name: {label, prefix, ytd, lastWeekYtd (hidden), goal}}, and the speaker `rotation`. Edited by hand every week. The site computes "+X since last week" = ytd − lastWeekYtd. Kept out of members.js because the sync rewrites that file.
- `data/members.js`: the member database. One record per person keyed by BNI member `id` (stable across syncs), with `enabled` (Members grid visibility), `trophyWinner` (This Week trophy card), `roles` (Chapter Leadership, shown regardless of `enabled`), contact fields, `photo` (chosen image; "" falls back to `bniPhoto`), plus a top-level `roles` table of `{role, section, max}` that sets section/order and caps. Valid JSON after `window.MEMBERS_DB = `. `scripts/sync-bni.py` adds new people and fills empty fields, never overwrites filled ones (except `bni*` mirror fields); never touches enabled/trophyWinner/email/photo, reports differences; `--dry-run`, `--update`.
- `img/members/`: member photos referenced by `photo` (see its README).
- `scripts/palms.py` (show / request / new-week / set, `--dry-run`) edits only the `palms` block of site-data.js; use it for PALMS updates. The `palms-report` skill in `.claude/skills/` documents the workflow.
- `js/app.js` renders the data files; `css/styles.css` holds the theme; `img/` holds site images (spec in `img/README.md`).
- `CNAME` = `bniwinningedge.com`. Don't remove it or GitHub drops the custom domain.

## Deploy workflow
1. Edit, then preview locally with `python3 -m http.server 8000` → http://localhost:8000
2. Commit and push to `main`.
3. Wait for the build: `gh api repos/Ikonera-Dev/site_bniwinningedge/pages/builds/latest --jq '.status + " " + .commit[0:7]'` until it shows `built <sha>`.
4. Verify live. Cloudflare sits in front and caches CSS/JS/data for about 10 min (HTML isn't cached), so new files can lag a push by up to 10 min. Check with `curl -s "https://bniwinningedge.com/data/site-data.js?x=$RANDOM"` (a query string bypasses the edge cache) or with `fetch(url,{cache:'reload'})`. A normal browser reload can show stale files.

## Infrastructure facts (user-managed; don't re-verify DNS unless asked)
- DNS on Cloudflare (proxied). `www` 301-redirects to the apex. TLS terminates at Cloudflare; GitHub's "Enforce HTTPS" is off, which is expected.
- Cloudflare injects a Web Analytics beacon into the served HTML. It isn't in the repo.
- `gh` auth uses a fine-grained PAT scoped to this repo only (Contents + Pages read/write). The user runs `gh auth login` themselves; never handle the token.

## Rules
- Never commit the weekly meeting email (`*.oft`, `*.eml`, `*.msg`). It's internal, and `.gitignore` covers it.
- The whole repo is served publicly by Pages, so every committed file is web-reachable. No secrets or private notes.
- Ask before pushing changes that alter behavior or layout. Content updates the user dictates can be pushed directly.

## Open items / known issues
- **Release on hold (branch `v2`, not pushed):** waiting for the user's images. Then: wire `img/bni-logo.*` into the header and add favicon / apple-touch-icon / og-image tags (spec in `img/README.md`), preview locally, fast-forward `main` to `v2`, push, wait for the Pages build, verify live. Cache: user says Cloudflare's edge TTL is 5 min, but GitHub Pages still sends `cache-control: max-age=600`, so browsers can hold old JS/data for up to 10 min; this release changes HTML + JS + data together, so a stale mix can show the error banner briefly. User declined `?v=` tags.
- Role caps are enforced: the sync's cap check resolves over-cap/empty capped roles from live BNI (`bniHolders`), else reports "fix by hand"; the site shows at most `max`, preferring `bniHolders`. Caps count sub-roles ("X - Y" counts toward "X"). Caps: President / Vice President / Secretary / Treasurer 1, Visitor Host 3, Membership Committee 3. Trophy winner max 1: site shows the first alphabetical, sync reports extras or none (can't fix from BNI).
- Not approved yet: having the sync download BNI photos into `img/members/`. BNI's member profile page (memberdetails) returns no data, so the chapter page is the only BNI source.
- Declined for now: `?v=` version numbers on the asset links in `index.html`.
- The header logo is still hot-linked from an email CDN (`fcebsch.stripocdn.email`). The user will supply their own logo, favicon and share images into `img/`.
- Referrals metric is `null` ("Not reported").
