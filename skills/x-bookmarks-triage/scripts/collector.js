/*
 * x-bookmarks-triage collector
 *
 * Paste this whole file into the page context of https://x.com/i/bookmarks
 * (for example with the Claude in Chrome `javascript_tool`). It defines
 * `window.__xb` and does nothing until you call one of its functions.
 *
 * Lessons baked in:
 *  - X virtualises the timeline. Scroll in small steps (700 px by default);
 *    a 3,000 px step silently skipped about 25 % of bookmarks in testing.
 *  - Browser automation tools usually time out after ~45 s per call, so long
 *    loops run in the background: call start(), then poll status().
 *  - Tool output is often truncated around 1,000 characters. Do not return
 *    the data from a JS call: use dump() then read the page text, or
 *    download() if the user has agreed to a file download.
 *
 * Everything stays in the page. Nothing is sent anywhere.
 */
(() => {
  const XB = (window.__xb = window.__xb || {});
  XB.rec = XB.rec || new Map();      // id -> record, in bookmark order
  XB.folders = XB.folders || {};      // folder name -> [ids]
  XB.state = XB.state || { running: false };

  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

  XB.parse = function (a) {
    const t = a.querySelector("time");
    const href = t && t.closest("a") ? t.closest("a").getAttribute("href") : null;
    if (!href) return null;
    const tt = [...a.querySelectorAll('[data-testid="tweetText"]')];
    const un = [...a.querySelectorAll('[data-testid="User-Name"]')];
    const linkTxt = (el) =>
      el
        ? [...el.querySelectorAll("a")]
            .map((x) => x.innerText.trim())
            .filter((s) => /\.[a-z]{2,}/i.test(s) && !s.startsWith("@") && !s.startsWith("#"))
        : [];
    const card = a.querySelector('[data-testid="card.wrapper"]');
    const handleOf = (el) => ((el && el.innerText.match(/@\w+/)) || [""])[0];
    return {
      id: href.split("/").pop(),
      url: "https://x.com" + href,
      handle: href.split("/")[1],
      author: ((un[0] && un[0].innerText.split("\n")[0]) || "").trim(),
      posted: t.getAttribute("datetime"),
      text: tt[0] ? tt[0].innerText : "",
      show_more: !!a.querySelector('[data-testid="tweet-text-show-more-link"]'),
      quote:
        tt.length > 1
          ? {
              author: (((un[1] && un[1].innerText.split("\n")[0]) || "").trim() + " " + handleOf(un[1])).trim(),
              text: tt[1].innerText,
            }
          : null,
      links: linkTxt(tt[0]),
      card: card ? card.innerText.replace(/\n+/g, " | ").slice(0, 300) : "",
      media: [
        ...new Set(
          [...a.querySelectorAll('[data-testid="tweetPhoto"] img, video')].map((m) =>
            m.tagName === "VIDEO" ? "video" : "photo"
          )
        ),
      ],
      // X long-form articles have no tweetText; keep the visible preview (title first).
      article_hint: !tt.length
        ? a.innerText.split("\n").filter((s) => s.length > 25).slice(0, 4).join(" | ").slice(0, 400)
        : "",
    };
  };

  /**
   * Start collecting from the bookmarks list currently displayed.
   * opts.knownIds        ids already in your vault (weekly runs stop early)
   * opts.stopAfterKnown  stop after this many consecutive known ids (default 15)
   * opts.step            scroll step in px (default 700)
   * opts.delay           ms between steps (default 1000)
   * opts.maxSteps        hard cap (default 2000)
   */
  XB.start = function (opts = {}) {
    const { knownIds = [], stopAfterKnown = 15, step = 700, delay = 1000, maxSteps = 2000 } = opts;
    if (XB.state.running) return "already running";
    const known = new Set(knownIds);
    const seen = new Set();
    XB.state = { running: true, steps: 0, consecutiveKnown: 0, newCount: 0, reason: null };
    window.scrollTo(0, 0);
    (async () => {
      await sleep(1500);
      let lastY = -1, still = 0;
      for (let i = 0; i < maxSteps && XB.state.running; i++) {
        for (const a of document.querySelectorAll('article[data-testid="tweet"]')) {
          let r;
          try { r = XB.parse(a); } catch (e) { continue; }
          if (!r || seen.has(r.id)) continue;
          seen.add(r.id);
          if (known.has(r.id)) {
            XB.state.consecutiveKnown++;
            continue;
          }
          XB.state.consecutiveKnown = 0;
          if (!XB.rec.has(r.id)) {
            r.order = XB.rec.size;
            XB.rec.set(r.id, r);
            XB.state.newCount++;
          }
        }
        if (known.size && XB.state.consecutiveKnown >= stopAfterKnown) { XB.state.reason = "reached known bookmarks"; break; }
        window.scrollBy(0, step);
        XB.state.steps = i + 1;
        await sleep(delay);
        if (Math.abs(window.scrollY - lastY) < 10) { if (++still > 12) { XB.state.reason = "end of list"; break; } }
        else still = 0;
        lastY = window.scrollY;
      }
      if (!XB.state.reason) XB.state.reason = XB.state.running ? "max steps" : "stopped";
      XB.state.running = false;
    })();
    return "started";
  };

  XB.stop = function () { XB.state.running = false; return "stopping"; };

  /** Short status line, safe for truncated tool output. */
  XB.status = function () {
    const s = XB.state;
    return `running=${s.running} new=${s.newCount || 0} total=${XB.rec.size} steps=${s.steps || 0} reason=${s.reason}`;
  };

  /**
   * Optional: record which bookmark folder each item belongs to (X Premium).
   * Open a folder from the "Bookmarks" menu in the SAME tab (the SPA keeps
   * window.__xb alive), then call collectFolder("Name") and poll status().
   * Call applyFolders() once all folders are done.
   */
  XB.collectFolder = function (name, { step = 700, delay = 900, maxSteps = 400 } = {}) {
    const ids = new Set();
    XB.state = { running: true, steps: 0, reason: null, folder: name };
    window.scrollTo(0, 0);
    (async () => {
      await sleep(1500);
      let lastY = -1, still = 0;
      for (let i = 0; i < maxSteps && XB.state.running; i++) {
        document.querySelectorAll('article[data-testid="tweet"] time').forEach((t) => {
          const h = t.closest("a") && t.closest("a").getAttribute("href");
          if (h) ids.add(h.split("/").pop());
        });
        window.scrollBy(0, step);
        XB.state.steps = i + 1;
        await sleep(delay);
        if (Math.abs(window.scrollY - lastY) < 10) { if (++still > 8) break; } else still = 0;
        lastY = window.scrollY;
      }
      XB.folders[name] = [...ids];
      XB.state.reason = `folder ${name}: ${ids.size}`;
      XB.state.running = false;
    })();
    return "started folder " + name;
  };

  XB.applyFolders = function () {
    let hit = 0;
    for (const [name, ids] of Object.entries(XB.folders)) {
      for (const id of ids) {
        const r = XB.rec.get(id);
        if (r) { (r.folders = r.folders || []).includes(name) || r.folders.push(name); hit++; }
      }
    }
    return `applied ${hit} folder memberships`;
  };

  XB.payload = function () {
    const items = [...XB.rec.values()].sort((a, b) => a.order - b.order);
    return {
      exported_at: new Date().toISOString(),
      source: "x.com/i/bookmarks (web UI)",
      count: items.length,
      items,
    };
  };

  /** Replace the page with the JSON export so a page-text reader can copy it verbatim. */
  XB.dump = function () {
    const json = JSON.stringify(XB.payload());
    document.body.innerHTML = "<article><pre id='xb-dump'></pre></article>";
    document.getElementById("xb-dump").textContent = json;
    return `dumped ${json.length} chars`;
  };

  /** Save the export as a file. Only with the user's explicit agreement. */
  XB.download = function (filename) {
    const blob = new Blob([JSON.stringify(XB.payload(), null, 1)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = filename || `x-bookmarks-export-${new Date().toISOString().slice(0, 10)}.json`;
    document.documentElement.appendChild(a);
    a.click();
    a.remove();
    return `download triggered (${blob.size} bytes)`;
  };

  return "x-bookmarks-triage collector ready";
})();
