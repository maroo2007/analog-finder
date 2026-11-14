// The one WebGL canvas behind the story. Every scene names a state for the
// planets (where they sit, how big, how visible); the stage blends between
// those states as you scroll, so the motion is fully reversible.
import * as THREE from 'three';
import { DEG, latLonToVec, faceLon } from '../lib/geo.js';

const IMG = `${import.meta.env.BASE_URL}img/`;

// Defaults: everything hidden. Positions are in half-viewport units
// (x: -1 left edge to 1 right edge, y: -1 bottom to 1 top); size is the
// globe's radius in units of half the shorter viewport side.
export const HIDDEN = {
  marsX: 0.42, marsY: 0, marsS: 0.78, marsO: 0, marsLight: 1, marsDissolve: 0,
  dotsX: 0, dotsY: 0, dotsS: 0.62, dotsO: 0,
  earthO: 0, earthTilt: 0.28,
  sMarsX: -0.62, sMarsO: 0, sMoonX: 0.62, sMoonO: 0, smallS: 0.2,
  moonX: 0.3, moonY: 0, moonS: 0.7, moonO: 0, moonTilt: 0, regionsO: 0,
  starsO: 1,
};

function sphere(radius, segs, material) {
  return new THREE.Mesh(new THREE.SphereGeometry(radius, segs, segs / 2), material);
}

function rimMaterial(color, power = 3.2, strength = 0.9) {
  return new THREE.ShaderMaterial({
    uniforms: { uColor: { value: new THREE.Color(color) }, uPower: { value: power }, uStrength: { value: strength }, uOpacity: { value: 1 }, uLight: { value: new THREE.Vector3(-1, 0.6, 0.6).normalize() } },
    vertexShader: `varying vec3 vN; varying vec3 vV; varying vec3 vW;
      void main(){ vec4 mv = modelViewMatrix * vec4(position,1.0); vN = normalize(normalMatrix*normal); vV = normalize(-mv.xyz); vW = normalize((modelMatrix*vec4(normal,0.0)).xyz); gl_Position = projectionMatrix*mv; }`,
    fragmentShader: `uniform vec3 uColor; uniform float uPower; uniform float uStrength; uniform float uOpacity; uniform vec3 uLight;
      varying vec3 vN; varying vec3 vV; varying vec3 vW;
      void main(){ float f = pow(1.0 - max(dot(vN, vV), 0.0), uPower); float lit = smoothstep(-0.2, 0.6, dot(vW, uLight));
        gl_FragColor = vec4(uColor, f * lit * uStrength * uOpacity); }`,
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.FrontSide,
  });
}

