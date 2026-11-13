// Flat maps for the Twin Finder: Mars plate carree, the Moon's south pole
// as a polar plot, and Earth as plate carree with the likeness layers.
import { dataUrl } from '../lib/data.js';

const NS = 'http://www.w3.org/2000/svg';
const el = (tag, attrs = {}, parent) => {
  const n = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, v);
  if (parent) parent.append(n);
  return n;
};

function graticule(svg, { x0, x1, y0, y1, step, toX, toY, labels, fontSize = 1 }) {
  const g = el('g', {}, svg);
  for (let lon = Math.ceil(x0 / step) * step; lon <= x1; lon += step) {
    el('line', { class: 'grat', x1: toX(lon), x2: toX(lon), y1: toY(y1), y2: toY(y0) }, g);
  }
  for (let lat = Math.ceil(y0 / step) * step; lat <= y1; lat += step) {
    el('line', { class: 'grat', x1: toX(x0), x2: toX(x1), y1: toY(lat), y2: toY(lat) }, g);
    if (labels) {
      const t = el('text', { class: 'grat-label', x: toX(x0) + fontSize * 0.6, y: toY(lat) - fontSize * 0.5, 'font-size': fontSize }, g);
      t.textContent = `${Math.abs(lat)}°${lat >= 0 ? 'N' : 'S'}`;
    }
  }
}

function marker(parent, { x, y, r, label, onSelect, color }) {
  const g = el('g', { class: 'marker', tabindex: '0', role: 'button', 'aria-label': label }, parent);
  if (color) g.style.setProperty('--c', color);
  el('circle', { class: 'ring', cx: x, cy: y, r: r * 2 }, g);
  el('circle', { class: 'dot', cx: x, cy: y, r }, g);
  const title = el('title', {}, g);
  title.textContent = label;
  g.addEventListener('click', onSelect);
  g.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onSelect(); }
  });
  return g;
}

/** Mars: the Viking colour mosaic, 360 x 180 degrees. */
export function drawMars(host, targets, onSelect) {
  host.classList.remove('is-moon');
  const W = 360; const H = 180;
  const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, role: 'group', 'aria-label': 'Map of Mars with the 38 Exploration Zones' });
  const toX = (lon) => lon + 180;
  const toY = (lat) => 90 - lat;
  el('image', { href: `${import.meta.env.BASE_URL}img/mars.jpg`, x: 0, y: 0, width: W, height: H, preserveAspectRatio: 'none', opacity: 0.85 }, svg);
  graticule(svg, { x0: -180, x1: 180, y0: -90, y1: 90, step: 30, toX, toY });
  const byId = new Map();
  for (const t of targets) {
    byId.set(t.id, marker(svg, { x: toX(t.lon), y: toY(t.lat), r: 2.1, label: t.name, onSelect: () => onSelect(t.id), color: 'var(--mars)' }));
  }
  host.replaceChildren(svg);
  return (id) => byId.forEach((g, k) => g.classList.toggle('is-on', k === id));
}

/**
 * Moon: azimuthal equidistant view of the south pole, out to 7 degrees from
 * the pole, with each Artemis region's bounding box drawn as its outline.
 */
