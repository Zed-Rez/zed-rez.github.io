/* ============================================================
   Youklid — Live figure renderer (opt-in, per-proposition).
   Pure vanilla JS + SVG. No dependencies.

   Public API:
     YouklidFigure.mount(hostEl, sidecar)   -> controller { setArg, destroy }
     YouklidFigure.load(propNumber)         -> Promise<sidecar|null>

   `sidecar` matches the schema in /site/figures/propN.json.
   Coordinates are in the sidecar's viewBox space — no math happens here
   beyond svg element creation and class toggling.
   ============================================================ */
(function (global) {
'use strict';

const SVG_NS = 'http://www.w3.org/2000/svg';
const HIGHLIGHT_MS = 900;

function svg(tag, attrs) {
  const el = document.createElementNS(SVG_NS, tag);
  if (attrs) for (const k in attrs) el.setAttribute(k, attrs[k]);
  return el;
}

function dist(p, q) { return Math.hypot(p.x - q.x, p.y - q.y); }

// Build one SVG node per element in sidecar.elements. Returns { id -> node }.
function buildElements(sidecar, layer) {
  const P = sidecar.points;
  const nodes = {};
  for (const e of sidecar.elements) {
    let node;
    if (e.kind === 'point') {
      const p = P[e.at];
      const g = svg('g', { class: 'fig-point' });
      g.appendChild(svg('circle', { cx: p.x, cy: p.y, r: 3.5, class: 'fig-dot' }));
      const tx = svg('text', { x: p.x, y: p.y, class: `fig-label fig-label-${p.label || 'right'}` });
      tx.textContent = e.at;
      g.appendChild(tx);
      node = g;
    } else if (e.kind === 'segment') {
      const a = P[e.from], b = P[e.to];
      node = svg('line', { x1: a.x, y1: a.y, x2: b.x, y2: b.y, class: 'fig-segment' });
    } else if (e.kind === 'circle') {
      const c = P[e.center], t = P[e.through];
      node = svg('circle', { cx: c.x, cy: c.y, r: dist(c, t), class: 'fig-circle' });
    } else if (e.kind === 'polygon') {
      const pts = e.vertices.map(v => `${P[v].x},${P[v].y}`).join(' ');
      node = svg('polygon', { points: pts, class: 'fig-polygon' });
    } else {
      continue;
    }
    node.setAttribute('data-fid', e.id);
    node.style.visibility = 'hidden';
    layer.appendChild(node);
    nodes[e.id] = node;
  }
  return nodes;
}

function mount(host, sidecar) {
  host.innerHTML = '';
  const [x, y, w, h] = sidecar.viewBox || [0, 0, 500, 360];
  const root = svg('svg', {
    viewBox: `${x} ${y} ${w} ${h}`,
    class: 'youklid-figure',
    role: 'img',
    'aria-label': `Figure for Proposition ${sidecar.prop}`,
  });
  const layer = svg('g', { class: 'fig-layer' });
  root.appendChild(layer);
  host.appendChild(root);

  const nodes = buildElements(sidecar, layer);

  // Reverse index: element id -> earliest step that introduces it.
  const introducedAt = {};
  sidecar.steps.forEach(s => (s.introduce || []).forEach(id => {
    if (introducedAt[id] == null) introducedAt[id] = s.arg;
  }));

  let pendingTimer = null;

  function setArg(i) {
    // Visibility: element visible iff introducedAt[id] <= i.
    for (const id in nodes) {
      const shown = introducedAt[id] != null && introducedAt[id] <= i;
      nodes[id].style.visibility = shown ? 'visible' : 'hidden';
      nodes[id].classList.remove('fig-new', 'fig-emph');
    }
    const step = sidecar.steps.find(s => s.arg === i);
    if (!step) return;
    (step.emphasize || []).forEach(id => nodes[id] && nodes[id].classList.add('fig-emph'));
    // Briefly flash elements freshly introduced at this step, plus the focus.
    const freshIds = new Set(step.introduce || []);
    if (step.focus) freshIds.add(step.focus);
    freshIds.forEach(id => nodes[id] && nodes[id].classList.add('fig-new'));
    clearTimeout(pendingTimer);
    pendingTimer = setTimeout(() => {
      freshIds.forEach(id => nodes[id] && nodes[id].classList.remove('fig-new'));
    }, HIGHLIGHT_MS);
  }

  function destroy() {
    clearTimeout(pendingTimer);
    host.innerHTML = '';
  }

  return { setArg, destroy, root };
}

async function load(propNumber) {
  try {
    const resp = await fetch(`./figures/prop${propNumber}.json`);
    if (!resp.ok) return null;
    return await resp.json();
  } catch (_e) { return null; }
}

global.YouklidFigure = { mount, load };

})(window);
