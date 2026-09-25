---
name: palms-report
description: Ask for, enter, correct, and verify the BNI Winning Edge chapter's weekly PALMS report stats (TYFCB, 1-to-1's, CEUs, Referrals, year-to-date totals, goals, report date) on the chapter site, using scripts/palms.py. Use this whenever the user mentions PALMS, TYFCB, 1-to-1s, CEUs, referrals, "this week's numbers", "the stats", updating the PALMS tiles, pastes or points to the weekly meeting email with numbers in it, wants to fix a PALMS number, starts a new reporting year, or wants a form to ask someone for the numbers, even if they don't say "PALMS".
---

# PALMS report

The chapter site shows a PALMS tile per metric: the year-to-date (YTD) total, a
"+X since last week" line, and a meter toward the full-year goal. The data lives
in the `palms` block of `data/site-data.js`:

```js
palms: {
  asOf: "2026-09-18",            // report date, YYYY-MM-DD (site shows 09/18/2026)
  ytdSince: "October 1st",
  metrics: {
    tyfcb: { label: "TYFCB", prefix: "$", ytd: 837970, lastWeekYtd: 802370, goal: 1000000 },
    ...
  }
}
```

The "+X since last week" line is never stored; the site calculates it as
`ytd − lastWeekYtd`. So a new week means moving each `ytd` into `lastWeekYtd` and
typing new totals. `scripts/palms.py` does that, checks the input, and rewrites
only the `palms` block. Use the script rather than editing the block by hand: it
keeps the rollover and the formatting consistent, and it refuses the common
mistakes listed below.

## Commands

```bash
python3 scripts/palms.py                 # current report, incl. what the site shows
python3 scripts/palms.py request         # fill-in form for whoever sends the numbers
python3 scripts/palms.py new-week --as-of 2026-09-25 tyfcb=+35600 oneToOnes=707 ceus=same referrals=- --dry-run
python3 scripts/palms.py new-week --from /path/to/filled-form.txt --dry-run
python3 scripts/palms.py set ceus=701 --dry-run                  # fix this week, no rollover
python3 scripts/palms.py new-week --new-year --as-of 2026-10-02 tyfcb=12500 ... --dry-run
```

Value formats for a metric in `new-week`:

| Value | Meaning |
|---|---|
| `873570` or `$873,570` | the new YTD total |
| `+35600` | amount added this week; added to last week's total |
| `same` | unchanged (the site shows "No change since last week") |
| `-` | not reported this week |

`set` takes `metric=value` (the YTD), `metric.goal=`, `metric.lastWeekYtd=`,
`metric.label=`, `asOf=`, and `ytdSince=`. Metric keys are the ones `show`
prints: `tyfcb`, `oneToOnes`, `ceus`, `referrals`.

## Workflow

1. **Show the current report** with `python3 scripts/palms.py`. You need last
   week's totals in front of you to read the new numbers correctly.

2. **Work out the job:**
   - New weekly numbers → `new-week`.
   - A wrong number in the current week → `set`. Don't use `new-week` for this;
     it would roll the wrong number into last week.
   - The first report after the reporting year restarts (YTD resets; the site
     says "YTD since October 1st") → `new-week --new-year`, which leaves out the
     change line that week. Pass `--ytd-since` if the start date text changes.
   - The user wants to ask someone else for the numbers → `request` (see
     "Requesting the numbers").

3. **Get the numbers.** Ask for the report date and one value per metric. If the
   user points at the weekly meeting email (`.oft`, `.eml`, `.msg`), read the
   numbers from it where it sits. It's internal: don't copy it into the repo or
   quote it anywhere public (the repo is served publicly and `.gitignore`
   blocks these files).

   The one real ambiguity is **total vs weekly amount**. PALMS emails and people
   give both: "TYFCB $35,600" might be this week's amount or the YTD. Compare
   with last week's YTD. A number much smaller than last week's total is
   almost certainly a weekly amount (use `+35600`); a number just above it is
   a total. If it could be either, ask. A wrong guess puts a wrong total on the
   public site and makes next week's change line wrong too.

4. **Preview with `--dry-run`** and show the user the resulting table,
   especially the "shown on site" column, which is exactly what visitors will
   read. Get a yes before saving.

5. **Save** by running the same command without `--dry-run`. The script reads
   the file back after writing and exits with an error if anything is off.

6. **Check the local site.** If the preview server isn't running, start it
   (`python3 -m http.server 8000` from the repo root, or the preview tool) and
   confirm the PALMS tiles and the "as of" date match the table.

7. **Commit** on the current branch with a message like
   `PALMS numbers as of 09/25/2026`. Pushing to `main` publishes the site, so
   ask before pushing and say which branch you're on.

## When the script refuses

Every refusal leaves the file untouched. Explain it to the user in plain words
and ask; don't reach for `--force` unless they confirm the numbers are right.

- **"went down"**: YTD totals only drop when a new reporting year starts. Either
  it's the first report of the year (`--new-year`) or a number was mistyped or
  misread as a weekly amount.
- **"isn't after the current one"**: the date is the same as or earlier than the
  current report. To fix this week, use `set`.
- **"'+' needs last week's total"**: last week wasn't reported, or it's a new
  year, so there's nothing to add to. Ask for the full YTD.
- **"no value for ..."**: every metric needs a value; use `same` or `-` for ones
  that didn't change or weren't reported.

## Requesting the numbers

`python3 scripts/palms.py request` prints a fill-in form with the next report
date and last week's totals, for example:

```
asOf = 2026-09-25    # date of the PALMS report (YYYY-MM-DD)
tyfcb = ?    # TYFCB: year-to-date total (last week: $837,970)
```

Give it to the user to send. Don't send messages on their behalf. When it comes
back filled in, save it outside the repo (a scratch or temp directory), then run
`new-week --from <file> --dry-run` and continue from step 4. Lines starting
with `#` are ignored, and values use the same formats as above.

## Adding or renaming a metric

Edit the `metrics` block in `data/site-data.js` by hand. Keep one metric per
line with all five fields (`label`, `prefix`, `ytd`, `lastWeekYtd`, `goal`).
The site shows tiles in the order listed, and the script picks up whatever
metrics are there. Run `python3 scripts/palms.py` afterwards to confirm it
still reads the block.
