import '../styles/base.css';
import '../styles/story.css';
import { fillContent, splitWords } from './content.js';
import { initHeader, initChapterBar } from './chrome.js';
import { createStage, HIDDEN } from './stage.js';
import { initScroll } from './scroll.js';

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
}

start();
