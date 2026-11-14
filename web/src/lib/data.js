// Reads whatever is in public/data/: today Africa and the Americas, and
// more continents later with the same files and bigger totals. Nothing here
// hardcodes a count: every number shown on the site comes through these
// helpers.

const BASE = `${import.meta.env.BASE_URL}data/`;
const cache = new Map();

export function getJSON(path) {
  if (!cache.has(path)) {
    cache.set(
      path,
      fetch(BASE + path).then((r) => {
        if (!r.ok) throw new Error(`${path}: HTTP ${r.status}`);
        return r.json();
      }),
    );
  }
  return cache.get(path);
}

export const dataUrl = (path) => BASE + path;

export const loadTargets = () => getJSON('targets.json');
export const loadMatches = (id) => getJSON(`matches/${id}.json`);
export const loadEgypt = () => getJSON('egypt.json');
export const loadLikeness = () => getJSON('likeness.json');

/**
 * Shaded relief images for one target (render_shades.py --twins), all small
 * WebP drawn the same way: 463 m pixels, 65 km across, sun from the north-west.
 *   world     the target itself, shade/<world>/<id>.webp
 *   twin(n)   the twin in place n, 1 to 25, of matches/<id>.json
 *   egypt     the best tile in Egypt (egypt.json)
 * Only build the URL of the pair on screen, so a visitor never downloads
 * all 25 at once.
 */
export function shadePaths(target) {
  return {
    world: dataUrl(`shade/${target.world}/${target.id}.webp`),
    twin: (n) => dataUrl(`shade/earth/${target.id}_${n}.webp`),
    egypt: dataUrl(`shade/earth/${target.id}_egypt.webp`),
  };
}

/**
 * Rank of a match, overall and within its continent. egypt.json rows carry
 * no continent name (Egypt is in Africa), and files written before the
 * Americas merge had no continent fields at all; both fall back to Africa.
 */
export function rankInfo(m) {
  return {
    rank: m.rank,
    of: m.of,
    rankContinent: m.rank_continent ?? m.rank,
    ofContinent: m.of_continent ?? m.of,
    continent: m.continent ?? 'Africa',
  };
}

/** A continent as it reads in a sentence: "in Africa", "in the Americas". */
export const continentName = (c) => (c === 'Americas' ? 'the Americas' : c);

/** Likeness map layers, old single-map format or the newer `maps` list. */
export function likenessLayers(lk) {
  if (Array.isArray(lk.maps) && lk.maps.length) return lk.maps;
  return [{ area: 'africa', image: 'likeness.png', bounds: lk.bounds }];
}

const nf = new Intl.NumberFormat('en-US');
export const fmtInt = (n) => nf.format(Math.round(n));

export function fmtLat(lat, dp = 2) {
  return `${Math.abs(lat).toFixed(dp)}°${lat >= 0 ? 'N' : 'S'}`;
}
export function fmtLon(lon, dp = 2) {
  return `${Math.abs(lon).toFixed(dp)}°${lon >= 0 ? 'E' : 'W'}`;
}
export const fmtLatLon = (lat, lon, dp = 2) => `${fmtLat(lat, dp)}, ${fmtLon(lon, dp)}`;

export function mapsUrl(lat, lon) {
  return `https://www.google.com/maps/@${lat.toFixed(4)},${lon.toFixed(4)},11z/data=!3m1!1e3`;
}

/**
 * NASA Worldview (on the challenge's resource list), framed on a box about
 * 40 km across around the place, with a marker on it.
 */
export function worldviewUrl(lat, lon) {
  const dLat = 0.18;
  const dLon = dLat / Math.max(0.2, Math.cos((lat * Math.PI) / 180));
  const v = [lon - dLon, lat - dLat, lon + dLon, lat + dLat].map((x) => x.toFixed(4)).join(',');
  return `https://worldview.earthdata.nasa.gov/?v=${v}&s=${lon.toFixed(4)},${lat.toFixed(4)}`;
}

/** Copernicus Browser (Copernicus Data Space Ecosystem, also on the list). */
export function copernicusUrl(lat, lon) {
  return `https://browser.dataspace.copernicus.eu/?zoom=12&lat=${lat.toFixed(4)}&lng=${lon.toFixed(4)}`;
}
