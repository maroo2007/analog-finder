// Word-by-word text reveal: each word comes in from a 12 px blur, 20 px low
// and transparent, one after another. The same motion as 21st.dev's
// TextReveal "fade-in-blur" preset (per word, speedReveal 1.2: 0.3 s per
// word, about 0.04 s between words), rebuilt with GSAP for this site,
// which has no React. It plays in time when a scene arrives and plays
// backwards when you scroll back above it.
import gsap from 'gsap';

export const WORD_STAGGER = 0.05 / 1.2; // seconds between words
export const WORD_DURATION = 0.3;       // seconds per word
const BLOCK_GAP = 0.12;                 // seconds between text blocks

/**
 * Wrap every word of el in <span class="rw">, leaving nested elements
 * (numbers filled from the data, links) in place, and statement words that
 * are already wrapped (.w) as they are. Returns the word elements in order.
 */
export function splitWords(el) {
  if (el.dataset.rwDone) return [...el.querySelectorAll('.rw, .w')];
  el.dataset.rwDone = '1';
  const words = [];
  const walk = (node) => {
    for (const child of [...node.childNodes]) {
      if (child.nodeType === Node.ELEMENT_NODE) {
        if (child.classList.contains('w')) { words.push(child); continue; }
        walk(child);
      } else if (child.nodeType === Node.TEXT_NODE && child.textContent.trim()) {
        const frag = document.createDocumentFragment();
        for (const part of child.textContent.split(/(\s+)/)) {
          if (!part) continue;
          if (/^\s+$/.test(part)) { frag.append(part); continue; }
          const span = document.createElement('span');
          span.className = 'rw';
          span.textContent = part;
          frag.append(span);
          words.push(span);
        }
        child.replaceWith(frag);
      }
    }
  };
  walk(el);
  return words;
}

/**
 * A paused timeline revealing the given text blocks in order, word by word.
 * Blur is lighter on phones, where big blurred text costs more to draw.
 */
export function revealTimeline(blocks, { phone = false } = {}) {
  const blur = phone ? 8 : 12;
  const tl = gsap.timeline({ paused: true });
  let at = 0;
  for (const block of blocks) {
    if (!block) continue;
    const words = splitWords(block);
    if (!words.length) continue;
    gsap.set(words, { opacity: 0, y: 20, filter: `blur(${blur}px)` });
    tl.to(words, {
      opacity: 1,
      y: 0,
      filter: 'blur(0px)',
      duration: WORD_DURATION,
      ease: 'power2.out',
      stagger: WORD_STAGGER,
      // Drop the filter once clear, so finished text is plain text again.
      onComplete: () => gsap.set(words, { clearProps: 'filter' }),
    }, at);
    at += BLOCK_GAP;
  }
  return tl;
}
