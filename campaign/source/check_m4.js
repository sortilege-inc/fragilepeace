// M4: the characters on the VTT sheet, play/ retired. Headless, served from disk, through the real
// controls. Every line printed is a measurement; a FAIL exits 1.
//   NODE_PATH=~/App/ray-so/scripts/node_modules node campaign/source/check_m4.js [shot-dir]
// The old-sheet saves it imports are TEST values planted in this throwaway browser profile only.
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const ROOT = process.env.ROOT || path.resolve(__dirname, '../..');
const UP = path.join(process.env.HOME, 'Sortilege/VTT/sortilege-vtt-l5r5e');
const OVER = (process.env.OVER || '').split(' ').filter(Boolean);   // upstream files laid over this repo's, before a merge
const ORIGIN = 'http://localhost:8763';
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.svg': 'image/svg+xml', '.json': 'application/json', '.png': 'image/png', '.webp': 'image/webp', '.jpg': 'image/jpeg', '.txt': 'text/plain' };
const errors = [], fails = [];
const wait = (ms) => new Promise((r) => setTimeout(r, ms));
function expect(label, got, want) {
  const ok = typeof want === 'function' ? want(got) : JSON.stringify(got) === JSON.stringify(want);
  console.log((ok ? '  ok   ' : '  FAIL ') + label + ' → ' + JSON.stringify(got) + (ok || typeof want === 'function' ? '' : '  (want ' + JSON.stringify(want) + ')'));
  if (!ok) fails.push(label);
}
const CAST = [
  ['#FPpcDojiSetsuna', 'Doji Setsuna', 'campaign/assets/setsuna.webp'],
  ['#FPpcShinjoHarunobu', 'Shinjō Harunobu', 'campaign/assets/harunobu.webp'],
  ['#FPpcTonboKuma', 'Tonbo Kuma', null],
  ['#FPpcAsahinaJujiro', 'Asahina Jūjirō', 'campaign/assets/jujiro.webp'],
  ['#FPpcShinjoAnzu', 'Shinjō Anzu', 'campaign/assets/anzu.webp'],
  ['#FPpcMatsuMorozane', 'Matsu Morozane', 'campaign/assets/morozane.webp'],
];

