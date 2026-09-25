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
 *  2. Update the `thisWeek` block: meetingDateLabel, trophyWinner,
 *     quoteOfWeek (+ optional quoteAuthor), speakers, metrics.
 *  3. Add new speaker dates to the bottom of `rotation`. Past dates are
 *     hidden on the site automatically, so deleting old rows is optional
 *     housekeeping.
 *  4. Save. Refresh the browser tab. That's it — no build step.
 *
 *  TROPHY WINNER / SPEAKERS — you only need `name` and `company`.
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
    trophyWinner: {
      name: "Peter Hamilton",
      company: "Mirick O'Connell",
      note: "Congratulations, Peter!"
    },
    quoteOfWeek: "Every problem is a gift, without problems we would not grow.",
    quoteAuthor: "Tony Robbins",
    speakers: [
      { name: "Raphael Guimaraes", company: "SumZero Energy Systems" },
      { name: "Brendon Mourao", company: "Ikonera" }
    ],
    metrics: {
      asOf: "09/18/2026",
      ytdSince: "October 1st",
      tyfcb:      { label: "TYFCB",      prefix: "$", lastWeek: 35600, ytd: 837970, goal: 1000000 },
      oneToOnes:  { label: "1-to-1's",   prefix: "",  lastWeek: 18,    ytd: 689,    goal: 2500 },
      ceus:       { label: "CEUs",       prefix: "",  lastWeek: 3,     ytd: 698,    goal: 2400 },
      referrals:  { label: "Referrals",  prefix: "",  lastWeek: null,  ytd: null,   goal: null }
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
