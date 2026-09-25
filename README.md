# BNI Winning Edge — chapter website

The website of **BNI Winning Edge**, a BNI referral marketing chapter that
meets Friday mornings in Framingham, Massachusetts.

Live at **https://bniwinningedge.com**

## What's on the site

- **This Week**: the week's trophy winner, quote of the week, and speakers,
  plus the chapter's PALMS report (TYFCB, 1-to-1's, CEUs, Referrals) with
  year-to-date totals, the change since last week, and progress toward the
  year's goals.
- **Upcoming Speaker Rotation**: who presents on each upcoming Friday. Past
  dates drop off automatically.
- **Our People**: the chapter leadership team, grouped by role, and the
  member directory with each member's company, category, and contact links.
- **Visit Us**: meeting day, time and location, directions, and what
  visitors should know.

## How it's built

A single static page: plain HTML, CSS and JavaScript, with no build step, no
server, and no framework. The page is filled in from a few data files when it
loads.

```
index.html          the page
css/styles.css      styling
js/app.js           fills the page from the data files
data/site-data.js   chapter info, this week's meeting, PALMS report, speaker rotation
data/members.js     members, leadership roles, and who appears on the site
img/                site images and member photos
scripts/            maintenance scripts for the data files
```

## Viewing it locally

Open `index.html` in a browser, or serve the folder:

```bash
python3 -m http.server 8000
```

then visit http://localhost:8000.
