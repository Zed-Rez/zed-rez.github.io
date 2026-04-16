/* ============================================================
   Youklid — Euclid's Elements Book I
   Vanilla-JS single-page application.
   ============================================================ */

(() => {
'use strict';

const $  = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

const STATE = {
  data: null,
  lang: localStorage.getItem('youklid.lang') || 'en',
  view: 'text',
  theme: localStorage.getItem('youklid.theme') || 'parchment',
  currentProp: 1,
  currentArg: 0,
  currentMapRef: null,
  mapMode: 'local',      // 'local' | 'global'
  popoverForArg: null,   // index of argument whose inline deps popover is currently open, or null
};

const KIND_LABEL = {
  def:  'Definition',
  post: 'Postulate',
  cn:   'Common Notion',
  prop: 'Proposition',
};
const ROLE_LABEL = {
  construction: 'Construction',
  setup:    'Setup',
  goal:     'Goal',
  assertion:'Claim',
  step:     '',
  conclusion:'Conclusion',
  qed:      'Q.E.D.',
};
// UI chrome (nav labels, panel titles, role tags) is always English, regardless of the
// source-text language toggle. Only the main source passages switch to Greek.
function roleLabel(r) { return ROLE_LABEL[r] || r; }

// ============================================================
// INIT
// ============================================================

async function init() {
  try {
    const resp = await fetch('./book1.json');
    STATE.data = await resp.json();
  } catch (e) {
    document.body.innerHTML = '<p style="padding:2rem">Failed to load book1.json: ' + e.message + '</p>';
    return;
  }
  applyTheme();
  applyLang();

  // Map page (youklidmap.html) always starts in map view
  if (document.body.dataset.initMap) STATE.view = 'map';

  // Deep-link via hash: #prop.5, #prop.5.a3, #post.1, #def.15, #cn.2, or map: #map/prop.4
  parseHash(location.hash);

  // Re-enforce map view after parseHash (parseHash may override STATE.view from hash)
  if (document.body.dataset.initMap) STATE.view = 'map';

  bindGlobal();
  renderProp();
  buildMapSidebar();

  // initial view
  setView(STATE.view);
}

// ============================================================
// HASH ROUTING
// ============================================================

function parseHash(h) {
  h = (h || '').replace(/^#/, '');
  if (!h) return;
  if (h.startsWith('map/')) {
    STATE.view = 'map';
    STATE.currentMapRef = h.slice(4) || null;
    return;
  }
  if (h === 'map') { STATE.view = 'map'; return; }
  // text hash: prop.0 = foundations page, prop.N or prop.N.aK
  const m = h.match(/^prop\.(\d+)(?:\.a(\d+))?$/);
  if (m) {
    STATE.currentProp = parseInt(m[1], 10);
    STATE.currentArg = m[2] != null ? parseInt(m[2], 10) : 0;
    return;
  }
  // foundation hash: post.1 / def.15 / cn.2 — jump to map view with that selected
  const fm = h.match(/^(post|def|cn)\.(\d+)$/);
  if (fm) {
    STATE.view = 'map';
    STATE.currentMapRef = `${fm[1]}.${fm[2]}`;
  }
}

function updateHash() {
  if (STATE.view === 'map') {
    const ref = STATE.currentMapRef || '';
    location.hash = ref ? `map/${ref}` : 'map';
  } else {
    location.hash = `prop.${STATE.currentProp}${STATE.currentArg ? `.a${STATE.currentArg}` : ''}`;
  }
}

// ============================================================
// GLOBAL BINDINGS
// ============================================================

function bindGlobal() {
  // Tabs
  $$('.tab').forEach(t => t.addEventListener('click', () => setView(t.dataset.view)));
  // Lang
  $$('.lang').forEach(b => b.addEventListener('click', () => setLang(b.dataset.lang)));
  // Theme
  $('#theme-btn').addEventListener('click', toggleTheme);

  // Prop nav (text page only — elements absent on map page)
  const _prevProp = $('#prev-prop'), _nextProp = $('#next-prop');
  if (_prevProp) _prevProp.addEventListener('click', () => setProp(STATE.currentProp - 1));
  if (_nextProp) _nextProp.addEventListener('click', () => setProp(STATE.currentProp + 1));
  // Arg nav (text page only)
  const _prevArg = $('#prev-arg'), _nextArg = $('#next-arg');
  if (_prevArg) _prevArg.addEventListener('click', () => setArg(STATE.currentArg - 1, {wrap: true}));
  if (_nextArg) _nextArg.addEventListener('click', () => setArg(STATE.currentArg + 1, {wrap: true}));

  // Map mode toggle (map page only)
  const _mapLocal = $('#map-mode-local'), _mapGlobal = $('#map-mode-global');
  if (_mapLocal) _mapLocal.addEventListener('click', () => {
    STATE.mapMode = 'local';
    $$('.map-mode-btn').forEach(b => b.classList.toggle('active', b.id === 'map-mode-local'));
    $$('.map-mode-btn').forEach(b => b.setAttribute('aria-pressed', b.id === 'map-mode-local' ? 'true' : 'false'));
    renderMap();
  });
  if (_mapGlobal) _mapGlobal.addEventListener('click', () => {
    STATE.mapMode = 'global';
    $$('.map-mode-btn').forEach(b => b.classList.toggle('active', b.id === 'map-mode-global'));
    $$('.map-mode-btn').forEach(b => b.setAttribute('aria-pressed', b.id === 'map-mode-global' ? 'true' : 'false'));
    renderMap();
  });

  // Brand — on text page override click to stay in-app; on map page, href="./index.html" handles it
  const _homeLink = $('#home-link');
  if (_homeLink && !document.body.dataset.initMap) {
    _homeLink.addEventListener('click', (e) => { e.preventDefault(); setProp(1); setArg(0); });
  }

  // Keyboard
  document.addEventListener('keydown', (e) => {
    const tag = (e.target && e.target.tagName) || '';
    if (tag === 'INPUT' || tag === 'TEXTAREA') return;
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    if (STATE.view === 'text') {
      if (e.key === 'ArrowRight') {
        if (e.shiftKey) { setArg(STATE.currentArg + 1, {wrap: true}); }
        else { setProp(STATE.currentProp + 1); }
        e.preventDefault();
      } else if (e.key === 'ArrowLeft') {
        if (e.shiftKey) { setArg(STATE.currentArg - 1, {wrap: true}); }
        else { setProp(STATE.currentProp - 1); }
        e.preventDefault();
      }
    }
    if (e.key === 'l' || e.key === 'L') { setLang(STATE.lang === 'en' ? 'gr' : 'en'); e.preventDefault(); }
    if (e.key === 'm' || e.key === 'M') {
      // M navigates between the two dedicated pages rather than toggling in-page views
      if (document.body.dataset.initMap) {
        window.location.href = `./index.html#prop.${STATE.currentProp}`;
      } else {
        const mapDest = STATE.currentMapRef ? `#map/${STATE.currentMapRef}` : '#map';
        window.location.href = `./youklidmap.html${mapDest}`;
      }
      e.preventDefault();
    }
    if (e.key === 't' || e.key === 'T') { toggleTheme(); e.preventDefault(); }
  });

  window.addEventListener('hashchange', () => {
    const prevView = STATE.view;
    parseHash(location.hash);
    if (STATE.view !== prevView) setView(STATE.view);
    else if (STATE.view === 'text') renderProp();
    else if (STATE.view === 'map') renderMap();
  });

  window.addEventListener('resize', () => {
    if (STATE.view === 'map') renderMap();
  });

  document.addEventListener('click', (e) => {
    const btn = e.target.closest('.fitz-marker');
    if (!btn) {
      // Close any open popover if clicking outside
      $$('.fitz-popover').forEach(p => p.remove());
      return;
    }
    e.stopPropagation();
    // Toggle: close if already open for this button
    const existing = btn.nextElementSibling;
    if (existing && existing.classList.contains('fitz-popover')) {
      existing.remove(); return;
    }
    $$('.fitz-popover').forEach(p => p.remove());
    const pop = document.createElement('span');
    pop.className = 'fitz-popover';
    pop.setAttribute('role', 'tooltip');
    const sym = btn.textContent.trim();
    pop.innerHTML = `<span class="fitz-pop-sym">${sym}</span> <span class="fitz-pop-text">${escapeHTML(btn.dataset.note)}</span>`;
    btn.insertAdjacentElement('afterend', pop);
  });
}

// ============================================================
// STATE SETTERS
// ============================================================

function setView(v) {
  STATE.view = v;
  $$('.tab').forEach(t => t.setAttribute('aria-pressed', t.dataset.view === v ? 'true' : 'false'));
  $('#text-view').classList.toggle('active', v === 'text');
  $('#map-view').classList.toggle('active', v === 'map');
  if (v === 'map') renderMap();
  else renderProp();
  updateHash();
  // Reset scroll so the target view lands at the top, not wherever the user left off.
  window.scrollTo({top: 0, left: 0, behavior: 'auto'});
}

function setLang(l) {
  STATE.lang = l;
  localStorage.setItem('youklid.lang', l);
  document.body.setAttribute('data-lang', l);
  $$('.lang').forEach(b => b.setAttribute('aria-pressed', b.dataset.lang === l ? 'true' : 'false'));
  if (STATE.view === 'text') renderProp();
  else renderMap();
}
function applyLang() {
  document.body.setAttribute('data-lang', STATE.lang);
  $$('.lang').forEach(b => b.setAttribute('aria-pressed', b.dataset.lang === STATE.lang ? 'true' : 'false'));
}

function toggleTheme() {
  STATE.theme = STATE.theme === 'parchment' ? 'dark' : 'parchment';
  localStorage.setItem('youklid.theme', STATE.theme);
  applyTheme();
}
function applyTheme() {
  document.body.setAttribute('data-theme', STATE.theme);
  $('#theme-btn').textContent = STATE.theme === 'dark' ? '☾' : '◐';
}

function setProp(n) {
  const total = STATE.data.propositions.length;
  if (n < 1) n = 1;
  if (n > total) n = total;
  STATE.currentProp = n;
  STATE.currentArg = 0;
  renderProp();
  updateHash();
  $('#center').focus({preventScroll:true});
  window.scrollTo({top: 0, left: 0, behavior: 'auto'});
}

function setArg(i, opts = {}) {
  const prop = currentProp();
  const total = prop.arguments.length;
  if (total === 0) return;
  if (i < 0) {
    if (opts.wrap && STATE.currentProp > 1) {
      setProp(STATE.currentProp - 1);
      const p = currentProp();
      STATE.currentArg = Math.max(0, p.arguments.length - 1);
      renderProp(); updateHash(); return;
    }
    i = 0;
  }
  if (i >= total) {
    if (opts.wrap && STATE.currentProp < STATE.data.propositions.length) {
      setProp(STATE.currentProp + 1); return;
    }
    i = total - 1;
  }
  STATE.currentArg = i;
  updateArgHighlight();
  scrollArgIntoView();
  updateHash();
}

// ============================================================
// RENDER: proposition view
// ============================================================

function currentProp() {
  return STATE.data.propositions[STATE.currentProp - 1];
}

function renderProp() {
  if (!$('#prop-kind')) return; // not on the text page (youklidmap.html)
  const p = currentProp();
  const lang = STATE.lang;
  // Chrome always English; only the body of the enunciation / arguments switches to Greek.
  $('#prop-kind').textContent = `Proposition ${p.n} / 48`;
  const L = $('#left-panel .panel-head h2');
  if (L) L.textContent = 'Depends on';
  $('#prop-title').textContent = lang === 'en'
    ? p.enunciation_en
    : (p.enunciation_gr ? transliterateDiagramLetters(p.enunciation_gr) : p.enunciation_en);
  // Fitzpatrick note on enunciation
  const enNote = $('#prop-enunciation-note');
  if (enNote) {
    if (p.fitzpatrick_note) {
      enNote.hidden = false;
      enNote.querySelector('.fitz-note-text').textContent = p.fitzpatrick_note;
    } else {
      enNote.hidden = true;
    }
  }

  // Bare diagram-label strings like "A B C D E F Z" are visual noise without an actual
  // figure. Hide them entirely until the live-figure feature is in place.
  const diagEl = $('#prop-diagram');
  if (diagEl) diagEl.hidden = true;
  // Live figure: load sidecar and mount if available
  const figHost = $('#prop-figure');
  if (figHost) {
    if (window._figureController) {
      window._figureController.destroy();
      window._figureController = null;
    }
    YouklidFigure.load(STATE.currentProp).then(sidecar => {
      if (!sidecar) { figHost.innerHTML = ''; figHost.hidden = true; return; }
      figHost.hidden = false;
      window._figureController = YouklidFigure.mount(figHost, sidecar);
      window._figureController.setArg(STATE.currentArg);
    });
  }
  // Enunciation re-use the title as heading; show an italicised restatement below as well?
  $('#prop-enunciation').textContent = '';

  // Arguments
  const list = $('#arguments');
  list.innerHTML = '';
  p.arguments.forEach((a, i) => {
    const li = document.createElement('li');
    li.className = 'argument';
    li.dataset.idx = String(i);
    if (a.unclear) li.classList.add('unclear');
    if (a.role && a.role !== 'step') {
      const tag = document.createElement('span');
      tag.className = `role-tag role-${a.role}`;
      tag.textContent = roleLabel(a.role);
      li.appendChild(tag);
    }
    const text = document.createElement('span');
    text.className = 'arg-text';
    text.innerHTML = renderArgText(a, lang);
    li.appendChild(text);

    // Borrowed-axiom marker: ★ star + amber highlight
    if (a.borrowed_axiom) {
      li.classList.add('has-borrowed-axiom');
      const star = document.createElement('span');
      star.className = 'borrowed-star';
      star.title = `External axiom required: ${a.borrowed_axiom}`;
      star.setAttribute('aria-label', `External axiom: ${a.borrowed_axiom}`);
      star.textContent = '★';
      li.appendChild(star);
      // Tooltip-style note showing which axiom
      const note = document.createElement('span');
      note.className = 'borrowed-axiom-note';
      note.textContent = a.borrowed_axiom.replace(/_/g, ' ');
      li.appendChild(note);
    }

    li.addEventListener('click', (ev) => {
      // Don't intercept clicks on interactive children (citations, fitz markers, the popover itself)
      if (ev.target.closest('.fitz-marker, a.cite, .borrowed-star, .deps-popover')) return;
      setArg(i);
      toggleDepsPopover(i);
    });
    list.appendChild(li);
  });

  // Nav enable/disable
  $('#prev-prop').disabled = STATE.currentProp <= 1;
  $('#next-prop').disabled = STATE.currentProp >= STATE.data.propositions.length;

  STATE.popoverForArg = null; // close any stale popover when prop changes
  updateArgHighlight();
  renderSuccessors();
}

// Heath-style transliteration of Greek capital diagram letters into the standard
// Latin alphabet so references match the English text (Α→A, Β→B, Γ→C, Δ→D, Ε→E,
// Ζ→F, Η→G, Θ→H, Κ→K, Λ→L, Μ→M, Ν→N, Ξ→X, Ο→O, Π→P, Ρ→R, Σ→S, Τ→T, Υ→U, Φ→Ph,
// Χ→Ch, Ψ→Ps, Ω→W, and the stray ∆ U+2206 → D). We apply this to the *main Greek
// source text only*, not to ordinary Greek prose — but since Euclid's prose uses
// only lowercase letters and all uppercase letters in the body are diagram labels,
// a blanket capital-letter substitution is safe.
const GR_CAP_MAP = {
  'Α':'A','Β':'B','Γ':'C','Δ':'D','Ε':'E','Ζ':'F','Η':'G','Θ':'H',
  'Ι':'I','Κ':'K','Λ':'L','Μ':'M','Ν':'N','Ξ':'X','Ο':'O','Π':'P',
  'Ρ':'R','Σ':'S','Τ':'T','Υ':'U','Φ':'Ph','Χ':'Ch','Ψ':'Ps','Ω':'W',
  '∆':'D', // U+2206 INCREMENT — Fitzpatrick uses this glyph for uppercase delta
};
const GR_CAP_RE = /[\u0391-\u03A9\u2206]/g;
function transliterateDiagramLetters(s) {
  if (!s) return s;
  return s.replace(GR_CAP_RE, ch => GR_CAP_MAP[ch] || ch);
}

function renderArgText(arg, lang) {
  let txt;
  let fellBack = false;
  if (lang === 'en') {
    txt = arg.en || '';
  } else {
    if (arg.gr && arg.gr.trim()) txt = transliterateDiagramLetters(arg.gr);
    else { txt = arg.en || ''; fellBack = true; }
  }
  // Escape
  let html = escapeHTML(txt);
  // Linkify inline citations (handles Fitzpatrick's inconsistent forms: [Prop. 1.15], [Prop 1.15],
  // [Post. 3], [Def. 1.22], [C.N. 1], [CN 1]) and re-render them in one canonical form.
  const NORM = { def: 'Def.', post: 'Post.', cn: 'C.N.', prop: 'Prop.' };
  html = html.replace(/\[(Post|Prop|Def|C\.N\.?|CN)\.?\s*([\d\.]+)\]/g, (_m, kind, num) => {
    let k = kind.toLowerCase().replace(/\./g,'');
    if (k === 'c' || k === 'cn') k = 'cn';
    let n = num.replace(/\.$/,'');
    // For Props keep full "1.N" form; for Def/Post/CN strip book prefix
    let refN = n.includes('.') ? n.split('.').slice(-1)[0] : n;
    let labelN = (k === 'prop' && n.includes('.')) ? n : refN;
    const ref   = `${k}.${refN}`;
    const label = `[${NORM[k]} ${labelN}]`;
    return `<a class="cite" href="${refToHash(ref)}" data-ref="${ref}">${label}</a>`;
  });
  // Replace Fitzpatrick footnote markers with interactive superscript buttons
  if (arg.fitzpatrick_note) {
    let markerFound = false;
    html = html.replace(/([†‡])/g, (_m, sym) => {
      markerFound = true;
      const escaped = escapeHTML(arg.fitzpatrick_note);
      return `<button class="fitz-marker" data-note="${escaped}" aria-label="Fitzpatrick note" title="${escaped}">${sym}</button>`;
    });
    // If marker wasn't in text but note exists, append a small superscript at end
    if (!markerFound) {
      const escaped = escapeHTML(arg.fitzpatrick_note);
      html += ` <button class="fitz-marker fitz-marker-sup" data-note="${escaped}" aria-label="Fitzpatrick note" title="${escaped}">†</button>`;
    }
  }
  if (fellBack) {
    html = `<em class="fallback-lang" title="No Greek sentence aligned to this argument — showing English">${html}</em>`;
  }
  // Append all inferred refs (CN, Post, Prop, Def) as inline [X. N] cite links.
  // Skip any ref whose data-ref is already present in the linkified text.
  const INFERRED_NORM = { cn: 'C.N.', post: 'Post.', prop: 'Prop.', def: 'Def.' };
  (arg.inferred || []).forEach(ref => {
    if (html.includes(`data-ref="${ref}"`)) return;
    const [k, nRaw] = ref.split('.');
    if (!INFERRED_NORM[k]) return;
    // For prop, label as "Prop. 1.N" to match the text citation style
    const labelN = k === 'prop' ? `1.${nRaw}` : nRaw;
    const label = `[${INFERRED_NORM[k]} ${labelN}]`;
    html += ` <a class="cite" href="${escapeHTML(refToHash(ref))}" data-ref="${ref}" title="${escapeHTML(refToTitle(ref))}">${label}</a>`;
  });
  return html;
}

function escapeHTML(s) {
  return s.replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;','\'':'&#39;'}[c]));
}

