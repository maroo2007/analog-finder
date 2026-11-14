const { chromium } = require('playwright');
const fs = require('fs');
const [, , mode, a, b, w] = process.argv;
(async () => {
  const br = await chromium.launch();
  const p = await br.newPage({ viewport: { width: 1920, height: 1080 } });
  p.on('pageerror', (e) => console.error('PAGE ERROR', e.message));
  await p.goto('file://' + process.cwd() + '/video.html');
  await p.evaluate(() => window.ready);
  if (mode === 'test') {
    for (const t of a.split(',').map(Number)) { await p.evaluate((t) => window.render(t), t); await p.screenshot({ path: `test_${String(t).replace('.', '_')}.jpg`, type: 'jpeg', quality: 80 }); }
  } else {
    fs.mkdirSync('frames', { recursive: true });
    const t0 = Date.now();
    for (let f = Number(a); f < Number(b); f++) {
      await p.evaluate((t) => window.render(t), f / 30);
      await p.screenshot({ path: `frames/f_${String(f).padStart(5, '0')}.jpg`, type: 'jpeg', quality: 94 });
    }
    console.log('worker', w, 'done', b - a, 'frames in', ((Date.now() - t0) / 1000).toFixed(1), 's');
  }
  await br.close();
})().catch((e) => { console.error(e); process.exit(1); });
