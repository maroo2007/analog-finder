// Fills every data-driven number and image on the story page from
// public/data/, so the page stays true when the data changes.
import {
  loadTargets, loadMatches, rankInfo, continentName, shadePaths, fmtInt, fmtLatLon,
} from '../lib/data.js';

const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

function bind(key, value) {
  for (const el of $$(`[data-bind="${key}"]`)) el.textContent = value;
}

export async function fillContent() {
  const { targets, features } = await loadTargets();
  const mars = targets.filter((t) => t.world === 'mars');
  const moon = targets.filter((t) => t.world === 'moon');
  const jezero = targets.find((t) => t.id === 'jezero');
  // Jezero's twins, and every Moon region's, for the counts and the places
  // named in the text (nine small files, about 8 KB each).
  const [twins, ...moonTwins] = await Promise.all([
    loadMatches('jezero'),
    ...moon.map((t) => loadMatches(t.id).catch(() => [])),
  ]);
  const best = twins[0];
  const r = rankInfo(best);
  const allTwins = [...twins, ...moonTwins.flat()];

  bind('marsCount', fmtInt(mars.length));
  bind('moonCount', fmtInt(moon.length));
  bind('placesTotal', fmtInt(r.of));
  bind('continent', continentName(r.continent));
  bind('continentUpper', r.continent.toUpperCase());
  bind('rankText', `#${fmtInt(r.rankContinent)}`);
  bind('rankShort', `#${fmtInt(r.rankContinent)}`);
  bind('scaleMid', `#${fmtInt(Math.round(r.ofContinent / 2))}`);
  bind('scaleEnd', `#${fmtInt(r.ofContinent)}`);
  bind('egyptCoords', fmtLatLon(best.lat, best.lon));
  bind('egyptPlace', `${best.country}, ${fmtLatLon(best.lat, best.lon, 1)}`);
  const odo = document.querySelector('[data-odo-digits]');
  if (odo && !odo.childElementCount) odo.textContent = `#${fmtInt(r.rankContinent)}`;

  // The areas scored so far, from the continents the twins come from.
  const areas = [...new Set(allTwins.map((m) => rankInfo(m).continent))]
    .sort((a, b) => (a === 'Africa' ? -1 : b === 'Africa' ? 1 : a.localeCompare(b)))
    .map(continentName);
  bind('areas', listWords(areas));
  // Where the Moon's closest twins are: the countries holding the #1 twin of
  // the most Moon regions (any country with at least two, else the top one).
  const tally = new Map();
  for (const list of moonTwins) if (list[0]) tally.set(list[0].country, (tally.get(list[0].country) || 0) + 1);
  const ranked = [...tally].sort((a, b) => b[1] - a[1]);
  const lead = ranked.filter(([, n]) => n >= 2).map(([c]) => c);
  if (ranked.length) bind('moonPlaces', listWords(lead.length ? lead : [ranked[0][0]]));

  // Egypt pair: Jezero's shaded relief beside its best Earth tile.
  const sp = shadePaths(jezero);
  const marsImg = document.querySelector('[data-shade="mars"]');
  const earthImg = document.querySelector('[data-shade="earth"]');
  if (marsImg) marsImg.src = sp.world;
  if (earthImg) earthImg.src = sp.twin(1);
  const tileImg = document.querySelector('[data-shade="mars-tile"]');
  if (tileImg) tileImg.src = sp.world;

  // Closeness bars, one per feature the target was matched on.
  const dl = document.querySelector('[data-closeness]');
  if (dl) {
    dl.replaceChildren(
      ...jezero.matched_on.map((key) => {
        const f = features.find((x) => x.key === key);
        const v = best.closeness[key];
        const div = document.createElement('div');
        div.innerHTML = `<dt>${f ? f.label : key}</dt><dd><span data-close-num>${Math.round(v)}</span>%</dd>
          <span class="bar" aria-hidden="true"><span class="bar-fill" style="--p:${v / 100}"></span></span>`;
        div.dataset.value = v;
        return div;
      }),
    );
  }

  buildThumbs({ mars, moon });

  return { best, rank: r, jezero, mars, moon, features };
}

function buildThumbs(byWorld) {
  const grid = document.querySelector('[data-thumbs]');
  const name = document.querySelector('[data-thumb-name]');
  if (!grid) return;

  const show = (world) => {
    const list = byWorld[world];
    const selectedId = world === 'mars' ? 'jezero' : list[0]?.id;
    grid.replaceChildren(
      ...list.map((t) => {
        const li = document.createElement('li');
        const b = document.createElement('button');
        b.type = 'button';
        b.title = t.name;
        b.setAttribute('aria-label', t.name);
        if (t.id === selectedId) b.classList.add('is-on');
        const img = new Image();
        img.alt = '';
        img.loading = 'lazy';
        img.decoding = 'async';
        img.src = shadePaths(t).world;
        b.append(img);
        b.addEventListener('click', () => {
          grid.querySelectorAll('.is-on').forEach((x) => x.classList.remove('is-on'));
          b.classList.add('is-on');
          name.textContent = t.name;
        });
        b.addEventListener('mouseenter', () => { name.textContent = t.name; });
        li.append(b);
        return li;
      }),
    );
    const sel = list.find((t) => t.id === selectedId);
    name.textContent = sel ? sel.name : '';
  };

  for (const tab of $$('[data-world-tab]')) {
    tab.addEventListener('click', () => {
      for (const t of $$('[data-world-tab]')) t.setAttribute('aria-selected', String(t === tab));
      show(tab.dataset.worldTab);
    });
  }
  show('mars');
}

/** "A", "A and B", "A, B and C". */
function listWords(items) {
  if (items.length < 2) return items.join('');
  return `${items.slice(0, -1).join(', ')} and ${items[items.length - 1]}`;
}

/** Wrap each word of a statement so it can fill from grey to white. */
export function splitWords(el) {
  const words = el.textContent.trim().split(/\s+/);
  el.setAttribute('aria-label', el.textContent.trim());
  el.innerHTML = words.map((w) => `<span class="w" aria-hidden="true">${w}</span>`).join(' ');
  return [...el.querySelectorAll('.w')];
}
