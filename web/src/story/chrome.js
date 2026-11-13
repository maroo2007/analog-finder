// The parts that stay on screen: header, chapter bar, launch button.

const CHAPTERS = ['problem', 'method', 'proof', 'egypt', 'moon', 'limits'];

export function initHeader() {
  const header = document.querySelector('[data-header]');
  if (!header) return;
  let last = window.scrollY;
  const onScroll = () => {
    const y = window.scrollY;
    const down = y > last;
    header.classList.toggle('is-hidden', down && y > 80);
    header.classList.toggle('is-solid', y > window.innerHeight * 0.6);
    last = y;
  };
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
}

/**
 * Chapter bar: each segment fills with the scroll progress through its
 * chapter; the current one widens and shows its name. It appears from the
 * "three worlds" scene on, as the storyboard asks.
 */
export function initChapterBar({ scrollTo, onRefresh } = {}) {
  const bar = document.querySelector('[data-chapter-bar]');
  if (!bar) return () => {};
  const showFrom = document.querySelector('[data-scene="worlds"]');
  const hideAfter = document.querySelector('[data-scene="cta"]');

  const ranges = CHAPTERS.map((id) => {
    const scenes = [...document.querySelectorAll(`[data-chapter="${id}"]`)];
    return { id, first: scenes[0], last: scenes[scenes.length - 1], link: bar.querySelector(`[data-chapter-link="${id}"]`) };
  });

  for (const r of ranges) {
    r.link.addEventListener('click', (e) => {
      e.preventDefault();
      if (scrollTo) scrollTo(r.first);
      else r.first.scrollIntoView({ behavior: 'smooth' });
    });
  }

  // A pinned scene sits inside a pin spacer that holds its real scroll range.
  const box = (el) => (el.parentElement?.classList.contains('pin-spacer') ? el.parentElement : el);
  const top = (el) => box(el).getBoundingClientRect().top + window.scrollY;

  // Measure once per layout change, not on every scroll event.
  let showAt = 0; let hideAt = Infinity;
  const measure = () => {
    for (const r of ranges) {
      r.start = top(r.first);
      r.end = top(r.last) + box(r.last).offsetHeight;
    }
    showAt = top(showFrom);
    hideAt = top(hideAfter);
  };

  const update = () => {
    const mid = window.scrollY + window.innerHeight * 0.5;
    let current = null;
    for (const r of ranges) {
      const { start, end } = r;
      const p = Math.min(1, Math.max(0, (mid - start) / (end - start)));
      r.link.querySelector('.seg-fill').style.setProperty('--p', p.toFixed(4));
      if (mid >= start && mid < end) current = r;
    }
    for (const r of ranges) {
      r.link.classList.toggle('is-current', r === current);
      if (r === current) r.link.setAttribute('aria-current', 'step');
      else r.link.removeAttribute('aria-current');
    }
    bar.classList.toggle('is-off', !(mid >= showAt && mid < hideAt));
  };
  const remeasure = () => { measure(); update(); };
  window.addEventListener('scroll', update, { passive: true });
  window.addEventListener('resize', remeasure);
  onRefresh?.(remeasure);
  remeasure();
  return remeasure;
}
