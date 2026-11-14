// A rolling-digit counter. `set(t)` maps scroll progress 0..1 to a value
// between `from` and `to` on a log curve, so the big numbers race past and
// the last few ranks roll slowly into place, like an odometer.

export function createOdometer(host, from, to) {
  const D = String(Math.round(from)).length;
  host.replaceChildren();
  host.classList.add('odo');

  const hash = document.createElement('span');
  hash.className = 'odo-hash';
  hash.textContent = '#';
  host.append(hash);

  const cols = [];
  const commas = [];
  for (let j = D - 1; j >= 0; j--) {
    const col = document.createElement('span');
    col.className = 'odo-col';
    const strip = document.createElement('span');
    strip.className = 'odo-strip';
    for (let d = 0; d <= 10; d++) {
      const s = document.createElement('span');
      s.textContent = d % 10;
      strip.append(s);
    }
    col.append(strip);
    host.append(col);
    cols[j] = { col, strip };
    if (j % 3 === 0 && j > 0) {
      const c = document.createElement('span');
      c.className = 'odo-comma';
      c.textContent = ',';
      host.append(c);
      commas[j] = c;
    }
  }

  const lf = Math.log(Math.max(from, 1));
  const lt = Math.log(Math.max(to, 1));

  function render(v) {
    for (let j = 0; j < D; j++) {
      const p = 10 ** j;
      const shown = j === 0 || v >= p;
      const { col, strip } = cols[j];
      col.classList.toggle('is-off', !shown);
      if (commas[j]) commas[j].classList.toggle('is-off', v < p);
      let digit = Math.floor(v / p) % 10;
      // Roll a higher wheel only while the wheels below pass from 9 to 0.
      const below = v % p;
      const roll = j === 0 ? v % 1 : Math.max(0, below - (p - 1));
      digit += roll;
      strip.style.transform = `translateY(${-(digit / 11) * 100}%)`;
    }
  }

  return {
    set(t) {
      const k = Math.min(1, Math.max(0, t));
      const v = Math.exp(lf + (lt - lf) * k);
      render(k >= 1 ? to : v);
    },
  };
}
