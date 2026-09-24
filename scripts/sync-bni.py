#!/usr/bin/env python3
"""
Pulls the current member + leadership roster from the chapter's public BNI
page and regenerates data/members-auto.js.

Run this whenever the roster changes (new member, someone updates their BNI
Connect photo, a title changes hands, etc):

    python scripts/sync-bni.py

This only touches data/members-auto.js. Anything you've entered by hand in
data/overrides.js is untouched and always wins over what's fetched here — so
re-running this is always safe.

Why a script instead of the page fetching this itself: BNI's server doesn't
send CORS headers, so a browser on your own domain is blocked from reading
the response directly (this is BNI's restriction, not something we can work
around from client-side JS). Running the fetch here, server-side, sidesteps
that — there's no CORS restriction on a script you run yourself.
"""

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

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "members-auto.js"

DEFAULT_PHOTO = "https://bniconnectglobal.com/web/images/default_profile.gif"


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
            })

        if people:
            sections.append({"section": section_name, "people": merge_duplicate_people(people)})

    return sections


def shorten_title(new_title, existing_titles):
    # BNI spells a specialty title as "Membership Committee - Quality
    # Assurance" — if "Membership Committee" is already one of this
    # person's titles, showing both in full repeats the shared prefix
    # ("Membership Committee · Membership Committee - Quality Assurance").
    # Trim to just the part after the separator in that case.
    for existing in existing_titles:
        prefix = existing + " - "
        if new_title.startswith(prefix):
            return new_title[len(prefix):]
    return new_title


def merge_duplicate_people(people):
    # BNI renders one card per (person, title) pair — someone on the
    # Membership Committee with a second specialty title shows up twice.
    # Fold those into a single card with multiple titles instead.
    merged = []
    by_name = {}
    for person in people:
        if person["name"] in by_name:
            existing = by_name[person["name"]]
            for title in person["titles"]:
                short_title = shorten_title(title, existing["titles"])
                if short_title not in existing["titles"]:
                    existing["titles"].append(short_title)
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
        if not name_m:
            continue

        category_raw = strip_tags(tds[2]) if len(tds) > 2 else ""
        category = category_raw.split(">")[-1].strip() if category_raw else ""

        members.append({
            "name": name_m.group(1).strip(),
            "company": strip_tags(tds[1]).strip() if len(tds) > 1 else "",
            "category": category,
            "phone": strip_tags(tds[3]).strip() if len(tds) > 3 else "",
            "companyUrl": "",
            "photo": DEFAULT_PHOTO,
            "memberId": urllib.parse.unquote(member_m.group(1)) if member_m else "",
        })

    return members


def enrich_members_from_leadership(members, leadership_sections):
    # The member table has no photos/company links; the leadership cards do.
    # Where a person appears in both, borrow the richer leadership fields.
    lookup = {}
    for section in leadership_sections:
        for person in section["people"]:
            lookup[person["name"]] = person

    for member in members:
        extra = lookup.get(member["name"])
        if not extra:
            continue
        if extra["photo"] and extra["photo"] != DEFAULT_PHOTO:
            member["photo"] = extra["photo"]
        if extra["companyUrl"]:
            member["companyUrl"] = extra["companyUrl"]

    return members


def to_js(value, indent=0):
    pad = "  " * indent
    pad_in = "  " * (indent + 1)

    if isinstance(value, dict):
        if not value:
            return "{}"
        lines = ["{"]
        for k, v in value.items():
            lines.append(f'{pad_in}{json.dumps(k)}: {to_js(v, indent + 1)},')
        lines.append(pad + "}")
        return "\n".join(lines)

    if isinstance(value, list):
        if not value:
            return "[]"
        lines = ["["]
        for item in value:
            lines.append(f"{pad_in}{to_js(item, indent + 1)},")
        lines.append(pad + "]")
        return "\n".join(lines)

    return json.dumps(value)


def main():
    print(f"Fetching chapter data from {BASE_URL}{ENDPOINT} ...")
    html = fetch_chapter_html()

    leadership = parse_leadership(html)
    members = parse_members(html)
    members = enrich_members_from_leadership(members, leadership)

    if not members:
        print("ERROR: parsed zero members — BNI likely changed their page "
              "structure and the regexes in this script need updating. "
              "Not overwriting members-auto.js.", file=sys.stderr)
        sys.exit(1)

    leadership_count = sum(len(s["people"]) for s in leadership)
    print(f"Parsed {len(members)} members and {leadership_count} leadership "
          f"entries across {len(leadership)} section(s).")

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    output = f"""/**
 * AUTO-GENERATED by scripts/sync-bni.py — do not hand-edit.
 * Last synced: {generated_at}
 *
 * To refresh: python scripts/sync-bni.py
 * To fix/add something this doesn't have (a missing company link, a
 * corrected photo, an email address), do NOT edit this file — put it in
 * data/overrides.js instead. Overrides always win and survive re-syncs.
 */

window.BNI_AUTO = {{
  generatedAt: {json.dumps(generated_at)},
  members: {to_js(members, 1)},
  leadership: {to_js(leadership, 1)}
}};
"""

    OUTPUT_PATH.write_text(output, encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
