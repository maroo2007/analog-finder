// Scroll choreography. Every scene pins for the same short distance, so the
// page moves at one even pace. Text and details animate on their own when a
// scene arrives (and rewind if you scroll back); only the planets are tied
// to the scroll position, which keeps their transitions smooth and
// reversible. Reduced motion gets plain fades.
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import Lenis from 'lenis';
import { HIDDEN } from './stage.js';
import { createOdometer } from './odometer.js';

gsap.registerPlugin(ScrollTrigger);

const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const S = (o) => ({ ...HIDDEN, ...o });

/** Every pinned scene holds for this share of the viewport height. */
const PIN_DESKTOP = 1.3;
const PIN_PHONE = 1.0;
const pinLength = () => (window.matchMedia('(max-width: 760px)').matches ? PIN_PHONE : PIN_DESKTOP);

// Phones: the address bar showing and hiding changes the viewport height;
// re-measuring every pin then makes scenes jump, so ignore those resizes.
ScrollTrigger.config({ ignoreMobileResize: true });
const PINNED = ['problem', 'idea', 'steps', 'worlds', 'pick', 'measure', 'match', 'finder', 'promises', 'egypt', 'counter', 'moon', 'limits'];

/** Planet states per scene, keyed by progress through the scene (0..1). */
function planetKeys(phone) {
  const k = phone ? 0.55 : 1; // phone: globes smaller and behind the text
  const hold = (state) => [[0, state], [1, state]];
  const marsEdge = S({ marsO: 1, marsX: phone ? 1.08 : 1.0, marsY: -0.05, marsS: 0.95, marsLight: 0.4 });
  // Small enough to show the whole globe beside the text, never cut off.
  const dotsSide = S({ dotsO: 1, dotsX: phone ? 0.2 : 0.46, dotsY: phone ? -0.5 : 0, dotsS: phone ? 0.6 : 0.6 });
  const worlds = { dotsO: 1, dotsY: 0.24, dotsS: 0.44 * k + 0.08 };
  const trio = { sMarsO: 1, sMoonO: 1, sMarsX: phone ? -0.72 : -0.46, sMoonX: phone ? 0.72 : 0.46, smallS: phone ? 0.13 : 0.18 };
  // Earth tilted forward so the horizon shows Africa rather than the Arctic.
  const horizon = (y) => ({ earthO: 1, earthTilt: -1.1, dotsY: phone ? y * 0.56 : y, dotsS: phone ? 1.4 : 2.2 });
  const moonAt = { moonO: 1, moonX: phone ? 0 : 0.36, moonY: phone ? -0.82 : 0, moonS: phone ? 0.7 : 0.72 * k + 0.1 };
  return {
    hero: [
      [0, S({ marsO: 1, marsX: phone ? 0.3 : 0.42, marsY: phone ? 0.42 : 0, marsS: phone ? 0.95 : 0.78 })],
      [1, S({ marsO: 1, marsX: 0.12, marsY: phone ? -1.55 : -2.8, marsS: phone ? 1.6 : 2.32 })],
    ],
    problem: hold(marsEdge),
    idea: hold(dotsSide),
    steps: hold(S({ dotsO: 1, dotsY: phone ? -0.58 : 0, dotsS: 0.52 * k + 0.12 })),
    worlds: [
      [0, S(worlds)],
      [0.4, S({ ...worlds, earthO: 1 })],
      [0.8, S({ ...worlds, earthO: 1, ...trio })],
      [1, S({ ...worlds, earthO: 1, ...trio })],
    ],
    pick: hold(S({ starsO: 0 })),
    measure: hold(S({ starsO: 0.45 })),
    match: hold(S(horizon(-2.62))),
    finder: hold(S({ ...horizon(-2.95), starsO: 0.6 })),
    promises: hold(S({ dotsO: phone ? 0.28 : 0.6, dotsY: phone ? -0.35 : 0, dotsS: 0.78 * k + 0.1 })),
    egypt: hold(S({ starsO: 0.35 })),
    counter: hold(S({ starsO: 0.35 })),
    moon: [
      [0, S({ ...moonAt, moonTilt: -0.25 })],
      [0.7, S({ ...moonAt, moonTilt: -1.22, regionsO: 1 })],
      [1, S({ ...moonAt, moonTilt: -1.22, regionsO: 1 })],
    ],
    limits: hold(S({ moonO: 1, moonY: phone ? -1.55 : -2.75, moonS: phone ? 1.4 : 2.25, moonTilt: -0.35, starsO: 0.8 })),
    cta: [[0, S({})]],
  };
}

