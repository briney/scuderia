/* scuderia feed renderer — turns cards into a page.
 * Knows what a *card* is (summary / review / alert / metric + the generic
 * fallback), never what a budget or a concept synthesis is.
 *
 * Gestures (documented on every empty state):
 *   swipe right = approve top item    swipe left = reject
 *   tap buttons = approve / reject / snooze(3d) / dismiss
 */

(() => {
  const out = document.getElementById("out");
  const stamp = document.getElementById("stamp");

  // --- auth: reader key via ?key=, kept in localStorage -------------------
  const params = new URLSearchParams(location.search);
  if (params.get("key")) {
    localStorage.setItem("feed_key", params.get("key"));
    history.replaceState(null, "", location.pathname); // keep key out of the URL
  }
  const KEY = localStorage.getItem("feed_key") || "";
  const H = { "x-feed-key": KEY };

  // --- tiny markdown subset (escape first; bold, italic, code, links, lists)
  function md(src) {
    if (!src) return "";
    const esc = src
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    const inline = (t) =>
      t
        .replace(/`([^`]+)`/g, "<code>$1</code>")
        .replace(/\*\*([^*]+)\*\*/g, "<b>$1</b>")
        .replace(/\*([^*]+)\*/g, "<i>$1</i>")
        .replace(/_([^_]+)_/g, "<i>$1</i>")
        .replace(/\[([^\]]+)\]\((https?:\/\/[^)]+)\)/g,
                 '<a href="$2" target="_blank" rel="noopener">$1</a>');
    const lines = esc.split("\n");
    let html = "", inList = false;
    for (const line of lines) {
      const m = line.match(/^\s*[-•]\s+(.*)/);
      if (m) {
        if (!inList) { html += "<ul>"; inList = true; }
        html += "<li>" + inline(m[1]) + "</li>";
      } else {
        if (inList) { html += "</ul>"; inList = false; }
        if (line.trim()) html += "<p>" + inline(line) + "</p>";
      }
    }
    if (inList) html += "</ul>";
    return html;
  }

  const esc = (s) =>
    String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;")
             .replace(/>/g, "&gt;").replace(/"/g, "&quot;");

  // --- decisions ------------------------------------------------------------
  async function decide(target, cardId, itemId, action) {
    const body = { card_id: cardId, action };
    if (itemId) body.item_id = itemId;
    if (action === "snooze") body.payload = "3d"; // v1 default (spec §11)
    target.classList.add("sent");
    const r = await fetch("/decide", {
      method: "POST",
      headers: { ...H, "content-type": "application/json" },
      body: JSON.stringify(body),
    });
    const note = document.createElement("div");
    note.className = "meta";
    if (r.ok) {
      note.textContent = "decision recorded: " + action +
        (action === "snooze" ? " (3 days)" : "") +
        " — applies on next drain";
      const acts = target.querySelector(".actions");
      if (acts) acts.replaceWith(note); else target.appendChild(note);
    } else if (r.status === 409) {
      note.textContent = "already pending — a decision for this is in flight";
      target.appendChild(note);
    } else {
      note.textContent = "failed: " + r.status;
      target.appendChild(note);
      target.classList.remove("sent");
    }
  }

  // --- swipe (right = approve, left = reject) --------------------------------
  function addSwipe(row, cardId, itemId, available) {
    let x0 = null, dx = 0;
    const hintR = row.querySelector(".swipe-hint.right");
    const hintL = row.querySelector(".swipe-hint.left");
    row.addEventListener("touchstart", (e) => { x0 = e.touches[0].clientX; dx = 0; },
      { passive: true });
    row.addEventListener("touchmove", (e) => {
      if (x0 === null) return;
      dx = e.touches[0].clientX - x0;
      if (Math.abs(dx) < 12) return;
      row.style.transform = `translateX(${dx * 0.6}px)`;
      const canR = available.includes("approve");
      const canL = available.includes("reject");
      if (hintR) hintR.style.opacity = dx > 30 && canR ? 1 : 0;
      if (hintL) hintL.style.opacity = dx < -30 && canL ? 1 : 0;
    }, { passive: true });
    row.addEventListener("touchend", () => {
      row.style.transform = "";
      if (hintR) hintR.style.opacity = 0;
      if (hintL) hintL.style.opacity = 0;
      if (dx > 90 && available.includes("approve")) decide(row, cardId, itemId, "approve");
      else if (dx < -90 && available.includes("reject")) decide(row, cardId, itemId, "reject");
      x0 = null; dx = 0;
    });
  }

  const ACTION_LABELS = {
    approve: "approve", reject: "reject", snooze: "snooze 3d", dismiss: "dismiss",
  };

  function actionButtons(cardId, itemId, actions) {
    const wrap = document.createElement("div");
    wrap.className = "actions";
    for (const a of actions) {
      const b = document.createElement("button");
      b.className = "act " + a;
      b.textContent = ACTION_LABELS[a] || a;
      b.addEventListener("click", () =>
        decide(itemId ? wrap.closest(".item") : wrap.closest(".card"),
               cardId, itemId, a));
      wrap.appendChild(b);
    }
    return wrap;
  }

  // --- rendering --------------------------------------------------------------
  function renderItem(card, it) {
    const row = document.createElement("div");
    row.className = "item";
    row.id = "it-" + it.item_id;

    const chip = document.createElement("span"); // hash chip: IDs stay visible
    chip.className = "chip";
    chip.textContent = it.item_id;
    row.appendChild(chip);

    const t = document.createElement("span");
    t.className = "title";
    t.textContent = it.title;
    row.appendChild(t);

    if (it.body) {
      const b = document.createElement("div");
      b.className = "itembody";
      b.innerHTML = md(it.body);
      row.appendChild(b);
    }
    if (it.source_ref) {
      const s = document.createElement("div");
      s.className = "src";
      s.textContent = it.source_ref;
      row.appendChild(s);
    }

    const hr = document.createElement("span");
    hr.className = "swipe-hint right"; hr.textContent = "approve →";
    const hl = document.createElement("span");
    hl.className = "swipe-hint left"; hl.textContent = "← reject";
    row.appendChild(hr); row.appendChild(hl);

    const avail = it.available_actions || ["approve", "reject", "snooze"];
    row.appendChild(actionButtons(card.card_id, it.item_id, avail));
    addSwipe(row, card.card_id, it.item_id, avail);
    return row;
  }

  function gestureMap() {
    return '<div class="gestures">' +
      "<div><b>swipe right</b> — approve top item</div>" +
      "<div><b>swipe left</b> — reject</div>" +
      "<div><b>buttons</b> — approve / reject / snooze 3d / dismiss</div>" +
      "</div>";
  }

  function renderCard(c) {
    const el = document.createElement("article");
    el.className = "card";
    el.dataset.profile = c.profile || "";
    el.dataset.type = c.type || "";

    let h = '<span class="tag">' + esc(c.profile || "?") + " · " +
            esc(c.type || "card") + "</span>";
    h += "<h2>" + esc(c.title || "(untitled)") + "</h2>";
    el.innerHTML = h;

    if (c.body) {
      const b = document.createElement("div");
      b.className = "body";
      b.innerHTML = md(c.body);
      el.appendChild(b);
    }

    // Review cards: the item stack. Empty stack → stable empty state, not a
    // vanished card (spec §3.2).
    if (c.type === "review") {
      const items = c.items || [];
      if (items.length === 0) {
        const e = document.createElement("div");
        e.className = "empty";
        e.innerHTML = "<b>queue clear</b> — nothing pending." + gestureMap();
        el.appendChild(e);
      } else {
        for (const it of items) el.appendChild(renderItem(c, it));
      }
    }

    if (c.actions && c.actions.length)
      el.appendChild(actionButtons(c.card_id, null, c.actions));

    const meta = document.createElement("div");
    meta.className = "meta";
    meta.textContent = c.card_id + " · refreshed " +
      (c.refreshed || "").replace("T", " ").slice(0, 16) + "Z";
    el.appendChild(meta);
    return el;
  }

  async function load() {
    let r;
    try {
      r = await fetch("/feed", { headers: H });
    } catch {
      out.textContent = "network error — pull to retry.";
      return;
    }
    if (r.status === 401) {
      out.innerHTML = '<div class="empty"><b>key required.</b> Open this page ' +
        "with <code>?key=…</code> once; it is remembered after that.</div>";
      return;
    }
    if (!r.ok) { out.textContent = "feed error: " + r.status; return; }

    const cards = await r.json();
    out.innerHTML = "";
    if (!cards.length) {
      const e = document.createElement("div");
      e.className = "empty";
      e.innerHTML = "<b>no cards yet.</b> The feed is a defined set of " +
        "persistent slots — cards appear as their producers emit them." +
        gestureMap();
      out.appendChild(e);
    }
    for (const c of cards) out.appendChild(renderCard(c));
    stamp.textContent = "loaded " + new Date().toLocaleTimeString();
  }

  document.getElementById("refresh").addEventListener("click", load);
  load();
})();
