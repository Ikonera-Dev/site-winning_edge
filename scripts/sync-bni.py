#!/usr/bin/env python3
"""
Checks the chapter's public BNI page against the member database
(data/members.js) and brings the database up to date:

    python3 scripts/sync-bni.py             # apply changes
    python3 scripts/sync-bni.py --dry-run   # only report, write nothing
    python3 scripts/sync-bni.py --update    # also let BNI overwrite fields
                                            # that differ from the database

For every person found on BNI (the member table and the leadership cards):
  - NOT in the database yet -> a new record is added with everything BNI
    has on them. Chapter members are added with "enabled": true, people who
    only appear in leadership (e.g. the Director Consultant) with false.
  - ALREADY in the database  -> fields that are empty in the database are
    filled in from BNI. Fields that already have a value are never changed
    (so your hand edits are safe); if BNI's value differs, it's reported.
    Pass --update to accept BNI's values for those instead.
    The exception is the fields starting with "bni" (bniPhoto,
    bniProfileUrl, bniMessageUrl): they mirror BNI and are always refreshed.
People are matched by their BNI member ID, falling back to an exact name
match. Anyone in the database who's enabled but no longer on BNI is
reported, not removed or disabled; set "enabled": false yourself if they've
left the chapter.

Leadership roles are stored per person ("roles": ["President"]) and follow
the same rule: empty roles are filled from BNI's leadership cards, different
ones are reported (--update takes BNI's). A role BNI shows that isn't in the
database's "roles" table yet is added to it, with no cap ("max": null).
The sync never changes "enabled", "trophyWinner", "email" or "photo".

Why a script instead of the page fetching this itself: BNI's server doesn't
send CORS headers, so a browser on your own domain is blocked from reading
the response directly (this is BNI's restriction, not something we can work
around from client-side JS). Running the fetch here, server-side, sidesteps
that — there's no CORS restriction on a script you run yourself.
"""

import argparse
import json
import re
import sys
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Chapter config — change these if you ever point this at a different
# chapter. Find them by opening the chapter's bninortheastma.com page,
# opening browser devtools -> Network tab, and looking at the POST request
# to .../bnicms/v3/frontend/chapterdetail/display for its form fields.
# ---------------------------------------------------------------------------
BASE_URL = "https://bninortheastma.com"
ENDPOINT = "/bnicms/v3/frontend/chapterdetail/display"
CHAPTER_ID = "uYMfymrQf2BYSn2giIGAwg=="   # decoded chapterId query param
WEBSITE_TYPE = "2"
WEBSITE_ID = "27402"

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "members.js"
DB_PREFIX = "window.MEMBERS_DB = "

DB_HEADER = """/**
 * ============================================================================
 *  MEMBER DATABASE: the leadership roles table and one record per person.
 *  Loaded by index.html, rendered by js/app.js.
 * ============================================================================
 *  Safe to edit by hand, but keep it valid JSON after the `=` sign: double
 *  quotes, no trailing commas, no comments inside. scripts/sync-bni.py reads
 *  and rewrites this file and will stop with an error if it can't parse it.
 *
 *  roles: every leadership role, in display order. Each has:
 *    role          the title, exactly as used in people's "roles"
 *    section       the Chapter Leadership heading it's listed under
 *    max           how many people may hold it (null = no limit)
 *  Sections appear in the order of their first role; people within a
 *  section are ordered by their highest-listed role, then by name.
 *
 *  Each person is addressed by "id" (their BNI member id). Fields:
 *    enabled       true = shown in the Members grid, false = hidden
 *                  (Leadership shows everyone who has a role, enabled or
 *                  not, so the Regional Support Team stays leadership-only)
 *    trophyWinner  true = shown as This Week's trophy winner
 *    roles         leadership roles held, e.g. ["President"]; [] = none
 *    name          display name; firstName / lastName are split from it
 *    company, companyUrl, category (categoryPath = BNI's full category)
 *    phone, email  email is never on BNI, add it by hand
 *    photo         the image the site shows. Leave "" to use bniPhoto.
 *                  Your own image: put the file in img/members/ and set
 *                  e.g. "photo": "img/members/adam-bortolussi.jpg"
 *    bniPhoto, bniProfileUrl, bniMessageUrl
 *                  mirror BNI; refreshed on every sync, don't edit
 *
 *  Refresh from BNI:  python3 scripts/sync-bni.py   (--dry-run to preview)
 * ============================================================================
 */
"""