function updateArgHighlight() {
  const list = $('#arguments');
  $$('#arguments li.argument').forEach((li, i) => {
    li.classList.toggle('current', i === STATE.currentArg);
  });
  const p = currentProp();
  const total = p.arguments.length;
  $('#arg-status').textContent = total ? `argument ${STATE.currentArg + 1} / ${total}` : '—';
  $('#prev-arg').disabled = total === 0;
  $('#next-arg').disabled = total === 0;
  if (window._figureController) {
    window._figureController.setArg(STATE.currentArg);
  }
}

function scrollArgIntoView() {
  const li = $('#arguments li.argument.current');
  if (li) li.scrollIntoView({block:'nearest', behavior: 'smooth'});
}

// Attach click handler for citations via delegation (after each renderProp)
document.addEventListener('click', (e) => {
  const a = e.target && e.target.closest ? e.target.closest('a.cite') : null;
  if (!a) return;
  const ref = a.getAttribute('data-ref');
  if (ref) refLinkClick(e, ref);
});

function refLinkClick(ev, ref) {
  ev.preventDefault();
  const [kind, nStr] = ref.split('.');
  const n = parseInt(nStr, 10);
  if (kind === 'prop') {
    if (document.body.dataset.initMap) {
      // On map page: navigate to text page for this proposition
      window.location.href = `./index.html#prop.${n}`;
    } else {
      setProp(n);
    }
  } else {
    if (document.body.dataset.initMap) {
      // Already on map page: update selection in-place
      STATE.currentMapRef = ref;
      renderMap();
      updateHash();
    } else {
      // On text page: navigate to map page for this foundation
      window.location.href = `./youklidmap.html#map/${ref}`;
    }
  }
}

