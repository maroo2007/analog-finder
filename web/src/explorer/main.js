import '../styles/base.css';
import '../styles/explorer.css';
import {
  loadTargets, loadMatches, loadEgypt, loadLikeness, likenessLayers,
  rankInfo, continentName, shadePaths, fmtInt, fmtLatLon, mapsUrl,
} from '../lib/data.js';
import { earthKm } from '../lib/geo.js';
import { drawMars, drawMoon, createEarthMap } from './maps.js';
import { createGlobe } from './globe.js';
import { createEarthMap as createEarthView } from './earthmap.js';
import { createAnalyst } from './analyst.js';

const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];

// Cities to measure "nearest twin" from: where the team is, where NASA
// trains astronauts, and large cities near the scored deserts.
const CITIES = [
  { id: 'cairo', name: 'Cairo', lat: 30.044, lon: 31.236 },
  { id: 'houston', name: 'Houston', lat: 29.76, lon: -95.37 },
  { id: 'nairobi', name: 'Nairobi', lat: -1.286, lon: 36.817 },
  { id: 'johannesburg', name: 'Johannesburg', lat: -26.204, lon: 28.047 },
  { id: 'casablanca', name: 'Casablanca', lat: 33.573, lon: -7.59 },
  { id: 'lagos', name: 'Lagos', lat: 6.524, lon: 3.379 },
  { id: 'santiago', name: 'Santiago', lat: -33.449, lon: -70.669 },
];

const WORLD = {
  mars: { map: 'mars.jpg', rim: 0xe0703a, color: '#e0703a', kind: 'Exploration Zone', start: { zoom: 4.3, pick: 7 } },
  moon: { map: 'moon_lroc.jpg', bump: 'moon_lola_bump.jpg', rim: 0xc4c9d1, color: '#c4c9d1', kind: 'Artemis III region', start: { zoom: 2.25, pick: 1.6 } },
};

const state = {
  world: 'mars', targetId: 'jezero', view: 'twins', key: null,
  sort: 'rank', city: 'cairo', earthMode: 'globe', query: '',
};
let T; let egypt = []; let layers = [];
let worldGlobe = null; let earthView = null; let earthMap = null; let highlightPin = () => {};
let webgl = true;
let current = { target: null, twins: [], egyptRow: null };
// How many dry places were scored, in total and per continent, read from
// every match row seen so far (each row carries the same totals). Sent to the
// analyst so it never relies on a typed-in count.
const coverage = { total: null, areas: new Map() };
function noteCoverage(rows) {
  for (const x of rows || []) {
    const r = rankInfo(x);
    if (r.of) coverage.total = r.of;
    if (r.ofContinent) coverage.areas.set(r.continent, r.ofContinent);
  }
}