function starField(count = 1400) {
  const pos = new Float32Array(count * 3);
  const col = new Float32Array(count * 3);
  for (let i = 0; i < count; i++) {
    const v = new THREE.Vector3().randomDirection().multiplyScalar(60 + Math.random() * 40);
    pos.set([v.x, v.y, v.z], i * 3);
    const b = 0.25 + Math.random() ** 3 * 0.75;
    col.set([b, b, b * 1.04], i * 3);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  g.setAttribute('color', new THREE.BufferAttribute(col, 3));
  const m = new THREE.PointsMaterial({ size: 1.4, sizeAttenuation: false, vertexColors: true, transparent: true, depthWrite: false });
  return new THREE.Points(g, m);
}

/** Land points sampled from the Blue Marble image: ocean pixels are skipped. */
function landDots(image, count = 42000) {
  const W = 1024; const H = 512;
  const c = document.createElement('canvas');
  c.width = W; c.height = H;
  const ctx = c.getContext('2d', { willReadFrequently: true });
  ctx.drawImage(image, 0, 0, W, H);
  const px = ctx.getImageData(0, 0, W, H).data;
  const out = [];
  const golden = Math.PI * (3 - Math.sqrt(5));
  for (let i = 0; i < count; i++) {
    const y = 1 - (i / (count - 1)) * 2;
    const lat = Math.asin(y) / DEG;
    const lon = ((((i * golden) / DEG) % 360) + 360) % 360 - 180;
    const u = Math.min(W - 1, Math.floor(((lon + 180) / 360) * W));
    const v = Math.min(H - 1, Math.floor(((90 - lat) / 180) * H));
    const k = (v * W + u) * 4;
    const r = px[k]; const g = px[k + 1]; const b = px[k + 2];
    const ocean = b > r * 1.2 && b > g * 0.95 && r < 110;
    if (!ocean) out.push(latLonToVec(lat, lon, 1.003));
  }
  const pos = new Float32Array(out.length * 3);
  out.forEach((v, i) => pos.set([v.x, v.y, v.z], i * 3));
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  return geo;
}

function regionOutlines(targets, color) {
  const group = new THREE.Group();
  const mat = new THREE.LineBasicMaterial({ color, transparent: true, opacity: 0, depthTest: true });
  for (const t of targets) {
    if (!Array.isArray(t.bbox)) continue;
    const [lo0, la0, lo1, la1] = t.bbox;
    const pts = [];
    const n = 12;
    for (let i = 0; i <= n; i++) pts.push(latLonToVec(la0, lo0 + ((lo1 - lo0) * i) / n, 1.004));
    for (let i = n; i >= 0; i--) pts.push(latLonToVec(la1, lo0 + ((lo1 - lo0) * i) / n, 1.004));
    group.add(new THREE.LineLoop(new THREE.BufferGeometry().setFromPoints(pts), mat));
  }
  group.userData.material = mat;
  return group;
}

export async function createStage(canvas, { moonTargets = [] } = {}) {
  // Phones and touch screens get a lighter stage: native pixel density, no
  // antialiasing, fewer polygons. The planets look the same at that size.
  const lite = window.matchMedia('(max-width: 760px), (pointer: coarse)').matches;
  const seg = lite ? 64 : 128;
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: !lite, powerPreference: 'high-performance' });
  renderer.setClearColor(0x06080b, 1);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(30, 1, 0.1, 200);
  camera.position.set(0, 0, 10);

  const sun = new THREE.DirectionalLight(0xffffff, 2.6);
  sun.position.set(-6, 3.5, 5);
  scene.add(sun, new THREE.AmbientLight(0xffffff, 0.05));

  const loader = new THREE.TextureLoader();
  const load = (f) => new Promise((res, rej) => loader.load(IMG + f, (t) => { t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; res(t); }, undefined, rej));
  const loadData = (f) => new Promise((res, rej) => loader.load(IMG + f, res, undefined, rej));

  const [marsTex, earthTex, moonTex, moonBump] = await Promise.all([
    load('mars.jpg'), load('earth_bluemarble.jpg'), load('moon_lroc.jpg'), loadData('moon_lola_bump.jpg'),
  ]);

  const stars = starField();
  scene.add(stars);

  // Mars, with a rim light on its sunlit limb. Its surface can dissolve
  // (uDissolve 0..1) in a noise pattern with a thin blue edge, which is how
  // Mars turns into the dotted Earth instead of being swapped for it.
  const mars = new THREE.Group();
  // depthWrite off: a nearly transparent Mars must never hide the Earth dots
  // drawn after it in the same place (it made Earth vanish for a moment just
  // after the change). One convex sphere needs no depth of its own.
  const marsMat = new THREE.MeshStandardMaterial({ map: marsTex, roughness: 1, metalness: 0, transparent: true, depthWrite: false });
  const dissolve = { value: 0 };
  marsMat.onBeforeCompile = (shader) => {
    shader.uniforms.uDissolve = dissolve;
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', '#include <common>\nvarying vec3 vObjPos;')
      .replace('#include <begin_vertex>', '#include <begin_vertex>\nvObjPos = position;');
    shader.fragmentShader = shader.fragmentShader
      .replace('#include <common>', `#include <common>
        uniform float uDissolve;
        varying vec3 vObjPos;
        float dHash(vec3 p) { p = fract(p * 0.3183099 + 0.1); p *= 17.0; return fract(p.x * p.y * p.z * (p.x + p.y + p.z)); }
        float dNoise(vec3 x) {
          vec3 i = floor(x); vec3 f = fract(x); f = f * f * (3.0 - 2.0 * f);
          return mix(mix(mix(dHash(i), dHash(i + vec3(1,0,0)), f.x), mix(dHash(i + vec3(0,1,0)), dHash(i + vec3(1,1,0)), f.x), f.y),
                     mix(mix(dHash(i + vec3(0,0,1)), dHash(i + vec3(1,0,1)), f.x), mix(dHash(i + vec3(0,1,1)), dHash(i + vec3(1,1,1)), f.x), f.y), f.z);
        }`)
      .replace('#include <dithering_fragment>', `
        if (uDissolve > 0.0) {
          float n = dNoise(vObjPos * 3.5) * 0.6 + dNoise(vObjPos * 9.0) * 0.4;
          float cut = uDissolve * 1.08 - 0.04;
          if (n < cut) discard;
          float edge = 1.0 - smoothstep(0.0, 0.03, n - cut);
          gl_FragColor.rgb = mix(gl_FragColor.rgb, vec3(0.35, 0.66, 0.9), edge * 0.85);
        }
        #include <dithering_fragment>`);
  };
  const marsBody = sphere(1, seg, marsMat);
  const marsRim = sphere(1.012, 96, rimMaterial(0xe0703a, 2.6, 1.1));
  mars.add(marsBody, marsRim);
  mars.rotation.y = faceLon(77.5);
  mars.rotation.x = 0.32;
  scene.add(mars);

  // Earth: dots for "the same profile everywhere", then the real texture.
  const earth = new THREE.Group();
  const dotsMat = new THREE.PointsMaterial({ color: 0x5aa9e6, size: 2.2, sizeAttenuation: false, transparent: true, depthWrite: false });
  const dots = new THREE.Points(landDots(earthTex.image, lite ? 26000 : 42000), dotsMat);
  const dotsBack = sphere(0.995, 64, new THREE.MeshBasicMaterial({ color: 0x06080b, transparent: true }));
  const earthMat = new THREE.MeshStandardMaterial({ map: earthTex, roughness: 0.9, metalness: 0, transparent: true });
  const earthBody = sphere(1, seg, earthMat);
  const earthRim = sphere(1.015, 96, rimMaterial(0x5aa9e6, 3.0, 0.8));
  earth.add(dotsBack, earthBody, dots, earthRim);
  // These all sit at the same spot, so the renderer cannot sort them by
  // distance; without a fixed order the dark backing sphere is sometimes
  // drawn over the dots and hides all but their edges.
  dotsBack.renderOrder = 1;
  earthBody.renderOrder = 2;
  dots.renderOrder = 3;
  earthRim.renderOrder = 4;
  marsBody.renderOrder = 1;
  marsRim.renderOrder = 2;
  earth.rotation.y = faceLon(22);
  earth.rotation.x = 0.28;
  scene.add(earth);

  // Small companions for "three worlds".
  const sMars = sphere(1, 64, new THREE.MeshStandardMaterial({ map: marsTex, roughness: 1, transparent: true }));
  sMars.rotation.y = faceLon(-60);
  const sMoon = sphere(1, 64, new THREE.MeshStandardMaterial({ map: moonTex, roughness: 1, transparent: true }));
  scene.add(sMars, sMoon);

  // The Moon, with the Artemis regions drawn from their bounding boxes.
  const moon = new THREE.Group();
  const moonMat = new THREE.MeshStandardMaterial({ map: moonTex, bumpMap: moonBump, bumpScale: 2.5, roughness: 1, transparent: true });
  const moonBody = sphere(1, lite ? 96 : 160, moonMat);
  const regions = regionOutlines(moonTargets, 0xf3f5f7);
  moon.add(moonBody, regions);
  scene.add(moon);

  // Upload every texture and compile every shader now, while the page loads,
  // so Earth or the Moon appearing mid-scroll never stalls a frame.
  for (const t of [marsTex, earthTex, moonTex, moonBump]) renderer.initTexture(t);
  scene.traverse((o) => { o.visible = true; });
  renderer.compile(scene, camera);
  // One hidden draw with everything on uploads the geometry too.
  renderer.setSize(64, 64, false);
  renderer.render(scene, camera);

  const p = { ...HIDDEN };
  let spin = true;
  let w = 1; let h = 1; let unitX = 1; let unitY = 1; let unitR = 1;

  function resize() {
    w = canvas.clientWidth || window.innerWidth; h = canvas.clientHeight || window.innerHeight;
    renderer.setPixelRatio(lite ? 1 : Math.min(window.devicePixelRatio || 1, 1.5));
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    const visH = 2 * camera.position.z * Math.tan((camera.fov * DEG) / 2);
    const visW = visH * camera.aspect;
    unitX = visW / 2; unitY = visH / 2; unitR = Math.min(visW, visH) / 2;
  }
  resize();
  window.addEventListener('resize', resize);

  const place = (obj, x, y, s) => { obj.position.set(x * unitX, y * unitY, 0); obj.scale.setScalar(Math.max(s, 0.0001) * unitR); };
  const show = (obj, o) => { obj.visible = o > 0.003; };

  let last = performance.now();
  function frame(now) {
    const dt = Math.min(0.05, (now - last) / 1000);
    last = now;
    // While hidden, each planet turns back to its home side (Mars to Jezero,
    // Earth to Africa), so it always appears showing the right face.
    if (p.marsO < 0.003) mars.rotation.y = faceLon(77.5);
    if (Math.max(p.dotsO, p.earthO) < 0.003) earth.rotation.y = faceLon(22);
    if (spin) {
      mars.rotation.y += dt * 0.035;
      earth.rotation.y += dt * 0.03;
      sMars.rotation.y += dt * 0.05;
      sMoon.rotation.y += dt * 0.04;
    }

    place(mars, p.marsX, p.marsY, p.marsS);
    marsMat.opacity = p.marsO;
    dissolve.value = p.marsDissolve;
    marsRim.material.uniforms.uOpacity.value = p.marsO * (1 - p.marsDissolve);
    sun.intensity = 2.6 * p.marsLight + 0.4;
    show(mars, p.marsO);

    place(earth, p.dotsX, p.dotsY, p.dotsS);
    earth.rotation.x = p.earthTilt;
    dotsMat.opacity = p.dotsO * (1 - p.earthO);
    dots.visible = dotsMat.opacity > 0.003;
    dotsBack.material.opacity = Math.max(p.dotsO, p.earthO);
    earthMat.opacity = p.earthO;
    earthRim.material.uniforms.uOpacity.value = p.earthO;
    show(earth, Math.max(p.dotsO, p.earthO));
    earthBody.visible = p.earthO > 0.003;

    const ss = p.smallS;
    place(sMars, p.sMarsX, 0, ss); sMars.material.opacity = p.sMarsO; show(sMars, p.sMarsO);
    place(sMoon, p.sMoonX, 0, ss * 0.8); sMoon.material.opacity = p.sMoonO; show(sMoon, p.sMoonO);

    place(moon, p.moonX, p.moonY, p.moonS);
    moon.rotation.set(p.moonTilt, faceLon(0), 0, 'XYZ');
    moonMat.opacity = p.moonO;
    regions.userData.material.opacity = p.regionsO * p.moonO;
    show(moon, p.moonO);

    stars.material.opacity = p.starsO;
    renderer.render(scene, camera);
  }

  let running = false; let raf = 0;
  const loop = (t) => { frame(t); raf = requestAnimationFrame(loop); };
  const start = () => { if (!running) { running = true; last = performance.now(); raf = requestAnimationFrame(loop); } };
  const stop = () => { running = false; cancelAnimationFrame(raf); };
  document.addEventListener('visibilitychange', () => (document.hidden ? stop() : start()));
  start();

  return {
    params: p,
    setSpin(on) { spin = on; },
    renderOnce() { frame(performance.now()); },
  };
}
