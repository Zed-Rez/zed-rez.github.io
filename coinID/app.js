// app.js -- the coin visualizer, in the browser: photos are cropped here (prep.js); only the 512 px faces go to the model
// server, which returns the model's reading and the type search. Layout and behaviour follow coin-visualizer/app/src/main.rs.
"use strict";
(function () {
  const LOCAL = /^(localhost|127\.0\.0\.1|\[::1\])$/.test(location.hostname);
  const ENDPOINT = LOCAL ? "http://127.0.0.1:8765" : "https://jetson-nano.tailc1c489.ts.net";
  const P = window.CoinPrep;
  const PAD = 10, GAP = 8, LABEL_H = 28, FILE_H = 18, CENTRE_MIN = 460;
  const MULTI = ["port6", "obv_design", "rev_design"];
  const BOLD = ["port6", "obv_design", "rev_design", "obv_legend", "rev_legend", "obv_desc", "rev_desc", "obv_symbols", "rev_symbols", "dating", "issue"];
  const isMulti = (k) => MULTI.includes(k);
  const vocabHead = (k) => (k === "obv_design" || k === "rev_design" ? "design" : k);

  const $ = (s) => document.querySelector(s);
  function el(tag, cls, text) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }

  // ---- text helpers (as the Rust app) ------------------------------------------------------------------------------
  const norm = (s) => (s || "").normalize("NFKD").replace(/\p{M}/gu, "").toLowerCase().split(/\s+/).filter(Boolean).join(" ");
  const LEG = { "ϲ": "σ", "ς": "σ", v: "u", j: "i" };
  const normLegend = (s) => [...norm(s)].filter((ch) => /[\p{L}\p{N}]/u.test(ch)).map((ch) => LEG[ch] || ch).join("");
  const year = (y) => (y < 0 ? `${-y} BC` : `AD ${y}`);
  function years(a, b) {
    if (a === b) return year(a);
    if (a < 0 && b < 0) return `${-a}–${-b} BC`;
    if (a >= 0) return `AD ${a}–${b}`;
    return `${year(a)}–${year(b)}`;
  }
  const topN = (v, n) => v.map((p, i) => [i, p]).sort((a, b) => b[1] - a[1]).slice(0, n);
  const pct = (p) => (p < 0.01 ? "<1%" : `${Math.round(p * 100)}%`);
  const natKey = (s) => s.toLowerCase().split(/(\d+)/).map((x, i) => (i % 2 ? x.padStart(20, "0") : x)).join("");
  const store = {
    get(k, d) { try { const v = localStorage.getItem("coinID." + k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } },
    set(k, v) { try { localStorage.setItem("coinID." + k, JSON.stringify(v)); } catch (e) { /* private mode */ } },
  };

  // ---- state ---------------------------------------------------------------------------------------------------------
  let meta = null, metaNames = {}, metaSuggest = {};
  const S = { scope: store.get("scope", 0), auto: store.get("auto", true), perPhoto: store.get("perPhoto", false) };
  let files = [];          // every photo uploaded, in order
  let coins = [];          // {name, photos: [{name, faces: [{blob, url}], kind}], status, err, token, sides, probs, auto, fields, locked, search, selected}
  let cur = 0, gen = 0, focusKey = null, built = null, offline = false;

  // ---- server ----------------------------------------------------------------------------------------------------------
  async function call(path, body) {
    let r;
    try {
      r = await fetch(ENDPOINT + path, body === undefined ? { cache: "default" } : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    } catch (e) {
      offline = true; status();
      const err = new Error("The model server is not reachable right now."); err.code = 0; throw err;
    }
    offline = false;
    let j = {};
    try { j = await r.json(); } catch (e) { /* empty reply */ }
    if (!r.ok) { const err = new Error(j.error || `server error ${r.status}`); err.code = r.status; throw err; }
    return j;
  }
  const sleep = (ms) => new Promise((ok) => setTimeout(ok, ms));
  const dataURL = (blob) => new Promise((ok, bad) => { const f = new FileReader(); f.onload = () => ok(f.result); f.onerror = bad; f.readAsDataURL(blob); });

  async function loadMeta() {
    try {
      meta = await call("/meta");
      for (const [h, names] of Object.entries(meta.names)) metaNames[h] = names.map(norm);
      for (const [k, vals] of Object.entries(meta.suggest)) metaSuggest[k] = vals.map((v) => [v[0], norm(v[0])]);
      if (!coins.length) built = null;
      render();
    } catch (e) {
      status();
      setTimeout(loadMeta, 15000);
    }
  }

  // ---- photos -> coins -----------------------------------------------------------------------------------------------
  // a photo showing both faces is a coin of its own; other photos pair up in order (or one photo per coin)
  async function rebuild() {
    const g = ++gen;
    for (const c of coins) for (const p of c.photos) for (const f of p.faces) URL.revokeObjectURL(f.url);
    coins = []; cur = 0; built = null; render();
    let open = null;
    for (const file of files) {
      if (g !== gen) return;
      let ph;
      try {
        const r = await P.photoFaces(file, S.auto);
        ph = { name: file.name, kind: r.kind, faces: r.faces.map((b) => ({ blob: b, url: URL.createObjectURL(b) })) };
      } catch (e) {
        coins.push({ name: file.name, photos: [{ name: file.name, faces: [], kind: "" }], status: "error", err: `${file.name}: ${e.message || "could not read this photo"}` });
        if (open) { ready(open); open = null; }
        render(); continue;
      }
      if (g !== gen) return;
      if (open && !S.perPhoto && ph.faces.length === 1) {
        open.photos.push(ph); open.name += " + " + ph.name; ready(open); open = null;
      } else {
        if (open) { ready(open); open = null; }
        const c = { name: ph.name, photos: [ph], status: "prep" };
        coins.push(c);
        if (S.perPhoto || ph.faces.length > 1) ready(c); else open = c;
      }
      render();
    }
    if (open) ready(open);
    render();
  }

  // identify one coin at a time, in order
  let queue = Promise.resolve();
  function ready(c) {
    c.status = "queued";
    const g = gen;
    queue = queue.then(() => (g === gen ? identify(c) : null));
  }

  function allFaces(c) { return c.photos.flatMap((p) => p.faces.map((f) => ({ ...f, photo: p.name }))).slice(0, 4); }

  async function identify(c, keep) {
    c.status = "reading"; c.err = null; render();
    const faces = await Promise.all(allFaces(c).map((f) => dataURL(f.blob)));
    for (let tries = 0; ; tries++) {
      try {
        const r = await call("/identify", { faces });
        c.token = r.token; c.sides = r.faces.map((f) => f.rev); c.probs = r.probs; c.status = "ready";
        if (keep) { c.auto = r.auto; return; }   // the server forgot the coin: same reading, keep the edits
        c.auto = r.auto; c.fields = { ...r.auto }; c.locked = new Set(); c.search = r.search; c.selected = 0;
        c.searchKey = skey(c.fields, c.locked, 0);
        if (S.scope !== 0) wantSearch(c);
        if (c === coins[cur]) built = null;
        render(); return;
      } catch (e) {
        // 429/503: rate or bandwidth cap (the server is on a home connection); a refused upload can also surface as a dropped connection
        if ((e.code === 429 || e.code === 503) && tries < 6 || e.code === 0 && tries < 2) { c.err = "Busy, waiting a moment…"; render(); await sleep(12000); continue; }
        c.status = "error"; c.err = e.message; render(); return;
      }
    }
  }

  // ---- search --------------------------------------------------------------------------------------------------------
  const skey = (fields, locked, scope) => JSON.stringify([fields, [...locked].sort(), scope]);
  function wantSearch(c) {
    if (c.status !== "ready") return;
    const k = skey(c.fields, c.locked, S.scope);
    if (k === c.searchKey) return;
    c.searchKey = k;
    clearTimeout(c.timer);
    c.timer = setTimeout(() => runSearch(c), 250);
  }
  async function runSearch(c, again) {
    const seq = (c.seq = (c.seq || 0) + 1);
    try {
      const r = await call("/search", { token: c.token, fields: c.fields, locked: [...c.locked], scope: S.scope });
      if (seq !== c.seq) return;
      c.search = r; c.selected = 0; c.err = null;
    } catch (e) {
      if (seq !== c.seq) return;
      if (e.code === 410 && !again) { await identify(c, true); return runSearch(c, true); }
      if ((e.code === 429 || e.code === 503) && !again) { await sleep(3000); return runSearch(c, true); }
      c.err = e.message; c.searchKey = null;
    }
    status();
    if (c === coins[cur]) { renderRight(); updateRows(); renderBanner(); }
  }

  // ---- options (the list under a focused box) ------------------------------------------------------------------------
  function classOf(head, text) { const t = norm(text); return t && metaNames[head] ? metaNames[head].indexOf(t) : -1; }
  function options(c, key, text, edited) {
    if (FIELD_KEYS.has(key)) {
      const t = norm(text), v = metaSuggest[key] || [];
      const out = [];
      for (const [s, n] of v) { if (n.includes(t)) { out.push([s, null]); if (out.length === 8) break; } }
      return out;
    }
    if (key === "date") return topN(c.probs.date || [], 6).map(([i, p]) => { const a = Math.trunc(meta.y0 + meta.bin * i); return [years(a, a + meta.bin - 1), p]; });
    if (key.endsWith("legend")) return [];
    const p = c.probs[key], head = vocabHead(key), names = meta.names[head], nn = metaNames[head];
    if (!p || !names) return [];
    const n = Math.min(names.length, p.length);
    const typed = isMulti(key) ? text.split(",").pop().trim() : text.trim();
    let ix = [...Array(n).keys()];
    if (edited && typed && !(isMulti(key) && classOf(head, typed) >= 0)) { const t = norm(typed); ix = ix.filter((i) => nn[i].includes(t)); }
    ix.sort((a, b) => p[b] - p[a]);
    let best = -1;
    for (let i = 0; i < n; i++) if (names[i] && (best < 0 || p[i] >= p[best])) best = i;
    if (best >= 0) { ix = ix.filter((i) => i !== best); ix.unshift(best); }
    const seen = new Set(), out = [];
    for (const i of ix) {
      if (!names[i] || seen.has(names[i])) continue;
      seen.add(names[i]); out.push([names[i], p[i]]);
      if (out.length === 8) break;
    }
    return out;
  }

  // `text` into `node`, the words (terms, in a multi-term box) not found in `other` in semibold
  function diffInto(node, key, text, other) {
    node.textContent = "";
    const on = BOLD.includes(key) && text.trim() && other.trim();
    if (!on) { node.textContent = text; return; }
    const multi = isMulti(key), legend = key.endsWith("legend");
    const oNorm = norm(other), oLeg = normLegend(other), oTerms = other.split(",").map(norm);
    const missing = (w) => {
      const t = multi ? norm(w) : legend ? normLegend(w) : norm(w.replace(/^[^\p{L}\p{N}]+|[^\p{L}\p{N}]+$/gu, ""));
      return !!t && !(multi ? oTerms.includes(t) : legend ? oLeg.includes(t) : oNorm.includes(t));
    };
    const sep = (ch) => (multi ? ch === "," : /[\s,;]/.test(ch));
    let run = "", word = null;
    const push = () => {
      if (!run) return;
      if (word && missing(run)) node.appendChild(el("b", null, run)); else node.appendChild(document.createTextNode(run));
    };
    for (const ch of text) {
      const w = !sep(ch);
      if (word !== w) { push(); run = ""; word = w; }
      run += ch;
    }
    push();
  }

  // ---- drawing -------------------------------------------------------------------------------------------------------
  function square(img, caption, captionHref, placeholder, alt) {
    const f = el("figure", "sq");
    const box = el("div", "img");
    if (img) {
      const i = el("img"); i.alt = alt || ""; i.src = img; i.decoding = "async"; i.referrerPolicy = "no-referrer";
      i.onerror = () => { box.textContent = ""; box.appendChild(el("span", "ph", placeholder || "No image available")); };
      box.appendChild(i);
    } else if (placeholder) box.appendChild(el("span", "ph", placeholder));
    f.appendChild(box);
    const cap = el("figcaption");
    if (caption && captionHref) { const a = el("a", null, caption); a.href = captionHref; a.target = "_blank"; a.rel = "noopener"; cap.appendChild(a); }
    else cap.textContent = caption || "";
    cap.title = caption || "";
    f.appendChild(cap);
    return f;
  }
  function thumb(img, corner, caption, border, placeholder, title) {
    const b = el("button", "th" + (border ? " " + border : ""));
    b.type = "button"; if (title) b.title = title;
    const box = el("div", "img");
    if (img) {
      const i = el("img"); i.alt = ""; i.loading = "lazy"; i.decoding = "async"; i.referrerPolicy = "no-referrer"; i.src = img;
      i.onerror = () => { box.textContent = ""; box.appendChild(el("span", "ph", "No image")); box.appendChild(el("span", "tag", corner)); };
      box.appendChild(i);
    } else box.appendChild(el("span", "ph", placeholder));
    box.appendChild(el("span", "tag", corner));
    b.appendChild(box);
    if (caption != null) b.appendChild(el("span", "cap", caption));
    return b;
  }
  const noImage = (uri) => (uri.includes("rpc.ashmus") ? "No image in the reference set" : "No image available");

  // the obverse and reverse shown for a coin: by the model's sides once it has read them, else in order
  function shownFaces(c) {
    const fs = allFaces(c);
    if (!c.sides) return [fs[0], fs[1]];
    return [false, true].map((rev) => fs.find((f, i) => c.sides[i] === rev));
  }

  function renderLeft() {
    const L = $("#left"); L.textContent = "";
    if (!coins.length) {
      const w = el("div", "start");
      const b = el("label", "btn big", "Upload photos…");
      b.htmlFor = "file";
      w.appendChild(b);
      w.appendChild(el("p", "hint", "One photo per side, or one photo of both sides."));
      L.appendChild(w);
      return;
    }
    const c = coins[cur], pair = el("div", "pair");
    for (const f of shownFaces(c)) pair.appendChild(square(f && f.url, f ? f.photo : "", null, "", "coin photo"));
    L.appendChild(pair);
    const row = el("div", "row-scroll");
    coins.forEach((k, i) => {
      const fs = allFaces(k), back = k.sides ? fs.find((f, j) => k.sides[j]) || fs[fs.length - 1] : fs[fs.length - 1];
      const t = thumb(back && back.url, String(i + 1), null, i === cur ? "on" : k.status === "error" ? "bad" : "", k.status === "error" ? "!" : "…", k.name);
      t.onclick = () => go(i);
      row.appendChild(t);
      if (i === cur) requestAnimationFrame(() => t.scrollIntoView({ block: "nearest", inline: "nearest" }));
    });
    L.appendChild(row);
  }

  function selected(c) {
    const s = c && c.search;
    if (!s || !s.cands.length) return null;
    return s.cands[Math.min(c.selected || 0, s.cands.length - 1)];
  }

  function renderRight() {
    const R = $("#right"); R.textContent = "";
    const c = coins[cur], t = selected(c), pair = el("div", "pair");
    if (!t) { pair.appendChild(square(null, "", null, "")); pair.appendChild(square(null, "", null, "")); R.appendChild(pair); return; }
    for (const side of ["obv", "rev"]) {
      const r = t.ref[side];
      if (r) pair.appendChild(square(r.img, r.id, r.page, r.img ? noImage(t.uri) : "No image available", side === "obv" ? "reference obverse" : "reference reverse"));
      else pair.appendChild(square(null, "", null, noImage(t.uri)));
    }
    R.appendChild(pair);
    const row = el("div", "row-scroll"), sel = Math.min(c.selected || 0, c.search.cands.length - 1);
    const tied = new Set(t.tied.map((x) => x.k));
    c.search.cands.forEach((x, i) => {
      const r = x.ref.rev;
      const th = thumb(r && r.thumb, String(i + 1), x.short, i === sel ? "on" : tied.has(i) ? "tie" : "", "No image", x.label);
      if (tied.has(i)) th.classList.add("tied");
      th.onclick = () => pick(i);
      row.appendChild(th);
      if (i === sel) requestAnimationFrame(() => th.scrollIntoView({ block: "nearest", inline: "nearest" }));
    });
    R.appendChild(row);
  }

  // not unique (the selected type cannot be told apart from others), then the selected type linked to its OCRE / RPC page
  function renderBanner() {
    const B = $("#banner"); B.textContent = "";
    const c = coins[cur];
    if (!c) return;
    if (c.status !== "ready") {
      const msg = c.status === "error" ? c.err : c.err || (c.status === "reading" ? "Reading the coin…" : "Cropping…");
      const p = el("p", c.status === "error" ? "err" : "wait", msg);
      B.appendChild(p);
      if (c.status === "error" && c.photos[0].faces.length) {
        const b = el("button", "btn", "Try again"); b.type = "button"; b.onclick = () => identify(c); B.appendChild(b);
      }
      return;
    }
    const t = selected(c);
    if (c.err) B.appendChild(el("p", "err", c.err));
    if (!t) { B.appendChild(el("p", "wait", "No type passes the locked boxes.")); return; }
    if (t.tied.length) {
      const w = el("div", "tied-box");
      w.appendChild(el("span", "nu", "Not unique"));
      for (const x of t.tied) {
        const b = x.k >= 0 ? el("button", "tb", x.label) : el("a", "tb", x.label);
        if (x.k >= 0) { b.type = "button"; b.onclick = () => pick(x.k); } else { b.href = x.link; b.target = "_blank"; b.rel = "noopener"; }
        if (x.k === c.selected) b.classList.add("on");
        w.appendChild(b);
      }
      B.appendChild(w);
    }
    const a = el("a", "type" + (t.tied.length ? " red" : ""), t.label);
    a.href = t.link; a.target = "_blank"; a.rel = "noopener";
    B.appendChild(a);
  }

  // ---- the boxes -----------------------------------------------------------------------------------------------------
  let FIELD_KEYS = new Set();
  const rowsEl = {};
  function padlock(on) {
    const lift = on ? 0 : 2.5, top = 8.5 - lift;
    return `<svg viewBox="0 0 14 24" width="14" height="24" aria-hidden="true"><rect x="2.5" y="11.5" width="9" height="7" rx="1"/>` +
      `<path d="M4.25 ${11.5 - lift + (on ? 0.5 : -0.5)} L4.25 ${top} A2.75 2.75 0 0 1 9.75 ${top} L9.75 12"/></svg>`;
  }

  function buildRows() {
    const box = $("#rows"); box.textContent = "";
    for (const k in rowsEl) delete rowsEl[k];
    const c = coins[cur];
    built = c;
    if (!c || c.status !== "ready" || !meta) return;
    const near = meta.fields.filter((f) => f[0] === "weight" || f[0] === "diameter"), rest = meta.fields.filter((f) => f[0] !== "weight" && f[0] !== "diameter");
    const all = [...meta.rows, ...near, null, ...rest];
    for (const f of all) {
      if (!f) { box.appendChild(el("div", "gap")); continue; }
      const [key, label] = f, r = el("div", "frow");
      const lock = el("button", "lock"); lock.type = "button"; lock.title = "Only types that agree"; lock.setAttribute("aria-label", `Lock ${label}: only types that agree`);
      lock.onclick = () => { if (c.locked.has(key)) c.locked.delete(key); else c.locked.add(key); updateRow(key); wantSearch(c); };
      const lab = el("span", "lab", label); lab.title = label;
      const wrap = el("div", "boxwrap");
      const show = el("div", "box show"); show.tabIndex = 0; show.setAttribute("role", "textbox"); show.setAttribute("aria-label", label);
      const ta = el("textarea", "box edit"); ta.rows = 1; ta.maxLength = 300; ta.hidden = true; ta.spellcheck = false; ta.setAttribute("aria-label", label);
      ta.autocapitalize = "off"; ta.autocomplete = "off";
      const list = el("div", "opts"); list.hidden = true; list.setAttribute("role", "listbox");
      wrap.append(show, ta, list);
      const other = el("span", "other");
      r.append(lock, lab, wrap, other);
      box.appendChild(r);
      rowsEl[key] = { r, lock, show, ta, list, other, hi: -1 };
      show.addEventListener("focus", () => openBox(key));
      show.addEventListener("mousedown", (e) => { e.preventDefault(); openBox(key); });
      ta.addEventListener("input", () => { setText(key, ta.value.replace(/\n/g, " ")); });
      ta.addEventListener("blur", () => { if (focusKey === key) closeBox(key); });
      ta.addEventListener("keydown", (e) => boxKey(e, key));
      updateRow(key);
    }
  }

  function grow(ta) { ta.style.height = "auto"; ta.style.height = ta.scrollHeight + 2 + "px"; }

  function updateRow(key) {
    const c = coins[cur], E = rowsEl[key];
    if (!E || !c || !c.fields) return;
    const text = c.fields[key] || "", t = selected(c), m = t && t.marks[key];
    const other = m ? m[0] || "" : "", ok = m ? m[1] : null;
    E.r.classList.toggle("locked", c.locked.has(key));
    E.lock.innerHTML = padlock(c.locked.has(key));
    E.lock.setAttribute("aria-pressed", c.locked.has(key) ? "true" : "false");
    for (const b of [E.show, E.ta]) { b.classList.toggle("good", ok === true); b.classList.toggle("bad", ok === false); }
    if (focusKey !== key) diffInto(E.show, key, text, other);
    diffInto(E.other, key, other, text);
  }
  function updateRows() { for (const k in rowsEl) updateRow(k); }

  function openBox(key) {
    const c = coins[cur], E = rowsEl[key];
    if (!E) return;
    if (focusKey && focusKey !== key) closeBox(focusKey);
    focusKey = key;
    E.show.hidden = true; E.ta.hidden = false; E.ta.value = c.fields[key] || "";
    E.ta.focus(); grow(E.ta);
    E.ta.setSelectionRange(E.ta.value.length, E.ta.value.length);
    E.hi = -1; showOptions(key);
  }
  function closeBox(key) {
    const E = rowsEl[key];
    if (focusKey === key) focusKey = null;
    if (!E) return;
    E.list.hidden = true; E.ta.hidden = true; E.show.hidden = false;
    updateRow(key);
  }

  function showOptions(key) {
    const c = coins[cur], E = rowsEl[key];
    const text = c.fields[key] || "";
    const opts = options(c, key, text, (c.auto[key] || "") !== text);
    E.opts = opts; E.list.textContent = "";
    if (!opts.length) { E.list.hidden = true; return; }
    const terms = isMulti(key) ? text.split(",").map(norm).filter(Boolean) : [];
    opts.forEach(([o, p], i) => {
      const b = el("div", "opt" + (i === E.hi ? " hi" : "") + (terms.includes(norm(o)) ? " in" : ""));
      b.setAttribute("role", "option");
      b.appendChild(el("span", "o", o));
      if (p != null) b.appendChild(el("span", "p", pct(p)));
      b.addEventListener("mousedown", (e) => { e.preventDefault(); choose(key, o); });
      E.list.appendChild(b);
    });
    E.list.hidden = false;
  }

  // clicking an option fills the box (multi-term boxes toggle the term)
  function choose(key, o) {
    const c = coins[cur], E = rowsEl[key];
    if (isMulti(key)) {
      const terms = (c.fields[key] || "").split(",").map((s) => s.trim()).filter(Boolean);
      const i = terms.findIndex((s) => norm(s) === norm(o));
      if (i >= 0) terms.splice(i, 1); else terms.push(o);
      E.ta.value = terms.join(", ");
      setText(key, E.ta.value);
    } else {
      E.ta.value = o; setText(key, o);
      E.ta.blur();
    }
  }

  // typing in a box, or picking from its list, locks it; emptying it unlocks it
  function setText(key, v) {
    const c = coins[cur], E = rowsEl[key];
    if (v === (c.fields[key] || "")) return;
    c.fields[key] = v;
    if (v.trim()) c.locked.add(key); else c.locked.delete(key);
    grow(E.ta); E.hi = -1;
    updateRow(key);
    if (focusKey === key) showOptions(key);
    wantSearch(c);
  }

  function boxKey(e, key) {
    const E = rowsEl[key], n = (E.opts || []).length;
    if (e.key === "ArrowDown" && n && !E.list.hidden) { e.preventDefault(); E.hi = (E.hi + 1) % n; showOptions(key); }
    else if (e.key === "ArrowUp" && n && !E.list.hidden) { e.preventDefault(); E.hi = E.hi <= 0 ? n - 1 : E.hi - 1; showOptions(key); }
    else if (e.key === "Enter") { e.preventDefault(); if (E.hi >= 0 && E.hi < n) choose(key, E.opts[E.hi][0]); else E.ta.blur(); }
    else if (e.key === "Escape") { e.preventDefault(); E.ta.blur(); }
  }

  // ---- navigation ----------------------------------------------------------------------------------------------------
  function go(i) {
    if (i < 0 || i >= coins.length || i === cur) return;
    if (focusKey) closeBox(focusKey);
    cur = i; render();
    wantSearch(coins[cur]);   // a coin opened after the scope changed searches again
  }
  function pick(i) {
    const c = coins[cur];
    if (!c || !c.search || i < 0 || i >= c.search.cands.length) return;
    c.selected = i; renderRight(); renderBanner(); updateRows();
  }
  document.addEventListener("keydown", (e) => {
    const t = e.target;
    if (t && (t.tagName === "TEXTAREA" || t.tagName === "INPUT" || t.isContentEditable) || e.metaKey || e.ctrlKey || e.altKey) return;
    if (t && t.classList && t.classList.contains("show")) return;
    const c = coins[cur];
    if (e.key === "ArrowLeft") { e.preventDefault(); go(cur - 1); }
    else if (e.key === "ArrowRight") { e.preventDefault(); go(cur + 1); }
    else if (e.key === "ArrowUp" && c && c.search) { e.preventDefault(); pick((c.selected || 0) - 1); }
    else if (e.key === "ArrowDown" && c && c.search) { e.preventDefault(); pick((c.selected || 0) + 1); }
    else if (e.key === "Enter" && t === document.body) { e.preventDefault(); go(cur + 1); }
  });

  // ---- top bar -------------------------------------------------------------------------------------------------------
  function status() {
    const s = $("#status");
    const n = coins.length, done = coins.filter((c) => c.status === "ready").length, busy = coins.some((c) => c.status === "reading" || c.status === "queued" || c.status === "prep");
    s.classList.toggle("err", offline || (!meta && files.length > 0));
    if (offline || !meta) s.textContent = offline || files.length ? "The model server is offline right now." : "";
    else s.textContent = n ? `${n} coin${n > 1 ? "s" : ""}${busy ? ` · read ${done}` : ""}` : "";
  }
  function settingsUI() {
    document.querySelectorAll("#scope button").forEach((b) => b.setAttribute("aria-pressed", String(+b.dataset.s === S.scope)));
    $("#autocrop").checked = S.auto; $("#perphoto").checked = S.perPhoto;
  }
  function addFiles(list) {
    const fs = [...list].filter(P.isPhoto);
    if (!fs.length) return;
    fs.sort((a, b) => (natKey(a.name) < natKey(b.name) ? -1 : natKey(a.name) > natKey(b.name) ? 1 : 0));
    files = fs.slice(0, 60);
    rebuild();
  }

  // ---- layout: both side columns hold a square per face, as tall as the window allows; the centre takes the rest ----
  function layout() {
    const w = document.documentElement.clientWidth, h = window.innerHeight - $("header.top").offsetHeight;
    let img = Math.min((h - 2 * PAD - 2 * FILE_H - 1.2 * GAP - LABEL_H) / 2.2, (w - CENTRE_MIN) / 2 - 2 * PAD);
    const narrow = img < 170;
    document.body.classList.toggle("narrow", narrow);
    if (narrow) img = Math.min((w - 2 * PAD - GAP) / 2, 360);
    let tw = Math.floor(((narrow ? Math.min(w - 2 * PAD, 2 * img + GAP) : img) - 4 * GAP) / 5);
    if (!narrow) img = 5 * tw + 4 * GAP; else img = Math.floor(img);
    const r = document.documentElement.style;
    r.setProperty("--img", img + "px"); r.setProperty("--tw", tw + "px");
    meander();
  }

  // a light Greek key in Princeton orange: one turn on a 5 x 5 grid, each running straight into the next
  function meander() {
    const band = $("#meander"), W = band.clientWidth, H = 16, g = H / 5, T = 5;
    const KEY = [[0, 5], [0, 0], [4, 0], [4, 3], [2, 3], [2, 2], [3, 2], [3, 1], [1, 1], [1, 5]];
    const n = Math.floor(W / (T * g)), x0 = (W - n * T * g) / 2, pts = [];
    for (let i = 0; i < n; i++) for (const [x, y] of KEY) pts.push([i * T + x, y]);
    pts.push([n * T, 5]);
    band.innerHTML = `<svg width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" aria-hidden="true"><polyline fill="none" stroke="currentColor" stroke-width="1.5" points="${pts.map(([x, y]) => `${(x0 + x * g).toFixed(1)},${(0.75 + y * g * (H - 1.5) / H).toFixed(1)}`).join(" ")}"/></svg>`;
  }

  function render() {
    if (meta && !FIELD_KEYS.size) FIELD_KEYS = new Set(meta.fields.map((f) => f[0]));
    status();
    renderLeft(); renderRight(); renderBanner();
    const c = coins[cur];
    if (built !== c || (c && c.status === "ready" && !Object.keys(rowsEl).length)) { if (!focusKey) buildRows(); }
    else updateRows();
    $("#next").disabled = cur + 1 >= coins.length;
  }

  // ---- start ---------------------------------------------------------------------------------------------------------
  function start() {
    const inp = $("#file");
    inp.addEventListener("change", () => { addFiles(inp.files); inp.value = ""; });
    document.querySelectorAll("#scope button").forEach((b) => b.addEventListener("click", () => {
      S.scope = +b.dataset.s; store.set("scope", S.scope); settingsUI();
      if (coins[cur]) wantSearch(coins[cur]);
    }));
    $("#autocrop").addEventListener("change", (e) => { S.auto = e.target.checked; store.set("auto", S.auto); if (files.length) rebuild(); });
    $("#perphoto").addEventListener("change", (e) => { S.perPhoto = e.target.checked; store.set("perPhoto", S.perPhoto); if (files.length) rebuild(); });
    $("#next").addEventListener("click", () => go(cur + 1));
    let depth = 0;
    window.addEventListener("dragenter", (e) => { e.preventDefault(); depth++; document.body.classList.add("drag"); });
    window.addEventListener("dragleave", () => { if (--depth <= 0) { depth = 0; document.body.classList.remove("drag"); } });
    window.addEventListener("dragover", (e) => e.preventDefault());
    window.addEventListener("drop", (e) => { e.preventDefault(); depth = 0; document.body.classList.remove("drag"); if (e.dataTransfer && e.dataTransfer.files) addFiles(e.dataTransfer.files); });
    window.addEventListener("resize", layout);
    settingsUI(); layout(); render(); loadMeta();
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start); else start();
})();