const ARROW = '<span class="arrow-box" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M7 17 17 7M9 7h8v8"/></svg></span>';
const CHEV = (d) => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="${d === 'l' ? 'm15 6-6 6 6 6' : 'm9 6 6 6-6 6'}"/></svg>`;

const byWorld = (w) => T.targets.filter((t) => t.world === w);
const feat = (key) => T.features.find((f) => f.key === key) || { key, label: key, unit: '' };
const city = () => CITIES.find((c) => c.id === state.city);

function fmtFeature(key, v) {
  if (v == null) return 'n/a';
  const f = feat(key);
  if (key === 'albedo') return v.toFixed(3);
  if (key === 'relief') return `${Math.round(v)} ${f.unit}`;
  return `${v.toFixed(2)}${f.unit}`;
}

/* ---------- start-up ---------- */

async function init() {
  const card = $('[data-card]');
  try {
    const [targets, eg, lk] = await Promise.all([loadTargets(), loadEgypt(), loadLikeness()]);
    T = targets; egypt = eg; layers = likenessLayers(lk);
    noteCoverage(egypt);
  } catch (err) {
    console.error(err);
    card.innerHTML = '<p class="card-error">The match data could not be loaded. Serve the site from its folder (for example <code>npm run dev</code>) rather than opening the file directly.</p>';
    return;
  }

  readHash();

  $('[data-city]').replaceChildren(...CITIES.map((c) => new Option(c.name, c.id)));
  $('[data-city]').value = state.city;

  for (const b of $$('[data-world]')) b.addEventListener('click', () => setWorld(b.dataset.world));
  for (const b of $$('[data-view]')) b.addEventListener('click', () => setView(b.dataset.view));
  for (const b of $$('[data-earth-mode]')) b.addEventListener('click', () => setEarthMode(b.dataset.earthMode));
  $('[data-sort]').addEventListener('change', (e) => { state.sort = e.target.value; $('[data-city-wrap]').hidden = state.sort !== 'distance'; renderTwins(); });
  $('[data-city]').addEventListener('change', (e) => { state.city = e.target.value; renderTwins(); });
  $('[data-target-search]').addEventListener('input', (e) => { state.query = e.target.value.trim().toLowerCase(); renderTargetList(); });
  $('[data-zoom="in"]').addEventListener('click', () => earthView?.zoomBy(1));
  $('[data-zoom="out"]').addEventListener('click', () => earthView?.zoomBy(-1));
  for (const b of $$('[data-earth-layer]')) b.addEventListener('click', () => setEarthLayer(b.dataset.earthLayer));
  document.addEventListener('keydown', onKey);
  window.addEventListener('hashchange', () => {
    const before = `${state.targetId}/${state.key}`;
    readHash();
    if (`${state.targetId}/${state.key}` !== before) setWorld(state.world, state.targetId, state.key);
  });

  try {
    earthView = createEarthView($('[data-earth-view]'), { onPick: (key) => selectKey(key) });
  } catch (err) {
    console.warn('WebGL unavailable; using the flat likeness map', err);
    webgl = false;
  }
  earthMap = createEarthMap($('[data-earth-map]'), layers);
  setEarthMode(state.earthMode);

  createAnalyst({ getContext: analystContext, selectTarget: analystSelectTarget, selectTwin: analystSelectTwin });

  await setWorld(state.world, state.targetId, state.key);
}

/* ---------- what the analyst sees and can do ---------- */

function analystContext() {
  const { target, twins, egyptRow } = current;
  const m = matchFor(state.key);
  const round = (o) => (o ? Object.fromEntries(Object.entries(o).map(([k, v]) => [k, typeof v === 'number' ? Math.round(v * 1000) / 1000 : v])) : o);
  return {
    world: state.world,
    coverage: { dry_places_scored: coverage.total, by_continent: Object.fromEntries(coverage.areas) },
    target: target && {
      id: target.id, name: target.name, world: target.world, lat: target.lat, lon: target.lon,
      matched_on: target.matched_on, features: round(target.features), best_score: target.best_score,
    },
    feature_labels: Object.fromEntries(T.features.map((f) => [f.key, `${f.label}${f.unit ? ` (${f.unit})` : ''}`])),
    twins: twins.map((x, i) => ({
      n: i + 1, country: x.country, continent: x.continent ?? 'Africa', lat: x.lat, lon: x.lon,
      score: x.score, rank: x.rank, of: x.of,
      rank_in_continent: x.rank_continent ?? x.rank, of_in_continent: x.of_continent ?? x.of,
      closeness_percent: x.closeness, features: round(x.features),
    })),
    selected: state.key === 'egypt'
      ? { kind: 'best place in Egypt', ...(egyptRow || {}) }
      : (m ? { kind: 'twin', n: Number(state.key.slice(1)) + 1, country: m.country } : null),
    best_in_egypt_for_this_target: egyptRow,
    best_in_egypt_for_every_target: egypt.map((e) => ({ ...e, name: T.targets.find((t) => t.id === e.target)?.name })),
    all_targets: T.targets.map((t) => ({ id: t.id, name: t.name, world: t.world, best_score: t.best_score })),
  };
}

async function analystSelectTarget(idOrName) {
  const q = String(idOrName || '').toLowerCase().trim();
  const t = T.targets.find((x) => x.id === q) || T.targets.find((x) => x.name.toLowerCase() === q)
    || T.targets.find((x) => x.name.toLowerCase().includes(q) && q.length > 2);
  if (!t) return false;
  if (t.world !== state.world) await setWorld(t.world, t.id);
  else await selectTarget(t.id);
  return t.name;
}

function analystSelectTwin(n) {
  const key = `r${n - 1}`;
  const m = current.twins[n - 1];
  if (!m) return false;
  selectKey(key);
  return `Showing twin ${n}: ${m.country}`;
}

/* ---------- URL: #target, #target/3, #target/egypt ---------- */

function readHash() {
  const [id, which] = decodeURIComponent(location.hash.slice(1)).split('/');
  const t = T.targets.find((x) => x.id === id);
  if (!t) return;
  state.world = t.world;
  state.targetId = t.id;
  state.key = which === 'egypt' ? 'egypt' : (Number(which) > 0 ? `r${Number(which) - 1}` : null);
}
function writeHash() {
  const which = state.key === 'egypt' ? '/egypt' : (state.key && state.key !== 'r0' ? `/${Number(state.key.slice(1)) + 1}` : '');
  const h = `#${state.targetId}${which}`;
  if (location.hash !== h) history.replaceState(null, '', h);
}

