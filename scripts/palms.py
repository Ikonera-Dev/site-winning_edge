#!/usr/bin/env python3
"""
View, request, and update the PALMS report in data/site-data.js.

    python3 scripts/palms.py                      # show the current report
    python3 scripts/palms.py request              # fill-in form to ask someone for the numbers
    python3 scripts/palms.py new-week             # start a new week (asks for each number)
    python3 scripts/palms.py new-week --as-of 2026-09-25 tyfcb=+35600 oneToOnes=707 ceus=same referrals=-
    python3 scripts/palms.py new-week --from numbers.txt
    python3 scripts/palms.py set tyfcb=840000 ceus.goal=2500 asOf=2026-09-18

new-week rolls the report forward: every metric's current `ytd` becomes its
`lastWeekYtd`, then the new numbers are filled in. `set` corrects the
current week in place and rolls nothing over. Both take --dry-run to preview
without saving.

Values for a metric's new year-to-date total:
    837970 or $837,970   the new YTD total
    +35600               amount added this week (added to last week's total)
    same                 unchanged from last week
    - or null            not reported this week

Only the `palms: { ... }` block of site-data.js is rewritten; everything else
in the file is left byte-for-byte as it was.
"""

import argparse
import re
import sys
from datetime import date, timedelta
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "site-data.js"

# The palms block runs from this line to the first line that is just "  }," at
# the same indent.
BLOCK_START = re.compile(r"^  palms: \{[ \t]*$", re.M)
BLOCK_END = re.compile(r"^  \},?[ \t]*$", re.M)

METRIC_FIELDS = ["label", "prefix", "ytd", "lastWeekYtd", "goal"]
NUMBER_FIELDS = {"ytd", "lastWeekYtd", "goal"}
TOP_FIELDS = ["asOf", "ytdSince"]


class PalmsError(Exception):
    pass


# ---------------------------------------------------------------------------
# Reading and writing the palms block
# ---------------------------------------------------------------------------

def parse_value(raw):
    raw = raw.strip()
    if raw == "null":
        return None
    if raw.startswith('"') and raw.endswith('"'):
        return raw[1:-1]
    if re.fullmatch(r"-?\d+", raw):
        return int(raw)
    raise PalmsError(f"can't read value {raw!r} in the palms block")


def parse_pairs(body):
    """'label: "TYFCB", ytd: 5' -> {"label": "TYFCB", "ytd": 5}"""
    pairs = {}
    for m in re.finditer(r'(\w+):\s*("(?:[^"\\]|\\.)*"|null|-?\d+)', body):
        pairs[m.group(1)] = parse_value(m.group(2))
    return pairs


def load():
    text = DATA_PATH.read_text(encoding="utf-8")
    start_m = BLOCK_START.search(text)
    if not start_m:
        raise PalmsError(f"no `palms: {{` block found in {DATA_PATH.name}")
    end_m = BLOCK_END.search(text, start_m.end())
    if not end_m:
        raise PalmsError(f"couldn't find the end of the palms block in {DATA_PATH.name}")

    block = text[start_m.start():end_m.end()]
    report = {"metrics": {}}
    for field in TOP_FIELDS:
        m = re.search(rf'^\s*{field}:\s*("(?:[^"\\]|\\.)*"|null)', block, re.M)
        report[field] = parse_value(m.group(1)) if m else ""

    metrics_m = re.search(r"metrics:\s*\{(.*)\}\s*\n\s*\},?\s*$", block, re.S)
    if not metrics_m:
        raise PalmsError("couldn't find `metrics: { ... }` inside the palms block")
    for m in re.finditer(r"^\s*(\w+):\s*\{([^{}]*)\}", metrics_m.group(1), re.M):
        fields = parse_pairs(m.group(2))
        missing = [f for f in METRIC_FIELDS if f not in fields]
        if missing:
            raise PalmsError(f"metric {m.group(1)!r} is missing {', '.join(missing)}")
        report["metrics"][m.group(1)] = fields
    if not report["metrics"]:
        raise PalmsError("no metrics found in the palms block")

    return text, (start_m.start(), end_m.end()), report


