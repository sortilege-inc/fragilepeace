// system/l5r5e/gm-panes.js — the GM's own panes: the campaign's overview, its Scenes (the arc), its
// Threads, Encounters and Places, and the Notes document an instance may still name. Everything
// here is the GM's own pack state (system/l5r5e/ops.js: gm, gmNotes, arc, threads, encounters) —
// saved with the pack, never shared, never sent to a session's room. The text is the GM's small
// Markdown with its prep tags (system/l5r5e/gm-text.js). The one rules text shown, the book's
// Group Rank / Encounter Rank and its Gauging an Encounter comparison, is the corpus's own (the
// GUIDANCE entry building-encounters, core p. 310).
(function () {
  const { el, button, debounce } = window.VttRender;
  const D = window.L5RData;
  const E = window.L5REntity;
  const G = window.L5RGmText;
  const Sheet = window.L5RSheet;
  const State = window.VttState;
  const Panels = window.VttPanels;
  const Bus = window.VttBus;
  const Sys = () => window.VttSystem;
  const S = () => State.state;
  const CFG = window.VttConfig || {};
  const OWN = CFG.ownAdventure || null;
  const editing = (c) => document.activeElement && /TEXTAREA|INPUT|SELECT/.test(document.activeElement.tagName) && c.contains(document.activeElement);
  const newId = (p) => State.genId(p);
  const redrawOn = (ctx, container, draw) => {
    ctx.on('state:changed', () => { if (!editing(container)) draw(); });
    ctx.on('state:remote', () => { if (!editing(container)) draw(); });
    ctx.on('gm:reveal', draw);
  };

  // ── Notes: an authored document (the instance names it: VttConfig.notes = { src, title, class, gate })
  // rendered, and the GM's free notes below it. A gate (the document's spoiler warning) stands in
  // front of it until the GM passes it, once per page load. A .html document is the instance's own
  // fragment and goes in as it is, under its class; anything else is Markdown ─────────────────────
  let docCache = null;
  let gatePassed = false;
  function renderNotes(container, ctx) {
    const draw = () => {
      container.innerHTML = '';
      const n = CFG.notes || null;
      if (n && n.src && n.gate && !gatePassed) {
        container.appendChild(el('h4', {}, [n.title || 'Notes']));
        container.appendChild(el('div', { class: 'paper notes-gate' }, [
          n.gate.title ? el('div', { class: 'notes-gate-title' }, [n.gate.title]) : null,
          n.gate.text ? el('p', {}, [n.gate.text]) : null,
          button(n.gate.enter || 'Show', () => { gatePassed = true; draw(); }, 'tiny'),
        ]));
      } else if (n && n.src) {
        const box = el('div', { class: 'paper notes-doc' + (n.class ? ' ' + n.class : '') }, [el('div', { class: 'muted loading' }, ['Reading ' + (n.title || n.src) + '…'])]);
        container.appendChild(el('h4', {}, [n.title || 'Notes']));
        container.appendChild(box);
        const show = (text) => { box.innerHTML = ''; if (/\.html?$/.test(n.src)) box.innerHTML = text; else box.appendChild(E.markdown(text, 'core')); };
        if (docCache != null) show(docCache);
        else fetch(n.src).then((r) => (r.ok ? r.text() : Promise.reject(new Error(r.status)))).then((t) => { docCache = t; show(t); })
          .catch((e) => { box.innerHTML = ''; box.appendChild(el('div', { class: 'empty' }, ['Could not read ' + n.src + ' (' + e.message + ').'])); });
      }
      container.appendChild(el('h4', {}, ['Free notes', el('span', { class: 'muted small' }, [' · saved with the pack, never sent to players'])]));
      container.appendChild(el('textarea', { class: 'text notes-free', rows: 10, placeholder: 'Jot as you play…', oninput: debounce((ev) => State.commit('setGmNotes', [ev.target.value]), 400) }, [S().gmNotes || '']));
    };
    ctx.on('state:remote', () => { if (!editing(container)) draw(); });
    draw();
  }

  // ── Overview: the campaign itself — its premise and standing facts, a search across every GM
  // pane, and the GM's free notes ─────────────────────────────────────
  let searchQ = '';
  function renderOverview(container, ctx) {
    const draw = () => {
      container.innerHTML = '';
      const q = el('input', { type: 'search', class: 'search', placeholder: 'Search the GM’s material — scenes, threads, places, people…', value: searchQ });
      const hits = el('div', { class: 'gm-hits' });
      const drawHits = () => {
        hits.innerHTML = '';
        const r = G.search(searchQ);
        if (searchQ.trim().length >= 2) hits.appendChild(el('div', { class: 'muted small' }, [r.length + ' found']));
        r.slice(0, 40).forEach((x) => hits.appendChild(el('div', { class: 'gm-hit' }, [
          el('button', { class: 'ref', type: 'button', onclick: () => G.goTo(x) }, [x.title]),
          el('span', { class: 'muted small' }, [' · ' + ((Panels.PANELS[x.pane] || {}).label || x.pane)]),
          el('div', { class: 'small' }, [x.snip]),
        ])));
      };
      q.addEventListener('input', debounce(() => { searchQ = q.value; drawHits(); }, 150));
      container.appendChild(q);
      container.appendChild(hits);
      drawHits();
      const items = G.list('overview');
      if (!items.length) container.appendChild(el('div', { class: 'empty' }, ['The campaign’s premise and standing facts go here — add a section below.']));
      G.sections(container, items, { redraw: draw, save: (l) => G.setList('overview', l), addLabel: 'Add a section…' });
      container.appendChild(el('h4', { 'data-gm-id': 'free-notes' }, ['Free notes', el('span', { class: 'muted small' }, [' · saved with the pack, never sent to players'])]));
      container.appendChild(el('textarea', { class: 'text notes-free', rows: 8, placeholder: 'Jot as you play…', oninput: debounce((ev) => State.commit('setGmNotes', [ev.target.value]), 400) }, [S().gmNotes || '']));
      G.reveal(container);
    };
    redrawOn(ctx, container, draw);
    draw();
  }

  // ── Scenes: the campaign's arc ─────────────────────────────────────
  // arc = [{ id, title, session, summary, text, sections: [beat], played }]. Sessions are its groups;
  // a session whose scenes are all played folds to one line. Where the campaign is its own adventure
  // one scene is running (the engine's `current`), and the table, the Cast pane and the player's
  // conflict follow it; a scene's cast is the shared `cast` (system op setSceneCast).
  const arc = () => JSON.parse(JSON.stringify(S().arc || []));
  const setArc = (list) => State.commit('setArc', [list]);
  const sessionOpen = {};
  function run(id) {
    State.commit('setCurrentScene', [Sys().moduleId(), id]);
    Bus.emit('scene:changed', { moduleId: Sys().moduleId(), sceneId: id });
  }
  function castRow(x, redraw) {
    const here = Sys().cast(x.id);
    const put = (ids) => State.commit('setSceneCast', [x.id, ids]);
    let q = '';
    const hits = el('div', { class: 'gm-cast-hits' });
    const find = el('input', { type: 'search', class: 'text', placeholder: '+ someone', 'aria-label': 'Put an NPC in ' + (x.title || 'this scene') });
    const mine = D.books().filter((b) => b.kind === 'campaign').map((b) => b.id);
    find.addEventListener('input', debounce(() => {
      q = find.value.trim().toLowerCase();
      hits.innerHTML = '';
      if (q.length < 2) return;
      D.npcs().filter((r) => r.name.toLowerCase().indexOf(q) !== -1).sort((a, b) => (mine.indexOf(b.book) !== -1) - (mine.indexOf(a.book) !== -1)).slice(0, 8)
        .forEach((r) => hits.appendChild(button('+ ' + r.name + (mine.indexOf(r.book) !== -1 ? '' : ' · ' + D.label(r.book)), () => { put(Sys().castIds(x.id).filter((id) => id !== r.id).concat([r.id])); redraw(); }, 'ghost tiny')));
    }, 150));
    return el('div', { class: 'gm-cast' }, [
      el('div', { class: 'chiprow tight' }, [el('span', { class: 'prop-k' }, ['In it'])].concat(here.map((e) => el('span', { class: 'chip' }, [
        el('button', { class: 'ref', type: 'button', onclick: () => window.L5ROpenEntity(e.id) }, [e.name]),
        el('button', { class: 'ref tiny', type: 'button', title: 'take out', onclick: () => put(Sys().castIds(x.id).filter((id) => id !== e.id)) }, ['×']),
      ]))).concat([find])),
      hits,
    ]);
  }
  function renderScenes(container, ctx) {
    const draw = () => {
      container.innerHTML = '';
      const list = arc();
      const cur = OWN ? Sys().currentSceneId() : null;
      const played = list.filter((x) => x.played).length;
      container.appendChild(el('h4', {}, [OWN ? (OWN.title || 'The arc') : 'The arc', el('span', { class: 'muted small' }, [' · ' + list.length + ' scenes, ' + played + ' played'])]));
      if (!list.length) container.appendChild(el('div', { class: 'empty' }, ['No scenes yet — add the first below.']));
      // the sessions, in arc order
      const groups = [];
      list.forEach((x, i) => {
        const g = groups[groups.length - 1];
        if (g && g.name === (x.session || null)) g.items.push([x, i]);
        else groups.push({ name: x.session || null, items: [[x, i]] });
      });
      const opts = {
        redraw: draw, save: setArc, subLabel: 'Beat',
        cls: (x) => 'arc-card' + (x.played ? ' played' : '') + (cur === x.id ? ' running' : ''),
        badges: (x) => el('span', { class: 'arc-badges' }, [cur === x.id ? el('span', { class: 'chip on' }, ['Running']) : null, x.played ? el('span', { class: 'chip' }, ['Played']) : null]),
        before: (x) => (x.summary ? el('p', { class: 'arc-summary' }, [x.summary]) : el('span')),
        after: (x) => castRow(x, draw),
        actions: (x) => el('span', { class: 'chiprow tight' }, [
          OWN && cur !== x.id ? button('Run this scene', () => run(x.id), 'tiny') : null,
          button(x.played ? 'Not played' : 'Mark played', () => { const l = arc(); const at = l.findIndex((y) => y.id === x.id); l[at].played = !x.played; setArc(l); }, 'ghost tiny'),
          button('Open on the table', () => { if (OWN) run(x.id); window.open(CFG.pages.table + '?scene=' + encodeURIComponent(x.id), (CFG.channel || 'vtt') + '-table'); }, 'ghost tiny'),
        ]),
        fields: (d) => el('div', { class: 'chiprow tight' }, [
          el('input', { class: 'text', type: 'text', value: d.session || '', placeholder: 'Session (groups the scenes)', oninput: (ev) => (d.session = ev.target.value.trim() || undefined) }),
          el('input', { class: 'text wide', type: 'text', value: d.summary || '', placeholder: 'One line: what the scene is', oninput: (ev) => (d.summary = ev.target.value.trim() || undefined) }),
        ]),
      };
      groups.forEach((g) => {
        const key = g.name || '';
        const allPlayed = g.items.every(([x]) => x.played);
        const isOpen = sessionOpen[key] != null ? sessionOpen[key] : !allPlayed;
        container.appendChild(el('button', { class: 'arc-session' + (allPlayed ? ' played' : ''), type: 'button', 'aria-expanded': isOpen ? 'true' : 'false', onclick: () => { sessionOpen[key] = !isOpen; draw(); } }, [
          el('span', { class: 'gm-caret', 'aria-hidden': 'true' }, [isOpen ? '▾' : '▸']), ' ', g.name || 'Scenes',
          el('span', { class: 'muted small' }, [' · ' + g.items.length + (g.items.length === 1 ? ' scene' : ' scenes') + (allPlayed ? ', played' : '')]),
        ]));
        if (!isOpen) return;
        g.items.forEach(([x, i]) => {
          if (G.open[x.id] == null) G.open[x.id] = cur === x.id || (!cur && !x.played);
          container.appendChild(G.editingId[x.id] ? G.sectionEditor(x, i, list, opts) : G.sectionView(x, opts));
        });
      });
      // a new scene joins the last session unless named otherwise
      const last = list.length ? list[list.length - 1].session : undefined;
      const t = el('input', { class: 'text', type: 'text', placeholder: 'Add a scene…' });
      container.appendChild(el('div', { class: 'chiprow tight gm-add' }, [t, button('Add', () => {
        if (!t.value.trim()) return;
        const x = { id: newId('arc'), title: t.value.trim(), session: last, text: '', played: false };
        G.editingId[x.id] = true; G.open[x.id] = true;
        setArc(arc().concat([x]));
      }, 'tiny')]));
      // the questions to put to the player, asked or not
      const qs = Object.assign({ note: '', items: [] }, (S().gm || {}).questions || {});
      const setQs = (patch) => State.commit('setGm', ['questions', Object.assign({}, qs, patch)]);
      container.appendChild(el('h4', { 'data-gm-id': 'questions' }, ['Questions for the table', el('span', { class: 'muted small' }, [' · ' + qs.items.filter((x) => !x.asked).length + ' not yet asked'])]));
      container.appendChild(G.note(() => qs.note, (v) => setQs({ note: v }), 'Add a note on the questions', draw));
      container.appendChild(el('ul', { class: 'gm-questions' }, qs.items.map((x, i) => el('li', { class: x.asked ? 'asked' : '', 'data-gm-id': x.id }, [
        el('input', { type: 'checkbox', checked: x.asked || null, title: 'Asked', onchange: (ev) => { const l = qs.items.slice(); l[i] = Object.assign({}, x, { asked: ev.target.checked }); setQs({ items: l }); } }),
        el('span', { class: 'gm-q', html: G.inline(x.text || '') }),
        button('×', () => { if (confirm('Remove this question?')) setQs({ items: qs.items.filter((_, j) => j !== i) }); }, 'ghost tiny'),
      ]))));
      const nq = el('input', { class: 'text', type: 'text', placeholder: 'Add a question…' });
      container.appendChild(el('div', { class: 'chiprow tight gm-add' }, [nq, button('Add', () => { if (nq.value.trim()) setQs({ items: qs.items.concat([{ id: newId('q'), text: nq.value.trim(), asked: false }]) }); }, 'tiny')]));
      G.reveal(container);
    };
    redrawOn(ctx, container, draw);
    ctx.on('scene:changed', draw);
    draw();
  }

  // ── Threads: what is in play, and what is held in reserve ───────────
  // threads = [{ id, title, text, sections, open, notes }] — notes are what happened to it in play
  const threads = () => JSON.parse(JSON.stringify(S().threads || []));
  const setThreads = (l) => State.commit('setThreads', [l]);
  function renderThreads(container, ctx) {
    const draw = () => {
      container.innerHTML = '';
      const ts = threads();
      container.appendChild(el('h4', { 'data-gm-id': 'threads-note' }, ['Threads', el('span', { class: 'muted small' }, [' · ' + ts.filter((x) => x.open !== false).length + ' open, ' + ts.filter((x) => x.open === false).length + ' closed'])]));
      container.appendChild(G.note(() => (S().gm || {}).threadsNote, (v) => State.commit('setGm', ['threadsNote', v]), 'Add a note on the threads', draw));
      const upd = (x, patch) => { const l = threads(); const at = l.findIndex((y) => y.id === x.id); l[at] = Object.assign({}, l[at], patch); setThreads(l); };
      G.sections(container, ts, {
        redraw: draw, save: setThreads, addLabel: 'Open a thread…', fresh: () => ({ open: true }),
        cls: (x) => 'thread' + (x.open === false ? ' closed' : ''),
        badges: (x) => (x.open === false ? el('span', { class: 'chip' }, ['Closed']) : null),
        after: (x) => el('div', { class: 'thread-notes' }, [
          el('div', { class: 'prop-k' }, ['In play']),
          el('textarea', { class: 'text', rows: 2, placeholder: 'What has happened to it at the table…', oninput: debounce((ev) => upd(x, { notes: ev.target.value }), 400) }, [x.notes || '']),
        ]),
        actions: (x) => button(x.open === false ? 'Reopen' : 'Close', () => upd(x, { open: x.open === false }), 'ghost tiny'),
      });
      G.reveal(container);
    };
    redrawOn(ctx, container, draw);
    draw();
  }

  // ── Encounters: build one against the party's rank, save it, put it in a scene ──
  const encounters = () => JSON.parse(JSON.stringify(S().encounters || []));
  const setEncounters = (l) => State.commit('setEncounters', [l]);


  // the book's own words for the ranks and the comparison (GUIDANCE building-encounters)
  function encounterRules() {
    const g = D.guidanceFor('#t53e040a67ec04e3085911').find((x) => x.id === '#u4U0YsCgQY4K0GgMcsyokm' || x.name === 'building-encounters');
    const paras = g ? String(g.text).split(/\n\n/) : [];
    const pick = (re) => paras.find((p) => re.test(p)) || null;
    return {
      group: pick(/^To estimate the Group Rank/), encounter: pick(/^To estimate the Encounter Rank/),
      even: pick(/^If the group rank is roughly equal/), edge: pick(/^If the group rank is 1\.5 to 2 times/), outmatched: pick(/^If the group rank is 0\.5 times/),
    };
  }
  // "take the sum of the group's school ranks"
  const groupRank = () => (S().party || []).reduce((a, m) => a + (Sheet.value(Sheet.complete(m.character || {}), 'School Rank') || 0), 0);
  const npcRank = (r, kind) => {
    const f = (r && r.fields) || {};
    const v = kind === 'intrigue' ? f['Intrigue Conflict Rank'] : f['Combat Conflict Rank'];
    return typeof v === 'number' ? v : null;
  };
  let draft = { name: '', kind: 'combat', npcs: [] };   // the encounter being built: npcs [{ id, count }]
  function renderEncounters(container, ctx) {
    let q = '';
    const draw = () => {
      container.innerHTML = '';
      // the encounter builder
      const rules = encounterRules();
      const recs = D.npcs();
      const byId = (id) => recs.find((r) => r.id === id);
      const gr = groupRank();
      const er = draft.npcs.reduce((a, n) => a + (npcRank(byId(n.id), draft.kind) || 0) * n.count, 0);
      const unranked = draft.npcs.filter((n) => npcRank(byId(n.id), draft.kind) == null).map((n) => (byId(n.id) || {}).name);
      container.appendChild(el('h4', {}, ['Build an encounter']));
      const kind = el('select', { class: 'scope tiny' }, [el('option', { value: 'combat', selected: draft.kind === 'combat' || null }, ['combat — a battle']), el('option', { value: 'intrigue', selected: draft.kind === 'intrigue' || null }, ['intrigue — a social scene'])]);
      kind.addEventListener('change', () => { draft.kind = kind.value; draw(); });
      const name = el('input', { class: 'text', type: 'text', value: draft.name, placeholder: 'name it to save it', oninput: (ev) => { draft.name = ev.target.value; } });
      container.appendChild(el('div', { class: 'chiprow tight' }, [kind, name]));
      draft.npcs.forEach((n, i) => {
        const r = byId(n.id);
        const rk = npcRank(r, draft.kind);
        container.appendChild(el('div', { class: 'chiprow tight enc-row' }, [
          el('button', { class: 'ref', type: 'button', onclick: () => window.L5ROpenEntity(n.id) }, [r ? r.name : n.id]),
          el('span', { class: 'muted small' }, [(rk == null ? 'no ' + draft.kind + ' rank' : draft.kind + ' ' + rk) + ' ×']),
          button('−', () => { n.count = Math.max(0, n.count - 1); if (!n.count) draft.npcs.splice(i, 1); draw(); }, 'ghost tiny'),
          el('b', { class: 'num' }, [String(n.count)]),
          button('+', () => { n.count++; draw(); }, 'ghost tiny'),
        ]));
      });
      const search = el('input', { type: 'search', class: 'search', placeholder: 'Add an NPC from any book…', value: q });
      const hits = el('div');
      const drawHits = () => {
        hits.innerHTML = '';
        if (q.length < 2) return;
        recs.filter((r) => r.name.toLowerCase().indexOf(q) !== -1).slice(0, 12).forEach((r) => hits.appendChild(el('div', { class: 'small' }, [
          button('+ ' + r.name, () => { const f = draft.npcs.find((x) => x.id === r.id); if (f) f.count++; else draft.npcs.push({ id: r.id, count: 1 }); q = ''; draw(); }, 'ghost tiny'),
          el('span', { class: 'muted' }, [' ' + [npcRank(r, 'combat') != null ? 'combat ' + npcRank(r, 'combat') : null, npcRank(r, 'intrigue') != null ? 'intrigue ' + npcRank(r, 'intrigue') : null, D.label(r.book)].filter(Boolean).join(' · ')]),
        ])));
      };
      search.addEventListener('input', debounce(() => { q = search.value.trim().toLowerCase(); drawHits(); }, 150));
      container.appendChild(search);
      container.appendChild(hits);
      drawHits();
      // the comparison, in the book's words
      const ratio = er ? gr / er : null;
      const band = ratio == null ? null : ratio <= 0.5 ? 'outmatched' : ratio >= 1.5 ? 'edge' : 'even';
      container.appendChild(el('div', { class: 'enc-sum' }, [
        el('div', {}, [el('b', {}, ['Group rank ' + gr]), el('span', { class: 'muted small' }, [' (' + (S().party || []).length + ' in the party)']), ' · ', el('b', {}, ['Encounter rank ' + er]), ratio != null ? el('span', { class: 'muted small' }, [' · ' + gr + ' : ' + er + ' = ' + (Math.round(ratio * 100) / 100)]) : null]),
        unranked.length ? el('div', { class: 'muted small' }, ['Not counted — no ' + draft.kind + ' conflict rank printed: ' + unranked.join(', ')]) : null,
        [['even', rules.even], ['edge', rules.edge], ['outmatched', rules.outmatched]].filter((x) => x[1]).map((x) => el('div', { class: 'small enc-band' + (band === x[0] ? ' on' : '') }, [E.span(x[1], 'core')])),
        band === 'edge' && ratio > 2 ? el('div', { class: 'muted small' }, ['The book’s band is 1.5 to 2 times; this is more.']) : null,
        band === 'even' && (ratio < 0.8 || ratio > 1.25) ? el('div', { class: 'muted small' }, ['Between the book’s bands; “roughly equal” is the nearest.']) : null,
      ]));
      const sc = Sys().scene && Sys().scene(Sys().currentSceneId());
      container.appendChild(el('div', { class: 'chiprow tight' }, [
        button('Save encounter', () => { if (!draft.npcs.length) return; const l = encounters(); const nm = draft.name.trim() || ('Encounter ' + (l.length + 1)); l.push({ id: newId('enc'), name: nm, kind: draft.kind, npcs: draft.npcs.map((n) => ({ id: n.id, count: n.count })) }); setEncounters(l); }, 'tiny'),
        sc && draft.npcs.length ? button('Put in ' + sc.name, () => { const cur = Sys().castIds(sc.id); State.commit('setSceneCast', [sc.id, cur.concat(draft.npcs.map((n) => n.id).filter((id) => cur.indexOf(id) === -1))]); }, 'ghost tiny') : null,
        draft.npcs.length ? button('Clear', () => { draft = { name: '', kind: draft.kind, npcs: [] }; draw(); }, 'ghost tiny') : null,
      ]));
      const saved = encounters();
      if (saved.length) container.appendChild(el('ul', { class: 'items' }, saved.map((x, i) => el('li', {}, [
        el('button', { class: 'ref', type: 'button', onclick: () => { draft = { name: x.name, kind: x.kind, npcs: x.npcs.map((n) => Object.assign({}, n)) }; draw(); } }, [x.name]),
        el('span', { class: 'muted small' }, [' · ' + x.kind + ' · ' + x.npcs.reduce((a, n) => a + n.count, 0) + ' NPCs']),
        button('×', () => setEncounters(encounters().filter((_, j) => j !== i)), 'ghost tiny'),
      ]))));
      if (rules.group || rules.encounter) container.appendChild(el('details', { class: 'small' }, [el('summary', { class: 'muted' }, ['The book: group rank and encounter rank']), rules.group ? E.span(rules.group, 'core') : null, el('br'), rules.encounter ? E.span(rules.encounter, 'core') : null]));

    };
    ctx.on('state:changed', () => { if (!editing(container)) draw(); });
    ctx.on('state:remote', () => { if (!editing(container)) draw(); });
    ctx.on('scene:changed', draw);
    draw();
  }

  // ── Places: the campaign's ground ──────────────────────────────────
  function renderPlaces(container, ctx) {
    G.listPane(container, ctx, 'places', { addLabel: 'Add a place…', empty: 'No places yet.' });
  }

  Panels.register('overview', { label: OWN ? (OWN.title || 'Overview') : 'Overview', render: renderOverview });
  Panels.register('scenes', { label: 'Scenes', render: renderScenes });
  Panels.register('threads', { label: 'Threads', render: renderThreads });
  Panels.register('encounters', { label: 'Encounters', render: renderEncounters });
  Panels.register('places', { label: 'Places', render: renderPlaces });
  Panels.register('notes', { label: 'Notes', render: renderNotes });
})();
