// system/l5r5e/creator.js — making a character: the Game of Twenty Questions as a wizard.
//
// The approach is the pregens archive's creator (sortilege-l5r5e-pregens, assets/creator.js),
// which was tested on every character that archive holds: a side nav whose ticks mean the
// question is actually answered, one question at a time in the corpus's own wording with the
// book's walkthrough beside it, and a work-in-progress panel that recomputes the character on
// every pick and says where each number came from ("+1 Hida, +1 Hida Defender"). Every choice
// the corpus prints is asked for — a family's ring, a school's five skills and its technique
// picks, the heritage result's heirloom or technique or ring swap — and nothing is guessed; what
// is still open is named in the panel. Two steps are asked only when they bind: moving a ring
// that came out above the creation cap, and settling the outfit's either-ors.
//
// Three ways in, as the corpus has them: a samurai (the core), a rōnin, peasant or gaijin (Path
// of Waves: region and upbringing for clan and family, a past for giri), and a character from
// the wilds (Writ of the Wilds, which restates six of Path of Waves' questions).
//
// The corpus readers and the arithmetic are system/l5r5e/chargen.js; this is the page. The
// answers are kept on the draft (`_cg`, one per character in this browser's roster), and what
// the draft saves is the character file (system/l5r5e/sheet.js) the table imports.
window.L5RCreator = (function () {
  const { el, button, debounce } = window.VttRender;
  const D = window.L5RData;
  const E = window.L5REntity;
  const Sheet = window.L5RSheet;
  const Dice = window.L5RDice;
  const Roster = window.L5RRoster;
  const G = window.L5RChargen;
  const Site = () => window.VttSite;
  const RINGS = G.RINGS;

  let C = null; // the draft's answers
  let draftId = null;
  let redrawPage = null;

  // ── the draft ──
  function draft() {
    const cur = Roster.current();
    if (cur && cur.character && cur.character._cg) return cur;
    const c = G.blank();
    const id = Roster.add(Object.assign(G.toSheet(c), { _cg: c }));
    return Roster.get(id);
  }
  function persist() {
    const v = G.toSheet(C);
    v._cg = C;
    Roster.save(draftId, v);
  }
  // a pick re-flows the page; typing only refreshes the panel and the nav
  function save() { persist(); if (redrawPage) redrawPage(); }
  const saveText = debounce(() => { persist(); refreshSide(); }, 250);
  let refreshSide = () => {};
  const chosen = (key) => G.chosen(C, key);
  function setChosen(key, list) { C.choices = C.choices || {}; if (list && list.length) C.choices[key] = list; else delete C.choices[key]; }
  function dropChoices(prefix) { Object.keys(C.choices || {}).forEach((k) => { if (k.indexOf(prefix) === 0) delete C.choices[k]; }); }
  const A = () => (C.a = C.a || {});
  const mode = () => C.mode || 'core';
  const isCore = () => mode() === 'core';
  const has = (v) => v != null && String(v).trim() !== '';
  const Q = (n) => G.question(mode(), n);
  const alt = (n) => G.alt(mode(), n);

  // ── widgets ──
  const lab = (t) => el('div', { class: 'cg-label' }, [t]);
  const note = (t, cls) => el('p', { class: 'cg-note ' + (cls || '') }, [t]);
  function choiceRow(pairs, current, onPick) {
    return el('div', { class: 'cg-choices' }, pairs.map(([v, t, title]) => el('button', { type: 'button', class: 'cg-choice' + (v === current ? ' on' : ''), title: title || null, onclick: () => onPick(v) }, [t])));
  }
  function textArea(get, set, placeholder, rows, ai) {
    return withAI(el('textarea', { class: 'cg-text', rows: rows || 3, placeholder: placeholder || '', oninput: (ev) => { set(ev.target.value); saveText(); } }, [get() || '']), set, ai);
  }
  function textLine(get, set, placeholder, ai) {
    return withAI(el('input', { class: 'cg-line', type: 'text', placeholder: placeholder || '', value: get() || '', oninput: (ev) => { set(ev.target.value); saveText(); } }), set, ai);
  }
  // AI suggestions (system/l5r5e/ai.js): only when the GM has switched them on in Settings.
  // Empty field: Suggest (or Tab). With text: rewrite it in the register, or a new one.
  function withAI(input, set, ai) {
    const AI = window.L5RAI;
    if (!ai || !AI || !AI.enabled()) return input;
    const field = typeof ai === 'string' ? ai : ai.field;
    const extra = typeof ai === 'string' ? null : ai.extra;
    const row = el('div', { class: 'cg-ai' });
    const go = (mode) => {
      const source = mode === 'from' ? input.value : '';
      Array.prototype.forEach.call(row.querySelectorAll('button'), (b) => (b.disabled = true));
      status.textContent = '…';
      AI.suggest(C, field, source, input.value, extra ? extra() : null).then((text) => {
        input.value = text;
        set(text);
        persist();
        refreshSide();
        paint();
      }).catch((e) => { paint(); status.textContent = e.message; });
    };
    const status = el('span', { class: 'cg-ai-status', 'aria-live': 'polite' });
    const paint = () => {
      const has = !!(input.value && input.value.trim());
      row.innerHTML = '';
      if (has) { row.appendChild(button('Suggest from text', () => go('from'), 'ghost tiny')); row.appendChild(button('New suggestion', () => go('new'), 'ghost tiny')); }
      else row.appendChild(button('Suggest', () => go('new'), 'ghost tiny'));
      row.appendChild(el('span', { class: 'cg-note' }, [has ? '' : 'or Tab in the empty field']));
      row.appendChild(status);
      status.textContent = '';
    };
    input.addEventListener('input', () => { const has = !!input.value.trim(); if (has !== (row.querySelectorAll('button').length > 1)) paint(); });
    input.addEventListener('keydown', (e) => { if (e.key === 'Tab' && !e.shiftKey && !input.value) { e.preventDefault(); go('new'); } });
    paint();
    return el('div', { class: 'cg-aiwrap' }, [input, row]);
  }
  // hover a pick to read its entry as the corpus prints it
  let tipBox = null;
  function tip(node, entity) {
    if (!entity) return node;
    node.addEventListener('mouseenter', () => {
      if (!tipBox) { tipBox = el('div', { class: 'cg-tip paper' }); document.body.appendChild(tipBox); }
      tipBox.innerHTML = '';
      tipBox.appendChild(E.render(entity));
      const r = node.getBoundingClientRect();
      const w = Math.min(460, window.innerWidth - 24);
      tipBox.style.width = w + 'px';
      tipBox.style.left = Math.max(12, Math.min(window.innerWidth - w - 12, r.right + 12)) + 'px';
      tipBox.style.top = Math.max(12, Math.min(window.innerHeight - 320, r.top)) + 'px';
      tipBox.style.display = 'block';
    });
    node.addEventListener('mouseleave', () => { if (tipBox) tipBox.style.display = 'none'; });
    return node;
  }
  function hideTip() { if (tipBox) tipBox.style.display = 'none'; }
  // A filterable list, the chosen one first. items: {value, label, meta, entity, off}
  function pickList(items, current, onPick) {
    const wrap = el('div', { class: 'cg-pickwrap' });
    const search = el('input', { type: 'search', class: 'cg-line', placeholder: 'Filter…' });
    const list = el('div', { class: 'cg-picklist' });
    function draw() {
      const q = search.value.trim().toLowerCase();
      let shown = items.filter((i) => !q || (i.label + ' ' + (i.meta || '')).toLowerCase().indexOf(q) !== -1);
      const on = shown.filter((i) => i.value === current);
      if (on.length) shown = on.concat(shown.filter((i) => i.value !== current));
      list.innerHTML = '';
      if (!shown.length) list.appendChild(note('Nothing matches.'));
      shown.forEach((i) => list.appendChild(tip(el('button', { type: 'button', class: 'cg-pick' + (i.value === current ? ' on' : '') + (i.off ? ' off' : ''), title: i.off || null, onclick: () => { hideTip(); onPick(i.value); } }, [
        el('span', { class: 'cg-pick-n' }, [i.label]), i.meta ? el('span', { class: 'cg-pick-m' }, [i.meta]) : null,
      ]), i.entity)));
    }
    search.addEventListener('input', draw);
    if (items.length > 8) wrap.appendChild(search);
    wrap.appendChild(list);
    draw();
    return wrap;
  }
  // What a pick would bring a ring or skill to, so the creation cap is visible before it binds.
  function wouldReach(kind, name, by) {
    const d = G.compute(C);
    const now = kind === 'rings' ? d.rings[name] : d.skills[name] || 0;
    if (now == null) return null;
    return { now, then: now + by, over: now + by > (kind === 'rings' ? G.ringCap() : G.skillCap()) };
  }
  // choose n of the options a CHOOSE prints; `kind` rings/skills/techniques
  function chooseGroup(key, heading, spec, kind, entities) {
    const n = spec.n || 1;
    const by = spec.by || 1;
    const picked = chosen(key).filter((o) => spec.of.indexOf(o) !== -1);
    const box = el('div', { class: 'cg-group' + (picked.length >= n ? ' done' : '') });
    box.appendChild(lab(heading + ' — choose ' + n + (by > 1 ? ' (+' + by + ' each)' : '')));
    box.appendChild(el('div', { class: 'cg-choices' }, spec.of.map((o) => {
      const on = picked.indexOf(o) !== -1;
      const w = !on && kind !== 'techniques' ? wouldReach(kind, o, by) : null;
      const b = el('button', { type: 'button', class: 'cg-choice' + (on ? ' on' : '') + (w && w.over ? ' over' : ''),
        title: w && w.over ? o + ' is at ' + w.now + '; this would make it ' + w.then + ', above the creation limit' : null,
        onclick: () => {
          hideTip();
          let next = picked.slice();
          if (on) next.splice(next.indexOf(o), 1);
          else { next.push(o); while (next.length > n) next.shift(); }
          setChosen(key, next);
          save();
        } }, [kind === 'rings' ? Dice.ringIcon(o) : null, o]);
      return tip(b, entities ? entities(o) : null);
    }).concat([el('span', { class: 'cg-count' + (picked.length >= n ? ' ok' : '') }, [picked.length + '/' + n])])));
    return box;
  }
  // every CHOOSE a clan/family/school/region/upbringing prints, as groups
  function increaseChoices(inc, prefix, kind, heading) {
    return inc.choose.map((ch, i) => {
      const key = prefix + '.' + i;
      if (ch.clan) {
        const cur = chosen(key)[0] || null;
        const items = G.clans().map((c) => ({ value: c.id, label: c.full, meta: G.label(kind === 'rings' ? c.rings : c.skills), entity: c.e }));
        if (ch.fallback) items.push({ value: 'none', label: 'The family had no clan', meta: 'instead: ' + G.label({ fixed: {}, choose: [ch.fallback] }) });
        const box = el('div', { class: 'cg-group' + (cur && (cur !== 'none' || chosen(key + '.f').length >= ch.fallback.n) ? ' done' : '') }, [lab(heading + ' — the ' + ch.clan + ' of the clan the family belonged to'),
          pickList(items, cur, (v) => { if (v !== cur) setChosen(key + '.f', []); setChosen(key, [v]); save(); })]);
        if (cur === 'none' && ch.fallback) box.appendChild(chooseGroup(key + '.f', heading, ch.fallback, kind, kind === 'skills' ? (o) => D.named(o, 'core') : null));
        return box;
      }
      return chooseGroup(key, heading, ch, kind, kind === 'skills' ? (o) => D.named(o, 'core') : null);
    });
  }
  const choicesDone = (inc, prefix) => inc.choose.every((ch, i) => {
    const k = prefix + '.' + i;
    if (!ch.clan) return chosen(k).filter((o) => ch.of.indexOf(o) !== -1).length >= ch.n;
    if (chosen(k)[0] !== 'none') return chosen(k).length > 0;
    return !!ch.fallback && chosen(k + '.f').filter((o) => ch.fallback.of.indexOf(o) !== -1).length >= ch.fallback.n;
  });
  function ringPicker(current, onPick, only) {
    return el('div', { class: 'cg-rings' }, (only || RINGS).map((r) => {
      const w = current === r ? null : wouldReach('rings', r, 1);
      return el('button', { type: 'button', class: 'cg-ringbtn' + (current === r ? ' on' : '') + (w && w.over ? ' over' : ''), title: w && w.over ? r + ' would pass the creation limit' : null, onclick: () => onPick(r) }, [Dice.ringIcon(r), el('span', {}, [r])]);
    }));
  }
  // a skill, from the core's groups; `atZero` offers only skills the character has no ranks in
  function skillPicker(current, onPick, opts) {
    opts = opts || {};
    const d = G.compute(C);
    const items = [];
    G.skillGroups().forEach((g) => g.skills.forEach((s) => {
      if (opts.only && opts.only.indexOf(s.name) === -1) return;
      const rank = (d.skills[s.name] || 0) - (s.name === current ? 1 : 0);
      if (opts.atZero && rank > 0) return;
      items.push({ value: s.name, label: s.name, meta: g.name + (rank ? ' · rank ' + rank : ''), entity: D.entity(s.id) });
    }));
    return pickList(items, current, onPick);
  }
  // an advantage or disadvantage of the given kinds
  function pecPicker(kinds, current, onPick) {
    const held = G.peculiarityList(C, G.compute(C)).map((p) => p.id);
    const items = [];
    kinds.forEach((k) => G.peculiarities(k).forEach((e) => items.push({
      value: e.id, label: e.name, entity: e, off: e.id !== current && held.indexOf(e.id) !== -1 ? 'already held' : null,
      meta: [kinds.length > 1 ? e.type : null, [].concat(D.val(e, 'Types') || []).join(', ') || null, D.label(e.book)].filter(Boolean).join(' · '),
    })));
    const box = el('div', {}, [pickList(items, current, onPick)]);
    const e = current && D.entity(current);
    if (e && /\[[^\]]+\]/.test(e.name)) {
      box.appendChild(lab('Who or what: ' + e.name));
      box.appendChild(textLine(() => (C.subjects || {})[e.id], (v) => { (C.subjects = C.subjects || {})[e.id] = v; }, (e.name.match(/\[([^\]]+)\]/) || [])[1]));
    }
    return box;
  }
  function itemPicker(maxRarity, type, current, onPick) {
    const items = G.items().filter((i) => i.rarity <= maxRarity && (!type || i.kind === type)).map((i) => ({ value: i.name, label: i.name, entity: i.e, meta: [i.kind, 'rarity ' + i.rarity, i.group, D.label(i.book)].filter(Boolean).join(' · ') }));
    return pickList(items, current, onPick);
  }
  // the corpus's roll tables: roll the printed die, or pick
  function rollTable(t, current, onPick) {
    const box = el('div', {});
    box.appendChild(el('div', { class: 'cg-choices' }, [button('Roll ' + t.die, () => { const r = G.rollOn(t.rows, t.die, (x) => x.range); if (r.row) onPick(r.row); }, 'ghost tiny'), el('span', { class: 'cg-note' }, [t.source])]));
    box.appendChild(pickList(t.rows.map((r) => ({ value: r.range, label: r.name, meta: r.range + (r.text ? ' · ' + r.text : '') })), current, (v) => onPick(t.rows.find((r) => r.range === v))));
    return box;
  }

  // ── the questions ──
  const optionRing = (text) => (RINGS.find((r) => new RegExp('\\+1\\s+' + r + '\\b', 'i').test(text || '')) || null);
  function clanStep(body) {
    if (!isCore()) {
      const set = G.originSet(mode(), 1, G.regions());
      body.appendChild(pickList(set.map((r) => ({ value: r.id, label: r.name, entity: r.e, meta: [G.label(r.rings), G.label(r.skills), r.glory != null ? 'Glory ' + r.glory : null].filter(Boolean).join(' · ') })), C.region, (v) => { if (v !== C.region) dropChoices('region.'); C.region = v; save(); }));
      const r = G.regions().find((x) => x.id === C.region);
      if (r) increaseChoices(r.rings, 'region.r', 'rings', 'Ring').concat(increaseChoices(r.skills, 'region.s', 'skills', 'Skill')).forEach((n) => body.appendChild(n));
      return;
    }
    body.appendChild(pickList(G.clans().map((c) => ({ value: c.id, label: c.full, entity: c.e, meta: [G.label(c.rings), G.label(c.skills), c.status != null ? 'Status ' + c.status : null, c.book !== 'core' ? D.label(c.book) : null].filter(Boolean).join(' · ') })), C.clan, (v) => {
      if (v !== C.clan) {
        const was = G.clans().find((x) => x.id === C.clan);
        const view = was && G.clanViews()[was.name];
        C.family = null; C.school = null; C.role = null;
        dropChoices('clan.'); dropChoices('family.'); dropChoices('school.');
        // an untouched default belongs to the old clan; a deliberate answer stays
        if (view && C.bushido.paramount === (view.paramount || [])[0]) C.bushido.paramount = null;
        if (view && C.bushido.lesser === (view.lesser || [])[0]) C.bushido.lesser = null;
      }
      C.clan = v; save();
    }));
    const c = G.clans().find((x) => x.id === C.clan);
    if (c) increaseChoices(c.rings, 'clan.r', 'rings', 'Ring').concat(increaseChoices(c.skills, 'clan.s', 'skills', 'Skill')).forEach((n) => body.appendChild(n));
  }
  function familyStep(body) {
    if (!isCore()) {
      const types = G.originTypes();
      if (types.length) {
        body.appendChild(lab('What kind of character is this'));
        body.appendChild(choiceRow(types.map((t) => [t.key, t.label + ' · status ' + t.status, t.text]), C.origin || types[0].key, (v) => { C.origin = v; save(); }));
        body.appendChild(note('Status begins there, and the upbringing below modifies it — never below 0.'));
      }
      body.appendChild(lab('Upbringing'));
      const set = G.originSet(mode(), 2, G.upbringings());
      body.appendChild(pickList(set.map((u) => ({ value: u.id, label: u.name, entity: u.e, meta: [G.label(u.rings), G.label(u.skills), u.status != null ? 'Status ' + (u.status > 0 ? '+' : '') + u.status : null, G.coinLabel(u.coins) !== '—' ? G.coinLabel(u.coins) : null].concat(u.items).filter(Boolean).join(' · ') })), C.upbringing, (v) => { if (v !== C.upbringing) dropChoices('upb.'); C.upbringing = v; save(); }));
      const u = G.upbringings().find((x) => x.id === C.upbringing);
      if (u) increaseChoices(u.rings, 'upb.r', 'rings', 'Ring').concat(increaseChoices(u.skills, 'upb.s', 'skills', 'Skill')).forEach((n) => body.appendChild(n));
      return;
    }
    const clan = G.clans().find((x) => x.id === C.clan);
    const mine = G.familiesOf(clan);
    const showAll = !!C.familyAll || !mine.length;
    if (!clan) body.appendChild(note('No clan is chosen, so every family is offered.'));
    else body.appendChild(choiceRow([['mine', 'The ' + clan.name + ' families'], ['all', 'Every family']], showAll ? 'all' : 'mine', (v) => { C.familyAll = v === 'all'; save(); }));
    const pool = showAll ? G.families() : mine;
    body.appendChild(pickList(pool.map((f) => ({ value: f.id, label: f.name, entity: f.e, meta: [showAll ? f.clan : null, G.label(f.rings), G.label(f.skills), f.glory != null ? 'Glory ' + f.glory : null, G.coinLabel(f.coins) !== '—' ? G.coinLabel(f.coins) : null].concat(f.items).filter(Boolean).join(' · ') })), C.family, (v) => { if (v !== C.family) dropChoices('family.'); C.family = v; save(); }));
    const f = G.families().find((x) => x.id === C.family);
    if (f) increaseChoices(f.rings, 'family.r', 'rings', 'Ring').concat(increaseChoices(f.skills, 'family.s', 'skills', 'Skill')).forEach((n) => body.appendChild(n));
  }
  function schoolStep(body) {
    const clan = isCore() ? G.clans().find((x) => x.id === C.clan) : null;
    const mine = clan ? G.schools().filter((s) => s.clan === clan.name) : isCore() ? [] : G.schools().filter((s) => /r[oō]nin|path-of-waves|writ-of-wilds/i.test(s.clan + ' ' + s.book));
    const showAll = !!C.schoolAll || !mine.length;
    body.appendChild(choiceRow([['mine', clan ? 'The ' + clan.name + ' schools' : 'Schools this book offers'], ['all', 'Every school']], showAll ? 'all' : 'mine', (v) => { C.schoolAll = v === 'all'; save(); }));
    if (showAll && clan) body.appendChild(note('Another clan’s school needs the GM’s approval (q3_other_clan_school_requires_gm_approval).'));
    const pool = showAll ? G.schools() : mine;
    body.appendChild(pickList(pool.map((s) => ({ value: s.id, label: s.name, entity: s.e, meta: [showAll ? s.clan || 'no clan' : null, s.roles.join(', '), G.label(s.rings), s.honor != null ? 'Honor ' + s.honor : null, s.book !== 'core' ? D.label(s.book) : null].filter(Boolean).join(' · ') })), C.school, (v) => {
      if (v !== C.school) dropChoices('school.');
      C.school = v;
      const s = G.schools().find((x) => x.id === v);
      // two roles is a question; one is not
      C.role = s && s.roles.length === 1 ? s.roles[0] : null;
      save();
    }));
    const s = G.schools().find((x) => x.id === C.school);
    if (!s) return;
    if (s.roles.length > 1) { body.appendChild(lab('Role — the school falls into ' + s.roles.join(' and '))); body.appendChild(choiceRow(s.roles.map((r) => [r, r]), C.role, (v) => { C.role = v; save(); })); }
    increaseChoices(s.rings, 'school.r', 'rings', 'Ring increase').concat(increaseChoices(s.skills, 'school.s', 'skills', 'Starting skills')).forEach((n) => body.appendChild(n));
    s.techniques.forEach((t, i) => {
      if (t.fixed) return;
      body.appendChild(chooseGroup('school.t.' + i, 'Starting technique (' + t.kind.toLowerCase() + ')', { n: t.n, of: t.of, by: 1 }, 'techniques', (o) => { const r = G.techniqueNamed(o); return r ? D.entity(r.id) : null; }));
    });
    const fixed = s.techniques.filter((t) => t.fixed);
    if (fixed.length) body.appendChild(el('div', {}, [lab('Starting techniques the school gives'), el('div', { class: 'cg-chips' }, fixed.map((t) => { const r = G.techniqueNamed(t.fixed); return tip(el('span', { class: 'cg-chip tech' }, [t.fixed]), r ? D.entity(r.id) : null); }))]));
  }
  function schoolDone() {
    const s = G.schools().find((x) => x.id === C.school);
    if (!s || !has(C.role)) return false;
    return choicesDone(s.rings, 'school.r') && choicesDone(s.skills, 'school.s') && s.techniques.every((t, i) => t.fixed || chosen('school.t.' + i).filter((o) => t.of.indexOf(o) !== -1).length >= t.n);
  }
  function standoutStep(body) {
    const q = alt(4);
    if (q && q.options.length) {
      body.appendChild(pickList(q.options.map((o) => ({ value: o.label, label: o.label, meta: o.text })), A().q4, (v) => { A().q4 = v; C.standout = optionRing((q.options.find((o) => o.label === v) || {}).text); save(); }));
    } else body.appendChild(ringPicker(C.standout, (r) => { C.standout = r; save(); }));
    body.appendChild(lab(q ? 'What gets them into trouble, and out of it' : 'What sets them apart'));
    body.appendChild(textArea(() => A().standout, (v) => (A().standout = v), 'In a sentence or two', 3, 'standout'));
  }
  function giriStep(body) {
    if (isCore()) { body.appendChild(textArea(() => A().giri, (v) => (A().giri = v), 'Whom do you serve, and what does that duty ask of you?', 4, 'giri')); return; }
    const t = G.rolled(mode(), 5);
    if (t) { body.appendChild(lab('A past from the table — or write your own')); body.appendChild(rollTable(t, A().pastRange, (r) => { A().pastRange = r.range; A().pastName = r.name; if (!has(A().past)) A().past = r.name + ': ' + r.text; save(); })); }
    body.appendChild(lab('The past, in your words'));
    body.appendChild(textArea(() => A().past, (v) => (A().past = v), 'What drives them, and what does it cost?', 4, 'past'));
  }
  function ninjoStep(body) {
    const t = G.rolled(mode(), 6);
    if (t) { body.appendChild(lab('A ninjō from the table — or write your own')); body.appendChild(rollTable(t, A().ninjoRange, (r) => { A().ninjoRange = r.range; if (!has(A().ninjo)) A().ninjo = r.name + ': ' + r.text; save(); })); }
    body.appendChild(textArea(() => A().ninjo, (v) => (A().ninjo = v), 'What do they long for?', 4, 'ninjo'));
  }
  function q7Step(body) {
    const q = alt(7);
    const glory = isCore() ? G.amount(G.summaryRow(7), 'glory') : G.amount(((q && q.options[0]) || {}).text, 'glory');
    const pairs = q && q.options.length
      ? [['glory', q.options[0].label + ' — ' + q.options[0].text], ['skill', q.options[1].label + ' — ' + q.options[1].text]]
      : [['glory', 'Embrace the clan’s ideals — +' + glory + ' glory'], ['skill', 'Diverge from them — +1 rank in a skill at rank 0']];
    body.appendChild(choiceRow(pairs, A().q7, (v) => { A().q7 = v; if (v !== 'skill') A().q7skill = null; save(); }));
    if (A().q7 === 'skill') { body.appendChild(lab('The skill (one at 0 ranks)')); body.appendChild(skillPicker(A().q7skill, (s) => { A().q7skill = s; save(); }, { atZero: true })); }
    body.appendChild(lab(q ? 'What are they known for, and to whom?' : 'How do they carry, or resist, the clan’s ideals?'));
    body.appendChild(textArea(() => A().q7text, (v) => (A().q7text = v), '', 3, 'q7text'));
  }
  function bushidoStep(body) {
    const clan = isCore() ? G.clans().find((x) => x.id === C.clan) : null;
    const view = clan ? G.clanViews()[clan.name] : null;
    const ts = G.tenets();
    // the clan's views are a starting point, filled in once; the answer is still the player's
    if (view && !C.bushido.touched && ((!C.bushido.paramount && view.paramount) || (!C.bushido.lesser && view.lesser))) {
      if (!C.bushido.paramount && view.paramount) C.bushido.paramount = view.paramount[0];
      if (!C.bushido.lesser && view.lesser) C.bushido.lesser = view.lesser[0];
      persist();
    }
    if (view) body.appendChild(note('The ' + clan.name + ' hold ' + (view.paramount || []).join(' and ') + ' paramount and ' + (view.lesser || []).join(' and ') + ' less significant (Clan Views of Bushidō). Filled in below; change either if this character sees it differently.'));
    const mark = (t, k) => (view && (view[k] || []).indexOf(t.name) !== -1 ? ' ✦' : '');
    body.appendChild(lab('Paramount tenet'));
    body.appendChild(choiceRow(ts.map((t) => [t.name, t.short + mark(t, 'paramount'), t.text]), C.bushido.paramount, (v) => { C.bushido.paramount = v; C.bushido.touched = true; save(); }));
    body.appendChild(lab('Less significant tenet'));
    body.appendChild(choiceRow(ts.map((t) => [t.name, t.short + mark(t, 'lesser'), t.text]), C.bushido.lesser, (v) => { C.bushido.lesser = v; C.bushido.touched = true; save(); }));
    const q = alt(8);
    body.appendChild(lab('What they make of it'));
    let pairs;
    let list;
    if (q && q.options.length) {
      pairs = q.options.map((o) => [/honor/i.test(o.text) ? 'honor' : /item/i.test(o.text) ? 'item' : 'skill', o.label + ' — ' + o.text]);
      list = G.listedSkills((q.options.find((o) => /skill/i.test(o.text) && !/honor|item/i.test(o.text)) || {}).text);
    } else {
      const wt = (G.walkthrough(8) || {}).text;
      list = G.listedSkills(wt);
      pairs = [['honor', 'Devoted to Bushidō — +' + (G.amount(wt, 'honor') || 0) + ' honor'], ['skill', 'Nuanced — +1 rank in ' + (list ? 'one of ' + list.join(', ') : 'a skill')]];
    }
    body.appendChild(choiceRow(pairs, C.bushido.attitude, (v) => { C.bushido.attitude = v; if (v !== 'skill') C.bushido.skill = null; if (v !== 'item') C.bushido.item = null; save(); }));
    if (C.bushido.attitude === 'skill') body.appendChild(skillPicker(C.bushido.skill, (s) => { C.bushido.skill = s; save(); }, { only: list || null }));
    if (C.bushido.attitude === 'item') { body.appendChild(lab('The item (rarity 5 or lower)')); body.appendChild(itemPicker(5, null, C.bushido.item, (v) => { C.bushido.item = v; save(); })); }
  }
  const bushidoDone = () => has(C.bushido.paramount) && has(C.bushido.lesser) && has(C.bushido.attitude) && (C.bushido.attitude !== 'skill' || has(C.bushido.skill)) && (C.bushido.attitude !== 'item' || has(C.bushido.item));
  function pecStep(kind, textKey, prompt, after) {
    return (body) => {
      body.appendChild(textArea(() => A()[textKey], (v) => (A()[textKey] = v), prompt, 3, textKey));
      body.appendChild(lab(after));
      body.appendChild(pecPicker([kind], C.pec[kind], (v) => { C.pec[kind] = v; save(); }));
    };
  }
  function mentorStep(body) {
    body.appendChild(lab('The mentor'));
    body.appendChild(textLine(() => A().mentor, (v) => (A().mentor = v), 'Their name'));
    const q = alt(13);
    const pairs = q && q.options.length ? [['adv', q.options[0].label + ' — ' + q.options[0].text], ['dis', q.options[1].label + ' — ' + q.options[1].text]] : [['adv', 'An extra advantage (a distinction or a passion)'], ['dis', 'An extra disadvantage (an adversity or an anxiety), and +1 rank in a skill']];
    body.appendChild(choiceRow(pairs, A().q13, (v) => { if (v !== A().q13) { A().q13pick = null; A().q13skill = null; } A().q13 = v; save(); }));
    if (A().q13 === 'dis') { body.appendChild(lab('The skill')); body.appendChild(skillPicker(A().q13skill, (s) => { A().q13skill = s; save(); })); }
    if (A().q13) { body.appendChild(lab(A().q13 === 'adv' ? 'The extra advantage' : 'The extra disadvantage')); body.appendChild(pecPicker(A().q13 === 'adv' ? ['distinction', 'passion'] : ['adversity', 'anxiety'], A().q13pick, (v) => { A().q13pick = v; save(); })); }
    body.appendChild(lab('What they taught, and at what cost'));
    body.appendChild(textArea(() => A().mentorText, (v) => (A().mentorText = v), '', 3, 'mentorText'));
  }
  function impressionStep(body) {
    const q = alt(14);
    if (q) {
      body.appendChild(lab('The possession — from the outfit, or any item of rarity 5 or lower'));
      const d = G.compute(C);
      const outfit = G.gear(C, d).filter((g) => /outfit/.test(g.note || '') && !g.open).map((g) => ({ value: g.name, label: g.name, meta: g.note }));
      const pool = outfit.concat(G.items().filter((i) => i.rarity <= 5).map((i) => ({ value: i.name, label: i.name, entity: i.e, meta: [i.kind, 'rarity ' + i.rarity, D.label(i.book)].join(' · ') })));
      body.appendChild(pickList(pool, A().prized, (v) => { A().prized = v; save(); }));
      if (q.gain) body.appendChild(note(q.gain));
      body.appendChild(lab('Why this one?'));
      body.appendChild(textArea(() => A().prizedText, (v) => (A().prizedText = v), '', 3, 'prizedText'));
      return;
    }
    body.appendChild(textArea(() => A().impression, (v) => (A().impression = v), 'A feature, a mannerism, a tic — something you could point at…', 3, 'impression'));
    body.appendChild(lab('The aesthetic accoutrement — the object, in a few words'));
    body.appendChild(textLine(() => A().accName, (v) => (A().accName = v), 'Rice bowl · Brass compass · Commander’s insignia'));
    body.appendChild(lab('…and what is particular about it'));
    body.appendChild(textLine(() => A().acc, (v) => (A().acc = v), 'Repaired with kintsugi.', 'acc'));
  }
  function tiesStep(body) {
    C.people = C.people && C.people.length ? C.people : [{ name: '', text: '' }];
    C.people.forEach((p, i) => body.appendChild(el('div', { class: 'cg-person' }, [
      textLine(() => p.name, (v) => (p.name = v), 'A name'),
      textArea(() => p.text, (v) => (p.text = v), 'Who they are to this character', 2, { field: 'person', extra: () => 'This sentence is about one person in the character\'s life' + (p.name ? ', ' + p.name : '') + ', and no one else.' }),
      C.people.length > 1 ? button('Remove', () => { C.people.splice(i, 1); save(); }, 'ghost tiny') : null,
    ])));
    body.appendChild(button('+ Another person', () => { C.people.push({ name: '', text: '' }); save(); }, 'ghost tiny'));
    const q = Q(16);
    body.appendChild(lab(q && q.gain ? q.gain : 'A starting item of rarity 7 or lower'));
    body.appendChild(itemPicker(7, null, C.item, (v) => { C.item = v; save(); }));
  }
  function parentStep(body) {
    const q = alt(17);
    if (q && q.prompts.length) {
      body.appendChild(pickList(q.prompts.map((p) => ({ value: p.label, label: p.label, meta: p.text })), A().q17prompt, (v) => { A().q17prompt = v; save(); }));
      if (q.gain) body.appendChild(note(q.gain));
      body.appendChild(textArea(() => A().group, (v) => (A().group = v), 'Answer it — who, and what happened?', 3, { field: 'group', extra: () => (A().q17prompt ? 'The prompt the player chose: ' + A().q17prompt + '.' : '') }));
      return;
    }
    body.appendChild(textArea(() => A().parent, (v) => (A().parent = v), 'What do they say of their child?', 3, 'parent'));
    body.appendChild(lab('The skill it gave them (one at 0 ranks)'));
    body.appendChild(skillPicker(A().q17skill, (s) => { A().q17skill = s; save(); }, { atZero: true }));
  }
  function heritageStep(body) {
    if (!isCore()) {
      body.appendChild(textArea(() => A().raised, (v) => (A().raised = v), 'Who raised them, and how do they feel about it?', 3, 'raised'));
      body.appendChild(lab('The skill it left them (one at 0 ranks)'));
      body.appendChild(skillPicker(A().q18skill, (s) => { A().q18skill = s; save(); }, { atZero: true }));
      return;
    }
    const tables = G.heritageTables();
    const h = C.heritage;
    if (!h.table || !G.heritageTable(h.table)) h.table = (tables[0] || {}).id || null;
    const forget = () => dropChoices('h.');
    body.appendChild(lab('The table — the core’s, or a supplement’s used in its place'));
    body.appendChild(choiceRow(tables.map((t) => [t.id, t.name + ' · ' + D.label(t.book)]), h.table, (v) => { if (v !== h.table) { forget(); h.entry = null; h.sub = null; } h.table = v; save(); }));
    const t = G.heritageTable(h.table);
    if (!t) return;
    if (t.intro) body.appendChild(E.prose(t.intro, 'cg-note prose', t.book));
    body.appendChild(el('div', { class: 'cg-choices' }, [button('Roll 1d10', () => { const r = G.rollOn(t.entries, '1d10', (e) => e.range); forget(); h.rolls = [r.n]; h.entry = r.row ? r.row.name : null; h.sub = null; save(); }, 'ghost tiny'),
      h.rolls && h.rolls.length ? el('span', { class: 'cg-note' }, ['rolled ' + h.rolls.join(', ')]) : null]));
    body.appendChild(el('div', { class: 'cg-heritage' }, t.entries.map((e) => el('button', { type: 'button', class: 'cg-her' + (e.name === h.entry ? ' on' : ''), onclick: () => { if (e.name !== h.entry) { forget(); h.sub = null; } h.entry = e.name; save(); } }, [
      el('span', { class: 'cg-her-roll' }, [e.range]),
      el('span', { class: 'cg-her-body' }, [
        el('span', { class: 'cg-her-name' }, [e.name]),
        e.description ? el('span', { class: 'cg-her-desc' }, [e.description]) : null,
        Object.keys(e.mods).length ? el('span', { class: 'cg-her-mod' }, [Object.keys(e.mods).map((k) => k + ' ' + (e.mods[k] > 0 ? '+' : '') + e.mods[k]).join(' · ')]) : null,
        e.effect.length ? el('span', { class: 'cg-her-eff' }, e.effect.map((x) => E.span(x, t.book))) : null,
      ]),
    ]))));
    const st = G.heritageState(C);
    if (st.entry && st.entry.sub.length) {
      body.appendChild(lab('Second roll — ' + (st.entry.die || '1d10')));
      body.appendChild(el('div', { class: 'cg-choices' }, [button('Roll ' + (st.entry.die || '1d10'), () => { const r = G.rollOn(st.entry.sub, st.entry.die, (x) => x.range); forget(); h.sub = r.row ? r.row.range : null; save(); }, 'ghost tiny')]));
      body.appendChild(choiceRow(st.entry.sub.map((s) => [s.range, s.range + ' · ' + G.refText(s.text)]), h.sub, (v) => { if (v !== h.sub) forget(); h.sub = v; save(); }));
    }
    st.reqs.forEach((r) => requirement(body, r));
    body.appendChild(lab('What it means to the family, in your words'));
    body.appendChild(textArea(() => A().heritageText, (v) => (A().heritageText = v), ''));
  }
  // one control per thing the heritage result asks for
  function requirement(body, r) {
    const pick1 = (k) => chosen(k)[0] || null;
    const set1 = (k, v) => { setChosen(k, v != null && v !== '' ? [v] : []); save(); };
    body.appendChild(lab(r.prompt + (r.categoryLabel ? ' — ' + r.categoryLabel : r.ring ? ' — ' + r.ring : '')));
    if (r.waiting) { body.appendChild(note('Make the second roll first: it names this.')); return; }
    if (r.kind === 'pick_one') {
      body.appendChild(choiceRow(r.options.map((o, i) => [String(i), o.prompt]), pick1(r.key + '.pick'), (v) => set1(r.key + '.pick', v)));
      const p = pick1(r.key + '.pick');
      if (p != null && r.options[Number(p)]) requirement(body, r.options[Number(p)]);
      return;
    }
    if (r.kind === 'skill') {
      if (r.skill) { body.appendChild(note('+1 ' + r.skill)); return; }
      let only = r.options || null;
      if (r.from === 'school_starting_at_zero') {
        const s = G.schools().find((x) => x.id === C.school);
        const d = G.compute(C);
        only = s ? [].concat(Object.keys(s.skills.fixed), ...s.skills.choose.map((c) => c.of)).filter((k) => !(d.skills[k] || 0) || k === pick1(r.key)) : [];
      }
      body.appendChild(skillPicker(pick1(r.key), (v) => set1(r.key, v), { only }));
      return;
    }
    if (r.kind === 'technique') {
      const d = G.compute(C);
      const have = G.techniqueList(C, d).map((t) => t.name);
      const want = r.category ? G.norm(r.category) : null;
      const ok = (t) => (r.rank == null || t.rank === r.rank) && (!want || want.split(' or ').some((w) => t.base === w.replace(/s$/, '')));
      let pool = G.techniques().filter(ok).filter((t) => have.indexOf(t.name) === -1 || t.name === pick1(r.key));
      // "an invocation of that ring": the ones the corpus files under the ring, where it does
      const ringed = r.ring ? pool.filter((t) => G.norm(t.category || '').indexOf(G.norm(r.ring)) === 0) : [];
      if (ringed.length) pool = ringed;
      body.appendChild(pickList(pool.map((t) => ({ value: t.name, label: t.name, entity: D.entity(t.id), meta: [t.category, 'rank ' + t.rank, D.label(t.book)].filter(Boolean).join(' · ') })), pick1(r.key), (v) => set1(r.key, v)));
      return;
    }
    if (r.kind === 'peculiarity') {
      const e = r.options ? null : G.peculiarityNamed(r.name);
      if (r.options) body.appendChild(choiceRow(r.options.map((o) => [o, o]), pick1(r.key), (v) => set1(r.key, v)));
      else body.appendChild(tip(el('span', { class: 'cg-chip' }, [(e ? e.name : r.name) + (r.subject ? ' — ' + r.subject : '')]), e));
      if (r.subject_options) body.appendChild(choiceRow(r.subject_options.map((o) => [o, o]), pick1(r.key + '.subject'), (v) => set1(r.key + '.subject', v)));
      if (r.subject_free) body.appendChild(textLine(() => pick1(r.key + '.subject'), (v) => { setChosen(r.key + '.subject', v ? [v] : []); }, r.subject_free));
      return;
    }
    if (r.kind === 'item') {
      if (r.name) { body.appendChild(el('span', { class: 'cg-chip' }, [r.name + (r.define ? ' — ' + r.define : '')])); return; }
      if (r.free) body.appendChild(textLine(() => pick1(r.key + '.item'), (v) => setChosen(r.key + '.item', v ? [v] : []), 'Name ' + r.free));
      else body.appendChild(itemPicker(r.rarity_max || 99, r.type || r.category || null, pick1(r.key + '.item'), (v) => set1(r.key + '.item', v)));
      if (r.qualities) {
        body.appendChild(lab('The quality you choose (' + (r.qualities.player || 1) + '), and the GM’s'));
        body.appendChild(choiceRow(G.qualities().map((q) => [q, q]), pick1(r.key + '.quality'), (v) => set1(r.key + '.quality', v)));
        body.appendChild(choiceRow(G.qualities().map((q) => [q, q + ' (GM)']), pick1(r.key + '.gm_quality'), (v) => set1(r.key + '.gm_quality', v)));
      }
      return;
    }
    if (r.kind === 'ring_swap') {
      const to = Array.isArray(r.to) ? r.to : RINGS;
      body.appendChild(note((r.optional ? 'Optional. ' : '') + 'Reduce one ring by 1 to raise another by 1 (never above ' + (r.cap || 3) + ').'));
      body.appendChild(el('div', { class: 'cg-swap' }, [lab('Lower'), ringPicker(pick1(r.key + '.from'), (v) => set1(r.key + '.from', v === pick1(r.key + '.from') ? null : v)), lab('Raise'), ringPicker(pick1(r.key + '.to'), (v) => set1(r.key + '.to', v === pick1(r.key + '.to') ? null : v), to)]));
      return;
    }
    if (r.kind === 'money') body.appendChild(note('Starting money is doubled.'));
  }
  function heritageDone() {
    if (!isCore()) return has(A().raised) && has(A().q18skill);
    return !!C.heritage.entry && !G.heritageOpen(C).length && !G.compute(C).pending.some((p) => p.type === 'swap');
  }
  function nameStep(body) {
    const d = G.compute(C);
    const fam = isCore() && d.family ? d.family.name : '';
    body.appendChild(lab(fam ? 'Personal name (it follows the family name, ' + fam + ')' : 'Name'));
    body.appendChild(textLine(() => C.personal, (v) => (C.personal = v), fam ? 'Yoshi' : 'A name'));
    body.appendChild(lab('Or the whole name, as it should read'));
    body.appendChild(textLine(() => C.name, (v) => (C.name = v), (fam ? fam + ' ' : '') + (C.personal || '')));
  }
  function ringCapStep(body) {
    const d = G.compute(C);
    const capN = G.ringCap();
    const over = RINGS.filter((r) => d.rings[r] > capN);
    body.appendChild(note(RINGS.map((r) => r + ' ' + d.rings[r]).join(' · ')));
    if (over.length) {
      const from = over[0];
      body.appendChild(lab(from + ' came out at ' + d.rings[from] + ' — move the excess rank to'));
      body.appendChild(ringPicker(null, (to) => { C.ring_reassign = (C.ring_reassign || []).concat([{ from, to }]); save(); }, RINGS.filter((r) => d.rings[r] < capN)));
    } else body.appendChild(note('Nothing is above ' + capN + '.'));
    if ((C.ring_reassign || []).length) {
      body.appendChild(note('Moved: ' + C.ring_reassign.map((m) => '1 rank from ' + m.from + ' to ' + m.to).join('; ') + '.'));
      body.appendChild(button('Start over', () => { C.ring_reassign = []; save(); }, 'ghost tiny'));
    }
  }
  function outfitStep(body) {
    const d = G.compute(C);
    const open = G.outfitLines(C, d).filter((g) => g.open);
    const ch = (C.outfit = C.outfit || {});
    open.forEach((g) => {
      body.appendChild(lab(g.name));
      const offer = G.outfitOffer(g.name);
      const done = ch[g.name] || [];
      if (offer.kind === 'either') body.appendChild(choiceRow(offer.options.map((o) => [o.join(' and '), o.join(' and ')]), done.join(' and ') || null, (v) => { ch[g.name] = offer.options.find((o) => o.join(' and ') === v); save(); }));
      else if (offer.kind === 'pick') {
        body.appendChild(note('Choose ' + offer.count + ' ' + offer.type + ' of rarity ' + offer.rarity + ' or lower' + (done.length ? ' — chosen: ' + done.join(', ') : '') + '.'));
        body.appendChild(itemPicker(offer.rarity, offer.type, null, (v) => { let cur = (ch[g.name] || []).slice(); if (cur.length >= offer.count) cur = []; ch[g.name] = cur.concat([v]); save(); }));
      } else body.appendChild(textLine(() => done.join(', '), (v) => { ch[g.name] = v ? [v] : []; }, 'What this character actually carries for this line'));
      if (done.length) body.appendChild(button('Undo', () => { delete ch[g.name]; save(); }, 'ghost tiny'));
    });
  }
  function sheetStep(body) {
    const v = G.toSheet(C);
    const d = G.compute(C);
    const warn = [];
    RINGS.forEach((r) => { if (d.rings[r] > G.ringCap()) warn.push(r + ' is ' + d.rings[r] + ' — above ' + G.ringCap() + ' during creation'); });
    Object.keys(d.skills).forEach((k) => { if (d.skills[k] > G.skillCap()) warn.push(k + ' is ' + d.skills[k] + ' — above ' + G.skillCap() + ' during creation; the book’s remedy is to raise a different skill'); });
    const open = steps().filter((s) => s.n && !s.done()).map((s) => s.n);
    if (open.length) warn.push('Still unanswered: question' + (open.length > 1 ? 's ' : ' ') + open.join(', '));
    if (warn.length) body.appendChild(el('div', { class: 'correction' }, [el('div', { class: 'guidance-k' }, ['Before it goes to the table']), warn.map((w) => el('div', {}, [w]))]));
    body.appendChild(el('h3', {}, [v.Name || 'An unnamed ' + (isCore() ? 'samurai' : 'wanderer')]));
    body.appendChild(el('div', { class: 'muted' }, [Sheet.sentence(v)]));
    body.appendChild(Sheet.render(v, null));
    body.appendChild(el('div', { class: 'cg-choices' }, [button('Download the character file', () => Sheet.download(v)), el('span', { class: 'cg-note' }, ['the GM imports it at the table; you can load it on the player’s page'])]));
  }

  // ── the steps: n is the question number (0 for the steps around them) ──
  const qTitle = (n) => { const q = Q(n); return q ? q.text : 'Question ' + n; };
  function steps() {
    const list = [
      { id: 'begin', n: 0, label: 'Begin', title: () => 'Begin a character', done: () => true, render: beginStep },
      { id: 'q1', n: 1, label: () => (isCore() ? 'Clan' : 'Region'), done: () => (isCore() ? has(C.clan) && choicesDone2('clan') : has(C.region) && choicesDone2('region')), render: clanStep },
      { id: 'q2', n: 2, label: () => (isCore() ? 'Family' : 'Upbringing'), done: () => (isCore() ? has(C.family) && choicesDone2('family') : has(C.upbringing) && choicesDone2('upb')), render: familyStep },
      { id: 'q3', n: 3, label: 'School', done: schoolDone, render: schoolStep },
      { id: 'q4', n: 4, label: () => (isCore() ? 'Stand out' : 'Trouble'), done: () => has(C.standout) && has(A().standout), render: standoutStep },
      { id: 'q5', n: 5, label: () => (isCore() ? 'Giri' : 'Past'), done: () => has(isCore() ? A().giri : A().past), render: giriStep },
      { id: 'q6', n: 6, label: 'Ninjō', done: () => has(A().ninjo), render: ninjoStep },
      { id: 'q7', n: 7, label: () => (isCore() ? 'Clan tie' : 'Known for'), done: () => has(A().q7) && (A().q7 !== 'skill' || has(A().q7skill)), render: q7Step },
      { id: 'q8', n: 8, label: 'Bushidō', done: bushidoDone, render: bushidoStep },
      { id: 'q9', n: 9, label: 'Distinction', done: () => has(A().accomplishment) && has(C.pec.distinction), render: pecStep('distinction', 'accomplishment', 'What did they do?', 'The distinction it earns them') },
      { id: 'q10', n: 10, label: 'Adversity', done: () => has(A().challenge) && has(C.pec.adversity), render: pecStep('adversity', 'challenge', 'What holds them back?', 'The adversity it reflects') },
      { id: 'q11', n: 11, label: 'Passion', done: () => has(A().peace) && has(C.pec.passion), render: pecStep('passion', 'peace', 'What do they do for themselves?', 'The passion it becomes') },
      { id: 'q12', n: 12, label: 'Anxiety', done: () => has(A().fear) && has(C.pec.anxiety), render: pecStep('anxiety', 'fear', 'What troubles them?', 'The anxiety it names') },
      { id: 'q13', n: 13, label: 'Mentor', done: () => has(A().mentor) && has(A().q13) && has(A().q13pick) && (A().q13 !== 'dis' || has(A().q13skill)), render: mentorStep },
      { id: 'q14', n: 14, label: () => (isCore() ? 'Noticed first' : 'Possession'), done: () => (alt(14) ? has(A().prized) : has(A().impression) && has(A().accName)), render: impressionStep },
      { id: 'q15', n: 15, label: 'Stress', done: () => has(A().stress), render: (b) => b.appendChild(textArea(() => A().stress, (v) => (A().stress = v), 'What happens when they break?', 3, 'stress')) },
      { id: 'q16', n: 16, label: 'Ties & item', done: () => has(C.item), render: tiesStep },
      { id: 'q17', n: 17, label: () => (isCore() ? 'Parent' : 'Group'), done: () => (alt(17) && alt(17).prompts.length ? has(A().q17prompt) && has(A().group) : has(A().parent) && has(A().q17skill)), render: parentStep },
      { id: 'q18', n: 18, label: () => (isCore() ? 'Heritage' : 'Raised by'), done: heritageDone, render: heritageStep },
      { id: 'q19', n: 19, label: 'Name', done: () => has(C.personal) || has(C.name), render: nameStep },
      { id: 'q20', n: 20, label: 'Death', done: () => has(A().death), render: (b) => b.appendChild(textArea(() => A().death, (v) => (A().death = v), 'The ending they would not regret…', 3, 'death')) },
      { id: 'rings', n: 0, label: 'Rings', eyebrow: 'Before it goes to the table', title: () => 'Rings above ' + G.ringCap(), desc: 'A ring cannot pass ' + G.ringCap() + ' during character creation. Every increase was legal by itself; only the total can break the limit, so it is settled last — the excess rank moves to a ring you choose.', done: () => !RINGS.some((r) => G.compute(C).rings[r] > G.ringCap()), render: ringCapStep },
      { id: 'outfit', n: 0, label: 'Outfit', eyebrow: 'Before it goes to the table', title: () => 'The outfit’s either-ors', desc: 'The school’s outfit is printed with choices in it — “yari or naginata”, “any one weapon of rarity 6 or lower”. A character owns things, not choices: settle each line to what they carry.', done: () => !G.outfitOpen(C, G.compute(C)).length, render: outfitStep },
      { id: 'sheet', n: 0, label: 'The sheet', eyebrow: 'Done', title: () => 'The character', done: () => false, render: sheetStep },
    ];
    // the two cleanup steps are asked only when they bind (and stay while they hold a decision)
    return list.filter((s) => {
      if (s.id === 'rings') return (C.ring_reassign || []).length || RINGS.some((r) => G.compute(C).rings[r] > G.ringCap());
      if (s.id === 'outfit') return G.outfitLines(C, G.compute(C)).some((g) => g.open);
      return true;
    });
  }
  function choicesDone2(which) {
    const pick = { clan: [G.clans(), C.clan, 'clan'], family: [G.families(), C.family, 'family'], region: [G.regions(), C.region, 'region'], upb: [G.upbringings(), C.upbringing, 'upb'] }[which];
    const o = pick[0].find((x) => x.id === pick[1]);
    return !!o && choicesDone(o.rings, pick[2] + '.r') && choicesDone(o.skills, pick[2] + '.s');
  }
  function beginStep(body) {
    body.appendChild(lab('Who is this'));
    body.appendChild(choiceRow(G.MODES.map((m) => [m.key, m.label + ' — ' + m.title]), mode(), (v) => {
      if (v === mode()) return;
      // questions 1 and 2 differ by mode, so their answers cannot carry
      C.mode = v; C.clan = C.family = C.region = C.upbringing = C.school = C.role = null;
      dropChoices('clan.'); dropChoices('family.'); dropChoices('region.'); dropChoices('upb.'); dropChoices('school.');
      save();
    }));
    body.appendChild(note(isCore() ? 'A samurai of a Great or Minor Clan: questions 1 and 2 are clan and family.' : 'Questions 1 and 2 become region and upbringing, and a past stands where giri would. ' + (mode() === 'wow' ? 'Writ of the Wilds restates questions 1, 2, 5, 6, 7 and 8; the rest are Path of Waves’.' : '')));
    body.appendChild(lab('A working name'));
    body.appendChild(textLine(() => C.name, (v) => (C.name = v), 'You can change it at question 19'));
    body.appendChild(lab('Concept — kept on the draft, not on the sheet'));
    body.appendChild(textArea(() => C.concept, (v) => (C.concept = v), 'A premise, an image, a line of dialogue, a role at the table…', 4));
  }

  // ── the side panel: the character so far, and where each number came from ──
  function provenance(list, base) {
    const bits = (list || []).map((c) => (c.by > 0 ? '+' : '') + c.by + ' ' + c.source);
    if (base != null) bits.unshift(base + ' base');
    return bits.join(', ');
  }
  function wip() {
    const d = G.compute(C);
    const v = G.toSheet(C);
    const der = Sheet.derived(v);
    const pecs = G.peculiarityList(C, d);
    const techs = G.techniqueList(C, d);
    const gear = G.gear(C, d);
    const sub = isCore() ? [d.clan && d.clan.name, d.family && d.family.name, d.school && d.school.name] : [d.region && d.region.name, d.upbringing && d.upbringing.name, d.school && d.school.name];
    const over = RINGS.filter((r) => d.rings[r] > G.ringCap()).map((r) => r + ' ' + d.rings[r]).concat(Object.keys(d.skills).filter((k) => d.skills[k] > G.skillCap()).map((k) => k + ' ' + d.skills[k]));
    const skills = Object.keys(d.skills).filter((k) => d.skills[k]).sort();
    const pend = d.pending.concat(G.heritageOpen(C).map((r) => ({ type: 'heritage', what: r.prompt })));
    const chips = (list, cls) => el('div', { class: 'cg-chips' }, list.map((x) => tip(el('span', { class: 'cg-chip ' + (cls || '') + (x.open ? ' open' : ''), title: x.title || null }, [x.name]), x.entity)));
    return el('div', { class: 'cg-wip' }, [
      el('h3', { class: 'cg-wip-name' }, [v.Name || 'Unnamed']),
      el('div', { class: 'cg-wip-sub' }, [sub.filter(Boolean).join(' · ') || '—']),
      el('div', { class: 'cg-wip-rings' }, RINGS.map((r) => el('div', { class: 'cg-wip-ring', 'data-ring': r.toLowerCase(), title: provenance(d.from.rings[r], 1) || null }, [Dice.ringIcon(r), el('span', { class: 'rn' }, [r]), el('span', { class: 'rv' }, [String(d.rings[r])])]))),
      el('div', { class: 'cg-wip-stats' }, [['Honor', d.honor], ['Glory', d.glory], ['Status', d.status], ['Purse', d.coinLabel]].map(([k, x]) => el('div', { class: 'cg-stat' }, [el('span', { class: 'k' }, [k]), el('span', { class: 'v' }, [String(x)])]))),
      el('div', { class: 'cg-wip-stats small' }, ['Endurance', 'Composure', 'Focus', 'Vigilance'].map((k) => el('div', { class: 'cg-stat' }, [el('span', { class: 'k' }, [k]), el('span', { class: 'v' }, [der[k] != null ? String(der[k]) : '—'])]))),
      over.length ? el('p', { class: 'cg-warn' }, ['Past the creation limit: ' + over.join(', ') + '. Nothing may pass ' + G.ringCap() + ' during creation — the rule is to raise something else instead.']) : null,
      pend.length ? el('p', { class: 'cg-pending' }, ['Still to settle: ' + pend.map((p) => (p.type === 'ring' ? 'a ring from ' + p.source : p.type === 'skill' ? p.n + ' skill' + (p.n > 1 ? 's' : '') + ' from ' + p.source : p.type === 'clan' ? 'the clan for ' + p.source : p.type === 'swap' ? 'the heritage’s swap (' + p.from + ' → ' + p.to + ' is not legal here)' : p.type === 'item' ? p.name + ' from ' + p.source : 'heritage: ' + p.what)).join('; ') + '.']) : null,
      el('div', { class: 'cg-label' }, ['Skills']),
      skills.length ? el('div', { class: 'cg-wip-skills' }, skills.map((k) => el('div', { class: 'cg-wip-skill', title: provenance(d.from.skills[k]) || null }, [el('span', {}, [k]), el('b', {}, [String(d.skills[k])])]))) : el('p', { class: 'cg-note' }, ['No skills yet.']),
      pecs.length ? el('div', {}, [el('div', { class: 'cg-label' }, ['Advantages & disadvantages']), chips(pecs.map((p) => ({ name: G.withSubject(p.name, p.subject), entity: p.e, title: p.source })), '')]) : null,
      techs.length ? el('div', {}, [el('div', { class: 'cg-label' }, ['Techniques']), chips(techs.map((t) => { const r = G.techniqueNamed(t.name); return { name: t.name, entity: r ? D.entity(r.id) : null, title: t.source }; }), 'tech')]) : null,
      gear.length ? el('div', {}, [el('div', { class: 'cg-label' }, ['Gear']), chips(gear.map((g) => { const it = G.itemNamed(g.name); return { name: g.name + (g.lost ? ' (lost)' : ''), open: g.open, entity: it ? it.e : null, title: g.note || null }; }), 'gear')]) : null,
    ]);
  }

  // ── the page ──
  function render(container, path, ctx) {
    const page = el('div', { class: 'page cg' });
    container.appendChild(page);
    const wait = el('div', { class: 'muted loading' }, ['Opening the books the questions draw on…']);
    page.appendChild(wait);
    // every book: clans, families, schools, heritages and advantages come from all of them
    D.ensureAll().then(() => { G.reset(); wait.remove(); draw(page, path, ctx); });
  }
  function draw(page, path, ctx) {
    const d0 = draft();
    draftId = d0.id;
    C = Object.assign(G.blank(), d0.character._cg);
    const all = steps();
    const cur = all.find((s) => s.id === path[0]) || all[0];
    const idx = all.indexOf(cur);
    const val = (x) => (typeof x === 'function' ? x() : x);
    redrawPage = () => { const y = window.scrollY; page.innerHTML = ''; draw(page, [cur.id], ctx); window.scrollTo(0, y); };

    // the drafts in this browser
    const file = el('input', { type: 'file', accept: '.json,application/json', hidden: true });
    file.addEventListener('change', () => {
      const f = file.files && file.files[0];
      if (!f) return;
      f.text().then((t) => { Roster.add(Sheet.readFile(JSON.parse(t))); Site().go('create', ['sheet']); }).catch((e) => alert(e.message)).finally(() => (file.value = ''));
    });
    const drafts = Roster.list().filter((r) => r.character && r.character._cg);
    page.appendChild(el('div', { class: 'creator-head' }, [
      el('div', {}, [el('h1', {}, ['Making a character']), el('div', { class: 'muted small' }, ['The Game of Twenty Questions, in the corpus’s own words; every number read from the books.'])]),
      el('div', { class: 'chiprow tight' }, [
        el('select', { class: 'scope', onchange: (ev) => { Roster.open(ev.target.value); redrawPage(); } }, drafts.map((r) => el('option', { value: r.id, selected: r.id === d0.id || null }, [(r.character.Name || 'unnamed') + (r.character.School ? ' · ' + r.character.School : '')]))),
        button('New', () => { const c = G.blank(); Roster.add(Object.assign(G.toSheet(c), { _cg: c })); Site().go('create', ['begin']); }, 'ghost tiny'),
        button('Duplicate', () => { Roster.duplicate(d0.id); redrawPage(); }, 'ghost tiny'),
        button('Remove', () => { if (confirm('Remove ' + (d0.character.Name || 'this character') + ' from this browser?')) { Roster.remove(d0.id); redrawPage(); } }, 'ghost tiny'),
        button('Load a file…', () => file.click(), 'ghost tiny'), file,
      ]),
    ]));

    const live = all.filter((s) => s.id !== 'sheet' && s.id !== 'begin');
    const doneN = live.filter((s) => s.done()).length;
    const bar = el('div', { class: 'cg-progress' }, [el('div', { class: 'cg-bar' }, [el('i', { style: 'width:' + Math.round((doneN / live.length) * 100) + '%' })]), el('span', { class: 'cg-note' }, [doneN + ' of ' + live.length + ' answered'])]);
    const nav = el('nav', { class: 'cg-nav' }, all.map((s) => el('a', { class: 'cg-navstep' + (s === cur ? ' on' : '') + (s.id !== 'sheet' && s.id !== 'begin' && s.done() ? ' done' : ''), href: ctx.href('create', [s.id]) }, [el('span', { class: 'n' }, [s.n ? String(s.n) : '·']), el('span', { class: 'l' }, [val(s.label)])])));

    const main = el('main', { class: 'cg-step' });
    main.appendChild(el('div', { class: 'cg-eyebrow' }, [cur.eyebrow || (cur.n ? 'Question ' + cur.n + (Q(cur.n) && Q(cur.n).book !== 'core' ? ' · ' + D.label(Q(cur.n).book) : '') : 'Begin')]));
    main.appendChild(el('h2', {}, [cur.title ? val(cur.title) : qTitle(cur.n)]));
    if (cur.desc) main.appendChild(el('p', { class: 'cg-desc' }, [val(cur.desc)]));
    if (cur.n) {
      const q = Q(cur.n);
      const sr = isCore() ? G.summaryRow(cur.n) : q && q.gain;
      if (sr) main.appendChild(E.prose(sr, 'prose cg-summary', 'core'));
      const book = el('details', { class: 'cg-book' }, [el('summary', {}, ['What the book says'])]);
      const wt = isCore() ? G.walkthrough(cur.n) : null;
      if (wt) book.appendChild(E.prose(wt.text, 'prose', 'core'));
      else if (q) q.rules.forEach((r) => r.text && book.appendChild(E.prose(r.text, 'prose', q.book)));
      if (book.children.length > 1) main.appendChild(book);
    }
    const body = el('div', { class: 'cg-body' });
    try { cur.render(body); } catch (e) { body.appendChild(el('div', { class: 'correction' }, ['This step failed to draw: ' + e.message])); console.error(e); }
    main.appendChild(body);
    main.appendChild(el('div', { class: 'cg-foot' }, [
      idx > 0 ? el('a', { class: 'btn ghost', href: ctx.href('create', [all[idx - 1].id]) }, ['‹ Back']) : el('span'),
      idx < all.length - 1 ? el('a', { class: 'btn', href: ctx.href('create', [all[idx + 1].id]) }, ['Next ›']) : el('span'),
    ]));
    const side = el('aside', { class: 'cg-side' }, [wip()]);
    refreshSide = () => {
      side.innerHTML = '';
      side.appendChild(wip());
      const n2 = live.filter((s) => s.done()).length;
      bar.querySelector('i').style.width = Math.round((n2 / live.length) * 100) + '%';
      bar.querySelector('span').textContent = n2 + ' of ' + live.length + ' answered';
      Array.prototype.forEach.call(nav.children, (a, i) => a.classList.toggle('done', all[i].id !== 'sheet' && all[i].id !== 'begin' && all[i].done()));
    };
    page.appendChild(bar);
    page.appendChild(el('div', { class: 'cg-grid' }, [nav, main, side]));
  }

  return { render, steps: () => steps() };
})();