export function drawMoon(host, targets, onSelect) {
  host.classList.add('is-moon');
  const R = 100; const maxCol = 7.2;
  const svg = el('svg', { viewBox: `${-R - 12} ${-R - 12} ${2 * R + 24} ${2 * R + 24}`, role: 'group', 'aria-label': 'The lunar south pole with the nine Artemis III regions' });
  const proj = (lat, lon) => {
    const rr = ((90 + lat) / maxCol) * R;
    const a = (lon * Math.PI) / 180;
    return [rr * Math.sin(a), rr * Math.cos(a)];
  };
  el('circle', { cx: 0, cy: 0, r: R, fill: 'var(--ground-3)' }, svg);
  for (const lat of [-89, -87, -85, -83]) {
    const rr = ((90 + lat) / maxCol) * R;
    el('circle', { class: 'grat', cx: 0, cy: 0, r: rr }, svg);
    const t = el('text', { class: 'grat-label', x: 3, y: rr - 3, 'font-size': 6 }, svg);
    t.textContent = `${Math.abs(lat)}°S`;
  }
  for (let lon = 0; lon < 360; lon += 45) {
    const [x, y] = proj(-90 + maxCol, lon);
    el('line', { class: 'grat', x1: 0, y1: 0, x2: x, y2: y }, svg);
  }
  const byId = new Map();
  for (const t of targets) {
    const g = marker(svg, { ...(() => { const [x, y] = proj(t.lat, t.lon); return { x, y }; })(), r: 2.6, label: t.name, onSelect: () => onSelect(t.id), color: 'var(--moon)' });
    if (Array.isArray(t.bbox)) {
      const [lo0, la0, lo1, la1] = t.bbox;
      const pts = [];
      for (let i = 0; i <= 8; i++) pts.push(proj(la0, lo0 + ((lo1 - lo0) * i) / 8));
      for (let i = 8; i >= 0; i--) pts.push(proj(la1, lo0 + ((lo1 - lo0) * i) / 8));
      const poly = el('polygon', { class: 'moon-region', points: pts.map((p) => p.join(',')).join(' ') });
      g.prepend(poly);
    }
    byId.set(t.id, g);
  }
  const north = el('text', { class: 'grat-label', x: 0, y: R + 9, 'text-anchor': 'middle', 'font-size': 6 }, svg);
  north.textContent = '0°';
  host.replaceChildren(svg);
  return (id) => byId.forEach((g, k) => g.classList.toggle('is-on', k === id));
}

/**
 * Earth: plate carree framed on the scored areas (the likeness layers) and
 * the pins, so it works for Africa alone and after the Americas merge.
 */
export function createEarthMap(host, layers) {
  let bounds = layers.reduce(
    (b, l) => ({
      s: Math.min(b.s, l.bounds[0][0]), w: Math.min(b.w, l.bounds[0][1]),
      n: Math.max(b.n, l.bounds[1][0]), e: Math.max(b.e, l.bounds[1][1]),
    }),
    { s: 90, w: 180, n: -90, e: -180 },
  );
  const pad = 4;
  bounds = { s: bounds.s - pad, w: bounds.w - pad, n: bounds.n + pad, e: bounds.e + pad };
  const W = bounds.e - bounds.w; const H = bounds.n - bounds.s;
  const toX = (lon) => lon - bounds.w;
  const toY = (lat) => bounds.n - lat;
  const svg = el('svg', { viewBox: `0 0 ${W} ${H}`, role: 'group', 'aria-label': 'Map of the scored dry land on Earth with numbered twins' });
  graticule(svg, { x0: bounds.w, x1: bounds.e, y0: bounds.s, y1: bounds.n, step: 10, toX, toY, labels: true, fontSize: (Math.max(W, H) / 100) * 1.6 });
  for (const l of layers) {
    const [[s, w], [n, e]] = l.bounds;
    el('image', { href: dataUrl(l.image), x: toX(w), y: toY(n), width: e - w, height: n - s, preserveAspectRatio: 'none', opacity: 0.8 }, svg);
  }
  const pinLayer = el('g', {}, svg);
  host.replaceChildren(svg);
  const scale = Math.max(W, H) / 100;

  return {
    setPins(pins, onSelect) {
      pinLayer.replaceChildren();
      const out = new Map();
      // Draw from the last rank up so #1 sits on top.
      for (const p of [...pins].reverse()) {
        const g = el('g', { class: `pin${p.egypt ? ' is-egypt' : ''}`, tabindex: '0', role: 'button', 'aria-label': p.label }, pinLayer);
        const r = 1.35 * scale;
        el('circle', { cx: toX(p.lon), cy: toY(p.lat), r }, g);
        const t = el('text', { x: toX(p.lon), y: toY(p.lat), 'font-size': r * 1.15 }, g);
        t.textContent = p.n;
        const title = el('title', {}, g);
        title.textContent = p.label;
        g.addEventListener('click', () => onSelect(p.key));
        g.addEventListener('keydown', (e) => {
          if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onSelect(p.key); }
        });
        out.set(p.key, g);
      }
      return (key) => out.forEach((g, k) => {
        g.classList.toggle('is-on', k === key);
        if (k === key) pinLayer.append(g);
      });
    },
  };
}