const easeInOut = (t) => (t < 0.5 ? 4 * t * t * t : 1 - (-2 * t + 2) ** 3 / 2);
const clamp01 = (v) => Math.min(1, Math.max(0, v));
// Gentler than easeInOut (half the steepest slope) for fades, so a fast
// scroll step never jumps an opacity in a single frame.
const smooth = (t) => t * t * (3 - 2 * t);

// Each planet: the keys that place it, and the opacity keys that show it.
const BODIES = [
  // marsDissolve counts as "place": while Mars fades out it stays dissolved,
  // and only resets once Mars is fully hidden (no Mars re-forming).
  { show: ['marsO'], place: ['marsX', 'marsY', 'marsS', 'marsLight', 'marsDissolve'], size: 'marsS', y: 'marsY' },
  { show: ['dotsO', 'earthO'], place: ['dotsX', 'dotsY', 'dotsS', 'earthTilt'], size: 'dotsS', y: 'dotsY' },
  { show: ['sMarsO', 'sMoonO'], place: ['sMarsX', 'sMoonX', 'smallS'], size: 'smallS' },
  { show: ['moonO'], place: ['moonX', 'moonY', 'moonS', 'moonTilt'], size: 'moonS', y: 'moonY' },
];
const vis = (s, keys) => Math.max(...keys.map((k) => s[k]));
const PLACE_KEYS = new Set(BODIES.flatMap((b) => b.place));

/**
 * Mars turning into the dotted Earth, in two steps on one body:
 * 1. (u 0 to 0.45) Mars glides from the screen edge to Earth's place and
 *    lights up fully, so the whole globe is on screen before anything changes;
 * 2. (u 0.4 to 0.95) in that same place Mars's surface dissolves while the
 *    dots of Earth appear on the same sphere.
 * Nothing arrives from the side, and scrolling back runs it in reverse.
 */
function morphMarsToEarth(a, b, u) {
  const move = easeInOut(clamp01(u / 0.45));
  const change = smooth(clamp01((u - 0.35) / 0.5));
  const out = {};
  for (const k of Object.keys(a)) out[k] = a[k] + (b[k] - a[k]) * change;
  const lerp = (x, y, t) => x + (y - x) * t;
  const x = lerp(a.marsX, b.dotsX, move);
  const y = lerp(a.marsY, b.dotsY, move);
  const s = lerp(a.marsS, b.dotsS, move);
  Object.assign(out, {
    marsX: x, marsY: y, marsS: s, dotsX: x, dotsY: y, dotsS: s,
    marsLight: lerp(a.marsLight, 1, move),
    // Once the dissolve is done, Mars is gone: no remnant lingers.
    marsO: 1 - smooth(clamp01((u - 0.8) / 0.15)),
    marsDissolve: change,
    dotsO: smooth(clamp01((u - 0.35) / 0.6)) * b.dotsO,
    earthO: b.earthO * change,
    earthTilt: b.earthTilt,
  });
  return out;
}

/**
 * Blend two planet states at progress u (0..1). Whatever leaves fades out
 * where it is; whatever arrives rises gently into place as it fades in, so
 * nothing pops out of nowhere. Planets that stay on screen simply move.
 */
