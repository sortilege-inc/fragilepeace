// M5: the old site as the VTT's site tabs. Headless, served from disk, through the real controls. Every line
// printed is a measurement; a FAIL exits 1.   NODE_PATH=~/App/ray-so/scripts/node_modules node campaign/source/check_tabs.js [shot-dir]
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const ROOT = process.env.ROOT || path.resolve(__dirname, '../..');
const ORIGIN = 'http://localhost:8764';
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.svg': 'image/svg+xml', '.json': 'application/json', '.png': 'image/png', '.webp': 'image/webp', '.jpg': 'image/jpeg', '.txt': 'text/plain' };
const errors = [], fails = [];
const wait = (ms) => new Promise((r) => setTimeout(r, ms));
function expect(label, got, want) {
  const ok = typeof want === 'function' ? want(got) : JSON.stringify(got) === JSON.stringify(want);
  console.log((ok ? '  ok   ' : '  FAIL ') + label + ' → ' + JSON.stringify(got) + (ok || typeof want === 'function' ? '' : '  (want ' + JSON.stringify(want) + ')'));
  if (!ok) fails.push(label);
}
// the old page's path → its route (campaign/source/to_docs.py route(), mirrored)
const TAB = { '': 'fp', character: 'pcs', party: 'party', chronicle: 'chronicle', 'dramatis-personae': 'personae', atlas: 'atlas', map: 'atlas', lore: 'rokugan', notes: 'notes' };
function routeOf(p) {
  const special = { 'index.html': [], 'map/index.html': [], 'atlas/index.html': ['gazetteer'] };
  const top = p.includes('/') ? p.split('/')[0] : '';
  let parts = special[p];
  if (!parts) { parts = (top ? p.slice(top.length + 1) : p).replace(/(^|\/)index\.html$/, '').split('/').filter(Boolean); if (parts.length) parts[parts.length - 1] = parts[parts.length - 1].replace(/\.html$/, ''); }
  return '#' + [TAB[top]].concat(parts).join('/');
}

