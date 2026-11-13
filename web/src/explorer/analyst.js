// "Ask the analyst": a chat panel that talks to our own serverless function
// (never to Gemini directly; the key lives only on the server). Each request
// carries only the data on screen, and the model can ask the page to select
// a target or a twin.

const ENDPOINT = `${import.meta.env.BASE_URL}api/analyst`.replace(/^\.\//, '/');
const MAX_TURNS = 12; // history kept per request, to stay small

const CHIPS = [
  'Why is Egypt Jezero\'s closest twin?',
  'What doesn\'t match here?',
  'Which Mars sites have a twin in Egypt?',
  'Compare the top 3 twins',
  'What could be tested here?',
  'Why are Moon scores low?',
  'How does the matching work?',
  'اشرحلي بالعربي',
];

/**
 * @param {object} app
 *   getContext(): the grounding data for the current view
 *   selectTarget(id): Promise, selects a target and loads its twins
 *   selectTwin(n): selects twin n (1-based) of the current target
 */
export function createAnalyst(app) {
  const panel = document.querySelector('[data-analyst]');
  const openBtn = document.querySelector('[data-analyst-open]');
  const closeBtn = panel.querySelector('[data-analyst-close]');
  const log = panel.querySelector('[data-analyst-log]');
  const form = panel.querySelector('[data-analyst-form]');
  const input = panel.querySelector('[data-analyst-input]');
  const send = panel.querySelector('[data-analyst-send]');
  const chips = panel.querySelector('[data-analyst-chips]');

  // The conversation in Gemini's own shape, so function calls can be
  // answered exactly as the model sent them.
  let history = [];
  let busy = false;

  chips.replaceChildren(...CHIPS.map((q) => {
    const b = document.createElement('button');
    b.type = 'button';
    b.textContent = q;
    b.dir = 'auto';
    b.addEventListener('click', () => ask(q));
    return b;
  }));

  const open = () => {
    panel.hidden = false;
    openBtn.setAttribute('aria-expanded', 'true');
    requestAnimationFrame(() => panel.classList.add('is-open'));
    input.focus();
  };
  const close = () => {
    panel.classList.remove('is-open');
    openBtn.setAttribute('aria-expanded', 'false');
    setTimeout(() => { if (!panel.classList.contains('is-open')) panel.hidden = true; }, 350);
    openBtn.focus();
  };
  openBtn.addEventListener('click', () => (panel.hidden ? open() : close()));
  closeBtn.addEventListener('click', close);
  panel.addEventListener('keydown', (e) => { if (e.key === 'Escape') close(); });

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const q = input.value.trim();
    if (q) ask(q);
  });
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); form.requestSubmit(); }
  });

  function bubble(kind, text) {
    const div = document.createElement('div');
    div.className = `msg msg-${kind}`;
    div.dir = 'auto';
    // Plain text only: the model's reply is never inserted as HTML.
    for (const [i, line] of text.split('\n').entries()) {
      if (i) div.append(document.createElement('br'));
      div.append(document.createTextNode(line));
    }
    log.append(div);
    log.scrollTop = log.scrollHeight;
    return div;
  }

  function setBusy(on) {
    busy = on;
    send.disabled = on;
    input.disabled = on;
    panel.classList.toggle('is-busy', on);
    let dots = log.querySelector('.msg-wait');
    if (on && !dots) {
      dots = bubble('wait', 'Reading the data');
      dots.setAttribute('aria-label', 'The analyst is answering');
    } else if (!on && dots) dots.remove();
  }

  async function call(contents) {
    const res = await fetch(ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ contents: contents.slice(-MAX_TURNS), context: app.getContext() }),
    });
    let data = {};
    try { data = await res.json(); } catch { /* handled below */ }
    if (!res.ok) {
      const err = new Error(data.error || `HTTP ${res.status}`);
      err.status = res.status;
      throw err;
    }
    return data; // { content: { role: 'model', parts: [...] } }
  }

  async function runActions(parts) {
    const responses = [];
    for (const p of parts) {
      const fc = p.functionCall;
      if (!fc) continue;
      let result;
      try {
        if (fc.name === 'select_target') {
          const ok = await app.selectTarget(fc.args?.id);
          result = ok ? { ok: true, selected: fc.args.id } : { ok: false, error: 'No target with that id' };
          if (ok) bubble('note', `Showing ${ok}`);
        } else if (fc.name === 'select_twin') {
          const ok = app.selectTwin(Number(fc.args?.n));
          result = ok ? { ok: true, selected: Number(fc.args.n) } : { ok: false, error: 'No twin with that number' };
          if (ok) bubble('note', ok);
        } else {
          result = { ok: false, error: 'Unknown action' };
        }
      } catch (err) {
        result = { ok: false, error: String(err.message || err) };
      }
      responses.push({ functionResponse: { name: fc.name, response: result } });
    }
    return responses;
  }

  async function ask(question) {
    if (busy) return;
    if (panel.hidden) open();
    input.value = '';
    bubble('user', question);
    const mark = history.length;
    history.push({ role: 'user', parts: [{ text: question }] });
    setBusy(true);
    try {
      // Up to two rounds: the model may first ask the page to do something,
      // then answer with the new data on screen.
      for (let round = 0; round < 2; round++) {
        const { content } = await call(history);
        const parts = content?.parts || [];
        history.push({ role: 'model', parts });
        const text = parts.filter((p) => p.text && !p.thought).map((p) => p.text).join('').trim();
        const calls = parts.filter((p) => p.functionCall);
        if (text) bubble('bot', text);
        if (!calls.length) break;
        const responses = await runActions(calls);
        history.push({ role: 'user', parts: responses });
        if (round === 1) bubble('note', 'Done.');
      }
    } catch (err) {
      console.error(err);
      const msg = err.status === 429
        ? (err.message && !err.message.startsWith('HTTP') ? err.message : 'The analyst has answered all the questions it can for now. Please try again later; everything else in the Twin Finder still works.')
        : err.status === 503
          ? 'The analyst is not switched on for this copy of the site yet.'
          : 'The analyst could not answer just now. Please try again in a moment.';
      bubble('error', msg);
      history = history.slice(0, mark);
    } finally {
      setBusy(false);
      input.focus();
    }
  }

  return { open, close, ask };
}