# BNI's "no photo" silhouette. Stored in the database as "" (no photo); the
# site shows this same image for anyone without one.
DEFAULT_PHOTO = "https://bniconnectglobal.com/web/images/default_profile.gif"

# Field order of a person record in members.js. `email` is never on BNI
# and is only ever filled in by hand.
RECORD_FIELDS = [
    "id", "enabled", "trophyWinner", "roles", "name", "firstName", "lastName",
    "company", "companyUrl", "category", "categoryPath",
    "phone", "email", "photo", "bniPhoto", "bniProfileUrl", "bniMessageUrl",
]

# Default for a field missing from a record (e.g. one added by hand).
FIELD_DEFAULTS = {"enabled": True, "trophyWinner": False, "roles": []}

# Fields the sync fills in from BNI when they're empty. `enabled`,
# `trophyWinner`, `email` and `photo` are never touched; `roles` is handled
# separately in sync().
BNI_FIELDS = [
    "name", "firstName", "lastName", "company", "companyUrl", "category",
    "categoryPath", "phone",
]

# Fields that mirror BNI and are overwritten on every sync.
MIRROR_FIELDS = ["bniPhoto", "bniProfileUrl", "bniMessageUrl"]


def fetch_chapter_html():
    body = urllib.parse.urlencode({
        "pageMode": "Live_Site",
        "chapterId": CHAPTER_ID,
        "languageLocaleCode": "en_US",
        "website_type": WEBSITE_TYPE,
        "website_id": WEBSITE_ID,
        "planyourvisit": "y",
    }).encode()

    req = urllib.request.Request(
        BASE_URL + ENDPOINT,
        data=body,
        method="POST",
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; BNI-chapter-site-sync/1.0)",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"{BASE_URL}/en-US/chapterdetail?chapterId={urllib.parse.quote(CHAPTER_ID)}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def strip_tags(html):
    return re.sub(r"<[^>]+>", "", html).strip()


def split_name(name):
    # "Christopher Orrick" -> ("Christopher", "Orrick"). BNI only publishes
    # the full name, so this is a best guess; correct it by hand if needed.
    parts = name.split(" ", 1)
    return parts[0], (parts[1] if len(parts) > 1 else "")


def profile_url(member_id, name):
    if not member_id:
        return ""
    return (f"{BASE_URL}/en-US/memberdetails?encryptedMemberId="
            f"{urllib.parse.quote(member_id, safe='')}&name={urllib.parse.quote_plus(name)}")


def message_url(user_id_quoted, name):
    if not user_id_quoted:
        return ""
    return f"{BASE_URL}/en-US/sendmessage?userId={user_id_quoted}&userName={urllib.parse.quote_plus(name)}"