/* ---------- world and target ---------- */

let globeWorld = null; // which world the left globe is showing now

async function setWorld(world, targetId, key) {
  const changed = world !== globeWorld || !worldGlobe;
  state.world = world;
  for (const b of $$('[data-world]')) b.setAttribute('aria-checked', String(b.dataset.world === world));
  const list = byWorld(world);
  $('[data-world-heading]').textContent = world === 'mars'
    ? `Mars · ${list.length} Exploration Zones`
    : `Moon · ${list.length} Artemis III regions`;

  const next = targetId && list.some((t) => t.id === targetId) ? targetId : (world === 'mars' ? 'jezero' : list[0].id);

  if (changed) {
    const host = $('[data-world-globe]');
    worldGlobe?.destroy();
    worldGlobe = null;
    host.replaceChildren();
    const w = WORLD[world];
    const first = T.targets.find((t) => t.id === next);
    if (webgl) {
      try {
        worldGlobe = await createGlobe(host, {
          map: w.map, bump: w.bump, rimColor: w.rim, label: `${world === 'mars' ? 'Mars' : 'Moon'} globe with the target sites`,
          start: world === 'moon' ? { lat: -84, lon: first.lon } : { lat: first.lat, lon: first.lon },
          startZoom: w.start.zoom, minZoom: world === 'moon' ? 1.25 : 1.5, maxZoom: 5, pickRadius: w.start.pick,
        });
        worldGlobe.onPick((id) => selectTarget(id));
        worldGlobe.setMarkers(list.map((t) => ({ key: t.id, lat: t.lat, lon: t.lon, label: '', fill: w.color, stroke: '#06080b', size: 0.62 })));
        if (world === 'moon') worldGlobe.setOutlines(list.map((t) => t.bbox).filter(Boolean), 0xf3f5f7);
      } catch (err) {
        console.warn(err);
      }
    }
    if (!worldGlobe) {
      const draw = world === 'mars' ? drawMars : drawMoon;
      host.classList.add('map');
      const hl = draw(host, list, selectTarget);
      worldGlobe = { setMarkers() {}, select: (id) => hl(id), flyTo() {}, destroy() { host.replaceChildren(); host.classList.remove('map'); } };
    }
    globeWorld = world;
  }

  renderTargetList();
  await selectTarget(next, key);
}