function refToHash(ref) {
  if (ref.startsWith('prop.')) {
    // On map page: links to propositions go to the text page
    if (document.body.dataset.initMap) return `./index.html#${ref}`;
    return `#${ref}`;
  }
  // Foundation ref: on map page stay in-page; on text page go to map page
  if (document.body.dataset.initMap) return `#map/${ref}`;
  return `./youklidmap.html#map/${ref}`;
}
function refToShort(ref) {
  const [k, n] = ref.split('.');
  if (k === 'def')  return `Def. ${n}`;
  if (k === 'post') return `Post. ${n}`;
  if (k === 'cn')   return `C.N. ${n}`;
  if (k === 'prop') return `§ ${n}`;
  return ref;
}
function refToTitle(ref) {
  const [k, nStr] = ref.split('.');
  const n = parseInt(nStr, 10);
  const data = STATE.data;
  if (k === 'def')  return `Def. ${n}: ${(data.definitions[n-1] || {}).en || ''}`;
  if (k === 'post') return `Post. ${n}: ${(data.postulates[n-1] || {}).en || ''}`;
  if (k === 'cn')   return `C.N. ${n}: ${(data.common_notions[n-1] || {}).en || ''}`;
  if (k === 'prop') {
    const p = data.propositions[n-1];
    return p ? `Prop. ${n}: ${p.enunciation_en}` : ref;
  }
  return ref;
}
function refToText(ref, lang = STATE.lang) {
  const [k, nStr] = ref.split('.');
  const n = parseInt(nStr, 10);
  const data = STATE.data;
  const pick = x => {
    if (!x) return '';
    if (lang === 'en') return x.en;
    return x.gr ? transliterateDiagramLetters(x.gr) : x.en;
  };
  if (k === 'def')  return pick(data.definitions[n-1]);
  if (k === 'post') return pick(data.postulates[n-1]);
  if (k === 'cn')   return pick(data.common_notions[n-1]);
  if (k === 'prop') {
    const p = data.propositions[n-1];
    if (!p) return '';
    return lang === 'en' ? p.enunciation_en : (transliterateDiagramLetters(p.enunciation_gr) || p.enunciation_en);
  }
  return '';
}
function refKindLabel(ref) {
  const k = ref.split('.')[0];
  return KIND_LABEL[k] || k;
}

