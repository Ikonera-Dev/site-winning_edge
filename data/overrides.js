/**
 * ============================================================================
 *  MANUAL OVERRIDES — this file is yours, sync-bni.py never touches it.
 * ============================================================================
 *  data/members-auto.js is regenerated every time you run the sync script,
 *  so anything you typed directly into it gets thrown away on the next
 *  sync. Put manual corrections/additions here instead — they're applied on
 *  top of the auto-fetched data every time the page loads, and survive
 *  re-syncs.
 *
 *  Common reasons to add an entry:
 *    - BNI doesn't have a company website on file for someone (shows as
 *      unlinked plain text) but you know it — add `companyUrl` here.
 *    - You want to add an email address (BNI Connect doesn't expose these
 *      publicly, so this file is the only place they can come from).
 *    - A photo on BNI Connect is wrong/outdated and you have a better one.
 *    - A title or company name is slightly off and you want to fix the
 *      display without waiting on BNI Connect to be updated.
 *
 *  HOW IT WORKS
 *  ------------------------------------------------------------------------
 *  Key each entry by the person's name EXACTLY as it appears in
 *  data/members-auto.js (open that file and copy the "name" value — safest
 *  way to avoid a silent typo-mismatch). Only include the fields you want
 *  to change; anything you leave out keeps whatever sync-bni.py fetched.
 *
 *  `members` overrides apply on the Members tab. `leadership` overrides
 *  apply on the Leadership tab. If someone appears in both places and you
 *  want the fix in both, add them under both keys.
 *
 *  EXAMPLE (remove the /* * / comment markers to activate):
 *
 *  window.SITE_OVERRIDES = {
 *    members: {
 *      "Christopher Mingace": {
 *        companyUrl: "https://www.hbmhlaw.com",
 *        email: "cmingace@hbmhlaw.com"
 *      }
 *    },
 *    leadership: {
 *      "Ian McCarthy": {
 *        companyUrl: "https://www.unitedhomeexperts.com"
 *      }
 *    }
 *  };
 * ============================================================================
 */

window.SITE_OVERRIDES = {
  members: {},
  leadership: {}
};
