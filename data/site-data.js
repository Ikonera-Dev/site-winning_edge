/**
 * ============================================================================
 *  BNI WINNING EDGE — SITE CONTENT
 * ============================================================================
 *  This is the file you touch every Friday. It holds the chapter info, this
 *  week's meeting recap, and the upcoming speaker rotation.
 *
 *  The member directory and leadership team are NOT in this file — they
 *  live in the member database, data/members.js (kept in sync with BNI by
 *  `python3 scripts/sync-bni.py`; edit it directly for anything BNI doesn't
 *  have, like a missing company link or an email).
 *
 *  HOW TO UPDATE EACH WEEK
 *  ------------------------------------------------------------------------
 *  1. Open the weekly BNI email (the .oft/.eml Outlook file, or whatever
 *     Friday recap you send out).
 *  2. Update the `thisWeek` block (meetingDateLabel, trophyNote,
 *     speakers), the `quote`, and the `palms` report (see its comment).
 *     The trophy winner itself is picked in data/members.js: move
 *     "trophyWinner": true to the winner's record (false on everyone else).
 *  3. Add new speaker dates to the bottom of `rotation`. Past dates are
 *     hidden on the site automatically, so deleting old rows is optional
 *     housekeeping.
 *  4. Save. Refresh the browser tab. That's it — no build step.
 *
 *  SPEAKERS — you only need `name` and `company`.
 *  ------------------------------------------------------------------------
 *  Their photo and company link are looked up automatically by matching
 *  `name` against the member database (data/members.js), so most
 *  weeks that's all you type. If a speaker is a visitor/not a chapter
 *  member (so there's nothing to match), you can add `photo` and
 *  `companyUrl` directly here and they'll be used as-is.
 * ============================================================================
 */

window.SITE_DATA = {

  chapter: {
    name: "BNI Winning Edge",
    region: "BNI Northeast Massachusetts",
    logo: "https://fcebsch.stripocdn.email/content/guids/CABINET_ba47cec0c6e108c64ef7caa6808463230f2a50304d6371bebf24351c9946f48c/images/bni_logo_red_pms_final.png",
    tagline: "Givers Gain — Framingham's weekly referral marketing chapter",
    meeting: {
      day: "Friday",
      time: "7:00 AM – 8:30 AM",
      format: "In-Person",
      venue: "St. Andrews Church",
      address: "3 Maple Street, Framingham, MA 01702",
      mapUrl: "https://goo.gl/maps/VLPn3aZJpQ32",
      parkingNote: "Please park in the main parking lot, to the left of the church's main entrance, which also leads into the chapter's meeting room."
    },
    social: {
      facebook: "https://www.facebook.com/BNIWinningEdgeMA/",
      instagram: "https://www.instagram.com/bniwinningedge/"
    },
    dues: {
      amount: "$75 / quarter",
      venmo: "@BniWinningEdge",
      note: "Due in the first 2 weeks of each quarter. Venmo $75 to @BniWinningEdge (search businesses, not individuals) or bring a check made out to BNI Winning Edge.",
      treasurerName: "Matt Cuneo"
    },
    policies: [
      "Bring a door prize ($20–$25 value) on the week you present — or it's a $5 fine.",
      "Meetings run 90 minutes. Networking starts at 7:00 AM; doors close at 7:15 AM. Arriving after doors close means forfeiting your 45-second commercial for a testimonial instead.",
      "Members should stay until 8:30 AM or the end of the meeting, whichever comes first.",
      "Can't make your speaking date? Find someone to swap with and let Leadership know so the rotation can be updated."
    ]
  },

  /**
   * THIS WEEK — replace every field each Friday.
   */
  thisWeek: {
    meetingDateLabel: "September 25th, 2026",
    trophyNote: "Congratulations, Peter!",
    speakers: [
      { name: "Raphael Guimaraes", company: "SumZero Energy Systems" },
      { name: "Brendon Mourao", company: "Ikonera" }
    ]
  },

  /**
   * QUOTE OF THE WEEK
   *   text    what was said (no quotation marks, the site adds them)
   *   author  who said it; "" to leave the attribution off
   */
  quote: {
    text: "Every problem is a gift, without problems we would not grow.",
    author: "Tony Robbins"
  },

  /**
   * PALMS REPORT
   *   asOf      date of the report, written YYYY-MM-DD (shown as MM/DD/YYYY)
   *   ytdSince  start of the reporting year, as shown on the site
   *   metrics   one entry per stat tile, shown in this order:
   *     ytd          year-to-date total from this week's report
   *     lastWeekYtd  the year-to-date total from LAST week's report. Not
   *                  shown; the site shows ytd − lastWeekYtd as
   *                  "+X since last week".
   *     goal         full-year goal; the meter shows ytd as a % of it
   *     label, prefix  tile title and value prefix ("$" for money)
   *   Use null for anything not reported.
   *
   *   Each week: copy every `ytd` into `lastWeekYtd`, then type the new
   *   `ytd` numbers and `asOf` date. Or let the script do it:
   *     python3 scripts/palms.py new-week     (asks for each number)
   *   It rewrites this block only, so keep one metric per line.
   */
  palms: {
    asOf: "2026-09-18",
    ytdSince: "October 1st",
    metrics: {
      tyfcb:     { label: "TYFCB",     prefix: "$", ytd: 837970, lastWeekYtd: 802370, goal: 1000000 },
      oneToOnes: { label: "1-to-1's",  prefix: "",  ytd: 689,    lastWeekYtd: 671,    goal: 2500 },
      ceus:      { label: "CEUs",      prefix: "",  ytd: 698,    lastWeekYtd: 695,    goal: 2400 },
      referrals: { label: "Referrals", prefix: "",  ytd: null,   lastWeekYtd: null,   goal: null }
    }
  },

  /**
   * ROTATION — upcoming presenter lineup. Add new rows at the bottom.
   * Write dates as "Month Day" (e.g. "October 2"). Dates before today are
   * hidden automatically; delete old rows whenever convenient.
   */
  rotation: [
    { date: "September 25", speakers: "Raphael G. / Brendon M." },
    { date: "October 2",    speakers: "Adam B. / Clif N." },
    { date: "October 9",    speakers: "Matt C. / Ian M." },
    { date: "October 16",   speakers: "Peter H. / Mike S." },
    { date: "October 23",   speakers: "Chris F. / Joe N." },
    { date: "October 30",   speakers: "Jeremy C. / Peter E." },
    { date: "November 6",   speakers: "Chris M. / Jake S." }
  ]
};