// ============================================================
// RENDER: bottom successors + inline predecessor popover
// ============================================================

function renderSuccessors() {
  const p = currentProp();
  const succContainer = $('#successors');
  const bottomTitle   = $('#bottom-title');
  const propRef   = `prop.${p.n}`;
  const propUsers = (STATE.data.item_successors[propRef] || []);
  bottomTitle.textContent = `Propositions depending on Prop ${p.n}`;
  if (propUsers.length === 0) {
    succContainer.innerHTML = `<p class="panel-empty">No later proposition in Book I directly depends on this.</p>`;
  } else {
    succContainer.innerHTML = propUsers.map(n => {
      const q     = STATE.data.propositions[n-1];
      // Enunciation titles stay in the selected source language, English otherwise.
      const title = STATE.lang === 'en' ? q.enunciation_en : (transliterateDiagramLetters(q.enunciation_gr) || q.enunciation_en);
      return `<a class="succ-card" href="#prop.${n}"><span class="succ-id">Prop. ${n}</span><br>${escapeHTML(title)}</a>`;
    }).join('');
  }
}

/**
 * Toggle an inline popover beneath the double-clicked argument listing its
 * logical predecessors (explicit Fitzpatrick citations + Haiku-inferred refs).
 * Clicking the same argument again closes the popover; opening another one
 * on a different argument moves the popover.
 */
