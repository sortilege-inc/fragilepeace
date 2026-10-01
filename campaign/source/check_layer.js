// F9: the campaign layer wired in at the data stage. Served from disk. Every line printed is a
// measurement, and a FAIL exits 1. OVER="system/l5r5e/sheet.js …" lays those files from the upstream
// checkout over this repo's own, to test an upstream change before it is merged.
//   NODE_PATH=~/App/ray-so/scripts/node_modules node campaign/source/check_layer.js [shot.png]
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const ROOT = process.env.ROOT || path.resolve(__dirname, '../..');
const UP = path.join(process.env.HOME, 'Sortilege/VTT/sortilege-vtt-l5r5e');
const OVER = (process.env.OVER || '').split(' ').filter(Boolean);
const ORIGIN = 'http://localhost:8762';
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.svg': 'image/svg+xml', '.json': 'application/json', '.png': 'image/png', '.webp': 'image/webp', '.jpg': 'image/jpeg' };
const errors = [], fails = [], requested = new Set();
const wait = (ms) => new Promise((r) => setTimeout(r, ms));
function expect(label, got, want) {
  const ok = typeof want === 'function' ? want(got) : JSON.stringify(got) === JSON.stringify(want);
  console.log((ok ? '  ok   ' : '  FAIL ') + label + ' → ' + JSON.stringify(got) + (ok || typeof want === 'function' ? '' : '  (want ' + JSON.stringify(want) + ')'));
  if (!ok) fails.push(label);
}
(async () => {
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 1500, height: +(process.env.H || 1000) } });
  await ctx.route(ORIGIN + '/**', (route) => {
    let p = decodeURIComponent(new URL(route.request().url()).pathname).replace(/^\//, '');
    if (p === '' || p.endsWith('/')) p += 'index.html';
    requested.add(p);
    const f = path.join(OVER.includes(p) ? UP : ROOT, p);
    if (!fs.existsSync(f) || fs.statSync(f).isDirectory()) { errors.push('404 ' + p); return route.fulfill({ status: 404, body: 'no' }); }
    route.fulfill({ status: 200, contentType: TYPES[path.extname(f)] || 'application/octet-stream', body: fs.readFileSync(f) });
  });
  await ctx.route(/^https?:\/\/(?!localhost:8762)/, (r) => (/fonts\.(googleapis|gstatic)/.test(r.request().url()) ? r.continue() : r.abort()));
  await ctx.addInitScript(() => { try { sessionStorage.setItem('fragilepeace-vtt:gm-gate', '1'); } catch (e) { /* */ } });
  const watch = (p, name) => { p.on('console', (m) => { if (m.type() === 'error') errors.push(name + ': ' + m.text()); }); p.on('pageerror', (e) => errors.push(name + ' pageerror: ' + e.message)); };

  // every page loads the layer
  const PCS = ['Doji Setsuna', 'Shinjō Harunobu', 'Tonbo Kuma', 'Asahina Jūjirō', 'Shinjō Anzu', 'Matsu Morozane'];
  // and Morozane's lion, transcribed (F10)
  const NPCS = ['Khar Baatar', 'Kurige', "Tonbo Kuma's Manifest Water Kami", 'Shigo no Chinmoku'];
  for (const pg of ['', 'gm/', 'gm/vtt.html', 'gm/play.html']) {
    const p = await ctx.newPage(); watch(p, pg || 'site');
    await p.goto(ORIGIN + '/' + pg); await wait(3500);
    const r = await p.evaluate(() => window.L5RData ? { campaign: L5RData.books().some((b) => b.id === 'campaign'), label: L5RData.label ? L5RData.label('campaign') : null, pregens: L5RData.pregens().filter((x) => x.book === 'campaign').map((x) => x.name), npcs: L5RData.npcs().filter((x) => x.book === 'campaign').map((x) => x.name).sort() } : null);
    expect((pg || 'site') + ': the campaign book, its 6 characters and 4 companions', r, (x) => x && x.campaign && JSON.stringify(x.pregens) === JSON.stringify(PCS) && JSON.stringify(x.npcs) === JSON.stringify(NPCS.slice().sort()));
    if (!pg) console.log('  site pregens: ' + JSON.stringify(r && r.pregens) + ' · label ' + JSON.stringify(r && r.label));
    await p.close();
  }
  expect('campaign/data/index.js requested', requested.has('campaign/data/index.js'), true);

  // the GM page: Setsuna added through the Party pane's own picker, opened in the Inspector
  const p = await ctx.newPage(); watch(p, 'gm');
  await p.goto(ORIGIN + '/gm/');
  await p.waitForFunction(() => window.VttState && VttState.state && /PARTY/i.test(document.body.innerText), null, { timeout: 30000 });
  await wait(1200);
  await p.locator('button, a', { hasText: /^Party$/i }).first().click(); await wait(600);
  const picker = p.locator('select.scope', { has: p.locator('option', { hasText: 'add a pregenerated character' }) }).first();
  const opt = await picker.locator('option', { hasText: 'Doji Setsuna' }).first().getAttribute('value');
  expect('Doji Setsuna offered in the picker', opt, '#FPpcDojiSetsuna');
  await picker.selectOption(opt); await wait(4000);
  const box = p.locator('.sheet.live').first();
  const m = await box.evaluate((b) => ({
    name: (b.querySelector('.sheet-head h2') || {}).innerText,
    line: (b.querySelector('.sheet-head .muted') || {}).innerText,
    rings: [...b.querySelectorAll('.ring-tile')].map((x) => x.innerText.replace(/\s+/g, ' ').trim()),
    techniques: b.querySelectorAll('.techniques .tech, .technique, [class*=tech] button').length,
    skills: b.querySelectorAll('.ac-skills .ac-chip').length,
    versions: [...b.querySelector('.sheet-head select.scope').options].map((o) => o.textContent),
    acRings: b.querySelectorAll('.ac-rings').length,
  }));
  for (const [k, v] of Object.entries(m)) console.log('  ' + k + ': ' + JSON.stringify(v));
  expect('the Inspector shows Doji Setsuna', m.name && m.name.trim(), 'Doji Setsuna');
  expect('five ring tiles, no duplicate row', [m.rings.length, m.acRings], [5, 0]);
  expect('skills to click', m.skills, (n) => n >= 3);
  // her rings and skills as the book holds them
  const want = await p.evaluate(() => { const v = L5RSheet.memberFromEntity(L5RData.entity('#FPpcDojiSetsuna')).character; return { rings: v.Rings, skills: v.Skills }; });
  const shown = await box.evaluate((b) => ({ rings: Object.fromEntries([...b.querySelectorAll('.ring-tile')].map((x) => { const t = x.innerText.trim().split(/\s+/); return [t[t.length - 1][0] + t[t.length - 1].slice(1).toLowerCase(), +t.find((y) => /^\d+$/.test(y))]; })), skills: Object.fromEntries([...b.querySelectorAll('.ac-skills .ac-chip')].map((c) => [c.querySelector('.ac-chip-nm').innerText.trim().toLowerCase(), c.querySelector('.ac-chip-v').innerText.trim()])) }));
  expect('rings as the book', shown.rings, (r) => Object.keys(want.rings).every((k) => r[k] === want.rings[k]));
  expect('skills as the book', Object.keys(want.skills).filter((k) => want.skills[k] != null && String(shown.skills[k.toLowerCase()]) !== String(want.skills[k])), []);
  // every technique on her sheet, in its order, whatever book it is from and whether or not it has a check
  const techWant = await p.evaluate(() => L5RSheet.memberFromEntity(L5RData.entity('#FPpcDojiSetsuna')).character.Techniques.map(String));
  const techShown = await box.evaluate((b) => [...b.querySelectorAll('.techniques-in-play .tech-row')].map((r) => (r.querySelector('button, .tech-name, span') || r).innerText.trim()));
  console.log('  techniques shown: ' + JSON.stringify(techShown));
  expect('every technique named, in order (' + techWant.length + ')', techShown.map((x) => x.toLowerCase()), techWant.map((x) => x.toLowerCase()));
  if (process.argv[2]) { await box.screenshot({ path: process.argv[2] }); console.log('  shot: ' + process.argv[2]); }
  expect('console and page errors (and 404s)', errors, []);
  console.log(fails.length ? '\nFAIL ' + fails.length + ': ' + fails.join('; ') : '\nPASS');
  await browser.close();
  process.exit(fails.length ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(2); });