(async () => {
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 1500, height: 3200 } });
  await ctx.route(ORIGIN + '/**', (route) => {
    let p = decodeURIComponent(new URL(route.request().url()).pathname).replace(/^\//, '');
    if (p === '' || p.endsWith('/')) p += 'index.html';
    const f = path.join(OVER.includes(p) ? UP : ROOT, p);
    if (!fs.existsSync(f) || fs.statSync(f).isDirectory()) { errors.push('404 ' + p); return route.fulfill({ status: 404, body: 'no' }); }
    route.fulfill({ status: 200, contentType: TYPES[path.extname(f)] || 'application/octet-stream', body: fs.readFileSync(f) });
  });
  await ctx.route(/^https?:\/\/(?!localhost:8763)/, (r) => (/fonts\.(googleapis|gstatic)/.test(r.request().url()) ? r.continue() : r.abort()));
  await ctx.addInitScript(() => { try { sessionStorage.setItem('fragilepeace-vtt:gm-gate', '1'); } catch (e) { /* */ } });
  const watch = (p, name) => { p.on('console', (m) => { if (m.type() === 'error') errors.push(name + ': ' + m.text()); }); p.on('pageerror', (e) => errors.push(name + ' pageerror: ' + e.message)); };

  // test saves, as the retired pages wrote them (the keys pf-sheet-<id>, pf-log-<id>)
  const seed = await ctx.newPage(); watch(seed, 'seed');
  await seed.goto(ORIGIN + '/robots.txt');
  await seed.evaluate(() => {
    localStorage.clear();
    // Setsuna: honor 69 is what her page printed (untouched, so not taken); glory 75 was changed in play
    localStorage.setItem('pf-sheet-setsuna', JSON.stringify({ strife: 5, fatigue: 3, 'void': 1, stance: 'water', honor: 69, glory: 75, status: 60, conditions: ['Dazed'], inConflict: false }));
    localStorage.setItem('pf-log-setsuna', JSON.stringify([{ skillLabel: 'Courtesy', ring: 'air', ringN: 3, tn: 2, su: 3, op: 1, pass: true, when: 's58' }, { kind: 'event', text: 'Spent a Void point' }]));
    // Harunobu: glory 49 is the pre-award value his page once printed — a stale save, so not taken
    localStorage.setItem('pf-sheet-harunobu', JSON.stringify({ strife: 2, fatigue: 0, 'void': 2, stance: 'fire', honor: 55, glory: 49, status: 35 }));
  });
  await seed.close();

  const p = await ctx.newPage(); watch(p, 'gm');
  await p.goto(ORIGIN + '/gm/');
  await p.waitForFunction(() => window.VttState && VttState.state && /PARTY/i.test(document.body.innerText), null, { timeout: 30000 });
  await wait(1200);
  await p.locator('button, a', { hasText: /^Party$/i }).first().click(); await wait(600);
  const picker = () => p.locator('select.scope', { has: p.locator('option', { hasText: 'add a pregenerated character' }) }).first();
  for (const [id, name, portrait] of CAST) {
    console.log('== ' + name);
    await picker().selectOption(id); await wait(3500);
    const box = p.locator('.sheet.live').first();
    const want = await p.evaluate((x) => { const v = L5RSheet.memberFromEntity(L5RData.entity(x)).character; return { techs: (v.Techniques || []).map(String) }; }, id);
    const got = await box.evaluate((b) => ({
      name: (b.querySelector('.sheet-head h2') || {}).innerText,
      portrait: (b.querySelector('.sheet-head img.portrait') || {}).getAttribute ? b.querySelector('.sheet-head img.portrait').getAttribute('src') : null,
      portraitLoaded: !!(b.querySelector('.sheet-head img.portrait') && b.querySelector('.sheet-head img.portrait').naturalWidth),
      techs: [...b.querySelectorAll('.techniques-in-play .tech-row')].map((r) => (r.querySelector('button, .tech-name, span') || r).innerText.trim().toLowerCase()),
      bio: (() => { const d = b.querySelector('details.ac-fold'); if (!d) return ''; d.open = true; return d.innerText; })(),
    }));
    expect('the Inspector shows ' + name, got.name && got.name.trim(), name);
    expect('portrait', [got.portrait, portrait ? got.portraitLoaded : null], [portrait, portrait ? true : null]);
    expect('every technique, a title\'s own included (' + want.techs.length + ')', got.techs, want.techs.map((t) => t.toLowerCase()));
    if (id === '#FPpcDojiSetsuna') {
      expect('Setsuna: Shallow Waters and the three kata', ['shallow waters', 'coiling serpent style', 'crescent moon style', 'open-hand style'].every((t) => got.techs.indexOf(t) !== -1), true);
      expect('Setsuna: the old sheet\'s facts in her biography', ['Rigid acquiescence', 'Kogarashi', 'Two boons, owed by the Lion', 'Miya Satoshi'].filter((t) => got.bio.indexOf(t) === -1), []);
    }
    if (id === '#FPpcDojiSetsuna') expect('Setsuna: no Void Wound (healed — owner, 2026-10-01)', /Void Wound/.test(got.bio), false);
    if (id === '#FPpcShinjoAnzu') expect('Anzu: not a campaign character', /does not appear in the chronicle/.test(got.bio), true);
    if (id === '#FPpcTonboKuma') expect('Kuma: the giri finished', /City of the Rich Frog/.test(got.bio), true);
  }

  if (process.argv[2]) { await p.locator('.sheet.live').first().screenshot({ path: path.join(process.argv[2], 'm4-last.png') }); }
  // the one-time import (the GM page loads it at its gm stage)
  await wait(1500);
  const imp = await p.evaluate(() => {
    const by = (n) => VttState.state.party.find((m) => m.name === n);
    const s = by('Doji Setsuna'), h = by('Shinjō Harunobu'), k = by('Tonbo Kuma');
    const pick = (m) => { const l = m.live || {}; return { Strife: l.Strife, Fatigue: l.Fatigue, voidPoints: l.voidPoints, stance: l.stance, Honor: l.Honor, Glory: l.Glory, conditions: l.conditions, from: (l.importedFrom || {}).key }; };
    return { setsuna: pick(s), harunobu: pick(h), kuma: pick(k), log: (VttState.state.log || []).filter((e) => e.memberId === s.id).map((e) => e.text) };
  });
  console.log('  import: ' + JSON.stringify(imp));
  expect('Setsuna took her save: trackers, stance, Dazed, glory changed in play — not the printed honor',
    imp.setsuna, { Strife: 5, Fatigue: 3, voidPoints: 1, stance: 'Water', Honor: undefined, Glory: 75, conditions: ['Dazed'], from: 'pf-sheet-setsuna' });
  expect('Harunobu took his trackers, and not the stale pre-award glory 49', [imp.harunobu.Strife, imp.harunobu.stance, imp.harunobu.Glory, imp.harunobu.from], [2, 'Fire', undefined, 'pf-sheet-harunobu']);
  expect('Kuma had no save, so nothing imported', imp.kuma.from, undefined);
  expect('Setsuna\'s old log, oldest first, then the import line', imp.log.slice(-3).map((t) => t.slice(0, 40)), (l) => l.length === 3 && /Spent a Void point/.test(l[0]) && /Courtesy/.test(l[1]) && /^Imported from the old sheet/.test(l[2]));
  const nLog = (await p.evaluate(() => (VttState.state.log || []).length));
  await p.reload(); await wait(3000);
  expect('a reload imports nothing again', await p.evaluate(() => (VttState.state.log || []).length), nLog);

  // the old site's Play links land on the player's page
  for (const pg of ['campaign/character/index.html', 'campaign/party/doji-setsuna.html']) {
    const q = await ctx.newPage(); watch(q, pg);
    await q.goto(ORIGIN + '/' + pg); await wait(800);
    const hrefs = await q.evaluate(() => [...document.querySelectorAll('a')].map((a) => a.href).filter((h) => /play/.test(h)));
    expect(pg + ': its Play links go to /gm/play.html', [...new Set(hrefs.map((h) => new URL(h).pathname))], ['/gm/play.html']);
    await q.close();
  }
  const pp = await ctx.newPage(); watch(pp, 'gm/play.html');
  await pp.goto(ORIGIN + '/gm/play.html'); await wait(2500);
  expect('the player\'s page opens', await pp.evaluate(() => !!document.body.innerText.trim()), true);
  expect('console and page errors (and 404s)', errors, []);
  console.log(fails.length ? '\nFAIL ' + fails.length + ': ' + fails.join('; ') : '\nPASS');
  await browser.close();
  process.exit(fails.length ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(2); });