function toggleDepsPopover(i) {
  // Close any existing popover
  $$('#arguments .deps-popover').forEach(n => n.remove());
  if (STATE.popoverForArg === i) { STATE.popoverForArg = null; return; }
  STATE.popoverForArg = i;

  const p    = currentProp();
  const arg  = p.arguments[i];
  if (!arg) return;
  const preds = arg.deps || [];
  const li = $(`#arguments li.argument[data-idx="${i}"]`);
  if (!li) return;

  const box = document.createElement('div');
  box.className = 'deps-popover';
  box.setAttribute('role', 'dialog');
  box.setAttribute('aria-label', 'Logical predecessors');

  const head = document.createElement('div');
  head.className = 'deps-popover-head';
  head.innerHTML = `<span>Depends on</span>`;
  const close = document.createElement('button');
  close.className = 'deps-popover-close';
  close.setAttribute('aria-label', 'Close');
  close.textContent = '×';
  close.addEventListener('click', (ev) => {
    ev.stopPropagation();
    STATE.popoverForArg = null;
    box.remove();
  });
  head.appendChild(close);
  box.appendChild(head);

  if (preds.length === 0) {
    const msg = document.createElement('p');
    msg.className = 'deps-popover-empty';
    if (arg.unclear) {
      msg.innerHTML = 'No clear predecessor — this step is marked <strong>unclear</strong>. It may be a restatement, visual inference, or chained reasoning with no single citation.';
    } else {
      msg.textContent = `This is a ${roleLabel(arg.role) || 'step'} that introduces structure without invoking a prior item.`;
    }
    box.appendChild(msg);
  } else {
    const groups = {post:[], def:[], cn:[], prop:[]};
    preds.forEach(r => { const k = r.split('.')[0]; if (groups[k]) groups[k].push(r); });
    const order = [['post','Postulates'], ['def','Definitions'], ['cn','Common Notions'], ['prop','Propositions']];
    order.forEach(([k, title]) => {
      if (!groups[k].length) return;
      const grp = document.createElement('div');
      grp.className = 'ref-group';
      grp.innerHTML = `<h3>${title}</h3>`;
      const ul = document.createElement('ul');
      ul.className = 'ref-list';
      groups[k].forEach(ref => {
        const txt = refToText(ref);
        const liRef = document.createElement('li');
        liRef.innerHTML = `<a class="ref-link" href="${refToHash(ref)}" data-ref="${ref}"><span class="ref-id">${refToShort(ref)}</span>${escapeHTML(txt)}</a>`;
        ul.appendChild(liRef);
      });
      grp.appendChild(ul);
      box.appendChild(grp);
    });
  }

  li.appendChild(box);
}

// Clicking outside an open popover closes it.
document.addEventListener('click', (e) => {
  if (STATE.popoverForArg == null) return;
  if (e.target.closest('.deps-popover')) return;
  if (e.target.closest('#arguments li.argument')) return;   // clicks on args route through dblclick too
  $$('#arguments .deps-popover').forEach(n => n.remove());
  STATE.popoverForArg = null;
});
// Escape closes the popover.
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && STATE.popoverForArg != null) {
    $$('#arguments .deps-popover').forEach(n => n.remove());
    STATE.popoverForArg = null;
  }
});

// ============================================================
// MAP VIEW
// ============================================================