def parse_leadership(html):
    sections = []
    row_marker = '<div class="chptr_leadr_card_row">'
    rows = html.split(row_marker)[1:]  # [0] is everything before the first row

    for row in rows:
        # a row ends where the next chptr_leadr_card_row (or the widget) ends;
        # since we already split on the marker, `row` naturally runs up to
        # the next occurrence (or end of string) — good enough here because
        # we only read fields out of it with independent regexes below.
        is_executive_row = "leader_headwrap" in row.split('<div class="leaders_card_holder">')[0]

        if is_executive_row:
            section_name = "Executive Team"
        else:
            heading_match = re.search(
                r'<div class="chptr_leadr_heading">\s*<p>(.*?)</p>', row, re.S
            )
            section_name = strip_tags(heading_match.group(1)) if heading_match else "Leadership"

        card_marker = '<div class="leaders_card_holder">'
        cards = row.split(card_marker)[1:]
        people = []

        for card in cards:
            name_m = re.search(r'<h4 title="([^"]*)"', card)
            title_m = re.search(r'<h5 title="([^"]*)"', card)
            photo_m = re.search(r'<img src="([^"]*)"\s+alt="default">', card)
            phone_m = re.search(r'href="tel:([^"]*)"', card)
            member_m = re.search(r"encryptedMemberId=([^&\"]*)&(?:amp;)?name=", card)
            user_m = re.search(r"sendmessage\?userId=([^&\"]*)&", card)

            company_link_m = re.search(
                r'<p class="company_name"><a\s+href="([^"]*)"\s+target="_blank"\s+title="([^"]*)">',
                card,
            )
            company_nolink_m = re.search(
                r'<a class="leadership_withoutwebsite" title="([^"]*)">', card
            )

            if not name_m:
                continue

            if company_link_m:
                company_url, company = company_link_m.group(1), company_link_m.group(2)
            elif company_nolink_m:
                company_url, company = "", company_nolink_m.group(1)
            else:
                company_url, company = "", ""

            people.append({
                "name": name_m.group(1).strip(),
                "titles": [title_m.group(1).strip()] if title_m else [],
                "company": company.strip(),
                "companyUrl": company_url.strip(),
                "phone": phone_m.group(1).strip() if phone_m else "",
                "photo": photo_m.group(1).strip() if photo_m else DEFAULT_PHOTO,
                "memberId": urllib.parse.unquote(member_m.group(1)) if member_m else "",
                "userId": user_m.group(1) if user_m else "",
            })

        if people:
            sections.append({"section": section_name, "people": merge_duplicate_people(people)})

    return sections


def merge_duplicate_people(people):
    # BNI renders one card per (person, title) pair — someone on the
    # Membership Committee with a second specialty title shows up twice.
    # Fold those into one person with multiple titles. Titles are kept in
    # full; js/app.js shortens repeated prefixes for display.
    merged = []
    by_name = {}
    for person in people:
        if person["name"] in by_name:
            existing = by_name[person["name"]]
            for title in person["titles"]:
                if title not in existing["titles"]:
                    existing["titles"].append(title)
            existing["companyUrl"] = existing["companyUrl"] or person["companyUrl"]
            if existing["photo"] == DEFAULT_PHOTO:
                existing["photo"] = person["photo"]
        else:
            by_name[person["name"]] = person
            merged.append(person)
    return merged


def parse_members(html):
    table_m = re.search(
        r'<table id="chapterListTable".*?<tbody>(.*?)</tbody>', html, re.S
    )
    if not table_m:
        return []

    rows = re.findall(r"<tr role=\"row\".*?</tr>", table_m.group(1), re.S)
    members = []

    for row in rows:
        tds = re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)
        if len(tds) < 4:
            continue

        name_m = re.search(r'class="linkone">([^<]*)</a>', tds[0])
        member_m = re.search(r"encryptedMemberId=([^&]*)&(?:amp;)?cmsv3", tds[0])
        user_m = re.search(r"sendmessage\?userId=([^&\"]*)&", row)
        if not name_m:
            continue

        # BNI shows the category as a path: "Consulting > Business
        # Consultant - Small Business > Business Consultant - Small
        # Business". The last step is what the site displays.
        category_raw = strip_tags(tds[2]) if len(tds) > 2 else ""
        category_raw = re.sub(r"\s*&gt;\s*|\s*>\s*", " > ", category_raw).strip()
        category = category_raw.split(" > ")[-1].strip() if category_raw else ""

        members.append({
            "name": name_m.group(1).strip(),
            "company": strip_tags(tds[1]).strip() if len(tds) > 1 else "",
            "category": category,
            "categoryPath": category_raw,
            "phone": strip_tags(tds[3]).strip() if len(tds) > 3 else "",
            "companyUrl": "",
            "photo": DEFAULT_PHOTO,
            "memberId": urllib.parse.unquote(member_m.group(1)) if member_m else "",
            "userId": user_m.group(1) if user_m else "",
        })

    return members


