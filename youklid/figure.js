/* ============================================================
   Youklid — Live figure renderer (opt-in, per-proposition).
   Pure vanilla JS + SVG. No dependencies.

   Public API:
     YouklidFigure.mount(hostEl, sidecar)   -> controller { setArg, destroy }
     YouklidFigure.load(propNumber)         -> Promise<sidecar|null>

   `sidecar` matches the schema in /site/figures/propN.json.

   Element kinds:
     segment  — { from, to }             straight line between two named points
     circle   — { center, through }      circle with radius = dist(center,through)
     polygon  — { vertices[] }           filled polygon
     point    — { at }                   labelled dot
     tick     — { a, b, count? }         congruence tick marks on a segment
                or { on: "seg_id", count? }
     arc      — { vertex, ray1, ray2,    angle-equality arc near a vertex
                  radius?, count? }
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

  // We need two passes: first non-tick/arc elements (so they sit below),
  // then tick/arc so they render on top.
  const sortedElements = [
    ...sidecar.elements.filter(e => e.kind !== 'tick' && e.kind !== 'arc'),
    ...sidecar.elements.filter(e => e.kind === 'tick' || e.kind === 'arc'),
  ];

  for (const e of sortedElements) {
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

    } else if (e.kind === 'tick') {
      // Congruence tick marks perpendicular to a segment.
      // Specify endpoints directly as e.a / e.b, or reference a segment via e.on.
      let pa, pb;
      if (e.on) {
        const ref = sidecar.elements.find(x => x.id === e.on);
        if (!ref || ref.kind !== 'segment') continue;
        pa = P[ref.from]; pb = P[ref.to];
      } else {
        pa = P[e.a]; pb = P[e.b];
      }
      if (!pa || !pb) continue;
      const count = e.count || 1;
      const mx = (pa.x + pb.x) / 2, my = (pa.y + pb.y) / 2;
      const dx = pb.x - pa.x, dy = pb.y - pa.y;
      const len = Math.hypot(dx, dy);
      if (len < 0.001) continue;
      // Unit perpendicular, scaled to half tick-height (7px)
      const nx = -dy / len * 7, ny = dx / len * 7;
      // Unit along-segment, scaled to inter-tick spacing (4.5px)
      const ux = dx / len * 4.5, uy = dy / len * 4.5;
      const g = svg('g', { class: 'fig-tick' });
      for (let k = 0; k < count; k++) {
        const offset = k - (count - 1) / 2;
        const ox = ux * offset, oy = uy * offset;
        g.appendChild(svg('line', {
          x1: mx + ox + nx, y1: my + oy + ny,
          x2: mx + ox - nx, y2: my + oy - ny,
        }));
      }
      node = g;

    } else if (e.kind === 'arc') {
      // Angle-equality arc drawn near a vertex.
      // Multiple arcs (count > 1) nest outward with 7px spacing.
      const v = P[e.vertex], r1 = P[e.ray1], r2 = P[e.ray2];
      if (!v || !r1 || !r2) continue;
      const baseRadius = e.radius || 22;
      const count = e.count || 1;
      const g = svg('g', { class: 'fig-arc' });
      for (let k = 0; k < count; k++) {
        const r = baseRadius + k * 7;
        const a1 = Math.atan2(r1.y - v.y, r1.x - v.x);
        const a2 = Math.atan2(r2.y - v.y, r2.x - v.x);
        const x1 = v.x + r * Math.cos(a1), y1 = v.y + r * Math.sin(a1);
        const x2 = v.x + r * Math.cos(a2), y2 = v.y + r * Math.sin(a2);
        // Sweep always takes the shorter arc through the interior of the angle.
        let diff = a2 - a1;
        while (diff >  Math.PI) diff -= 2 * Math.PI;
        while (diff < -Math.PI) diff += 2 * Math.PI;
        const sweep = diff > 0 ? 1 : 0;
        const large = Math.abs(diff) > Math.PI ? 1 : 0;
        g.appendChild(svg('path', {
          d: `M ${x1.toFixed(2)} ${y1.toFixed(2)} A ${r} ${r} 0 ${large} ${sweep} ${x2.toFixed(2)} ${y2.toFixed(2)}`,
          fill: 'none',
        }));
      }
      node = g;

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

  // Build a map: element id -> parent element id (for tick/arc emphasis propagation)
  const parentOf = {};
  for (const e of sidecar.elements) {
    if (e.kind === 'tick') {
      const parentId = e.on || null;
      if (parentId) parentOf[e.id] = parentId;
    } else if (e.kind === 'arc') {
      // arcs annotate an angle; no single parent segment, but we can propagate
      // from the first ray segment if explicitly specified via e.parent
      if (e.parent) parentOf[e.id] = e.parent;
    }
  }

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

    // Collect explicit emphasize set, then add any tick/arc whose parent is emphasized.
    const emphSet = new Set(step.emphasize || []);
    for (const [childId, parentId] of Object.entries(parentOf)) {
      if (emphSet.has(parentId)) emphSet.add(childId);
    }
    emphSet.forEach(id => nodes[id] && nodes[id].classList.add('fig-emph'));

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