function buildMapSidebar() {
  if (!$('#map-list-posts')) return; // not on the map page
  const data = STATE.data;
  const mkItem = (ref, label) => {
    const b = document.createElement('button');
    b.className = 'map-item';
    b.textContent = label;
    b.dataset.ref = ref;
    b.addEventListener('click', () => { STATE.currentMapRef = ref; renderMap(); updateHash(); });
    return b;
  };
  const pl = $('#map-list-posts'); pl.innerHTML='';
  data.postulates.forEach(p => pl.appendChild(mkItem(`post.${p.n}`, refToShort(`post.${p.n}`))));
  const dl = $('#map-list-defs'); dl.innerHTML='';
  data.definitions.forEach(d => dl.appendChild(mkItem(`def.${d.n}`, refToShort(`def.${d.n}`))));
  const cl = $('#map-list-cns'); cl.innerHTML='';
  data.common_notions.forEach(c => cl.appendChild(mkItem(`cn.${c.n}`, refToShort(`cn.${c.n}`))));
  const ppl = $('#map-list-props'); ppl.innerHTML='';
  data.propositions.forEach(p => ppl.appendChild(mkItem(`prop.${p.n}`, refToShort(`prop.${p.n}`))));
}

function renderMap() {
  if (!$('#map-svg')) return; // not on the map page
  // Default selection = post.1
  if (!STATE.currentMapRef) STATE.currentMapRef = 'post.1';

  // Always full graph on the dedicated map page
  drawFullGraph();
  if (STATE.currentMapRef) {
    updateMapInfoStrip(STATE.currentMapRef);
    highlightMapNode(STATE.currentMapRef);
  }
}

/**
 * Draw a simple force-free layered graph.
 * Seed in the middle. Direct successors (propositions depending on seed) arranged in a ring or grid below.
 * For propositions: also show direct predecessors above (those this prop depends on).
 */
function drawMap(ref) {
  const svg = $('#map-svg');
  svg.innerHTML = '';
  const rect = svg.getBoundingClientRect();
  const W = Math.max(700, rect.width);
  const H = Math.max(500, rect.height);
  svg.setAttribute('viewBox', `0 0 ${W} ${H}`);

  const data = STATE.data;
  const successors = (data.item_successors[ref] || []).slice(); // numbers = prop numbers
  const [k, nStr] = ref.split('.');
  const n = parseInt(nStr, 10);

  // Predecessors only applicable if ref is a prop
  let preds = [];
  if (k === 'prop') {
    const pg = data.prop_graph[ref];
    if (pg) {
      preds = [
        ...pg.deps_posts,
        ...pg.deps_defs,
        ...pg.deps_cns,
        ...pg.deps_props,
      ];
    }
  }

  const ns = 'http://www.w3.org/2000/svg';
  const nodeR = 26;

  // Layout:
  //   predecessors row   (top)
  //   seed node          (middle)
  //   successors rows    (bottom, multiple rows if many)
  const topY = 80;
  const midY = H / 2;
  const botBaseY = H - 120;

  // Place predecessors in a single row at top (if any)
  const predPos = [];
  const predGap = preds.length ? Math.min(140, (W - 140) / Math.max(1, preds.length)) : 0;
  preds.forEach((pref, i) => {
    const x = 80 + i * predGap;
    predPos.push({ref: pref, x, y: topY});
  });

  // Place successors in rows of up to ~10 per row
  const succPos = [];
  const perRow = Math.min(12, Math.max(4, Math.floor((W - 120) / 90)));
  successors.forEach((sn, i) => {
    const row = Math.floor(i / perRow);
    const col = i % perRow;
    const thisRowCount = Math.min(perRow, successors.length - row * perRow);
    const gap = (W - 120) / Math.max(1, thisRowCount);
    const x = 60 + gap / 2 + col * gap;
    const y = botBaseY - (Math.floor((successors.length - 1) / perRow) - row) * 80;
    succPos.push({ref: `prop.${sn}`, x, y});
  });

  const seedPos = {ref, x: W / 2, y: midY};

  // Layer labels
  if (preds.length) {
    const t = document.createElementNS(ns, 'text');
    t.setAttribute('x', 16); t.setAttribute('y', topY + 4);
    t.setAttribute('class', 'layer-label');
    t.textContent = 'directly used by this proposition';
    svg.appendChild(t);
  }
  if (successors.length) {
    const t = document.createElementNS(ns, 'text');
    t.setAttribute('x', 16); t.setAttribute('y', botBaseY + 40);
    t.setAttribute('class', 'layer-label');
    t.textContent = 'propositions that cite this item';
    svg.appendChild(t);
  }

  // Edges
  function addEdge(x1,y1,x2,y2, cls='edge direct') {
    const p = document.createElementNS(ns, 'path');
    const dy = y2 - y1;
    const d = `M ${x1} ${y1} C ${x1} ${y1 + dy*0.5}, ${x2} ${y1 + dy*0.5}, ${x2} ${y2}`;
    p.setAttribute('d', d); p.setAttribute('class', cls);
    svg.appendChild(p);
  }
  predPos.forEach(pp => addEdge(pp.x, pp.y + nodeR*0.5, seedPos.x, seedPos.y - nodeR*0.8));
  succPos.forEach(sp => addEdge(seedPos.x, seedPos.y + nodeR*0.8, sp.x, sp.y - nodeR*0.5));

  // Nodes
  function addNode(pos, role) {
    const g = document.createElementNS(ns, 'g');
    g.setAttribute('class', `node ${role}`);
    g.setAttribute('transform', `translate(${pos.x}, ${pos.y})`);
    g.style.cursor = 'pointer';
    g.addEventListener('click', () => { STATE.currentMapRef = pos.ref; renderMap(); updateHash(); });
    const [k] = pos.ref.split('.');
    let r, label;
    if (k === 'prop') {
      r = document.createElementNS(ns, 'rect');
      r.setAttribute('x', -nodeR); r.setAttribute('y', -16);
      r.setAttribute('width', nodeR*2); r.setAttribute('height', 32);
      r.setAttribute('rx', 4);
    } else {
      r = document.createElementNS(ns, 'circle');
      r.setAttribute('r', nodeR);
    }
    g.appendChild(r);
    const t = document.createElementNS(ns, 'text');
    t.setAttribute('y', 1);
    t.textContent = refToShort(pos.ref);
    g.appendChild(t);
    // title for hover
    const title = document.createElementNS(ns, 'title');
    title.textContent = refToTitle(pos.ref);
    g.appendChild(title);
    svg.appendChild(g);
  }

  addNode(seedPos, 'seed');
  predPos.forEach(pp => addNode(pp, 'successor'));
  succPos.forEach(sp => addNode(sp, 'successor'));

  // Empty-state
  if (!preds.length && !successors.length) {
    const t = document.createElementNS(ns, 'text');
    t.setAttribute('x', W/2); t.setAttribute('y', H/2 + 60);
    t.setAttribute('class', 'layer-label'); t.setAttribute('text-anchor','middle');
    t.textContent = 'This item is self-contained in Book I — nothing here directly depends on it.';
    svg.appendChild(t);
  }
}