def to_record(person, enabled):
    """Turns a parsed BNI person into a members.js record."""
    first, last = split_name(person["name"])
    photo = person.get("photo", "")
    return {
        "id": person["memberId"] or f"name:{person['name']}",
        "enabled": enabled,
        "trophyWinner": False,
        "roles": list(person.get("titles", [])),
        "name": person["name"],
        "firstName": first,
        "lastName": last,
        "company": person.get("company", ""),
        "companyUrl": person.get("companyUrl", ""),
        "category": person.get("category", ""),
        "categoryPath": person.get("categoryPath", ""),
        "phone": person.get("phone", ""),
        "email": "",
        "photo": "",
        "bniPhoto": "" if photo == DEFAULT_PHOTO else photo,
        "bniProfileUrl": profile_url(person["memberId"], person["name"]),
        "bniMessageUrl": message_url(person.get("userId", ""), person["name"]),
    }


def found_on_bni(members, leadership_sections):
    """Everyone on BNI's page as records, keyed by id. Chapter members first,
    then leadership-only people. Where someone is in both, the leadership
    card fills in what the member table lacks (photo, company link)."""
    found = {}
    for m in members:
        rec = to_record(m, enabled=True)
        found[rec["id"]] = rec

    by_name = {rec["name"]: rec for rec in found.values()}
    for section in leadership_sections:
        for p in section["people"]:
            leader = to_record(p, enabled=False)
            existing = found.get(leader["id"]) or by_name.get(leader["name"])
            if existing:
                for field in BNI_FIELDS + MIRROR_FIELDS:
                    if not existing[field] and leader[field]:
                        existing[field] = leader[field]
                for title in leader["roles"]:
                    if title not in existing["roles"]:
                        existing["roles"].append(title)
                p["id"] = existing["id"]
            else:
                found[leader["id"]] = leader
                by_name[leader["name"]] = leader
                p["id"] = leader["id"]
    return found


def load_db():
    if not DB_PATH.exists():
        return {"lastSynced": "", "roles": [], "people": []}
    text = DB_PATH.read_text(encoding="utf-8")
    if DB_PREFIX not in text:
        print(f"ERROR: {DB_PATH.name} should contain `{DB_PREFIX}{{...}};`. "
              "Nothing was changed.", file=sys.stderr)
        sys.exit(1)
    body = text.split(DB_PREFIX, 1)[1].strip().rstrip(";")
    try:
        return json.loads(body)
    except json.JSONDecodeError as e:
        print(f"ERROR: {DB_PATH.name} isn't valid JSON (line {e.lineno}, column "
              f"{e.colno}: {e.msg}). Fix that first; nothing was changed.", file=sys.stderr)
        sys.exit(1)


def sync(db, found, update):
    """Merges BNI's people into db["people"]. Returns a list of report lines."""
    people = db["people"]
    by_id = {p.get("id"): p for p in people}
    by_name = {p.get("name", "").lower(): p for p in people}
    report = {"added": [], "filled": [], "updated": [], "differs": [], "refreshed": [],
              "missing": [], "disabled": [], "newRoles": []}

    for rec in found.values():
        existing = by_id.get(rec["id"]) or by_name.get(rec["name"].lower())
        if not existing:
            people.append(rec)
            report["added"].append(f"{rec['name']} ({'enabled' if rec['enabled'] else 'disabled, leadership only'})")
            continue

        # Records added by hand might not have every field yet.
        for field in RECORD_FIELDS:
            existing.setdefault(field, FIELD_DEFAULTS.get(field, ""))
        if existing["id"] != rec["id"] and existing["id"].startswith("name:"):
            existing["id"] = rec["id"]

        for field in BNI_FIELDS:
            ours, theirs = existing[field], rec[field]
            if not theirs or ours == theirs:
                continue
            if not ours:
                existing[field] = theirs
                report["filled"].append(f"{existing['name']}: {field} = {theirs}")
            elif update:
                existing[field] = theirs
                report["updated"].append(f"{existing['name']}: {field} {ours!r} -> {theirs!r}")
            else:
                report["differs"].append(f"{existing['name']}: {field} is {ours!r}, BNI has {theirs!r}")

        # Roles: an empty list is filled in; a different one (including BNI
        # no longer listing a role) is reported, or taken with --update.
        ours, theirs = existing["roles"], rec["roles"]
        if set(ours) != set(theirs):
            if not ours:
                existing["roles"] = theirs
                report["filled"].append(f"{existing['name']}: roles = {theirs}")
            elif update:
                existing["roles"] = theirs
                report["updated"].append(f"{existing['name']}: roles {ours} -> {theirs}")
            else:
                report["differs"].append(f"{existing['name']}: roles are {ours}, BNI has {theirs}")

        for field in MIRROR_FIELDS:
            if existing[field] != rec[field]:
                report["refreshed"].append(f"{existing['name']}: {field}")
                existing[field] = rec[field]

        if rec["enabled"] and not existing["enabled"]:
            report["disabled"].append(existing["name"])

    found_ids = set(found)
    for p in people:
        if p["enabled"] and p["id"] not in found_ids:
            report["missing"].append(p["name"])

    return report


