import '../styles/base.css';
import '../styles/story.css';
import { fillContent, splitWords } from './content.js';
import { initHeader, initChapterBar } from './chrome.js';
import { createStage, HIDDEN } from './stage.js';
import { initScroll } from './scroll.js';

// The pinned scenes change the page's length after load, so the browser's
// own "restore the old scroll position" lands in the wrong scene. The page
// starts at the top, or at the #section in the address (handled below).
if ('scrollRestoration' in history) history.scrollRestoration = 'manual';

const root = document.documentElement;
const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
root.classList.toggle('reduced', reduced);

initHeader();
document.querySelectorAll('[data-fill]').forEach(splitWords);

async function start() {
  let data;
  try {
    data = await fillContent();
  } catch (err) {
    // The text still reads without the data; only the live numbers are lost.
    console.error('Story data failed to load', err);
    document.querySelectorAll('[data-fill] .w').forEach((w) => w.classList.add('on'));
    initChapterBar();
    return;
  }

  let stage;
  try {
    stage = await createStage(document.getElementById('scene-canvas'), { moonTargets: data.moon });
    root.classList.add('has-webgl');
  } catch (err) {
    console.warn('WebGL stage unavailable; showing the page without globes', err);
    root.classList.add('no-webgl');
    stage = { params: { ...HIDDEN }, setSpin() {}, renderOnce() {} };
  }

  const scroller = initScroll({ stage, data });
  // Development only (stripped from the build): lets tests read the planets.
  if (import.meta.env.DEV) window.__stage = stage;

  // Decode every story image in the background now, so the first time a
  // scene with a big image arrives (the Mars map, the Twin Finder shot, the
  // relief pairs) it doesn't stall a frame while the browser decodes it.
  // One image per idle moment, so this never competes with the first scroll.
  const queue = [...document.querySelectorAll('main img')];
  const idle = window.requestIdleCallback || ((fn) => setTimeout(fn, 200));
  const warmNext = () => {
    const img = queue.shift();
    if (!img) return;
    img.loading = 'eager';
    const next = () => idle(warmNext, { timeout: 3000 });
    if (img.decode) img.decode().then(next, next);
    else next();
  };
  idle(warmNext, { timeout: 3000 });
  initChapterBar({ scrollTo: scroller?.scrollTo, onRefresh: scroller?.onRefresh });

  // Arriving with an address like index.html#credits (the Twin Finder links
  // here): the browser jumped before the pinned scenes added their scroll
  // length, so it landed in the wrong place. Jump again now the layout is
  // final.
  // Wait for the page's load event too, after which ScrollTrigger measures
  // the layout one last time.
  const id = decodeURIComponent(location.hash.slice(1));
  const target = id && document.getElementById(id);
  if (target && id !== 'top' && scroller?.scrollTo) {
    const jump = () => requestAnimationFrame(() => requestAnimationFrame(() => scroller.scrollTo(target, { immediate: true })));
    if (document.readyState === 'complete') jump();
    else window.addEventListener('load', jump, { once: true });
  }
}

start();