// ============================================================
// FULL DEPENDENCY GRAPH (global map mode)
// ============================================================

function drawFullGraph() {
  const svg = $('#map-svg');
  svg.innerHTML = '';
  const rect = svg.getBoundingClientRect();
  const W = Math.max(700, rect.width);
  const H = Math.max(600, rect.height);
  svg.setAttribute('viewBox', `0 0 ${W} ${H}`);

  const ns = 'http://www.w3.org/2000/svg';
  const data = STATE.data;
  const props = data.propositions;

  // Compute depth for each proposition:
  // depth = 1 + max depth of its prop dependencies (props with no prop deps get depth 0)
  const depthMap = {};
  const propGraph = data.prop_graph;

  function getDepth(ref) {
    if (depthMap[ref] !== undefined) return depthMap[ref];
    depthMap[ref] = -1; // guard against cycles
    const pg = propGraph[ref];
    const propDeps = pg ? pg.deps_props : [];
    if (!propDeps || propDeps.length === 0) {
      depthMap[ref] = 0;
    } else {
      let maxD = 0;
      // deps_props are full ref strings like "prop.1"
      propDeps.forEach(depRef => { maxD = Math.max(maxD, getDepth(depRef) + 1); });
      depthMap[ref] = maxD;
    }
    return depthMap[ref];
  }
  props.forEach(p => getDepth(`prop.${p.n}`));

  // Group by depth layer
  const layers = {};
  props.forEach(p => {
    const d = depthMap[`prop.${p.n}`];
    if (!layers[d]) layers[d] = [];
    layers[d].push(p.n);
  });
  const layerKeys = Object.keys(layers).map(Number).sort((a, b) => a - b);
  const numLayers = layerKeys.length;

  const padX = 32, padY = 40;
  const layerH = Math.max(48, Math.floor((H - padY * 2) / Math.max(1, numLayers)));
  const nodeW = 44, nodeH = 22, nodeRx = 4;

  // Position map: ref -> {x, y}
  const posMap = {};
  layerKeys.forEach((lk, li) => {
    const group = layers[lk];
    const count = group.length;
    const slotW = (W - padX * 2) / Math.max(1, count);
    const y = padY + li * layerH + layerH / 2;
    group.forEach((pn, i) => {
      const x = padX + slotW * i + slotW / 2;
      posMap[`prop.${pn}`] = {x, y, ref: `prop.${pn}`};
    });
  });

  // Draw edges first (under nodes)
  props.forEach(p => {
    const ref = `prop.${p.n}`;
    const pg = propGraph[ref];
    if (!pg) return;
    const from = posMap[ref];
    (pg.deps_props || []).forEach(depRef => {
      const to = posMap[depRef];  // depRef is already "prop.N"
      if (!from || !to) return;
      const path = document.createElementNS(ns, 'path');
      const dy = to.y - from.y;
      const d = `M ${from.x} ${from.y - nodeH/2} C ${from.x} ${from.y - nodeH/2 - Math.abs(dy)*0.4}, ${to.x} ${to.y + nodeH/2 + Math.abs(dy)*0.4}, ${to.x} ${to.y + nodeH/2}`;
      path.setAttribute('d', d);
      path.setAttribute('class', 'edge');
      svg.appendChild(path);
    });
  });

  // Draw nodes
  const selectedRef = STATE.currentMapRef && STATE.currentMapRef.startsWith('prop.') ? STATE.currentMapRef : null;
  props.forEach(p => {
    const ref = `prop.${p.n}`;
    const pos = posMap[ref];
    if (!pos) return;
    const isSeed = ref === selectedRef;

    const g = document.createElementNS(ns, 'g');
    g.setAttribute('class', `node ${isSeed ? 'seed' : 'successor'}`);
    g.setAttribute('transform', `translate(${pos.x}, ${pos.y})`);
    g.setAttribute('data-map-ref', ref);
    g.style.cursor = 'pointer';
    g.addEventListener('click', () => {
      STATE.currentMapRef = ref;
      updateHash();
      updateMapInfoStrip(ref);
      highlightMapNode(ref);
    });
    g.addEventListener('mouseenter', (e) => showMapTooltip(e, ref));
    g.addEventListener('mouseleave', () => hideMapTooltip());

    const r = document.createElementNS(ns, 'rect');
    r.setAttribute('x', -nodeW/2); r.setAttribute('y', -nodeH/2);
    r.setAttribute('width', nodeW); r.setAttribute('height', nodeH);
    r.setAttribute('rx', nodeRx);
    g.appendChild(r);

    const t = document.createElementNS(ns, 'text');
    t.setAttribute('y', 1);
    t.textContent = `§ ${p.n}`;
    g.appendChild(t);

    const title = document.createElementNS(ns, 'title');
    title.textContent = refToTitle(ref);
    g.appendChild(title);

    svg.appendChild(g);
  });

  // Layer depth labels on the left
  layerKeys.forEach((lk, li) => {
    const y = padY + li * layerH + layerH / 2 + 4;
    const tl = document.createElementNS(ns, 'text');
    tl.setAttribute('x', 4); tl.setAttribute('y', y);
    tl.setAttribute('class', 'layer-label');
    tl.textContent = `d${lk}`;
    svg.appendChild(tl);
  });
}