def js(value):
    if value is None:
        return "null"
    if isinstance(value, str):
        return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return str(value)


def render_block(report, trailing_comma):
    """Writes the palms block with each metric on one aligned line."""
    metrics = report["metrics"]
    cells = {k: {f: js(v[f]) + "," for f in METRIC_FIELDS} for k, v in metrics.items()}
    key_w = max(len(k) for k in metrics) + 2
    widths = {f: max(len(c[f]) for c in cells.values()) + 1 for f in METRIC_FIELDS}

    lines = ["  palms: {"]
    for field in TOP_FIELDS:
        lines.append(f"    {field}: {js(report[field])},")
    lines.append("    metrics: {")
    keys = list(metrics)
    for i, key in enumerate(keys):
        parts = []
        for f in METRIC_FIELDS[:-1]:
            parts.append(f"{f}: {cells[key][f]:<{widths[f]}}")
        parts.append(f"{METRIC_FIELDS[-1]}: {js(metrics[key][METRIC_FIELDS[-1]])}")
        comma = "," if i < len(keys) - 1 else ""
        lines.append(f"      {key + ':':<{key_w}}{{ {''.join(parts)} }}{comma}")
    lines.append("    }")
    lines.append("  }," if trailing_comma else "  }")
    return "\n".join(lines)


def save(text, span, report):
    old_block = text[span[0]:span[1]]
    new_block = render_block(report, old_block.rstrip().endswith(","))
    DATA_PATH.write_text(text[:span[0]] + new_block + text[span[1]:], encoding="utf-8")


# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------

def money(metric, n):
    return "—" if n is None else f"{metric['prefix']}{n:,}"


def change_text(metric):
    # Same rule as js/app.js: this week's YTD minus last week's YTD.
    if metric["ytd"] is None:
        return "not reported"
    if metric["lastWeekYtd"] is None:
        return "(no change line)"
    diff = metric["ytd"] - metric["lastWeekYtd"]
    if diff == 0:
        return "No change since last week"
    sign = "+" if diff > 0 else "−"
    return f"{sign}{metric['prefix']}{abs(diff):,} since last week"


def goal_text(metric):
    if metric["ytd"] is None or not metric["goal"]:
        return ""
    pct = max(0, min(100, metric["ytd"] / metric["goal"] * 100))
    return f"{pct:.0f}% of {money(metric, metric['goal'])}"


def show(report, title="PALMS report"):
    print(f"{title} — as of {display_date(report['asOf'])} · YTD since {report['ytdSince']}")
    rows = [("metric", "key", "YTD", "last week YTD", "shown on site", "goal")]
    for key, m in report["metrics"].items():
        rows.append((m["label"], key, money(m, m["ytd"]), money(m, m["lastWeekYtd"]),
                     change_text(m), goal_text(m)))
    widths = [max(len(r[i]) for r in rows) for i in range(len(rows[0]))]
    for i, row in enumerate(rows):
        print("  " + "  ".join(cell.ljust(w) for cell, w in zip(row, widths)).rstrip())
        if i == 0:
            print("  " + "  ".join("-" * w for w in widths))


def display_date(iso):
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", str(iso))
    return f"{m.group(2)}/{m.group(3)}/{m.group(1)}" if m else str(iso)


# ---------------------------------------------------------------------------
# Input handling
# ---------------------------------------------------------------------------

def parse_date(raw):
    raw = raw.strip()
    try:
        return date.fromisoformat(raw).isoformat()
    except ValueError:
        pass
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", raw)
    if m:
        try:
            return date(int(m.group(3)), int(m.group(1)), int(m.group(2))).isoformat()
        except ValueError:
            pass
    raise PalmsError(f"{raw!r} isn't a date — use YYYY-MM-DD (or MM/DD/YYYY)")


def parse_number(raw, what):
    cleaned = raw.strip().replace(",", "").replace("$", "").replace(" ", "")
    if not re.fullmatch(r"\d+", cleaned):
        raise PalmsError(f"{what}: {raw!r} isn't a whole number")
    return int(cleaned)