function blendStates(a, b, u) {
  const marsLeaves = a.marsO > 0.01 && b.marsO <= 0.01;
  const earthArrives = vis(a, ['dotsO', 'earthO']) <= 0.01 && vis(b, ['dotsO', 'earthO']) > 0.01;
  if (marsLeaves && earthArrives) return morphMarsToEarth(a, b, u);
  if (b.marsO > 0.01 && a.marsO <= 0.01 && vis(a, ['dotsO', 'earthO']) > 0.01 && vis(b, ['dotsO', 'earthO']) <= 0.01) {
    return morphMarsToEarth(b, a, 1 - u); // scrolling back up: Earth turns back into Mars
  }
  const t = easeInOut(u);
  const out = {};
  for (const k of Object.keys(a)) out[k] = a[k] + (b[k] - a[k]) * t;
  const fadeOut = smooth(clamp01(u / 0.6));
  const fadeIn = smooth(clamp01((u - 0.3) / 0.7));
  // Earth jumping between a horizon and a whole globe (or back) would fly
  // across the screen as a part-sphere; instead it fades out where it is
  // and fades back in at its new place.
  const earthJumps = vis(a, ['dotsO', 'earthO']) > 0.01 && vis(b, ['dotsO', 'earthO']) > 0.01
    && (Math.abs(a.dotsY - b.dotsY) > 1 || Math.abs(a.dotsS - b.dotsS) > 0.8);
  if (earthJumps) {
    out.earthJump = 1; // tells applyPlanets: never move Earth while it shows
    const leaving = u < 0.5;
    const src = leaving ? a : b;
    const fade = leaving ? 1 - smooth(clamp01(u / 0.35)) : smooth(clamp01((u - 0.65) / 0.35));
    for (const k of ['dotsX', 'dotsY', 'dotsS', 'earthTilt']) out[k] = src[k];
    out.dotsO = src.dotsO * fade;
    out.earthO = src.earthO * fade;
    if (!leaving) {
      out.dotsY = b.dotsY - 0.22 * (1 - fade);
      out.dotsS = b.dotsS * (0.93 + 0.07 * fade);
    }
  }
  for (const body of BODIES) {
    if (earthJumps && body.show.includes('dotsO')) continue;
    const visA = Math.max(...body.show.map((k) => a[k]));
    const visB = Math.max(...body.show.map((k) => b[k]));
    for (const k of body.show) {
      out[k] = b[k] < a[k] ? a[k] + (b[k] - a[k]) * fadeOut : a[k] + (b[k] - a[k]) * fadeIn;
    }
    if (visA > 0.01 && visB <= 0.01) {
      for (const k of body.place) out[k] = a[k]; // leaving: stay put while fading
    } else if (visA <= 0.01 && visB > 0.01) {
      for (const k of body.place) out[k] = b[k]; // arriving: rise gently into place
      out[body.size] = b[body.size] * (0.93 + 0.07 * fadeIn);
      if (body.y) out[body.y] = b[body.y] - 0.22 * (1 - fadeIn);
    }
  }
  return out;
}

