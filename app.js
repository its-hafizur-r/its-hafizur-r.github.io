// Renders both pages from data/manual.json (hand-edited) and data/stats.json (daily sync).
const ICONS = {
  kit: '<path d="M4 7h16v12a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V7Z"/><path d="M9 7V5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2"/><path d="M4 12h16"/>',
  tiktok: '<path d="M14 3v11.5a3.5 3.5 0 1 1-3.5-3.5"/><path d="M14 3c.5 2.8 2.4 4.6 5 5"/>',
  instagram: '<rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r=".6" fill="currentColor"/>',
  mail: '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/>',
  link: '<path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1"/><path d="M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1"/>',
  play: '<circle cx="12" cy="12" r="9"/><path d="m10 8.5 5.5 3.5-5.5 3.5v-7Z" fill="currentColor"/>',
  star: '<path d="m12 3 2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1-4.4-4.3 6.1-.9L12 3Z"/>',
  plane: '<path d="M17.8 19.2 16 11l3.5-3.5C21 6 21.5 4 21 3c-1-.5-3 0-4.5 1.5L13 8 4.8 6.2c-.5-.1-.9.1-1.1.5l-.3.5c-.2.5-.1 1 .3 1.3L9 12l-2 3H4l-1 1 3 2 2 3 1-1v-3l3-2 3.5 5.3c.3.4.8.5 1.3.3l.5-.2c.4-.3.6-.7.5-1.2z"/>',
  pin: '<path d="M12 21s-7-6.2-7-11.5a7 7 0 0 1 14 0C19 14.8 12 21 12 21Z"/><circle cx="12" cy="9.5" r="2.5"/>',
  eye: '<path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/>',
  arrow: '<path d="M5 12h14"/><path d="m13 6 6 6-6 6"/>',
  back: '<path d="M19 12H5"/><path d="m11 6-6 6 6 6"/>',
};
const icon = (n) =>
  `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICONS[n] || ICONS.link}</svg>`;

