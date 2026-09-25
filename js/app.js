/**
 * Renders the page from three data sources, loaded before this script:
 *   - data/site-data.js     chapter info, this week, rotation (hand-edited)
 *   - data/members-auto.js  member + leadership roster (auto-fetched by
 *                           scripts/sync-bni.py — do not hand-edit)
 *   - data/overrides.js     manual per-person corrections/additions
 *                           (hand-edited, always wins, survives re-syncs)
 *
 * No build step, no framework — plain DOM.
 */
(function () {
  try {
  const siteData = window.SITE_DATA;
  const auto = window.BNI_AUTO;
  const overrides = window.SITE_OVERRIDES || { members: {}, leadership: {} };

  if (!siteData) throw new Error("SITE_DATA not found — is data/site-data.js loaded?");
  if (!auto) throw new Error("BNI_AUTO not found — run `python scripts/sync-bni.py`, or is data/members-auto.js loaded?");

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

  /* ---------------- Merge auto-fetched roster with manual overrides ---------------- */
  // Only fields present in the override object are changed; everything else
  // keeps whatever sync-bni.py fetched from BNI.

  function mergePerson(person, override) {
    return override ? { ...person, ...override } : person;
  }

  const members = auto.members.map((m) => mergePerson(m, overrides.members[m.name]));

  const leadership = auto.leadership.map((section) => ({
    section: section.section,
    people: section.people.map((p) => mergePerson(p, overrides.leadership[p.name])),
  }));

  // A single name -> {photo, companyUrl} lookup, used to auto-fill This
  // Week's trophy winner / speakers so you only have to type a name there.
  const directory = {};
  members.forEach((m) => { directory[m.name] = m; });
  leadership.forEach((section) => section.people.forEach((p) => {
    if (!directory[p.name]) directory[p.name] = p;
  }));

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

  const tw = resolvePerson(siteData.thisWeek.trophyWinner);
  $("#trophy-winner").innerHTML = `
    <img class="avatar" src="${esc(tw.photo)}" alt="${esc(tw.name)}">
    <div>
      <p class="person-name">${esc(tw.name)}</p>
      <p class="person-company">${tw.companyUrl ? `<a href="${esc(tw.companyUrl)}" target="_blank" rel="noopener">${esc(tw.company)}</a>` : esc(tw.company)}</p>
      ${siteData.thisWeek.trophyWinner.note ? `<p class="person-note">${esc(siteData.thisWeek.trophyWinner.note)}</p>` : ""}
    </div>
  `;

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

  // Company name renders as a link when we have a URL (fetched from BNI or
  // supplied in data/overrides.js) and as plain unlinked text when we don't.
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