def new_ytd(metric, raw, key, new_year):
    """Turns one new-week answer into the new YTD value."""
    raw = raw.strip()
    low = raw.lower()
    if low in ("same", "unchanged", "="):
        return metric["ytd"]
    if low in ("-", "null", "none", "n/a", "not reported"):
        return None
    if raw.startswith("+"):
        if new_year:
            raise PalmsError(f"{key}: '+' amounts add to last week's total, which doesn't "
                             "carry into a new reporting year. Give the full YTD instead.")
        if metric["ytd"] is None:
            raise PalmsError(f"{key}: '+' needs last week's total, but last week wasn't "
                             "reported. Give the full YTD instead.")
        return metric["ytd"] + parse_number(raw[1:], key)
    return parse_number(raw, key)


def read_answers_file(path):
    """Reads 'key = value' lines (as printed by `request`), ignoring # comments."""
    answers = {}
    for n, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        if "=" not in line:
            raise PalmsError(f"{path}, line {n}: expected `name = value`")
        key, value = (part.strip() for part in line.split("=", 1))
        if value in ("", "?"):
            raise PalmsError(f"{path}, line {n}: no value filled in for {key}")
        answers[key] = value
    return answers


def split_assignments(items):
    answers = {}
    for item in items:
        if "=" not in item:
            raise PalmsError(f"expected name=value, got {item!r}")
        key, value = item.split("=", 1)
        answers[key.strip()] = value
    return answers


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_request(report, args):
    next_date = default_next_date(report)
    print("# PALMS numbers for the website. Fill in each value and send it back.")
    print("# For each stat give the new year-to-date total, or +amount added this week.")
    print("# Use - for anything not reported.\n")
    print(f"asOf = {next_date}    # date of the PALMS report (YYYY-MM-DD)")
    for key, m in report["metrics"].items():
        print(f"{key} = ?    # {m['label']}: year-to-date total (last week: {money(m, m['ytd'])})")


def default_next_date(report):
    try:
        return (date.fromisoformat(report["asOf"]) + timedelta(days=7)).isoformat()
    except (TypeError, ValueError):
        return date.today().isoformat()


def cmd_new_week(report, args):
    answers = split_assignments(args.values)
    if args.from_file:
        answers = {**read_answers_file(args.from_file), **answers}

    as_of = answers.pop("asOf", None) or args.as_of
    interactive = not answers and not args.from_file and sys.stdin.isatty()

    unknown = [k for k in answers if k not in report["metrics"]]
    if unknown:
        raise PalmsError(f"unknown metric(s): {', '.join(unknown)}. "
                         f"Known: {', '.join(report['metrics'])}")

    if interactive:
        show(report, "Current report")
        print("\nNew week. Enter each new year-to-date total, or +amount added this week.")
        print("Enter = unchanged, - = not reported.\n")
        suggested = default_next_date(report)
        as_of = as_of or input(f"Report date [{suggested}]: ").strip() or suggested
        for key, m in report["metrics"].items():
            answers[key] = input(f"{m['label']} YTD [was {money(m, m['ytd'])}]: ").strip() or "same"
    else:
        missing = [k for k in report["metrics"] if k not in answers]
        if missing:
            raise PalmsError(f"no value for {', '.join(missing)}. Give every metric "
                             "(use `same` to keep a total or `-` if not reported).")
        if not as_of:
            raise PalmsError("give the report date with --as-of YYYY-MM-DD (or asOf=... in the file)")

    as_of = parse_date(as_of)
    if report["asOf"] and re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(report["asOf"])) \
            and as_of <= report["asOf"] and not args.force:
        raise PalmsError(f"report date {as_of} isn't after the current one ({report['asOf']}). "
                         "To fix the current week use `set` instead; --force to override.")

    new = {"asOf": as_of, "ytdSince": args.ytd_since or report["ytdSince"], "metrics": {}}
    warnings = []
    for key, m in report["metrics"].items():
        ytd = new_ytd(m, answers[key], key, args.new_year)
        if (not args.new_year and ytd is not None and m["ytd"] is not None and ytd < m["ytd"]):
            warnings.append(f"{m['label']} went down ({money(m, m['ytd'])} -> {money(m, ytd)})")
        new["metrics"][key] = {**m, "ytd": ytd,
                               "lastWeekYtd": None if args.new_year else m["ytd"]}

    if warnings and not args.force:
        raise PalmsError("; ".join(warnings) + ". Year-to-date totals only go down when a new "
                         "reporting year starts: use --new-year for that, or --force if the "
                         "numbers are right anyway.")
    return new