/** What each scene does when it arrives. All time-based, one shared rhythm. */
const REVEALS = {
  hero: null,
  problem: (tl, el) => tl
    .from($('.statement', el), { opacity: 0, y: 28, duration: 0.7 }, 0)
    .to($$('.w', el), { color: '#f3f5f7', stagger: 0.045, duration: 0.5, ease: 'power1.out' }, 0.15),
  idea: (tl, el) => tl
    .from($('.statement', el), { opacity: 0, y: 28, duration: 0.7 }, 0)
    .to($$('.w', el), { color: '#f3f5f7', stagger: 0.045, duration: 0.5, ease: 'power1.out' }, 0.15),
  steps: (tl, el) => tl
    .from($('.step-pick', el), { x: -40, opacity: 0 })
    .from($('.step-match', el), { x: 40, opacity: 0 }, '<0.12')
    .from($('.steps-across', el), { y: 24, opacity: 0 }, '<0.3')
    .fromTo($('[data-across-fill]', el), { '--p': 0 }, { '--p': 1, duration: 1.2, ease: 'power2.inOut' }, '<0.2'),
  worlds: (tl, el) => tl
    .from($('.worlds-title', el), { y: 36, opacity: 0 }, 0.25)
    .from($('.world-keys', el), { opacity: 0 }, '<0.2'),
  pick: (tl, el) => tl
    .from($('.pick-map img', el), { scale: 1.12, duration: 1.4, ease: 'power2.out' }, 0)
    .from($('.pick-title', el), { x: -30, opacity: 0 }, 0.1)
    .from($('.world-panel', el), { x: 60, opacity: 0 }, 0.2),
  measure: (tl, el) => tl
    .from($$('.measure-steps li', el), { x: -24, opacity: 0, stagger: 0.18 }, 0.1),
  match: (tl, el) => tl.from($('.match-title', el), { x: 60, opacity: 0 }),
  finder: (tl, el) => tl
    .from($$('.finder-captions li', el), { y: 16, opacity: 0, stagger: 0.18 }, 0.3),
  promises: (tl, el) => {
    $$('.promises li', el).forEach((it, i) => {
      tl.from(it, { y: 40, opacity: 0 }, i * 0.18);
      tl.fromTo($('.promise-line', it), { clipPath: 'inset(0 100% 0 0)' }, { clipPath: 'inset(0 0% 0 0)', duration: 0.7 }, i * 0.18 + 0.25);
    });
  },
  egypt: (tl, el) => {
    const figs = $$('.pair figure', el);
    tl.from($('.egypt-title', el), { y: 30, opacity: 0 }, 0)
      .fromTo(figs[0], { rotateY: 24, x: -20 }, { rotateY: 0, x: 0, duration: 1.1 }, 0)
      .fromTo(figs[1], { rotateY: -24, x: 20 }, { rotateY: 0, x: 0, duration: 1.1 }, 0);
    $$('.closeness > div', el).forEach((d, i) => {
      const v = Number(d.dataset.value) || 0;
      const num = $('[data-close-num]', d);
      const proxy = { v: 0 };
      tl.fromTo($('.bar-fill', d), { '--p': 0 }, { '--p': v / 100, duration: 1, ease: 'power2.out' }, 0.35 + i * 0.1);
      tl.to(proxy, { v, duration: 1, ease: 'power2.out', onUpdate: () => { num.textContent = Math.round(proxy.v); } }, 0.35 + i * 0.1);
    });
    tl.from($('.egypt-caption', el), { y: 16, opacity: 0 }, 0.7);
  },
  moon: (tl, el) => tl
    .from($('.moon-title', el), { y: 36, opacity: 0 }, 0)
    .from($$('.moon-copy p', el), { y: 20, opacity: 0, stagger: 0.2 }, 0.2),
  limits: (tl, el) => tl
    .from($$('.limits li', el), { y: 36, opacity: 0, stagger: 0.18 }, 0)
    .from($('.limits-line', el), { opacity: 0 }, 0.6),
  cta: (tl, el) => tl
    .from($('.cta-title', el), { y: 36, opacity: 0 }, 0)
    .from($('.btn-primary', el), { y: 16, opacity: 0 }, 0.2),
};

/**
 * Motion tied to the scroll inside a pinned scene (smoothed), for the big
 * moves that must never be skipped: fast scrolling plays them quickly,
 * slow scrolling slowly, and every frame is shown. The move fills the first
 * part of the hold; the rest is a still moment to look at the result.
 */
const SCRUBS = {
  measure: (tl, el) => {
    // The stack arrives closed and visible, then lifts apart; each label
    // rides on its own layer (a compositor transform, no re-layout).
    const layers = $$('.tile-layer', el);
    const gap = () => Math.min(46, el.querySelector('.tile-3d').offsetWidth * 0.12);
    tl.fromTo(layers, { z: 0 }, { z: (i) => (i + 1) * gap(), duration: 1, ease: 'power2.inOut', stagger: 0.05 }, 0)
      .fromTo($$('.tile-tag', el), { opacity: 0 }, { opacity: 1, duration: 0.7, stagger: 0.1 }, 0.3);
  },
  finder: (tl, el) => {
    // The Twin Finder arrives tilted over the globe and turns flat.
    tl.fromTo($('[data-finder-shot]', el), { rotateX: 30, y: 40, scale: 0.92 }, { rotateX: 0, y: 0, scale: 1, duration: 1, ease: 'power2.out' }, 0);
  },
};

