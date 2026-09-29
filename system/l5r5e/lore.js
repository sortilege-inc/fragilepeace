// system/l5r5e/lore.js — the GM's Lore pane: search the L5R fan wiki for inspiration.
//
// The index is l5r-lore (~/Sortilege/Experiments/l5r-lore), which stays on the GM's machine: the
// wiki text is CC BY-SA and is never copied into this repo or served by the campaign's site. The
// GM runs `python -m lore serve` there and puts its address in Settings (blank by default); this
// pane calls it from the GM's own browser. With no address, or the server down, the pane says so.
// To use it away from that machine, l5r-lore publishes the server through Tailscale Funnel and
// requires a token (the campaign's LORE-PROXY runbook): the GM types the token into Settings, it is
// kept in this browser's localStorage beside the address, and it is sent as a Bearer header — never
// in the pack or a session.
//
// Neither continuity is canon at this table — both are sources of inspiration. So by default a
// search runs twice and shows the two side by side: the Fantasy Flight reboot (the continuity
// the table uses, labelled ffg in the index) and the AEG legacy continuity. Every result and
// every section carries its continuity, and how the index decided it where that was only
// inferred or defaulted. A page that has a version in the other continuity links to it. The
// wiki paraphrases rules, so rules questions belong to the Rules & Book pane, not here.
window.L5RLore = (function () {
  const { el, button } = window.VttRender;
  const State = window.VttState;
  const LS = 'sortilege.l5r5e.lore';
  const DEFAULT_URL = 'http://127.0.0.1:8797';
  const CANON = {
    ffg: { label: 'Fantasy Flight', long: 'Fantasy Flight reboot (2017) — the table’s continuity' },
    'aeg-legacy': { label: 'AEG legacy', long: 'AEG legacy continuity (1995–2015)' },
    unknown: { label: 'unlabelled', long: 'continuity not decided by the index' },
    none: { label: 'real world', long: 'real-world page (a book, an artist, a card set)' },
  };
  const LAYERS = [['', 'Any kind'], ['lore', 'Lore'], ['fiction', 'Fiction'], ['rpg', 'RPG'], ['card', 'Cards'], ['product', 'Products']];

  function settings() {
    let s = null;
    try { s = JSON.parse(localStorage.getItem(LS) || 'null'); } catch (e) { s = null; }
    return Object.assign({ url: '', token: '' }, s || {});
  }
  function save(patch) { try { localStorage.setItem(LS, JSON.stringify(Object.assign(settings(), patch))); } catch (e) { /* private mode */ } }
  const base = () => (settings().url || '').trim().replace(/\/+$/, '');
  const configured = () => !!base();
  function api(path, params) {
    const u = new URL(base() + path);
    Object.keys(params || {}).forEach((k) => [].concat(params[k]).forEach((v) => v != null && v !== '' && u.searchParams.append(k, v)));
    const token = (settings().token || '').trim();
    return fetch(u.toString(), token ? { headers: { Authorization: 'Bearer ' + token } } : undefined).then((r) => {
      if (r.status === 401) throw new Error(token ? 'the server refused the token in Settings' : 'the server needs a token; put it in Settings');
      return r.json().then((d) => { if (!r.ok && !d.error) throw new Error('HTTP ' + r.status); return d; });
    });
  }

  // the pane's own state survives redraws within a page load
  const view = { q: '', canon: 'both', layer: '', results: null, page: null, error: null, busy: false, health: null, back: [] };
  let redraw = () => {};

  // the continuity, and — only where the index inferred or defaulted it — that it is a hint;
  // the index's full reasoning ("explicit: category Falcon Clan Members (TCG)") is the tooltip
  const badge = (canon, basis) => {
    const how = String(basis || '').split(':')[0].trim();
    return el('span', { class: 'lore-badge lore-' + canon, title: [(CANON[canon] || {}).long || canon, basis].filter(Boolean).join(' — ') }, [
      (CANON[canon] || {}).label || canon, how === 'inferred' || how === 'default' ? el('i', {}, [' · ' + how]) : null]);
  };
  const shorten = (t, n) => { const s = String(t || '').replace(/\s+/g, ' ').trim(); return s.length > n ? s.slice(0, s.lastIndexOf(' ', n) > n / 2 ? s.lastIndexOf(' ', n) : n) + '…' : s; };

  function search() {
    if (!view.q.trim()) return;
    view.busy = true; view.page = null; view.error = null; redraw();
    const layer = view.layer || null;
    const run = (canon) => api('/search', { q: view.q, canon, layer, k: view.canon === 'both' ? 6 : 12 });
    const jobs = view.canon === 'both' ? [run(['ffg']), run(['aeg-legacy', 'unknown'])] : [run(view.canon === 'ffg' ? ['ffg'] : ['aeg-legacy', 'unknown'])];
    Promise.all(jobs).then((rs) => {
      view.results = view.canon === 'both'
        ? [{ key: 'ffg', title: CANON.ffg.long, data: rs[0] }, { key: 'aeg-legacy', title: CANON['aeg-legacy'].long, data: rs[1] }]
        : [{ key: view.canon, title: CANON[view.canon].long, data: rs[0] }];
    }).catch((e) => { view.error = e; }).finally(() => { view.busy = false; redraw(); });
  }
  function openPage(name, pushBack) {
    if (pushBack && view.page) view.back.push(view.page.title);
    view.busy = true; view.error = null; redraw();
    Promise.all([api('/page', { name }), api('/related', { name }).catch(() => null)]).then(([p, rel]) => {
      if (p.error) { view.error = new Error(p.error + (p.did_you_mean && p.did_you_mean.length ? ' — did you mean ' + p.did_you_mean.join(', ') + '?' : '')); return; }
      view.page = Object.assign(p, { related: rel && !rel.error ? rel : null });
    }).catch((e) => { view.error = e; }).finally(() => { view.busy = false; redraw(); });
  }
  // a quoted passage, with its citation, appended to the GM's own notes
  function toNotes(page, sec) {
    const cur = (State.state && State.state.gmNotes) || '';
    const quote = String(sec.text || '').trim().split('\n').map((l) => '> ' + l).join('\n');
    const cite = '— ' + page.title + ' › ' + sec.section + ' (' + ((CANON[sec.canon] || {}).label || sec.canon) + ', l5r.fandom.com) ' + page.url;
    State.commit('setGmNotes', [(cur ? cur.replace(/\s+$/, '') + '\n\n' : '') + quote + '\n' + cite + '\n']);
  }

  function status(box) {
    if (!configured()) {
      box.appendChild(el('div', { class: 'paper' }, [
        el('div', { class: 'guidance-k' }, ['The lore server is not set up']),
        el('p', { class: 'muted small' }, ['This pane searches the L5R wiki index on the GM’s own machine. Start it, then put its address in Settings:']),
        el('pre', { class: 'lore-cmd' }, ['cd ~/Sortilege/Experiments/l5r-lore\n.venv/bin/python -m lore serve']),
        el('p', { class: 'muted small' }, ['Its address is ' + DEFAULT_URL + ' unless started with --port.']),
      ]));
      return false;
    }
    if (view.health === null) {
      view.health = 'checking';
      api('/health').then((h) => { view.health = h; }).catch((e) => { view.health = { down: e.message }; }).finally(redraw);
    }
    const h = view.health;
    if (h && h.down) {
      box.appendChild(el('div', { class: 'correction' }, ['The lore server at ' + base() + ' did not answer (' + h.down + '). Is `python -m lore serve` running?  ', button('Try again', () => { view.health = null; redraw(); }, 'ghost tiny')]));
      return false;
    }
    if (h && h.ok && !h.ollama) box.appendChild(el('p', { class: 'muted small' }, ['Ollama is not running, so search is keyword-only.']));
    return true;
  }

  function resultList(group) {
    const d = group.data || {};
    return el('div', { class: 'lore-col' }, [
      el('div', { class: 'lore-col-h' }, [badge(group.key), ' ', el('span', { class: 'muted small' }, [group.title])]),
      (d.notes || []).length ? el('p', { class: 'muted small' }, [d.notes.join('; ')]) : null,
      (d.results || []).length ? el('ol', { class: 'lore-results' }, d.results.map((r) => el('li', {}, [
        el('button', { class: 'ref lore-title', type: 'button', onclick: () => openPage(r.title) }, [r.title]),
        el('span', { class: 'muted small' }, [' › ' + r.section + ' ']), badge(r.canon, r.canon_basis), el('span', { class: 'lore-layer' }, [r.layer]),
        el('div', { class: 'lore-snip' }, [shorten(r.text, 260)]),
      ]))) : el('p', { class: 'muted small' }, ['Nothing in this continuity. (About 5,800 wiki articles were never scraped, so absence here is not absence on the wiki.)']),
    ]);
  }

  function pageView(p) {
    const box = el('div', { class: 'lore-page' });
    box.appendChild(el('div', { class: 'chiprow tight' }, [
      button('‹ ' + (view.back.length ? view.back[view.back.length - 1] : 'Results'), () => { const b = view.back.pop(); if (b) openPage(b); else { view.page = null; redraw(); } }, 'ghost tiny'),
      el('a', { class: 'btn ghost tiny', href: p.url, target: '_blank', rel: 'noopener' }, ['On the wiki ↗']),
    ]));
    box.appendChild(el('h3', {}, [p.title, ' ', ...(p.canon || []).map((c) => badge(c, p.canon_basis))]));
    if (p.counterpart) box.appendChild(el('div', { class: 'lore-counter' }, ['The other continuity’s version: ',
      el('button', { class: 'ref', type: 'button', onclick: () => openPage(p.counterpart.title, true) }, [p.counterpart.title]), ' ', ...(p.counterpart.canon || []).map((c) => badge(c))]));
    if ((p.aliases || []).length) box.appendChild(el('div', { class: 'muted small' }, ['Also: ' + p.aliases.slice(0, 12).join(', ')]));
    const info = p.infobox || {};
    const keys = Object.keys(info).filter((k) => info[k] && typeof info[k] !== 'object').slice(0, 14);
    if (keys.length) box.appendChild(el('dl', { class: 'lore-info' }, [].concat(...keys.map((k) => [el('dt', {}, [k]), el('dd', {}, [String(info[k])])]))));
    (p.sections || []).forEach((s, i) => {
      const paras = String(s.text || '').split(/\n{2,}/).map((t) => t.trim()).filter(Boolean);
      box.appendChild(el('details', { class: 'lore-sec', open: i < 2 || null }, [
        el('summary', {}, [s.section, ' ', badge(s.canon, s.canon_basis)]),
        ...paras.map((t) => el('p', {}, [t.replace(/^#+\s*/, '')])),
        el('div', { class: 'chiprow tight' }, [button('Copy to Notes', () => { toNotes(p, s); flash(box, 'Copied to Notes with its citation.'); }, 'ghost tiny')]),
      ]));
    });
    const rel = p.related;
    if (rel) {
      const list = (label, items) => (items && items.length ? el('div', { class: 'lore-rel' }, [el('div', { class: 'guidance-k' }, [label]), el('div', { class: 'chiprow tight' }, items.slice(0, 30).map((x) => el('button', { class: 'ref', type: 'button', title: (x.canon || []).map((c) => (CANON[c] || {}).label || c).join(', '), onclick: () => openPage(x.title, true) }, [x.title])))]) : null);
      box.appendChild(list('Links to', rel.links_to));
      box.appendChild(list('Linked from', rel.linked_from));
    }
    box.appendChild(el('p', { class: 'muted small' }, ['Text from the Legend of the Five Rings wiki (l5r.fandom.com), CC BY-SA. Inspiration, not canon; rules are in Rules & Book.']));
    return box;
  }
  function flash(box, text) { const n = el('div', { class: 'lore-flash' }, [text]); box.prepend(n); setTimeout(() => n.remove(), 2500); }

  function renderPane(container, ctx) {
    redraw = () => {
      container.innerHTML = '';
      container.appendChild(el('h4', {}, ['Lore', el('span', { class: 'muted small' }, [' · the L5R wiki, for inspiration'])]));
      if (!status(container)) return;
      const q = el('input', { type: 'search', class: 'text wide', placeholder: 'A name, a place, an idea — “Toritaka”, “haunted shrine”, “Kisada”', value: view.q, oninput: (ev) => (view.q = ev.target.value), onkeydown: (ev) => { if (ev.key === 'Enter') search(); } });
      const canon = el('select', { class: 'scope', onchange: (ev) => { view.canon = ev.target.value; if (view.results) search(); } }, [['both', 'Both continuities, side by side'], ['ffg', 'Fantasy Flight only'], ['aeg-legacy', 'AEG legacy only']].map(([v, t]) => el('option', { value: v, selected: v === view.canon || null }, [t])));
      const layer = el('select', { class: 'scope', onchange: (ev) => { view.layer = ev.target.value; if (view.results) search(); } }, LAYERS.map(([v, t]) => el('option', { value: v, selected: v === view.layer || null }, [t])));
      container.appendChild(el('div', { class: 'lore-bar' }, [q, canon, layer, button('Search', search, 'tiny')]));
      if (view.busy) container.appendChild(el('div', { class: 'muted loading' }, ['Searching…']));
      if (view.error) container.appendChild(el('div', { class: 'correction' }, [String(view.error.message || view.error)]));
      if (view.page) container.appendChild(pageView(view.page));
      else if (view.results) container.appendChild(el('div', { class: 'lore-cols' + (view.results.length > 1 ? ' two' : '') }, view.results.map(resultList)));
      if (document.activeElement === document.body) q.focus();
    };
    redraw();
    ctx.on('lore:find', redraw);
  }

  // "Find in lore" from anywhere (the Inspector): open the pane on a search for a name
  function find(name) {
    view.q = name; view.page = null; view.back = [];
    if (window.VttApp) window.VttApp.open('lore');
    search();
  }

  function renderSettings(box, redrawSettings) {
    const s = settings();
    box.appendChild(el('div', { class: 'guidance-k' }, ['The Lore pane’s server']));
    box.appendChild(el('p', { class: 'muted small' }, ['The address of the l5r-lore index (`python -m lore serve` in ~/Sortilege/Experiments/l5r-lore): ' + DEFAULT_URL + ' on that machine, or its published https address from anywhere else. Blank turns the pane off. The index stays on that machine: this browser asks the server directly.']));
    box.appendChild(el('div', { class: 'set-row' }, [
      el('input', { type: 'text', class: 'text wide', placeholder: DEFAULT_URL, value: s.url || '', onchange: (ev) => { save({ url: ev.target.value.trim() }); view.health = null; redrawSettings(); } }),
      !s.url ? button('Use ' + DEFAULT_URL, () => { save({ url: DEFAULT_URL }); view.health = null; redrawSettings(); }, 'ghost tiny') : null,
    ]));
    box.appendChild(el('div', { class: 'set-row' }, [
      el('input', { type: 'password', class: 'text wide', autocomplete: 'off', placeholder: 'Token (only if the server asks for one)', value: s.token || '', onchange: (ev) => { save({ token: ev.target.value.trim() }); view.health = null; redrawSettings(); } }),
    ]));
    if (s.url) {
      const st = el('span', { class: 'cond' }, ['checking…']);
      box.appendChild(el('div', { class: 'set-row' }, [st]));
      api('/health').then((h) => { st.textContent = 'Answering · ' + h.pages + ' pages' + (h.ollama ? '' : ' · keyword-only (no Ollama)'); st.classList.add('ok'); })
        .catch((e) => { st.textContent = 'Not answering (' + e.message + ')'; });
    }
  }

  if (window.VttPanels) window.VttPanels.register('lore', { label: 'Lore', render: renderPane });
  if (window.L5RSettings) window.L5RSettings.section({ id: 'lore', render: renderSettings });
  return { configured, find, settings };
})();
