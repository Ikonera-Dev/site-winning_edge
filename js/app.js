/**
 * Renders the page from two data sources, loaded before this script:
 *   - data/site-data.js  chapter info, this week, rotation (hand-edited)
 *   - data/members.js    member database + leadership roles (kept in sync
 *                        with BNI by scripts/sync-bni.py, safe to hand-edit)
 *
 * No build step, no framework — plain DOM.
 */
(function () {
  try {
  const siteData = window.SITE_DATA;
  const db = window.MEMBERS_DB;

  if (!siteData) throw new Error("SITE_DATA not found — is data/site-data.js loaded?");
  if (!db) throw new Error("MEMBERS_DB not found — is data/members.js loaded? Run `python3 scripts/sync-bni.py` to create it.");

  const DEFAULT_PHOTO = "https://bniconnectglobal.com/web/images/default_profile.gif";

  const $ = (sel, root) => (root || document).querySelector(sel);

  function esc(str) {
    if (str === null || str === undefined) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  function formatNumber(n) {
    if (n === null || n === undefined) return null;
    return n.toLocaleString("en-US");
  }

  function statValue(metric) {
    if (metric.ytd === null || metric.ytd === undefined) return null;
    return `${metric.prefix || ""}${formatNumber(metric.ytd)}`;
  }

  /* ---------------- Member database ---------------- */
  // Every person in data/members.js, addressable by id. `photo` is the
  // chosen image (a file in img/members/ or a URL); when it's empty the
  // BNI Connect photo is used, then BNI's default silhouette.

  const people = db.people.map((p) => ({ ...p, photo: p.photo || p.bniPhoto || DEFAULT_PHOTO }));
  const byId = {};
  people.forEach((p) => { byId[p.id] = p; });

  // The Members grid shows only enabled people.
  const members = people.filter((p) => p.enabled);

  // Chapter Leadership is built from each person's `roles`. The roles table
  // gives every role its section and order: sections appear in the order of
  // their first role, and people within a section by their highest-listed
  // role, then by name. Everyone with a role is listed, enabled or not.
  const roleOrder = {};
  const roleSection = {};
  db.roles.forEach((r, i) => { roleOrder[r.role] = i; roleSection[r.role] = r.section; });

  // A role with a `max` is shown on at most that many people. If the file
  // has more (the sync script normally fixes this from live BNI), the ones
  // BNI listed at the last sync (`bniHolders`) win, then alphabetical.
  const hiddenRoles = new Set(); // "personId|role" pairs over the cap
  db.roles.forEach((r) => {
    if (r.max === null || r.max === undefined) return;
    const bniRank = (p) => { const i = (r.bniHolders || []).indexOf(p.id); return i < 0 ? Infinity : i; };
    const holders = people.filter((p) => (p.roles || []).includes(r.role))
      .sort((a, b) => bniRank(a) - bniRank(b) || a.name.localeCompare(b.name));
    if (holders.length <= r.max) return;
    const extra = holders.slice(r.max);
    extra.forEach((p) => hiddenRoles.add(`${p.id}|${r.role}`));
    console.warn(`"${r.role}" allows ${r.max}, ${holders.length} have it. Not showing it for: ${extra.map((p) => p.name).join(", ")}. Run scripts/sync-bni.py to fix.`);
  });

  const OTHER_SECTION = "Leadership"; // for a role missing from the roles table
  const sectionOf = (role) => roleSection[role] || OTHER_SECTION;
  const sectionNames = [...new Set(db.roles.map((r) => r.section))];

  people.forEach((p) => (p.roles || []).forEach((role) => {
    if (!(role in roleSection)) {
      console.warn(`"${role}" (${p.name}) isn't in the roles table in data/members.js`);
      if (!sectionNames.includes(OTHER_SECTION)) sectionNames.push(OTHER_SECTION);
    }
  }));

  // BNI spells a specialty title as "Membership Committee - Quality
  // Assurance". When the same person also holds "Membership Committee",
  // show just "Quality Assurance" rather than repeating the prefix.
  function displayTitles(roles) {
    const shown = [];
    roles.forEach((role) => {
      const parent = roles.find((other) => role.startsWith(other + " - "));
      shown.push(parent ? role.slice(parent.length + 3) : role);
    });
    return shown;
  }

  const rank = (role) => (role in roleOrder ? roleOrder[role] : Infinity);

  const leadership = sectionNames.map((section) => ({
    section,
    people: people
      .map((p) => {
        const roles = (p.roles || [])
          .filter((role) => sectionOf(role) === section && !hiddenRoles.has(`${p.id}|${role}`))
          .sort((a, b) => rank(a) - rank(b));
        return roles.length ? { ...p, titles: displayTitles(roles), rank: rank(roles[0]) } : null;
      })
      .filter(Boolean)
      .sort((a, b) => a.rank - b.rank || a.name.localeCompare(b.name)),
  })).filter((section) => section.people.length);

  // A single name -> {photo, companyUrl} lookup, used to auto-fill This
  // Week's speakers so you only have to type a name there.
  const directory = {};
  people.forEach((p) => { directory[p.name] = p; });

  function resolvePerson(entry) {
    const known = directory[entry.name];
    return {
      name: entry.name,
      company: entry.company || (known && known.company) || "",
      companyUrl: entry.companyUrl || (known && known.companyUrl) || "",
      photo: entry.photo || (known && known.photo) || DEFAULT_PHOTO,
    };
  }

  /* ---------------- Header / hero / footer ---------------- */

  document.title = `${siteData.chapter.name} | ${siteData.chapter.region}`;
  $("#chapter-name").textContent = siteData.chapter.name;
  $("#chapter-tagline").textContent = siteData.chapter.tagline;
  $("#footer-chapter-name").textContent = siteData.chapter.name;
  $("#footer-region").textContent = siteData.chapter.region;

  const m = siteData.chapter.meeting;
  $("#hero-meeting").innerHTML = `
    <span><strong>${esc(m.day)}s</strong> · ${esc(m.time)}</span>
    <span>${esc(m.format)}</span>
    <span>${esc(m.venue)}, ${esc(m.address.split(",")[1] || "")}</span>
  `;

  $("#visit-meeting-line").textContent = `${m.day}s, ${m.time} — ${m.format}`;
  $("#visit-address").innerHTML = `<strong>${esc(m.venue)}</strong><br>${esc(m.address)}`;
  $("#visit-parking").textContent = m.parkingNote;
  $("#visit-map-link").href = m.mapUrl;

  const policiesList = $("#policies-list");
  siteData.chapter.policies.forEach((p) => {
    const li = document.createElement("li");
    li.textContent = p;
    policiesList.appendChild(li);
  });

  const social = siteData.chapter.social;
  const socialLinks = [];
  if (social.facebook) socialLinks.push(`<a href="${esc(social.facebook)}" target="_blank" rel="noopener">Facebook</a>`);
  if (social.instagram) socialLinks.push(`<a href="${esc(social.instagram)}" target="_blank" rel="noopener">Instagram</a>`);
  $("#footer-social").innerHTML = socialLinks.join("");

  $("#footer-dues").innerHTML = `<strong style="color:#fff">Dues:</strong> ${esc(siteData.chapter.dues.note)}`;

  /* ---------------- This Week ---------------- */

  $("#this-week-date").textContent = `Meeting of ${siteData.thisWeek.meetingDateLabel}`;

  // The trophy winner is whoever has "trophyWinner": true in data/members.js.
  // Everyone flagged is shown; the note comes from site-data.js.
  const trophyWinners = people.filter((p) => p.trophyWinner);
  const trophyNote = siteData.thisWeek.trophyNote;
  $("#trophy-winner").innerHTML = trophyWinners.length
    ? trophyWinners.map((tw) => `
      <img class="avatar" src="${esc(tw.photo)}" alt="${esc(tw.name)}">
      <div>
        <p class="person-name">${esc(tw.name)}</p>
        <p class="person-company">${companyLine(tw)}</p>
        ${trophyNote ? `<p class="person-note">${esc(trophyNote)}</p>` : ""}
      </div>
    `).join("")
    : `<p class="muted">No trophy winner selected this week.</p>`;

  const quoteEl = $("#quote-of-week");
  quoteEl.textContent = `“${siteData.thisWeek.quoteOfWeek}”`;
  if (siteData.thisWeek.quoteAuthor) {
    const cite = document.createElement("cite");
    cite.textContent = `— ${siteData.thisWeek.quoteAuthor}`;
    quoteEl.appendChild(cite);
  }

  const speakersEl = $("#this-week-speakers");
  speakersEl.innerHTML = siteData.thisWeek.speakers.map(resolvePerson).map((s) => `
    <div class="person">
      <img class="avatar" src="${esc(s.photo)}" alt="${esc(s.name)}">
      <div>
        <p class="person-name">${esc(s.name)}</p>
        <p class="person-company">${s.companyUrl ? `<a href="${esc(s.companyUrl)}" target="_blank" rel="noopener">${esc(s.company)}</a>` : esc(s.company)}</p>
      </div>
    </div>
  `).join("");

  /* ---------------- PALMS stat meters ---------------- */

  $("#palms-asof").textContent = `— as of ${siteData.thisWeek.metrics.asOf} · YTD since ${siteData.thisWeek.metrics.ytdSince}`;

  const metricKeys = ["tyfcb", "oneToOnes", "ceus", "referrals"];
  const statsEl = $("#palms-stats");
  statsEl.innerHTML = metricKeys.map((key) => {
    const metric = siteData.thisWeek.metrics[key];
    const value = statValue(metric);

    if (value === null) {
      return `
        <div class="stat-tile">
          <p class="stat-label">${esc(metric.label)}</p>
          <p class="stat-empty">Not reported this week</p>
        </div>
      `;
    }

    const pct = metric.goal ? Math.max(0, Math.min(100, (metric.ytd / metric.goal) * 100)) : 0;
    const lastWeekStr = metric.lastWeek !== null && metric.lastWeek !== undefined
      ? `Last week: ${metric.prefix || ""}${formatNumber(metric.lastWeek)}`
      : "";

    return `
      <div class="stat-tile">
        <p class="stat-label">${esc(metric.label)}</p>
        <p class="stat-value">${value}</p>
        ${lastWeekStr ? `<p class="stat-delta">${lastWeekStr}</p>` : ""}
        ${metric.goal ? `
          <div class="meter-track"><div class="meter-fill" style="width:${pct}%"></div></div>
          <p class="stat-goal">${pct.toFixed(0)}% of ${metric.prefix || ""}${formatNumber(metric.goal)} goal</p>
        ` : ""}
      </div>
    `;
  }).join("");

  /* ---------------- Rotation ---------------- */

  // Rotation dates are written without a year ("October 2"). Each one is read
  // as whichever of last/this/next year puts it closest to today, so January
  // rows added in December count as upcoming and last fall's leftover rows
  // count as past. Rows before today are hidden; today's stays visible all day.
  function rotationDate(label, today) {
    if (!/^[A-Za-z]+\.? \d{1,2}$/.test(String(label).trim())) return null;
    const y = today.getFullYear();
    const candidates = [y - 1, y, y + 1].map((year) => new Date(`${label} ${year}`));
    if (isNaN(candidates[0])) return null;
    return candidates.reduce((best, d) =>
      Math.abs(d - today) < Math.abs(best - today) ? d : best);
  }

  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const upcoming = siteData.rotation.filter((row) => {
    const d = rotationDate(row.date, today);
    return d === null || d >= today; // an unparseable label is shown, not dropped
  });

  const rotationBody = $("#rotation-body");
  rotationBody.innerHTML = upcoming.length
    ? upcoming.map((row) => `
        <tr><td>${esc(row.date)}</td><td>${esc(row.speakers)}</td></tr>
      `).join("")
    : `<tr><td colspan="2" class="muted">The next rotation will be posted soon.</td></tr>`;

  /* ---------------- Leadership ---------------- */

  // Always shows all three (Call / Website / Email) so gaps are visible at a
  // glance for later follow-up — a missing one renders as a greyed,
  // unclickable placeholder instead of disappearing.
  function contactItem(label, href, title) {
    return href
      ? `<a href="${esc(href)}"${href.startsWith("http") ? ' target="_blank" rel="noopener"' : ""}>${label}</a>`
      : `<span class="contact-missing" title="${esc(title)}">${label}</span>`;
  }

  function contactRow(person) {
    const items = [
      contactItem("Call", person.phone ? `tel:${person.phone.replace(/[^0-9+]/g, "")}` : "", "No phone number on file"),
      contactItem("Website", person.companyUrl || "", "No company website on file"),
      contactItem("Email", person.email ? `mailto:${person.email}` : "", "No email on file"),
    ];
    return `<div class="contact-row">${items.join("")}</div>`;
  }

  // Company name renders as a link when we have a URL (from BNI or added by
  // hand in data/members.js) and as plain unlinked text when we don't.
  function companyLine(person) {
    return person.companyUrl
      ? `<a href="${esc(person.companyUrl)}" target="_blank" rel="noopener">${esc(person.company)}</a>`
      : esc(person.company);
  }

  const leadershipPanel = $("#leadership-panel");
  leadershipPanel.innerHTML = leadership.map((section) => `
    <div class="leadership-section">
      <h3>${esc(section.section)}</h3>
      <div class="leader-grid">
        ${section.people.map((p) => `
          <div class="leader-card">
            <img class="avatar" src="${esc(p.photo)}" alt="${esc(p.name)}">
            <p class="person-name">${esc(p.name)}</p>
            <p class="titles">${p.titles.map(esc).join(" · ")}</p>
            <p class="person-company">${companyLine(p)}</p>
            ${contactRow(p)}
          </div>
        `).join("")}
      </div>
    </div>
  `).join("");

  /* ---------------- Members ---------------- */

  const membersGrid = $("#members-grid");
  const sortedMembers = [...members].sort((a, b) => a.name.localeCompare(b.name));
  membersGrid.innerHTML = sortedMembers.map((mem) => `
    <div class="member-card">
      <img class="avatar" src="${esc(mem.photo)}" alt="${esc(mem.name)}">
      <div>
        <p class="person-name">${esc(mem.name)}</p>
        <p class="person-company">${companyLine(mem)}</p>
        <p class="category">${esc(mem.category)}</p>
        ${contactRow(mem)}
      </div>
    </div>
  `).join("");

  /* ---------------- Tabs ---------------- */

  const tabButtons = document.querySelectorAll(".tab-btn");
  const tabPanels = document.querySelectorAll(".tab-panel");
  tabButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      tabButtons.forEach((b) => { b.classList.remove("active"); b.setAttribute("aria-selected", "false"); });
      tabPanels.forEach((p) => p.classList.remove("active"));
      btn.classList.add("active");
      btn.setAttribute("aria-selected", "true");
      $(`[data-panel="${btn.dataset.tab}"]`).classList.add("active");
    });
  });
  } catch (err) {
    // A typo in one of the data files shouldn't leave editors staring at a blank page.
    const banner = document.createElement("pre");
    banner.style.cssText = "position:fixed;top:0;left:0;right:0;z-index:9999;background:#fff3f3;color:#a00;padding:12px;white-space:pre-wrap;font-size:12px;border-bottom:2px solid red;";
    banner.textContent = "This page couldn't render — check your data files for a syntax error:\n" + err.message;
    document.body.prepend(banner);
    console.error(err);
  }
})();