export function initScroll({ stage, data }) {
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const phoneQuery = window.matchMedia('(max-width: 760px)');

  if (reduced) {
    initReduced({ stage, data, phoneQuery });
    return null;
  }

  // A calm scroll: each wheel notch moves less, and the page eases there.
  const lenis = new Lenis({ lerp: 0.075, wheelMultiplier: 0.7, touchMultiplier: 1.1 });
  lenis.on('scroll', ScrollTrigger.update);
  if (import.meta.env.DEV) window.__lenis = lenis; // tests only, stripped from the build
  gsap.ticker.add((t) => lenis.raf(t * 1000));
  gsap.ticker.lagSmoothing(0);

  const triggers = {};
  const sceneEl = (name) => $(`[data-scene="${name}"]`);

  // The big moves inside pinned scenes, the planets, the odometer and the
  // exit fades are tied to the scroll position (scrub: true): they move as
  // fast as you scroll and run backwards identically when you scroll up.
  // Each scene's text reveal (REVEALS) plays in time as the scene arrives.

  // The odometer rolls while the counter scene is held.
  const odo = createOdometer($('[data-odo-digits]'), data.rank.ofContinent, data.rank.rankContinent);
  odo.set(0);
  const odoProxy = { t: 0 };
  SCRUBS.counter = (tl) => tl.to(odoProxy, { t: 1, duration: 1, ease: 'power1.inOut', onUpdate: () => odo.set(odoProxy.t) }, 0);
  REVEALS.counter = (tl, el) => tl
    .from($('.counter-side', el), { x: -20, opacity: 0 }, 0)
    .from($('.counter-lead', el), { y: 14, opacity: 0 }, 0.3)
    .from($('.counter-label', el), { opacity: 0 }, 0.5);

  // Build every scene top to bottom: its reveal first, then its pin.
  for (const el of $$('[data-scene]')) {
    const name = el.dataset.scene;
    const build = REVEALS[name];
    if (build) {
      // The scene's reveal plays by itself, in time, when its top reaches
      // 60% of the screen: headings rise in with a strong ease-out and the
      // statement words fill one after another (the site's first motion,
      // restored on 2026-11-14). Scrolling back above that point plays it
      // backwards at the same speed, so up mirrors down.
      const tl = gsap.timeline({ paused: true, defaults: { duration: 0.9, ease: 'power3.out' } });
      build(tl, el);
      ScrollTrigger.create({
        trigger: el,
        start: 'top 60%',
        onEnter: () => tl.play(),
        onLeaveBack: () => tl.reverse(),
      });
    }
    if (PINNED.includes(name)) {
      let scrubTl;
      if (SCRUBS[name]) {
        scrubTl = gsap.timeline({ defaults: { ease: 'none' } });
        SCRUBS[name](scrubTl, el);
        // The move takes the first ~55% of the hold; then the scene rests.
        scrubTl.to({}, { duration: scrubTl.duration() * 0.8 });
      }
      triggers[name] = ScrollTrigger.create({
        trigger: el,
        start: () => (el.offsetHeight > window.innerHeight + 2 ? 'bottom bottom' : 'top top'),
        end: () => `+=${Math.round(window.innerHeight * pinLength())}`,
        pin: true,
        pinSpacing: true,
        invalidateOnRefresh: true,
        ...(scrubTl ? { animation: scrubTl, scrub: true } : {}),
      });
      // As the scene leaves, its content fades with the scroll, so the old
      // text never sits on top of the new one.
      const pinST = triggers[name];
      gsap.fromTo(el, { opacity: 1 }, {
        opacity: 0,
        ease: 'power1.in',
        immediateRender: false,
        scrollTrigger: {
          start: () => pinST.end,
          end: () => pinST.end + window.innerHeight * 0.6,
          scrub: true,
          invalidateOnRefresh: true,
        },
      });
    }
  }

  // 1 Hero: the headline slides up and fades as the globe becomes a horizon.
  const hero = sceneEl('hero');
  gsap.to('.hero-copy', {
    yPercent: -40, opacity: 0, ease: 'none',
    scrollTrigger: { trigger: hero, start: 'top top', end: 'bottom top', scrub: true },
  });
  triggers.hero = ScrollTrigger.create({ trigger: hero, start: 'top top', end: () => `+=${Math.round(window.innerHeight * 0.6)}` });

  // 16 The counters count up with the scroll as they come in.
  $$('.numbers [data-count]').forEach((n) => {
    const target = Number(n.textContent.replace(/[^0-9]/g, '')) || 0;
    const proxy = { v: 0 };
    n.textContent = '0';
    gsap.to(proxy, {
      v: target, ease: 'power2.out',
      onUpdate: () => { n.textContent = Math.round(proxy.v).toLocaleString('en-US'); },
      scrollTrigger: { trigger: n, start: 'top 95%', end: 'top 45%', scrub: true },
    });
  });

  // ---- Planet keyframes, positioned from the pinned ranges ----
  let keys = [];
  function buildKeys() {
    const table = planetKeys(phoneQuery.matches);
    keys = [];
    for (const [name, list] of Object.entries(table)) {
      const st = triggers[name];
      const el = sceneEl(name);
      if (!el) continue;
      const start = st ? st.start : el.getBoundingClientRect().top + window.scrollY;
      const end = st ? st.end : start + window.innerHeight * 0.5;
      for (const [t, state] of list) keys.push({ pos: start + (end - start) * t, state });
    }
    keys.sort((a, b) => a.pos - b.pos);
  }
  ScrollTrigger.addEventListener('refresh', buildKeys);

  function applyPlanets() {
    if (!keys.length) return;
    const y = window.scrollY;
    let i = keys.findIndex((k) => k.pos > y);
    if (i === -1) i = keys.length;
    const a = keys[Math.max(0, i - 1)];
    const b = keys[Math.min(keys.length - 1, i)];
    const span = b.pos - a.pos;
    const u = span > 0 ? Math.min(1, Math.max(0, (y - a.pos) / span)) : 1;
    const goal = blendStates(a.state, b.state, u);
    // Ease toward the scroll's target rather than snapping to it, so the
    // planets glide even when the wheel moves in jumps.
    // Everything eases toward the scroll's target, so even a very fast
    // scroll never jumps a value in one frame. Positions follow three rules:
    // a planet that is hidden jumps (unseen) to its place; a planet that is
    // fading out stays exactly where it is; only a visible planet moves.
    const p = stage.params;
    const ease = (k, rate) => {
      const d = goal[k] - p[k];
      p[k] = Math.abs(d) < 1e-4 ? goal[k] : p[k] + d * rate;
    };
    // Fading out is quicker than fading in, so a planet is fully gone before
    // it is moved to its next place.
    for (const k of Object.keys(p)) if (!PLACE_KEYS.has(k)) ease(k, goal[k] < p[k] ? 0.3 : 0.16);
    for (const body of BODIES) {
      const shown = vis(p, body.show);
      const far = Math.max(...body.place.map((k) => Math.abs(goal[k] - p[k])));
      if (shown < 0.02) for (const k of body.place) p[k] = goal[k];
      else if (vis(goal, body.show) < 0.02) continue;
      else if (body.y === 'dotsY' && far > 0.3 && (p.dotsS > 1.5) !== (goal.dotsS > 1.5)) {
        // Earth showing as a horizon but due to be a globe (or the reverse):
        // never fly between the two. Hide it in place, then it reappears.
        for (const k of body.show) p[k] += (0 - p[k]) * 0.4;
      } else for (const k of body.place) ease(k, 0.1);
    }
  }
  gsap.ticker.add(applyPlanets);

  ScrollTrigger.refresh();
  buildKeys();
  phoneQuery.addEventListener('change', () => ScrollTrigger.refresh());

  return {
    onRefresh: (fn) => ScrollTrigger.addEventListener('refresh', fn),
    scrollTo(el, { immediate = false } = {}) {
      // Lenis clamps to the page length it last measured; the pins may have
      // made the page longer since.
      lenis.resize();
      const name = el?.dataset.scene;
      const st = name && triggers[name];
      lenis.scrollTo(st ? st.start + 2 : el, immediate ? { immediate: true, force: true } : { duration: 1.2 });
    },
  };
}

/** Reduced motion: no pins, no scrubbing; planets cross-fade per scene. */
function initReduced({ stage, data, phoneQuery }) {
  stage.setSpin(false);
  $$('[data-fill] .w').forEach((w) => w.classList.add('on'));
  const digits = $('[data-odo-digits]');
  if (digits) digits.textContent = `#${data.rank.rankContinent.toLocaleString('en-US')}`;
  const table = planetKeys(phoneQuery.matches);
  const io = new IntersectionObserver((entries) => {
    for (const e of entries) {
      if (!e.isIntersecting) continue;
      const list = table[e.target.dataset.scene];
      if (!list) continue;
      const state = list[list.length - 1][1];
      gsap.to(stage.params, { ...state, duration: 0.6, ease: 'power2.out', overwrite: true });
    }
  }, { threshold: 0.5 });
  $$('[data-scene]').forEach((s) => io.observe(s));
}
