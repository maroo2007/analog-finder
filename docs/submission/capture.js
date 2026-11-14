const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  await p.goto('https://duplicaa.vercel.app/', { waitUntil: 'networkidle', timeout: 90000 });
  await p.waitForTimeout(5000);
  const h = await p.evaluate(() => document.documentElement.scrollHeight);
  const shots = { s1_hero: 0, s2_problem: 0.06, s3_idea: 0.15, s4_pick: 0.30, s5_match: 0.45, s6_proof: 0.60 };
  for (const [name, f] of Object.entries(shots)) {
    await p.evaluate((y) => window.scrollTo(0, y), Math.round(h * f));
    await p.waitForTimeout(3500);
    await p.screenshot({ path: `${name}.png` });
    console.log('shot', name);
  }
  await p.goto('https://duplicaa.vercel.app/explorer.html', { waitUntil: 'networkidle', timeout: 90000 });
  await p.waitForTimeout(5000);
  await p.click('[data-target-list] button[data-id="jezero"]');
  await p.waitForTimeout(5000);
  await p.click('[data-twin-list] button[data-key]');
  await p.waitForTimeout(9000);
  await p.screenshot({ path: 's7b_close.png' });
  console.log('shot close');
  // zoom out for regional context (Red Sea, Nile)
  const out = p.locator('.maplibregl-ctrl-zoom-out');
  if (await out.count()) { for (let i = 0; i < 4; i++) { await out.first().click(); await p.waitForTimeout(900); } }
  else { await p.mouse.move(1150, 520); for (let i = 0; i < 4; i++) { await p.mouse.wheel(0, 500); await p.waitForTimeout(900); } }
  await p.waitForTimeout(8000);
  await p.screenshot({ path: 's7a_region.png' });
  console.log('shot region, zoom ctrl:', await out.count());
  await b.close();
})().catch(e => { console.error(e); process.exit(1); });