// ============================================================
// MAP INFO STRIP + HIGHLIGHT
// ============================================================

function updateMapInfoStrip(ref) {
  if (!ref) return;
  const data = STATE.data;
  const [kind, nStr] = ref.split('.');
  const n = parseInt(nStr, 10);
  const kindEl = $('#map-selected-kind');
  const titleEl = $('#map-selected-title');
  const textEl = $('#map-selected-text');
  const fitzEl = $('#map-fitz-note');
  const gotoEl = $('#map-goto-text');

  if (!kindEl) return;

  if (kind === 'prop') {
    const p = data.propositions[n - 1];
    kindEl.textContent = `Proposition ${n}`;
    titleEl.textContent = p ? (STATE.lang === 'gr' ? (p.enunciation_gr ? transliterateDiagramLetters(p.enunciation_gr) : p.enunciation_en) : p.enunciation_en) : '';
    textEl.textContent = '';
    if (gotoEl) { gotoEl.href = `./index.html#prop.${n}`; gotoEl.hidden = false; }
    if (fitzEl) fitzEl.hidden = true;
  } else {
    const labels = { post: 'Postulate', def: 'Definition', cn: 'Common Notion' };
    const key = kind === 'cn' ? 'common_notions' : kind === 'post' ? 'postulates' : 'definitions';
    const arr = data[key];
    const item = arr ? arr[n - 1] : null;
    kindEl.textContent = `${labels[kind] || kind} ${n}`;
    titleEl.textContent = item ? (STATE.lang === 'gr' ? (item.gr ? transliterateDiagramLetters(item.gr) : (item.en || '')) : (item.en || '')) : '';
    textEl.textContent = '';
    if (gotoEl) gotoEl.hidden = true;
    // Fitzpatrick note for foundations
    if (fitzEl) {
      if (item && item.fitzpatrick_note) {
        fitzEl.hidden = false;
        fitzEl.querySelector('.fitz-note-text').textContent = item.fitzpatrick_note;
      } else {
        fitzEl.hidden = true;
      }
    }
  }
}

function highlightMapNode(ref) {
  // Remove existing highlights
  $$('.map-node-selected, .map-node-adjacent').forEach(el => {
    el.classList.remove('map-node-selected', 'map-node-adjacent');
  });
  if (!ref) return;
  const data = STATE.data;

  // Find adjacent refs (predecessors + successors)
  const adjacent = new Set();
  if (ref.startsWith('prop.')) {
    const n = parseInt(ref.split('.')[1], 10);
    const p = data.propositions[n - 1];
    if (p) {
      (p.deps || []).forEach(d => adjacent.add(d));
      // Also use prop_graph deps_props if available
      const pg = data.prop_graph && data.prop_graph[ref];
      if (pg) (pg.deps_props || []).forEach(d => adjacent.add(d));
      // Find propositions that depend on this one
      data.propositions.forEach((pp, i) => {
        const ppRef = `prop.${i + 1}`;
        const ppg = data.prop_graph && data.prop_graph[ppRef];
        if (ppg && (ppg.deps_props || []).includes(ref)) adjacent.add(ppRef);
      });
    }
  }

  // Apply classes
  $$('[data-map-ref]').forEach(g => {
    const r = g.getAttribute('data-map-ref');
    if (r === ref) g.classList.add('map-node-selected');
    else if (adjacent.has(r)) g.classList.add('map-node-adjacent');
  });
}

// ============================================================
// MAP TOOLTIPS
// ============================================================

let _mapTooltip = null;
function showMapTooltip(e, ref) {
  hideMapTooltip();
  const data = STATE.data;
  const [kind, nStr] = ref.split('.');
  const n = parseInt(nStr, 10);
  let label = '';
  if (kind === 'prop') {
    const p = data.propositions[n - 1];
    const enunc = p ? (p.enunciation_en || p.title || '') : '';
    label = p ? `§ ${n} — ${enunc.slice(0, 60)}${enunc.length > 60 ? '…' : ''}` : `§ ${n}`;
  } else {
    const labels = { post: 'Post.', def: 'Def.', cn: 'C.N.' };
    const key = kind === 'cn' ? 'common_notions' : kind === 'post' ? 'postulates' : 'definitions';
    const arr = data[key];
    const item = arr ? arr[n - 1] : null;
    label = `${labels[kind] || kind} ${n}${item ? ' — ' + (item.en || '').slice(0, 50) : ''}`;
  }
  const tip = document.createElement('div');
  tip.className = 'map-tooltip';
  tip.textContent = label;
  document.body.appendChild(tip);
  const x = e.clientX + 12;
  const y = e.clientY - 8;
  tip.style.left = `${Math.min(x, window.innerWidth - tip.offsetWidth - 16)}px`;
  tip.style.top = `${y}px`;
  _mapTooltip = tip;
}
function hideMapTooltip() {
  if (_mapTooltip) { _mapTooltip.remove(); _mapTooltip = null; }
}

// ============================================================
// START
// ============================================================

init();

})();