function renderTargetList() {
  const host = $('[data-target-list]');
  const list = byWorld(state.world)
    .filter((t) => !state.query || t.name.toLowerCase().includes(state.query))
    .sort((a, b) => a.name.localeCompare(b.name));
  if (!list.length) {
    host.innerHTML = '<li class="empty">No site matches that name</li>';
    return;
  }
  host.replaceChildren(...list.map((t) => {
    const li = document.createElement('li');
    const b = document.createElement('button');
    b.type = 'button';
    b.dataset.id = t.id;
    if (t.id === state.targetId) b.setAttribute('aria-current', 'true');
    b.innerHTML = `<span>${t.name}</span><span class="best" title="Best score">${t.best_score != null ? t.best_score.toFixed(1) : ''}</span>`;
    b.addEventListener('click', () => selectTarget(t.id));
    li.append(b);
    return li;
  }));
}

async function selectTarget(id, key = null) {
  state.targetId = id;
  const target = T.targets.find((t) => t.id === id);
  worldGlobe?.select(id, { fill: '#f3f5f7', stroke: WORLD[target.world].color, size: 0.62 });
  worldGlobe?.flyTo(target.lat, target.lon);
  for (const b of $$('[data-target-list] button')) {
    if (b.dataset.id === id) b.setAttribute('aria-current', 'true');
    else b.removeAttribute('aria-current');
  }

  $('[data-target-kind]').textContent = WORLD[target.world].kind;
  $('[data-target-name]').textContent = target.name;
  $('[data-target-feats]').innerHTML = (target.matched_on || []).map((k) => `<div><dt>${feat(k).label}</dt><dd>${fmtFeature(k, target.features?.[k])}</dd></div>`).join('');

  $('[data-card]').innerHTML = '<p class="card-loading">Loading twins</p>';
  let twins = [];
  try { twins = await loadMatches(id); } catch (err) { console.error(err); }
  if (state.targetId !== id) return; // a newer click won
  noteCoverage(twins);
  const egyptRow = egypt.find((e) => e.target === id) || null;
  current = { target, twins, egyptRow };
  state.key = key && (key === 'egypt' ? egyptRow : twins[Number(key.slice(1))]) ? key : (twins.length ? 'r0' : (egyptRow ? 'egypt' : null));

  const of = twins[0] ? rankInfo(twins[0]).of : egyptRow?.of;
  $('[data-earth-heading]').textContent = `Closest places on Earth to ${target.name}`;
  $('[data-earth-note]').textContent = of ? `Top ${twins.length} of ${fmtInt(of)} dry places scored` : '';

  renderTwins({ fit: true });
}

/* ---------- twins ---------- */

function orderedTwins() {
  const list = current.twins.map((m, i) => ({ m, i, key: `r${i}`, n: i + 1 }));
  if (state.sort === 'distance') {
    const c = city();
    for (const x of list) x.km = earthKm(c, x.m);
    list.sort((a, b) => a.km - b.km);
  }
  return list;
}

function renderTwins({ fit = false } = {}) {
  const { twins, egyptRow, target } = current;
  if (!target) return;
  const list = orderedTwins();
  const c = state.sort === 'distance' ? city() : null;

  // Earth pins: numbered twins, Egypt's best place, the chosen city.
  const pins = list.map((x) => ({ key: x.key, lat: x.m.lat, lon: x.m.lon, label: String(x.n), kind: 'twin', title: `Twin ${x.n}: ${x.m.country}` }));
  const egyptInTop = egyptRow && twins.some((m) => m.rank === egyptRow.rank);
  if (egyptRow && !egyptInTop) pins.push({ key: 'egypt', lat: egyptRow.lat, lon: egyptRow.lon, label: 'E', kind: 'egypt', title: 'Best place in Egypt' });
  if (c) pins.push({ key: `city-${c.id}`, lat: c.lat, lon: c.lon, label: '', kind: 'city', title: c.name });
  earthView?.setPins(pins);

  const svgPins = pins.filter((p) => p.kind !== 'city').map((p) => ({ key: p.key, n: p.label, lat: p.lat, lon: p.lon, egypt: p.kind === 'egypt', label: p.title }));
  highlightPin = earthMap.setPins(svgPins, (key) => selectKey(key));

  renderStrip(list);
  // A new target frames all its twins; picking one then flies down to it.
  if (fit) {
    earthView?.fitPins(pins);
    selectKey(state.key, { fly: state.key !== 'r0' });
  } else {
    selectKey(state.key, { fly: false });
  }
}