def cmd_set(report, args):
    if not args.values:
        raise PalmsError("nothing to set. Example: set tyfcb=840000 ceus.goal=2500 asOf=2026-09-18")
    new = {"asOf": report["asOf"], "ytdSince": report["ytdSince"],
           "metrics": {k: dict(v) for k, v in report["metrics"].items()}}
    for target, raw in split_assignments(args.values).items():
        if target == "asOf":
            new["asOf"] = parse_date(raw)
            continue
        if target == "ytdSince":
            new["ytdSince"] = raw.strip()
            continue
        key, _, field = target.partition(".")
        field = field or "ytd"
        if key not in new["metrics"]:
            raise PalmsError(f"unknown metric {key!r}. Known: {', '.join(new['metrics'])}")
        if field not in METRIC_FIELDS:
            raise PalmsError(f"unknown field {field!r}. Fields: {', '.join(METRIC_FIELDS)}")
        if field in NUMBER_FIELDS:
            low = raw.strip().lower()
            value = None if low in ("-", "null", "none") else parse_number(raw, target)
        else:
            value = raw
        new["metrics"][key][field] = value
    return new


def main():
    parser = argparse.ArgumentParser(
        description="View, request, and update the PALMS report in data/site-data.js.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("\n\n", 1)[1],
    )
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("show", help="show the current report (default)")
    sub.add_parser("request", help="print a fill-in form for whoever sends the numbers")

    nw = sub.add_parser("new-week", help="roll the report forward and enter new numbers")
    nw.add_argument("values", nargs="*", help="metric=value, e.g. tyfcb=+35600")
    nw.add_argument("--as-of", help="report date, YYYY-MM-DD")
    nw.add_argument("--from", dest="from_file", help="read answers from a filled-in `request` form")
    nw.add_argument("--new-year", action="store_true",
                    help="first report of a new reporting year (no change line this week)")
    nw.add_argument("--ytd-since", help="new 'YTD since' text, e.g. 'October 1st'")
    nw.add_argument("--force", action="store_true", help="allow a lower total or an earlier date")
    nw.add_argument("--dry-run", action="store_true", help="preview only, don't save")

    st = sub.add_parser("set", help="correct the current week (no rollover)")
    st.add_argument("values", nargs="*", help="metric=ytd, metric.field=value, asOf=, ytdSince=")
    st.add_argument("--dry-run", action="store_true", help="preview only, don't save")

    args = parser.parse_args()

    try:
        text, span, report = load()
        if args.command in (None, "show"):
            show(report)
            return
        if args.command == "request":
            cmd_request(report, args)
            return

        new = cmd_new_week(report, args) if args.command == "new-week" else cmd_set(report, args)
        print()
        show(new, "Preview" if args.dry_run else "Saved")
        if args.dry_run:
            print("\n--dry-run: nothing saved.")
            return
        save(text, span, new)
        # Read it back so a formatting problem shows up here, not on the site.
        _, _, check = load()
        if check != new:
            raise PalmsError("the saved report didn't read back the same; check data/site-data.js")
        print(f"\nUpdated {DATA_PATH.relative_to(DATA_PATH.parent.parent)}. "
              "Preview with: python3 -m http.server 8000")
    except PalmsError as e:
        print(f"ERROR: {e}\nNothing was saved.", file=sys.stderr)
        sys.exit(1)
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled. Nothing was saved.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
