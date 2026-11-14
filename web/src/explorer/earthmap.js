// The Earth view: MapLibre GL JS on a globe projection, so the same globe
// zooms smoothly down to real imagery. All three layers live in one style
// and switching only toggles visibility, so it is instant: no reload, same
// camera, same pins (which are HTML buttons, outside the style anyway).
import * as maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
// MapLibre finds its worker next to its own file, which Vite's bundling
// moves; give it the worker's real URL instead (works in dev and build).
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?url';
import { baseSources, baseLayers, GROUND } from './tiles.js';

maplibregl.setWorkerUrl(workerUrl);

const DEFAULT_VIEW = { center: [20, 12], zoom: 1.35 };
const narrow = () => window.matchMedia('(max-width: 760px)').matches;
// On a globe, the diameter in pixels is about 163 x 2^zoom (512 px world
// width over pi). The zoom at which the globe fills a given width:
const fillZoom = (px) => Math.log2(px / 163);

export function createEarthMap(host, { onPick }) {
  let projection = 'globe';
  let layer = 'satellite';
  let markers = new Map();
  let selected = null;
  const groups = { satellite: [], terrain: [], map: [] };

  const layers = baseLayers();
  groups.satellite = layers.satellite.map((l) => l.id);
  groups.terrain = layers.terrain.map((l) => l.id);
  groups.map = layers.map.map((l) => l.id);
  const vis = (name, l) => ({ ...l, layout: { ...(l.layout || {}), visibility: name === layer ? 'visible' : 'none' } });

  const map = new maplibregl.Map({
    container: host,
    style: {
      version: 8,
      projection: { type: projection },
      sky: { 'atmosphere-blend': ['interpolate', ['linear'], ['zoom'], 0, 0.9, 4, 0.6, 7, 0] },
      sources: baseSources(),
      layers: [
        { id: 'ground', type: 'background', paint: { 'background-color': GROUND } },
        ...layers.satellite.map((l) => vis('satellite', l)),
        ...layers.map.map((l) => vis('map', l)),
        ...layers.terrain.map((l) => vis('terrain', l)),
      ],
    },
    center: DEFAULT_VIEW.center,
    zoom: DEFAULT_VIEW.zoom,
    attributionControl: false,
    dragRotate: false,
    pitchWithRotate: false,
    maxPitch: 0,
    renderWorldCopies: false,
    fadeDuration: 0,
    maxParallelImageRequests: 24,
  });
  map.touchZoomRotate.disableRotation();
  map.keyboard.disableRotation?.();
  // Credits stay visible: EOX's licence asks for attribution wherever the
  // imagery is shown, screenshots included. On a phone the full credit line
  // covered a third of the map, so there it sits just under the map instead,
  // still in full and still next to the imagery.
  const attribution = new maplibregl.AttributionControl({ compact: false });
  const stage = host.closest('.earth-stage');
  if (narrow() && stage) {
    const el = attribution.onAdd(map);
    el.classList.add('earth-attrib');
    stage.after(el);
  } else {
    map.addControl(attribution, 'bottom-left');
  }

  // A loading veil instead of a black box, until the first Earth tiles land.
  const veil = document.createElement('div');
  veil.className = 'earth-veil';
  veil.innerHTML = '<span>Loading Earth</span>';
  host.append(veil);
  // firstView resolves once the first Earth tiles are drawn (or after 6 s),
  // so the page's loading screen can wait for a real Earth, not a black box.
  let shown;
  const firstView = new Promise((res) => { shown = res; });
  const lift = () => { veil.classList.add('is-gone'); shown(); };
  map.on('sourcedata', (e) => { if (e.sourceId === 'sat-bluemarble' && e.tile) lift(); });
  setTimeout(lift, 6000);

  // After the first 'load' the style exists and layers can be toggled at
  // any time; isStyleLoaded() can be briefly false while tiles load, so it
  // is not used as the test.
  let ready = false;
  const whenReady = (fn) => (ready ? fn() : map.once('load', fn));
  map.once('load', () => { ready = true; });

  function show(name) {
    for (const [g, ids] of Object.entries(groups)) {
      for (const id of ids) {
        if (map.getLayer(id)) map.setLayoutProperty(id, 'visibility', g === name ? 'visible' : 'none');
      }
    }
  }

  return {
    map,
    firstView,
    get layer() { return layer; },
    hasLayer: (name) => groups[name].length > 0,
    setLayer(name) {
      if (name === layer || !groups[name]) return;
      layer = name;
      whenReady(() => show(name));
    },
    setProjection(name) {
      projection = name;
      whenReady(() => map.setProjection({ type: name }));
    },
    /** pins: [{ key, lat, lon, label, kind: 'twin'|'egypt'|'city', title }] */
    setPins(pins) {
      for (const m of markers.values()) m.remove();
      markers = new Map();
      for (const p of pins) {
        const el = document.createElement(p.kind === 'city' ? 'span' : 'button');
        el.className = `mpin mpin-${p.kind}`;
        if (p.kind !== 'city') {
          el.type = 'button';
          el.textContent = p.label;
          el.setAttribute('aria-label', p.title);
          el.addEventListener('click', (e) => { e.stopPropagation(); onPick(p.key); });
        } else {
          el.setAttribute('aria-hidden', 'true');
        }
        el.title = p.title;
        const marker = new maplibregl.Marker({ element: el, anchor: 'center', opacityWhenCovered: '0' })
          .setLngLat([p.lon, p.lat])
          .addTo(map);
        markers.set(p.key, marker);
      }
      this.select(selected);
    },
    select(key) {
      selected = key;
      for (const [k, m] of markers) {
        const el = m.getElement();
        const on = k === key;
        el.classList.toggle('is-on', on);
        if (on) el.setAttribute('aria-current', 'true');
        else el.removeAttribute('aria-current');
        el.style.zIndex = on ? '3' : '';
      }
    },
    /** Frame every pin, staying zoomed out enough to read the region. */
    fitPins(pins) {
      if (!pins.length) return;
      const b = new maplibregl.LngLatBounds();
      for (const p of pins) b.extend([p.lon, p.lat]);
      if (narrow() && projection === 'globe') {
        // Phone: twins spread over two continents made the globe a small
        // ball in the middle. Never frame it smaller than the map is wide;
        // the whole globe still fits, so no pin on its near side is lost.
        const cam = map.cameraForBounds(b, { padding: 24, maxZoom: 3.4 });
        const zoom = Math.max(cam?.zoom ?? 0, fillZoom(host.clientWidth * 0.94));
        map.easeTo({ center: cam?.center ?? b.getCenter(), zoom, duration: 1600, essential: true });
        return;
      }
      map.fitBounds(b, { padding: 70, maxZoom: 3.4, duration: 1600, essential: true });
    },
    flyTo(lat, lon, zoom = 11) {
      map.flyTo({ center: [lon, lat], zoom, speed: 1.1, curve: 1.4, essential: true });
    },
    zoomBy(dir) { if (dir > 0) map.zoomIn({ duration: 400 }); else map.zoomOut({ duration: 400 }); },
    resize() { map.resize(); },
  };
}