function renderStrip(list) {
  const host = $('[data-twin-list]');
  if (state.view === 'egypt') return renderEgyptTable(host);
  if (!list.length) {
    host.innerHTML = '<li class="empty">No twins are stored for this target yet.</li>';
    return;
  }
  host.replaceChildren(...list.map((x) => {
    const li = document.createElement('li');
    const b = document.createElement('button');
    b.type = 'button';
    b.dataset.key = x.key;
    const meta = state.sort === 'distance' ? `${fmtInt(x.km)} km · ${x.m.score.toFixed(1)}` : `#${fmtInt(x.m.rank)} · ${x.m.score.toFixed(1)}`;
    b.innerHTML = `<span class="n">${x.n}</span><span class="where">${x.m.country}</span><span class="meta">${meta}</span>`;
    b.addEventListener('click', () => selectKey(x.key));
    li.append(b);
    return li;
  }));
}

function renderEgyptTable(host) {
  const rows = egypt.map((e) => ({ e, t: T.targets.find((x) => x.id === e.target) }))
    .filter((r) => r.t && r.t.world === state.world)
    .sort((a, b) => a.e.rank - b.e.rank);
  const li = document.createElement('li');
  li.className = 'egypt-wrap';
  li.innerHTML = `<table class="egypt-table">
    <caption class="visually-hidden">Best place in Egypt for each ${state.world === 'mars' ? 'Mars zone' : 'Moon region'}</caption>
    <thead><tr><th scope="col">Target</th><th scope="col">Rank</th><th scope="col">Score</th><th scope="col">Place</th></tr></thead>
    <tbody></tbody></table>`;
  const tb = $('tbody', li);
  for (const { e, t } of rows) {
    const tr = document.createElement('tr');
    if (t.id === state.targetId) tr.setAttribute('aria-current', 'true');
    tr.innerHTML = `<td><button type="button">${t.name}</button></td><td>#${fmtInt(e.rank)}</td><td>${e.score.toFixed(1)}</td><td>${fmtLatLon(e.lat, e.lon, 1)}</td>`;
    tr.addEventListener('click', () => selectTarget(t.id, 'egypt'));
    tb.append(tr);
  }
  host.replaceChildren(li);
}

function selectKey(key, { fly = true } = {}) {
  if (!key || key.startsWith('city')) return;
  state.key = key;
  writeHash();
  earthView?.select(key);
  highlightPin(key);
  for (const b of $$('[data-twin-list] button[data-key]')) {
    if (b.dataset.key === key) {
      b.setAttribute('aria-current', 'true');
      b.scrollIntoView({ block: 'nearest', inline: 'nearest' });
    } else {
      b.removeAttribute('aria-current');
    }
  }
  const m = matchFor(key);
  if (m && fly) earthView?.flyTo(m.lat, m.lon, 11);
  renderCard();
}

function matchFor(key) {
  const { twins, egyptRow } = current;
  if (key === 'egypt' && egyptRow) {
    const i = twins.findIndex((x) => x.rank === egyptRow.rank);
    return i >= 0 ? twins[i] : { ...egyptRow, country: 'Egypt' };
  }
  return twins[Number(key?.slice(1))] || null;
}

function step(dir) {
  if (state.view === 'egypt') return;
  const list = orderedTwins();
  const i = list.findIndex((x) => x.key === state.key);
  const next = list[Math.min(list.length - 1, Math.max(0, (i < 0 ? 0 : i) + dir))];
  if (next) selectKey(next.key);
}

function onKey(e) {
  const tag = (e.target.tagName || '').toLowerCase();
  if (['input', 'select', 'textarea'].includes(tag) || e.target.classList?.contains('globe-canvas')) return;
  if (e.key === 'ArrowRight') { e.preventDefault(); step(1); }
  if (e.key === 'ArrowLeft') { e.preventDefault(); step(-1); }
}

