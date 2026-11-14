// An interactive globe for the Twin Finder: drag to turn, wheel or pinch to
// zoom, click to pick the nearest marker, arrow keys when focused. It only
// renders while something is moving.
import * as THREE from 'three';
import { DEG, latLonToVec, vecToLatLon, faceLon, angleDeg } from '../lib/geo.js';

const IMG = `${import.meta.env.BASE_URL}img/`;
const loader = new THREE.TextureLoader();
const texCache = new Map();
function texture(file, color = true) {
  if (!texCache.has(file)) {
    texCache.set(file, new Promise((res, rej) => loader.load(IMG + file, (t) => {
      if (color) t.colorSpace = THREE.SRGBColorSpace;
      t.anisotropy = 8;
      res(t);
    }, undefined, rej)));
  }
  return texCache.get(file);
}

/** A round marker sprite, optionally numbered. */
function markerTexture({ label = '', fill, stroke, text = '#06080b', dashed = false }) {
  const s = 128;
  const c = document.createElement('canvas');
  c.width = s; c.height = s;
  const g = c.getContext('2d');
  g.beginPath();
  g.arc(s / 2, s / 2, s / 2 - 10, 0, Math.PI * 2);
  g.fillStyle = fill;
  g.fill();
  g.lineWidth = 8;
  g.strokeStyle = stroke;
  if (dashed) g.setLineDash([14, 10]);
  g.stroke();
  if (label !== '') {
    g.fillStyle = text;
    g.font = `800 ${String(label).length > 1 ? 54 : 64}px "Archivo Variable", Archivo, sans-serif`;
    g.textAlign = 'center';
    g.textBaseline = 'middle';
    g.fillText(String(label), s / 2, s / 2 + 4);
  }
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

export async function createGlobe(host, {
  map, bump, rimColor = 0xffffff, label = 'Globe', start = { lat: 0, lon: 0 }, startZoom = 3.2,
  minZoom = 1.6, maxZoom = 5, pickRadius = 6,
}) {
  const canvas = document.createElement('canvas');
  canvas.className = 'globe-canvas';
  canvas.tabIndex = 0;
  canvas.setAttribute('role', 'application');
  canvas.setAttribute('aria-label', `${label}. Drag or use the arrow keys to turn, scroll or plus and minus to zoom.`);
  host.append(canvas);

  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.setClearColor(0x000000, 0);
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(32, 1, 0.05, 50);
  camera.position.set(0, 0, startZoom);

  // Even light from the viewer's side: a tool should show the whole face.
  scene.add(new THREE.AmbientLight(0xffffff, 1.1));
  const key = new THREE.DirectionalLight(0xffffff, 1.4);
  key.position.set(-2, 1.5, 4);
  scene.add(key);

  const globe = new THREE.Group();
  scene.add(globe);
  const [mapTex, bumpTex] = await Promise.all([texture(map), bump ? texture(bump, false) : null]);
  const body = new THREE.Mesh(
    new THREE.SphereGeometry(1, 128, 64),
    new THREE.MeshStandardMaterial({ map: mapTex, bumpMap: bumpTex || null, bumpScale: bumpTex ? 2 : 0, roughness: 1, metalness: 0 }),
  );
  globe.add(body);
  const rim = new THREE.Mesh(
    new THREE.SphereGeometry(1.02, 64, 32),
    new THREE.ShaderMaterial({
      uniforms: { uColor: { value: new THREE.Color(rimColor) } },
      vertexShader: 'varying vec3 vN; varying vec3 vV; void main(){ vec4 mv = modelViewMatrix*vec4(position,1.); vN = normalize(normalMatrix*normal); vV = normalize(-mv.xyz); gl_Position = projectionMatrix*mv; }',
      fragmentShader: 'uniform vec3 uColor; varying vec3 vN; varying vec3 vV; void main(){ float f = pow(1. - max(dot(vN,vV),0.), 3.); gl_FragColor = vec4(uColor, f*0.55); }',
      transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
    }),
  );
  scene.add(rim);
  renderer.initTexture(mapTex);
  if (bumpTex) renderer.initTexture(bumpTex);

  const markerLayer = new THREE.Group();
  const outlineLayer = new THREE.Group();
  globe.add(outlineLayer, markerLayer);

  // View state: yaw/pitch turn the globe, zoom is the camera distance.
  const view = { yaw: faceLon(start.lon), pitch: start.lat * DEG, zoom: startZoom };
  const goal = { ...view };
  let markers = [];
  let selectedKey = null;
  let onPick = () => {};

  function resize() {
    const r = host.getBoundingClientRect();
    const w = Math.max(1, r.width); const h = Math.max(1, r.height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    wake();
  }
  new ResizeObserver(resize).observe(host);

  // Render on demand.
  let raf = 0;
  function wake() { if (!raf) raf = requestAnimationFrame(frame); }
  function frame() {
    raf = 0;
    const k = 0.16;
    let moving = false;
    for (const f of ['yaw', 'pitch', 'zoom']) {
      const d = goal[f] - view[f];
      if (Math.abs(d) > 1e-4) { view[f] += d * k; moving = true; } else view[f] = goal[f];
    }
    globe.rotation.set(view.pitch, view.yaw, 0, 'XYZ');
    camera.position.set(0, 0, view.zoom);
    // Markers keep a constant size on screen whatever the zoom.
    const s = (view.zoom - 1) * 0.045;
    for (const m of markers) m.sprite.scale.setScalar(s * (m.key === selectedKey ? 1.45 : 1) * (m.size || 1));
    renderer.render(scene, camera);
    if (moving || dragging) wake();
  }

  // ---- Interaction ----
  let dragging = false; let moved = 0; let last = null;
  const pointers = new Map(); let pinch0 = 0; let zoom0 = 0;
  canvas.addEventListener('pointerdown', (e) => {
    canvas.setPointerCapture(e.pointerId);
    pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
    if (pointers.size === 2) {
      const [a, b] = [...pointers.values()];
      pinch0 = Math.hypot(a.x - b.x, a.y - b.y); zoom0 = goal.zoom;
    }
    dragging = true; moved = 0; last = { x: e.clientX, y: e.clientY };
    canvas.classList.add('is-dragging');
  });
  canvas.addEventListener('pointermove', (e) => {
    if (!pointers.has(e.pointerId)) return;
    pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
    if (pointers.size === 2) {
      const [a, b] = [...pointers.values()];
      const d = Math.hypot(a.x - b.x, a.y - b.y);
      if (pinch0) goal.zoom = clampZoom(zoom0 * (pinch0 / d));
      wake();
      return;
    }
    const dx = e.clientX - last.x; const dy = e.clientY - last.y;
    moved += Math.abs(dx) + Math.abs(dy);
    last = { x: e.clientX, y: e.clientY };
    const speed = (view.zoom - 1) * 0.0032;
    goal.yaw += dx * speed;
    goal.pitch = clampPitch(goal.pitch + dy * speed);
    view.yaw = goal.yaw; view.pitch = goal.pitch;
    wake();
  });
  const end = (e) => {
    pointers.delete(e.pointerId);
    if (pointers.size < 2) pinch0 = 0;
    if (pointers.size === 0) {
      dragging = false;
      canvas.classList.remove('is-dragging');
      if (moved < 6 && e.type === 'pointerup') pick(e);
    }
  };
  canvas.addEventListener('pointerup', end);
  canvas.addEventListener('pointercancel', end);
  canvas.addEventListener('wheel', (e) => {
    e.preventDefault();
    goal.zoom = clampZoom(goal.zoom * (1 + Math.sign(e.deltaY) * 0.12));
    wake();
  }, { passive: false });
  canvas.addEventListener('keydown', (e) => {
    const step = 6 * DEG;
    const keys = {
      ArrowLeft: () => { goal.yaw += step; }, ArrowRight: () => { goal.yaw -= step; },
      ArrowUp: () => { goal.pitch = clampPitch(goal.pitch + step); }, ArrowDown: () => { goal.pitch = clampPitch(goal.pitch - step); },
      '+': () => { goal.zoom = clampZoom(goal.zoom * 0.85); }, '=': () => { goal.zoom = clampZoom(goal.zoom * 0.85); },
      '-': () => { goal.zoom = clampZoom(goal.zoom * 1.18); },
    };
    if (keys[e.key]) { e.preventDefault(); e.stopPropagation(); keys[e.key](); wake(); }
  });
  const clampZoom = (z) => Math.min(maxZoom, Math.max(minZoom, z));
  const clampPitch = (p) => Math.min(88 * DEG, Math.max(-88 * DEG, p));

  const ray = new THREE.Raycaster();
  function pick(e) {
    const r = canvas.getBoundingClientRect();
    const ndc = new THREE.Vector2(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
    ray.setFromCamera(ndc, camera);
    const hit = ray.intersectObject(body, false)[0];
    if (!hit) return;
    const local = globe.worldToLocal(hit.point.clone());
    const ll = vecToLatLon(local);
    // Nearest marker within a few degrees; the radius shrinks as you zoom in.
    const radius = pickRadius * ((view.zoom - 1) / (startZoom - 1));
    let best = null; let bestD = Infinity;
    for (const m of markers) {
      const d = angleDeg(ll, m);
      if (d < bestD) { bestD = d; best = m; }
    }
    if (best && bestD <= radius) onPick(best.key);
  }

  return {
    canvas,
    onPick(fn) { onPick = fn; },
    /** markers: [{ key, lat, lon, label?, fill, stroke, text?, dashed?, size? }] */
    setMarkers(list) {
      for (const m of markers) { m.sprite.material.map.dispose(); m.sprite.material.dispose(); }
      markerLayer.clear();
      markers = list.map((m) => {
        const tex = markerTexture(m);
        const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, depthTest: true, depthWrite: false }));
        sprite.position.copy(latLonToVec(m.lat, m.lon, 1.012));
        sprite.renderOrder = m.label === '' ? 1 : 2;
        sprite.userData.base = m;
        markerLayer.add(sprite);
        return { ...m, sprite, tex };
      });
      wake();
    },
    /** Recolour the selected marker without rebuilding the rest. */
    select(key, look) {
      selectedKey = key;
      for (const m of markers) {
        const on = m.key === key;
        const next = markerTexture(on && look ? { ...m, ...look } : m);
        m.sprite.material.map.dispose();
        m.sprite.material.map = next;
        m.sprite.material.needsUpdate = true;
        m.sprite.renderOrder = on ? 3 : (m.label === '' ? 1 : 2);
      }
      wake();
    },
    /** Outlines drawn on the surface, e.g. the Artemis regions' boxes. */
    setOutlines(boxes, color = 0xffffff) {
      outlineLayer.clear();
      const mat = new THREE.LineBasicMaterial({ color, transparent: true, opacity: 0.85 });
      for (const [lo0, la0, lo1, la1] of boxes) {
        const pts = [];
        for (let i = 0; i <= 12; i++) pts.push(latLonToVec(la0, lo0 + ((lo1 - lo0) * i) / 12, 1.003));
        for (let i = 12; i >= 0; i--) pts.push(latLonToVec(la1, lo0 + ((lo1 - lo0) * i) / 12, 1.003));
        outlineLayer.add(new THREE.LineLoop(new THREE.BufferGeometry().setFromPoints(pts), mat));
      }
      wake();
    },
    flyTo(lat, lon, zoom) {
      // Take the short way round.
      let yaw = faceLon(lon);
      const turn = Math.PI * 2;
      while (yaw - goal.yaw > Math.PI) yaw -= turn;
      while (yaw - goal.yaw < -Math.PI) yaw += turn;
      goal.yaw = yaw;
      goal.pitch = clampPitch(lat * DEG);
      if (zoom) goal.zoom = clampZoom(zoom);
      wake();
    },
    zoomBy(f) { goal.zoom = clampZoom(goal.zoom * f); wake(); },
    destroy() {
      cancelAnimationFrame(raf);
      renderer.dispose();
      canvas.remove();
    },
  };
}