def add_new_roles(db, leadership_sections, report):
    """Adds any role BNI shows that the roles table doesn't have yet, under
    BNI's section heading, with no cap."""
    known = {r["role"] for r in db["roles"]}
    for section in leadership_sections:
        for p in section["people"]:
            for title in p["titles"]:
                if title not in known:
                    known.add(title)
                    db["roles"].append({"role": title, "section": section["section"], "max": None})
                    report["newRoles"].append(f"{title} (section: {section['section']}, no cap)")


def print_report(report, update):
    labels = [
        ("added", "New, added to the database"),
        ("filled", "Empty fields filled in from BNI"),
        ("updated", "Changed to BNI's value (--update)"),
        ("differs", "Different on BNI, kept yours (re-run with --update to take BNI's)"),
        ("refreshed", "BNI photo/links refreshed"),
        ("missing", "Enabled but no longer on BNI (set \"enabled\": false if they left)"),
        ("disabled", "On BNI's member list but disabled in the database"),
        ("newRoles", "New roles added to the roles table (set \"max\" if it has a cap)"),
    ]
    any_output = False
    for key, label in labels:
        if report[key]:
            any_output = True
            print(f"\n{label}:")
            for line in report[key]:
                print(f"  - {line}")
    if not any_output:
        print("\nEveryone on BNI is already in the database and up to date.")


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--dry-run", action="store_true", help="report only, don't write members.js")
    parser.add_argument("--update", action="store_true", help="overwrite fields that differ from BNI")
    args = parser.parse_args()

    db = load_db()

    print(f"Fetching chapter data from {BASE_URL}{ENDPOINT} ...")
    html = fetch_chapter_html()

    leadership = parse_leadership(html)
    members = parse_members(html)

    if not members:
        print("ERROR: parsed zero members — BNI likely changed their page "
              "structure and the regexes in this script need updating. "
              "Not changing members.js.", file=sys.stderr)
        sys.exit(1)

    leadership_count = sum(len(s["people"]) for s in leadership)
    print(f"Parsed {len(members)} members and {leadership_count} leadership "
          f"entries across {len(leadership)} section(s).")

    db.setdefault("roles", [])
    found = found_on_bni(members, leadership)
    report = sync(db, found, args.update)
    add_new_roles(db, leadership, report)
    print_report(report, args.update)

    db["people"] = sorted(
        ({f: p.get(f, FIELD_DEFAULTS.get(f, "")) for f in RECORD_FIELDS} | p for p in db["people"]),
        key=lambda p: p["name"].lower(),
    )
    db["lastSynced"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    output = {"lastSynced": db["lastSynced"], "roles": db["roles"], "people": db["people"]}

    if args.dry_run:
        print("\n--dry-run: nothing written.")
        return

    DB_PATH.write_text(
        DB_HEADER + "\n" + DB_PREFIX + json.dumps(output, indent=2, ensure_ascii=False) + ";\n",
        encoding="utf-8",
    )
    print(f"\nWrote {DB_PATH}")


if __name__ == "__main__":
    main()