function setView(view) {
  state.view = view;
  for (const b of $$('[data-view]')) b.setAttribute('aria-selected', String(b.dataset.view === view));
  $('.twin-tools').hidden = view === 'egypt';
  if (view === 'egypt' && current.egyptRow) state.key = 'egypt';
  renderTwins();
}

/** Globe or flat (Mercator): the same imagery, pins and camera. */
function setEarthMode(mode) {
  state.earthMode = mode === 'mercator' ? 'mercator' : 'globe';
  for (const b of $$('[data-earth-mode]')) b.setAttribute('aria-checked', String(b.dataset.earthMode === state.earthMode));
  // Without WebGL the only Earth view is the flat likeness map.
  $('[data-earth-view]').hidden = !webgl;
  $('[data-earth-map]').hidden = webgl;
  $('.earth-stage').classList.toggle('is-map', !webgl);
  $('.earth-switches').hidden = !webgl;
  earthView?.setProjection(state.earthMode);
}

/** Satellite, map or terrain: switching keeps the camera and the pins. */
function setEarthLayer(name) {
  state.layer = name;
  for (const b of $$('[data-earth-layer]')) b.setAttribute('aria-checked', String(b.dataset.earthLayer === name));
  earthView?.setLayer(name);
}

/* ---------- the twin card ---------- */