const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const short = (n) => {
  if (n == null) return "–";
  const f = (x, s) => (x >= 100 ? Math.round(x) : Math.round(x * 10) / 10) + s;
  if (n >= 1e6) return f(n / 1e6, "M");
  if (n >= 1e4) return f(n / 1e3, "K");
  if (n >= 1e3) return (Math.round(n / 100) / 10) + "K";
  return String(n);
};
const date = (iso) => (iso ? new Date(iso).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" }) : "");
const $ = (id) => document.getElementById(id);
const fill = (id, html) => { const el = $(id); if (el) el.innerHTML = html; };

async function getJSON(path) {
  try {
    const r = await fetch(path + "?v=" + Date.now().toString().slice(0, -5));
    return r.ok ? await r.json() : {};
  } catch { return {}; }
}

function vidTile(v) {
  const title = (v.title || "").replace(/#\S+/g, "").trim();
  return `
    <a class="vid${v.cover ? "" : " noimg"}" href="${esc(v.url)}" target="_blank" rel="noopener">
      ${v.cover ? `<img src="${esc(v.cover)}" alt="" loading="lazy" onerror="this.remove();this.parentNode.classList.add('noimg')">` : ""}
      ${v.label ? `<span class="style-tag">${esc(v.label)}</span>` : ""}
      <span class="shade"></span>
      <span class="meta">${v.views != null ? `<span class="views">${icon("play")}${short(v.views)}</span>` : ""}<span class="t">${esc(title)}</span></span>
    </a>`;
}

function featured(m, s) {
  const known = Object.fromEntries([...(s.top_videos || []), ...(s.featured || [])].map((v) => [String(v.id), v]));
  const tiles = (m.featured_videos || []).map((f) => {
    const id = (String(f).match(/\d{17,20}/) || [])[0];
    if (!id) return "";
    return vidTile(known[id] || { id, url: `https://www.tiktok.com/@${m.handle}/video/${id}`, title: "Watch on TikTok" });
  }).join("");
  if (!tiles) { $("featured-sec")?.classList.add("hidden"); return; }
  fill("featured-title", esc(m.featured_title || "Watch"));
  fill("featured", tiles);
}

function hero(m) {
  document.querySelectorAll("[data-name]").forEach((el) => (el.textContent = m.name || ""));
  fill("handle", "@" + esc(m.handle));
  fill("tagline", esc(m.tagline));
  fill("place", `<span class="pill">${icon("pin")}${esc(m.location)}</span>`);
}

function bioPage(m, s) {
  const btn = (l) => `
    <a class="link-btn${l.highlight ? " highlight" : ""}" href="${esc(l.url)}"${/^https?:/.test(l.url) ? ' target="_blank" rel="noopener"' : ""}>
      <span class="ic">${icon(l.icon)}</span><span class="lbl">${esc(l.label)}</span><span class="arrow">${icon("arrow")}</span>
    </a>`;
  const all = m.bio_links || [];
  fill("links", all.filter((l) => !l.bottom).map(btn).join(""));
  fill("links-bottom", all.filter((l) => l.bottom).map(btn).join(""));
  featured(m, s);
  const L = m.links || {};
  const icons = [
    ["tiktok", L.tiktok, "TikTok"],
    ["mail", m.email ? "mailto:" + m.email : "", "Email"],
    ["instagram", L.instagram, "Instagram"],
  ].filter((x) => x[1]);
  fill("socials", icons.map(([ic, url, name]) =>
    `<a class="icon-btn" href="${esc(url)}" aria-label="${name}" title="${name}"${/^https?:/.test(url) ? ' target="_blank" rel="noopener"' : ""}>${icon(ic)}</a>`).join(""));
}

function kitPage(m, s) {
  fill("intro", [].concat(m.intro || []).map((x) => `<p>${esc(x)}</p>`).join(""));
  const p = s.profile || {}, r = s.recent || {}, a = m.audience || {};
  const tv = p.total_views != null ? short(p.total_views) + (p.total_views_complete ? "" : "+") : "–";
  const tiles = [
    ["Followers", short(p.followers), true],
    ["Total views", tv],
    ["Total likes", short(p.likes)],
    ["Avg views (last 30 days)", short(r.avg_views)],
    [`Profile views (${esc(a.period || "30 days")})`, short(a.profile_views)],
    [`Impressions (${esc(a.period || "30 days")})`, short(a.impressions)],
  ].filter((t) => t[1] !== "–");
  fill("stats", tiles.map(([l, v, f]) => `<div class="stat${f ? " feature" : ""}"><div class="num">${v}</div><div class="lab">${l}</div></div>`).join(""));
  fill("stats-note", r.videos_counted
    ? `Average views cover the ${r.videos_counted} videos I posted ${date(r.from)} to ${date(r.to)}. Updated ${date(s.updated)}.`
    : "");

  const bars = (rows) => rows.map(([k, v]) => {
    const max = Math.max(...rows.map((x) => x[1]));
    return `<div class="bar-row"><span>${esc(k)}</span><span class="bar"><i style="width:${(v / max) * 100}%"></i></span><b>${v}%</b></div>`;
  }).join("");
  const g = a.gender || {};
  fill("audience", `
    <div class="card"><h3>Top countries</h3>${bars(a.top_countries || [])}</div>
    <div class="card"><h3>Age</h3>${bars(a.age || [])}</div>
    <div class="card"><h3>Gender</h3>
      <div class="split"><i style="width:${g.female || 50}%"></i><i style="width:${g.male || 50}%"></i></div>
      <div class="split-key"><span><span class="dot" style="background:var(--accent)"></span>Female ${g.female ?? "–"}%</span>
      <span><span class="dot" style="background:var(--accent-2)"></span>Male ${g.male ?? "–"}%</span></div>
    </div>`);
  fill("aud-note", a.updated ? `Audience from TikTok analytics, ${esc(a.period || "")}, updated ${date(a.updated)}.` : "");

  fill("videos", (s.top_videos || []).map(vidTile).join(""));

  const known = Object.fromEntries([...(s.top_videos || []), ...(s.featured || [])].map((v) => [String(v.id), v]));
  const styles = (m.style_videos || []).map((x) => {
    const id = (String(x.url || "").match(/\d{17,20}/) || [])[0];
    if (!id) return "";
    const v = known[id] || { id, url: `https://www.tiktok.com/@${m.handle}/video/${id}`, title: "" };
    return vidTile({ ...v, label: x.label });
  }).join("");
  if (styles) { fill("styles-title", esc(m.style_videos_title || "Video styles")); fill("styles", styles); }
  else $("styles-sec")?.classList.add("hidden");

  fill("pillars", (m.pillars || []).map((x) => `<span class="chip">${esc(x)}</span>`).join(""));
  const brands = (m.brands || []).map((b) => (typeof b === "string" ? { name: b } : b));
  fill("brands-title", esc(m.brands_title || "Brands I've worked with"));
  fill("brands", brands.map((b) => {
    const style = b.bg ? ` style="background:${esc(b.bg)};border-color:transparent"` : "";
    const inner = b.logo
      ? `<img src="${esc(b.logo)}" alt="${esc(b.name)}" loading="lazy">` + (b.caption ? `<span class="brand-cap"${b.caption_color ? ` style="color:${esc(b.caption_color)}"` : ""}>${esc(b.caption)}${b.caption2 ? `<small>${esc(b.caption2)}</small>` : ""}</span>` : "")
      : `<span class="brand-name">${esc(b.name)}</span>`;
    return b.url
      ? `<a class="brand-tile${b.fill ? " fill" : ""}"${style} href="${esc(b.url)}" target="_blank" rel="noopener" title="${esc(b.name)}">${inner}</a>`
      : `<div class="brand-tile${b.fill ? " fill" : ""}"${style} title="${esc(b.name)}">${inner}</div>`;
  }).join(""));
  if (!brands.length) $("brands-sec")?.classList.add("hidden");
  fill("services", (m.services || []).map((x) => `<div class="card svc"><h3>${esc(x.title)}</h3><p>${esc(x.text)}</p></div>`).join(""));

  const mail = `mailto:${m.email}?subject=${encodeURIComponent("Collaboration with @" + m.handle)}`;
  document.querySelectorAll("[data-mail]").forEach((el) => (el.href = mail));
  fill("email-text", esc(m.email));
}

(async () => {
  const [m, s] = await Promise.all([getJSON("data/manual.json"), getJSON("data/stats.json")]);
  document.documentElement.dataset.theme = m.theme || "sunset";
  hero(m);
  if (document.body.dataset.page === "bio") bioPage(m, s);
  if (document.body.dataset.page === "kit") kitPage(m, s);
  fill("updated", s.updated ? `Stats updated ${date(s.updated)}` : "");
  document.body.classList.add("ready");
})();

// ---------------------------------------------------------------- email
// mailto: links do nothing on laptops without a mail app and inside TikTok's
// in-app browser, so every email button opens this small sheet instead.
function emailSheet(addr, subject) {
  let el = document.getElementById("mail-sheet");
  if (!el) {
    el = document.createElement("div");
    el.id = "mail-sheet";
    el.className = "sheet-bg";
    document.body.appendChild(el);
    el.addEventListener("click", (e) => { if (e.target === el || e.target.dataset.close != null) el.classList.remove("open"); });
  }
  const s = encodeURIComponent(subject || "");
  const to = encodeURIComponent(addr);
  el.innerHTML = `
    <div class="sheet" role="dialog" aria-label="Email">
      <div class="eyebrow">Email me</div>
      <div class="mail-addr">${esc(addr)}</div>
      <button class="btn" id="mail-copy">Copy email address</button>
      <div class="mail-opts">
        <a class="btn ghost" href="https://mail.google.com/mail/?view=cm&fs=1&to=${to}&su=${s}" target="_blank" rel="noopener">Gmail</a>
        <a class="btn ghost" href="https://outlook.live.com/mail/0/deeplink/compose?to=${to}&subject=${s}" target="_blank" rel="noopener">Outlook</a>
        <a class="btn ghost" href="mailto:${esc(addr)}?subject=${s}">Mail app</a>
      </div>
      <button class="sheet-close" data-close aria-label="Close">Close</button>
    </div>`;
  el.querySelector("#mail-copy").onclick = async (e) => {
    try { await navigator.clipboard.writeText(addr); }
    catch {
      const r = document.createRange(); r.selectNodeContents(el.querySelector(".mail-addr"));
      const sel = getSelection(); sel.removeAllRanges(); sel.addRange(r); document.execCommand("copy");
    }
    e.target.textContent = "Copied ✓";
  };
  el.classList.add("open");
}
document.addEventListener("click", (e) => {
  const a = e.target.closest('a[href^="mailto:"]');
  if (!a || a.closest("#mail-sheet")) return;
  e.preventDefault();
  const u = new URL(a.href);
  emailSheet(decodeURIComponent(u.pathname), u.searchParams.get("subject"));
});