(async () => {
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 1400, height: 1000 } });
  await ctx.route(ORIGIN + '/**', (route) => {
    let p = decodeURIComponent(new URL(route.request().url()).pathname).replace(/^\//, '');
    if (p === '' || p.endsWith('/')) p += 'index.html';
    const f = path.join(ROOT, p);
    if (!fs.existsSync(f) || fs.statSync(f).isDirectory()) { errors.push('404 ' + p); return route.fulfill({ status: 404, body: 'no' }); }
    route.fulfill({ status: 200, contentType: TYPES[path.extname(f)] || 'application/octet-stream', body: fs.readFileSync(f) });
  });
  await ctx.route(/^https?:\/\/(?!localhost:8764)/, (r) => (/fonts\.(googleapis|gstatic)/.test(r.request().url()) ? r.continue() : r.abort()));
  const p = await ctx.newPage();
  p.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
  p.on('pageerror', (e) => errors.push('pageerror: ' + e.message));
  await p.goto(ORIGIN + '/');
  await p.waitForFunction(() => document.querySelector('#site-tabs a.site-tab') && document.querySelector('.fp-doc .masthead, .fp-doc h1'), null, { timeout: 30000 });
  await wait(800);

  console.log('== the tabs');
  expect('the campaign\'s tabs first, in the old nav\'s order', (await p.locator('#site-tabs a.site-tab').allInnerTexts()).slice(0, 8).map((t) => t.trim().toUpperCase()),
    ['THE FRAGILE PEACE', 'THE CHARACTERS', 'THE PARTY', 'CHRONICLE', 'DRAMATIS PERSONAE', 'ATLAS', 'LORE', 'PLAYER NOTES']);
  expect('the site opens on the campaign\'s home', await p.evaluate(() => document.querySelector('.fp-doc h1') && document.querySelector('.fp-doc h1').innerText.trim()), (t) => !!t);

  console.log('== every document, by its route');
  const docs = await p.evaluate(() => window.FP_DOCS);
  expect('the manifest lists 517 documents', docs.length, 517);
  const bad = [];
  for (const d of docs) {
    await p.evaluate((h) => { location.hash = h; }, routeOf(d));
    try {
      await p.waitForFunction(() => { const h = document.querySelector('.fp-doc'); return h && !h.querySelector('.fp-reading'); }, null, { timeout: 8000 });
    } catch (e) { bad.push(d + ': never drew'); continue; }
    const t = await p.evaluate(() => document.querySelector('.fp-doc').innerText);
    if (/^Nothing in the record|^Could not read/.test(t.trim()) || t.trim().length < 20) bad.push(d + ': ' + t.trim().slice(0, 60));
  }
  expect('every document draws at its route', bad, []);

  console.log('== links, anchors, the map, the roster');
  await p.evaluate(() => { location.hash = '#chronicle/s42-midnight-tea'; }); await wait(900);
  // the session page's own Chronicle / Entities switch (radio buttons and CSS, no script)
  await p.locator('.fp-doc label[for="ct-ent"]').click(); await wait(300);
  expect('the session page\'s Entities switch shows its panel', await p.evaluate(() => getComputedStyle(document.querySelector('.fp-doc .tab-panel.tp-ent')).display !== 'none' && getComputedStyle(document.querySelector('.fp-doc .tab-panel.tp-chr')).display === 'none'), true);
  await p.locator('.fp-doc label[for="ct-chr"]').click(); await wait(200);
  const first = await p.locator('.fp-doc a.ref[href^="#party/"]').first().getAttribute('href');
  await p.locator('.fp-doc a.ref[href^="#party/"]').first().click(); await wait(900);
  expect('a link in a document opens its route (' + first + ')', await p.evaluate(() => location.hash), first);
  expect('… and draws that document', await p.evaluate(() => document.querySelector('.fp-doc h1').innerText.trim()), (t) => /\w/.test(t));
  await p.evaluate(() => { location.hash = '#pcs/setsuna/timeline'; }); await wait(1200);
  expect('an anchor route scrolls to its element', await p.evaluate(() => { const e = document.getElementById('timeline'); if (!e) return null; const r = e.getBoundingClientRect(); return r.top < innerHeight && r.bottom > 0 && scrollY > 100; }), true);
  await p.evaluate(() => { location.hash = '#atlas'; }); await wait(1500);
  const map = await p.evaluate(() => ({ regions: document.querySelectorAll('#hotspots polygon').length, base: !!(document.getElementById('baseimg') || {}).naturalWidth, title: (document.getElementById('rtitle') || {}).textContent }));
  expect('the Atlas tab draws the map, its regions live', map, (m) => m.regions >= 6 && m.base);
  await p.locator('#hotspots polygon').first().dispatchEvent('click'); await wait(1200);
  expect('a region opens on click', await p.evaluate(() => ({ title: document.getElementById('rtitle').textContent, region: !!(document.getElementById('regionimg') || {}).src && getComputedStyle(document.getElementById('regionimg')).display !== 'none' })), (r) => r.title !== map.title);
  await p.evaluate(() => { location.hash = '#personae'; }); await wait(1200);
  const before = await p.evaluate(() => document.querySelectorAll('.rost:not([hidden])').length);
  await p.locator('.fp-doc [data-filter="q"]').fill('doji'); await wait(300);
  const after = await p.evaluate(() => ({ shown: document.querySelectorAll('.rost:not([hidden])').length, count: document.querySelector('[data-roster-count]').textContent }));
  expect('the roster filters (all ' + before + ' → "doji")', after, (a) => a.shown > 0 && a.shown < before && /of/.test(a.count));

  console.log('== the styles');
  const st = await p.evaluate(() => {
    location.hash = '#rokugan';
    const cs = (sel, prop) => { const e = document.querySelector(sel); return e ? getComputedStyle(e)[prop] : null; };
    return { docFont: cs('.fp-doc', 'fontFamily').split(',')[0], vttTabFont: cs('#site-tabs a.site-tab', 'fontFamily').split(',')[0], bodyBg: getComputedStyle(document.body).backgroundColor };
  });
  await wait(900);
  const st2 = await p.evaluate(() => { location.hash = '#chronicle/s42-midnight-tea'; return 1; }); await wait(900);
  const tag = await p.evaluate(() => {
    const host = document.querySelector('.fp-doc');
    const probe = document.createElement('span'); probe.className = 'tag tag-open'; probe.textContent = 'x'; host.appendChild(probe);
    const c = getComputedStyle(probe); const out = { bg: c.backgroundColor, tt: c.textTransform }; probe.remove(); return out;
  });
  console.log('  ' + JSON.stringify(st));
  expect('the documents read in the old site\'s font', st.docFont.replace(/"/g, ''), 'EB Garamond');
  expect('a tag keeps the old colour and case, not the VTT\'s', tag, { bg: 'rgb(142, 47, 58)', tt: 'none' });
  // the VTT's page is as it is without the campaign's styles
  const bare = await browser.newContext(); await bare.route(ORIGIN + '/**', (route) => {
    let q = decodeURIComponent(new URL(route.request().url()).pathname).replace(/^\//, ''); if (q === '' || q.endsWith('/')) q += 'index.html';
    const f = path.join(ROOT, q); if (/campaign\/site\/(campaign|fp)\.css$/.test(q)) return route.fulfill({ status: 200, contentType: 'text/css', body: '' });
    if (!fs.existsSync(f) || fs.statSync(f).isDirectory()) return route.fulfill({ status: 404, body: 'no' });
    route.fulfill({ status: 200, contentType: TYPES[path.extname(f)] || 'application/octet-stream', body: fs.readFileSync(f) });
  });
  await bare.route(/^https?:\/\/(?!localhost:8764)/, (r) => (/fonts\.(googleapis|gstatic)/.test(r.request().url()) ? r.continue() : r.abort()));
  const b = await bare.newPage(); await b.goto(ORIGIN + '/'); await wait(2000);
  await p.evaluate(() => { location.hash = '#fp'; }); await wait(900);   // the same tab active on both
  const vtt = (pg) => pg.evaluate(() => { const g = (s, k) => { const e = document.querySelector(s); return e ? getComputedStyle(e)[k] : null; }; return [g('body', 'backgroundColor'), g('body', 'fontFamily'), g('#site-tabs a.site-tab', 'fontFamily'), g('#site-tabs a.site-tab', 'color'), g('.site-head', 'backgroundColor')]; });
  expect('the VTT\'s own page untouched by the campaign\'s styles (body, tabs, header)', await vtt(p), await vtt(b));
  await bare.close();

  console.log('== the look, as the old page (computed styles, element by element)');
  // only while the old pages are served (before they are deleted): OLD=1
  if (process.env.OLD) {
    const SAMPLE = ['index.html', 'character/index.html', 'character/setsuna.html', 'character/harunobu.html', 'character/jujiro.html',
      'character/anzu.html', 'party/index.html', 'party/doji-setsuna.html', 'chronicle/index.html', 'chronicle/s42-midnight-tea.html',
      'dramatis-personae/index.html', 'dramatis-personae/' + (docs.find((d) => /^dramatis-personae\/(?!index)/.test(d)) || '').split('/')[1],
      'atlas/index.html', 'map/index.html', 'lore/index.html', 'lore/factions/index.html', 'notes/index.html'];
    const sig = (root) => {
      const out = [];
      const walk = (e) => {
        for (const c of e.children) {
          if (c.matches('nav.topnav, footer.foot, script, style, link, .fp-reading')) continue;
          const s = getComputedStyle(c);
          out.push([c.tagName, s.fontFamily.split(',')[0].replace(/"/g, ''), s.fontSize, s.fontWeight, s.fontStyle, s.color, s.backgroundColor, s.textTransform, s.letterSpacing].join('|'));
          walk(c);
        }
      };
      walk(root);
      return out;
    };
    const old = await ctx.newPage(); await old.setViewportSize({ width: 1400, height: 1000 });
    await p.setViewportSize({ width: 1400, height: 1000 });
    const diffs = [];
    for (const d of SAMPLE) {
      await old.goto(ORIGIN + '/campaign/' + d); await wait(700);
      const a = await old.evaluate((f) => (new Function('return ' + f))()(document.body), sig.toString());
      await p.evaluate((h) => { location.hash = h; }, routeOf(d)); await p.mouse.move(1, 1); await wait(900);   // no :hover under a resting mouse
      const b = await p.evaluate((f) => (new Function('return ' + f))()(document.querySelector('.fp-doc')), sig.toString());
      let n = 0, first = null;
      for (let i = 0; i < Math.max(a.length, b.length); i++) if (a[i] !== b[i]) { n++; if (!first) first = i + ': ' + a[i] + '  →  ' + b[i]; }
      console.log('  ' + d + ': ' + a.length + ' elements, ' + n + ' differ' + (first ? ' — first ' + first : ''));
      if (n) diffs.push(d);
    }
    await old.close();
    expect('every sampled document styled as its old page', diffs, []);
  } else console.log('  (skipped: OLD=1 compares against the old pages while they are served)');

  console.log('== a phone');
  await p.setViewportSize({ width: 375, height: 812 });
  const wide = [];
  for (const h of ['#fp', '#chronicle/s42-midnight-tea', '#personae', '#atlas/gazetteer', '#pcs/setsuna', '#rokugan/factions']) {
    await p.evaluate((x) => { location.hash = x; }, h); await wait(900);
    const w = await p.evaluate(() => document.documentElement.scrollWidth - innerWidth);
    if (w > 1) wide.push(h + ' +' + w + 'px');
  }
  expect('no page scrolls sideways at 375px', wide, []);
  if (process.argv[2]) { await p.evaluate(() => { location.hash = '#chronicle/s42-midnight-tea'; }); await wait(900); await p.screenshot({ path: path.join(process.argv[2], 'm5-phone.png') });
    await p.setViewportSize({ width: 1400, height: 1000 }); await wait(500); await p.screenshot({ path: path.join(process.argv[2], 'm5-desk.png') }); }

  expect('console and page errors (and 404s)', errors, []);
  console.log(fails.length ? '\nFAIL ' + fails.length + ': ' + fails.join('; ') : '\nPASS');
  await browser.close();
  process.exit(fails.length ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(2); });