function renderCard() {
  const card = $('[data-card]');
  const { target, twins } = current;
  if (!target) return;
  const key = state.key;
  const m = matchFor(key);
  if (!m) {
    card.innerHTML = `<h2 id="card-heading" class="pane-title">${target.name}</h2><p class="card-error">No twins are stored for this target yet.</p>`;
    return;
  }
  const isMoon = target.world === 'moon';
  const isEgypt = key === 'egypt';
  const index = twins.indexOf(m);
  const r = rankInfo(m);
  const sp = shadePaths(target);
  // Only the pair on screen is requested: the card is the one place that
  // shows twin reliefs, and it holds one twin at a time.
  const earthImg = isEgypt ? sp.egypt : sp.twin(index + 1);
  const keys = target.matched_on || Object.keys(m.closeness || {});
  const close = m.closeness || null;
  const list = orderedTwins();
  const pos = list.findIndex((x) => x.key === key);
  const c = city();

  const continentLine = (m.continent || r.ofContinent !== r.of)
    ? `<strong>#${fmtInt(r.rankContinent)}</strong> of ${fmtInt(r.ofContinent)} in ${continentName(r.continent)}`
    : `among the dry places scored in ${continentName(r.continent)}`;

  const relief = `<div data-relief>
      <div class="compare" style="--cut:50%">
        <img src="${earthImg}" alt="Shaded relief of the matching place in ${m.country}" decoding="async" data-shade-img>
        <img class="over" src="${sp.world}" alt="Shaded relief of ${target.name}" decoding="async" data-shade-img>
        <input type="range" min="0" max="100" value="50" aria-label="Slide to compare ${target.name} with ${m.country}" data-compare>
        <span class="handle" aria-hidden="true"></span>
      </div>
      <div class="compare-tags"><span><i style="--c:${WORLD[target.world].color}"></i>${target.name}</span><span>${m.country}<i style="--c:var(--earth)"></i></span></div>
    </div>`;

  let print = '<p class="card-note">The per-feature breakdown is stored for the top 25 twins only.</p>';
  let verdict = '';
  if (close) {
    print = `<div class="print">
      <div class="print-head"><h3 class="pane-title">Fingerprint</h3>
        <p class="print-key"><span><i style="--c:${WORLD[target.world].color}"></i>${target.name}</span><span><i style="--c:var(--earth)"></i>This place</span></p></div>
      ${keys.map((k) => {
        // One scale per feature, spanning the target and all its stored twins.
        const vals = [target.features?.[k], ...twins.map((x) => x.features?.[k])].filter((v) => v != null);
        const lo = Math.min(...vals); const hi = Math.max(...vals);
        const at = (v) => (hi > lo ? ((v - lo) / (hi - lo)) * 100 : 50);
        const a = at(target.features?.[k]); const b = at(m.features?.[k]);
        return `<div class="feat">
          <div class="feat-top"><span>${feat(k).label}</span><b>${Math.round(close[k])}% close</b></div>
          <div class="feat-scale" aria-hidden="true">
            <span class="gap" style="left:${Math.min(a, b)}%;width:${Math.abs(a - b)}%"></span>
            <span class="dot" style="left:${a}%;--c:${WORLD[target.world].color}"></span>
            <span class="dot" style="left:${b}%;--c:var(--earth)"></span>
          </div>
          <div class="feat-vals"><span>${fmtFeature(k, target.features?.[k])}</span><span>${fmtFeature(k, m.features?.[k])}</span></div>
        </div>`;
      }).join('')}
    </div>`;
    const sorted = [...keys].sort((x, y) => close[y] - close[x]);
    const bestK = sorted[0]; const worstK = sorted[sorted.length - 1];
    verdict = `<div class="verdict">
      <p>Matches best on <strong>${feat(bestK).label.toLowerCase()}</strong> (${Math.round(close[bestK])}% close).</p>
      <p>Weakest on <strong>${feat(worstK).label.toLowerCase()}</strong> (${Math.round(close[worstK])}% close).</p>
    </div>`;
  }

  card.innerHTML = `
    <div class="card-top">
      <h2 id="card-heading" class="pane-title">${isEgypt ? `Best place in Egypt for ${target.name}` : `Twin ${index + 1} of ${twins.length} · ${target.name}`}</h2>
      ${isEgypt ? '' : `<div class="card-step">
        <button type="button" data-step="-1" aria-label="Previous twin" ${pos <= 0 ? 'disabled' : ''}>${CHEV('l')}</button>
        <button type="button" data-step="1" aria-label="Next twin" ${pos >= list.length - 1 ? 'disabled' : ''}>${CHEV('r')}</button>
      </div>`}
    </div>
    <p class="card-rank num">#${fmtInt(r.rank)}<small>of ${fmtInt(r.of)}</small></p>
    <p class="card-sub">${continentLine}</p>
    <p class="card-score">Score <b>${m.score.toFixed(1)}</b> / 100</p>
    ${isMoon ? '<p class="card-note">Moon scores are low because the lunar south pole is far rougher than almost any dry land on Earth. The rank is the useful number: these are the closest places there are.</p>' : ''}
    <p class="card-place">${m.country}</p>
    <p class="card-coords">${fmtLatLon(m.lat, m.lon)}</p>
    ${state.sort === 'distance' ? `<p class="card-dist">${fmtInt(earthKm(c, m))} km from ${c.name}</p>` : ''}
    ${relief}
    ${print}
    ${verdict}
    <p class="card-limits">Gravity, air and radiation: no place on Earth copies these.</p>
    <div class="card-actions">
      <a class="btn-maps" href="${mapsUrl(m.lat, m.lon)}" target="_blank" rel="noopener">Open in Google Maps ${ARROW}</a>
      <button type="button" class="btn-ghost" data-copy>Copy link</button>
    </div>`;

  card.querySelectorAll('[data-step]').forEach((b) => b.addEventListener('click', () => step(Number(b.dataset.step))));
  const range = $('[data-compare]', card);
  range.addEventListener('input', () => range.closest('.compare').style.setProperty('--cut', `${range.value}%`));
  // If a relief image is ever missing, leave its half as an empty panel
  // rather than a broken-image icon.
  card.querySelectorAll('[data-shade-img]').forEach((img) => img.addEventListener('error', () => { img.hidden = true; }, { once: true }));
  $('[data-copy]', card).addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(location.href);
      toast('Link copied');
    } catch {
      toast('Copy the address bar to share this twin');
    }
  });
}

let toastTimer;
function toast(text) {
  let t = $('.toast');
  if (!t) { t = document.createElement('p'); t.className = 'toast'; t.setAttribute('role', 'status'); document.body.append(t); }
  t.textContent = text;
  t.classList.add('is-on');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.remove('is-on'), 1800);
}

init();
