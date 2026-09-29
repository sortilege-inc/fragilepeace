// system/l5r5e/chargen.js — what the Game of Twenty Questions reads from the corpus, and the
// character its answers make. The wizard is system/l5r5e/creator.js; this holds no DOM.
//
// The approach is the pregens archive's (sortilege-l5r5e-pregens, assets/creator.js), which was
// tested on every character that archive holds: the draft keeps only the answers, and the
// character is recomputed from them every time — rings, skills, honor, glory, status and coin,
// each increase credited to where it came from, every choice still open named rather than
// guessed. What changed in the port is the source: the archive reads its own slimmed copies of
// an older corpus; this reads the 0.5 corpus the VTT is built from, through L5RData.
//
//   modes      core (a samurai), Path of Waves (a rōnin, peasant or gaijin: region and
//              upbringing replace clan and family), Writ of the Wilds (which restates Path of
//              Waves' questions 1, 2, 5, 6, 7 and 8 and leaves the rest to it)
//   questions  each book's own `^"Question" INTEGER n` DEFs, with their Gain, OPTIONS, PROMPTS
//   origin     clans, families, schools, regions, upbringings: their Ring Increase / Skill
//              Increases DEFs, CHOOSEs included, glory, status, wealth, items
//   heritage   every HERITAGE_TABLE in the corpus, read the same way however it is encoded,
//              and what each result obliges (system/l5r5e/heritage-rules.js)
//   limits     Starting Values' rule ids (`ring_maximum_during_creation_is_three`)
window.L5RChargen = (function () {
  const D = window.L5RData;
  const Sheet = () => window.L5RSheet;
  const RULES = window.L5RHeritageRules || { REQUIRES: {}, HEIRLOOM: [], CUSTOM_ITEMS: [] };
  const RINGS = ['Air', 'Earth', 'Fire', 'Water', 'Void'];
  const WORDS = { one: 1, two: 2, three: 3, four: 4, five: 5 };

  const norm = (s) => String(s || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[’‘`]/g, "'").toLowerCase().replace(/\s+/g, ' ').trim();
  const refText = (t) => String(t == null ? '' : t).replace(/\^"([^"]*)"/g, '$1');
  const cap = (s) => String(s || '').charAt(0).toUpperCase() + String(s || '').slice(1);
  // a rule's text: `id "prose"` → {id, text}
  function rule(r) {
    const m = /^(\w+)\s+"([\s\S]*)"$/.exec((r && r.text) || '');
    return m ? { id: m[1], text: m[2].replace(/\\"/g, '"').replace(/\\n/g, '\n') } : { id: (r && r.text) || '', text: '' };
  }
  const memo = {};
  const once = (k, fn) => () => (memo[k] !== undefined ? memo[k] : (memo[k] = fn()));
  function reset() { Object.keys(memo).forEach((k) => delete memo[k]); }

  // ── the three ways to make a character ──
  const QFILES = { core: 'core-chargen.ttrpg', pow: 'path-of-waves-character.ttrpg', wow: 'writ-of-wilds-mechanics.ttrpg' };
  const MODES = [
    { key: 'core', label: 'Samurai', book: 'core', title: 'Core Rulebook' },
    { key: 'pow', label: 'Rōnin, peasant or gaijin', book: 'path-of-waves', title: 'Path of Waves' },
    { key: 'wow', label: 'From the wilds', book: 'writ-of-wilds', title: 'Writ of the Wilds' },
  ];
  // "Label" "text" pairs, as OPTIONS and PROMPTS print them
  function pairs(b) {
    const s = ((b && b.body) || []).filter((x) => 's' in x).map((x) => x.s);
    const out = [];
    for (let i = 0; i + 1 < s.length; i += 2) out.push({ label: s[i], text: s[i + 1] });
    return out;
  }
  const questionSets = once('q', () => {
    const out = { core: {}, pow: {}, wow: {} };
    D.all().forEach((e) => {
      const n = D.num(e, 'Question');
      if (n == null || !D.text(e, 'Question Text')) return;
      const m = Object.keys(QFILES).find((k) => e.file.endsWith(QFILES[k]));
      if (!m) return;
      out[m][n] = {
        n, id: e.id, book: e.book, text: D.text(e, 'Question Text'), gain: D.text(e, 'Gain'),
        options: pairs(D.block(e, 'OPTIONS')), prompts: pairs(D.block(e, 'PROMPTS')),
        rules: (e.rules || []).map(rule),
      };
    });
    return out;
  });
  // A mode's question n: Writ of the Wilds falls back to Path of Waves, and both to the core.
  function question(mode, n) {
    const s = questionSets();
    if (mode === 'wow') return s.wow[n] || s.pow[n] || s.core[n] || null;
    if (mode === 'pow') return s.pow[n] || s.core[n] || null;
    return s.core[n] || null;
  }
  // the mode's own version of n, when it asks something other than the core does
  const alt = (mode, n) => (mode === 'core' ? null : (mode === 'wow' ? questionSets().wow[n] || questionSets().pow[n] : questionSets().pow[n]) || null);
  const hasRule = (q, id) => !!q && q.rules.some((r) => r.id === id);

  // the core's one-line summary of each question and its walkthrough (GUIDANCE q07-…)
  const summaryEntity = once('sum', () => D.all(['core']).find((e) => e.name === 'Twenty Questions' && e.file.endsWith('core-character.ttrpg')) || null);
  function summaryRow(n) {
    let out = null;
    const walk = (list) => (list || []).forEach((b) => {
      if (!b) return;
      if (b.num === n && b.args && b.args[0] && out == null) out = b.args[0].s;
      if (b.body) walk(b.body);
      if (b.ent) walk((D.entity(b.ent) || {}).blocks);
    });
    const s = summaryEntity();
    if (s) walk(s.blocks);
    return out;
  }
  function walkthrough(n) {
    const s = summaryEntity();
    const key = 'q' + (n < 10 ? '0' : '') + n + '-';
    return (s ? D.guidanceFor(s.id) : []).find((g) => g.name && g.name.indexOf(key) === 0) || null;
  }
  // "+5 glory" out of a line of text
  function amount(text, what) {
    const m = new RegExp('\\+(\\d+)\\s+' + what, 'i').exec(text || '');
    return m ? parseInt(m[1], 10) : null;
  }
  const skillNames = once('sk', () => Sheet().skills().map((s) => s.name));
  const skillGroups = () => Sheet().skillGroups();
  const isSkill = (n) => skillNames().indexOf(n) !== -1;
  // "the following skills: Commerce, Labor, Medicine, Seafaring, Skulduggery, or Survival."
  function listedSkills(text) {
    const m = /(?:following skills|one skill)[^:]*:\s*([^.]+)/i.exec(text || '');
    if (!m) return null;
    const out = m[1].split(/,\s*(?:or\s+)?|\s+or\s+/).map((s) => s.trim()).filter(isSkill);
    return out.length ? out : null;
  }

  // ── the creation limits and starting values ──
  const startingValues = once('sv', () => D.all(['core']).find((e) => e.name === 'Starting Values') || null);
  function limit(kind) {
    const sv = startingValues();
    const r = ((sv && sv.rules) || []).map((x) => new RegExp('^' + kind + '_maximum_during_creation_is_(\\w+)').exec(x.text)).find(Boolean);
    return r ? WORDS[r[1]] || parseInt(r[1], 10) || null : null;
  }
  const ringCap = () => limit('ring') || 3;
  const skillCap = () => limit('skill') || 3;
  const baseRing = () => { const sv = startingValues(); const v = sv ? D.val(sv, 'All Rings') : null; return typeof v === 'number' ? v : 1; };

  // Path of Waves: "If you are a rōnin … your status begins at 24" — the base the upbringing modifies
  const originTypes = once('ot', () => {
    const e = D.all(['path-of-waves']).find((x) => x.name === 'Path of Waves Character Creation');
    const out = [];
    ((e && e.rules) || []).map(rule).forEach((r) => {
      const m = /^pow_(\w+?)_base_status_(\d+)$/.exec(r.id);
      if (m) out.push({ key: m[1], label: m[1] === 'ronin' ? 'Rōnin' : cap(m[1]), status: parseInt(m[2], 10), text: r.text });
    });
    return out;
  });

  // ── a DEF of increases: `{ Earth 1 }`, `{ CHOOSE 1 [^"Earth", ^"Fire"] INTEGER 1 }`, both ──
  // → { fixed: {Name: n}, choose: [{n, of, by, distinct, clan}] }. Fallen Noble's
  // `CHOOSE <Chosen Clan> "Clan Ring Bonus"` is a clan to pick, whose bonus it grants.
  function increases(p) {
    const out = { fixed: {}, choose: [] };
    if (!p) return out;
    if (p.vk === 'scalar' && typeof p.value === 'string') {
      // a region's `^"Skill Increase" STRING "+1 Survival"`
      p.value.split(/,\s*/).forEach((part) => { const m = /^\+(\d+)\s+(.+)$/.exec(part.trim()); if (m) out.fixed[m[2]] = (out.fixed[m[2]] || 0) + parseInt(m[1], 10); });
      return out;
    }
    if (p.vk !== 'def') return out;
    (p.fields || []).forEach((f) => { const v = f.value !== undefined ? f.value : f.default; if (typeof v === 'number') out.fixed[f.name] = (out.fixed[f.name] || 0) + v; });
    const choose = (b) => {
      const list = b.args.find((a) => 'l' in a);
      if (!list) return null;
      const n = b.args.slice(0, b.args.indexOf(list)).find((a) => 'i' in a);
      const by = b.args.slice(b.args.indexOf(list) + 1).find((a) => 'i' in a);
      return { n: n ? n.i : 1, of: list.l.map((a) => D.arg(a)), by: by ? by.i : 1, distinct: b.args.some((a) => a.w === 'DISTINCT') };
    };
    const blocks = p.blocks || [];
    blocks.forEach((b, i) => {
      if (b.kw === 'CHOOSE') { const ch = choose(b); if (ch) out.choose.push(ch); return; }
      // Fallen Noble: `FROM_CLAN ^"<Chosen Clan>"."Clan Ring Bonus" FALLBACK { CHOOSE … }` — the
      // bonus of the clan the family belonged to, or the printed choice when it had none
      if (b.kw === 'FROM_CLAN') {
        const which = b.args.find((a) => 's' in a);
        const fb = blocks[i + 1] && blocks[i + 1].kw === 'FALLBACK' ? (blocks[i + 1].body || []).filter((x) => x.kw === 'CHOOSE').map(choose).filter(Boolean)[0] : null;
        out.choose.push({ n: 1, of: [], by: 1, clan: which ? which.s : 'bonus', fallback: fb || null });
      }
    });
    return out;
  }
  const label = (inc) => [].concat(Object.keys(inc.fixed).map((k) => '+' + inc.fixed[k] + ' ' + k), inc.choose.map((c) => (c.clan ? 'a clan’s ' + c.clan : (c.n > 1 ? c.n + ' of ' : '') + c.of.map((o) => '+' + c.by + ' ' + o).join(' or ')))).join(', ');
  // coin: {koku, bu, zeni} from a `Wealth` DEF; an `Item` DEF is a thing, not money
  function purseOf(e) {
    const out = { koku: 0, bu: 0, zeni: 0 };
    (e.props || []).filter((p) => p.name === 'Wealth' && p.vk === 'def').forEach((p) => {
      const f = D.defFields(p).fields;
      const t = String(f.Type || '').toLowerCase();
      if (out[t] != null && typeof f.Count === 'number') out[t] += f.Count;
    });
    return out;
  }
  const itemsOf = (e) => (e.props || []).filter((p) => p.name === 'Item' && p.vk === 'def').map((p) => D.defFields(p).fields.Description).filter(Boolean);
  const coinLabel = (c) => ['koku', 'bu', 'zeni'].filter((k) => c[k]).map((k) => c[k] + ' ' + k).join(', ') || '—';
  const addCoins = (a, b) => ['koku', 'bu', 'zeni'].forEach((k) => (a[k] += (b && b[k]) || 0));
  // a number the corpus may print as "+3" or "-2 (minimum 0)"
  const signed = (v) => (typeof v === 'number' ? v : v == null ? null : (/^\s*([+-]?\d+)/.exec(String(v)) || [])[1] != null ? parseInt(/^\s*([+-]?\d+)/.exec(String(v))[1], 10) : null);

  // ── the options ──
  const clans = once('clans', () => D.all().filter((e) => e.type === 'Clan').map((e) => ({
    id: e.id, e, book: e.book, name: D.text(e, 'Clan Name') || e.name.replace(/ (Minor )?Clan$/, ''), full: e.name,
    rings: increases(D.prop(e, 'Clan Ring Bonus')), skills: increases(D.prop(e, 'Clan Skill Bonus')), status: D.val(e, 'Clan Status'),
    families: [].concat(...D.blocks(e, 'FAMILIES').map((b) => (b.body || []).filter((x) => x.name).map((x) => x.name))),
  })).sort((a, b) => (a.book === 'core' ? 0 : 1) - (b.book === 'core' ? 0 : 1) || a.name.localeCompare(b.name)));
  const families = once('fams', () => D.all().filter((e) => e.type === 'Family').map((e) => ({
    id: e.id, e, book: e.book, name: D.text(e, 'Family Name') || e.name, clan: D.text(e, 'Clan'),
    rings: increases(D.prop(e, 'Ring Increase')), skills: increases(D.prop(e, 'Skill Increases')), glory: D.val(e, 'Glory'),
    coins: purseOf(e), items: itemsOf(e),
  })).sort((a, b) => a.name.localeCompare(b.name)));
  function familiesOf(clan) {
    if (!clan) return [];
    const by = families().filter((f) => clan.families.indexOf(f.name) !== -1 || clan.families.indexOf(f.e.name) !== -1);
    return by.length ? by : families().filter((f) => f.clan === clan.name);
  }
  // a school's STARTING_TECHNIQUES: `KATA ^"X"` fixed; `KATA` then `CHOOSE n [ … ]` a pick
  function startingTechniques(e) {
    const b = D.block(e, 'STARTING_TECHNIQUES');
    const out = [];
    const body = (b && b.body) || [];
    for (let i = 0; i < body.length; i++) {
      const x = body[i];
      if (x.kw === 'CHOOSE') continue;
      const named = (x.args || []).filter((a) => 'c' in a).map((a) => a.c);
      if (named.length) named.forEach((n) => out.push({ kind: x.kw, fixed: n }));
      else if (body[i + 1] && body[i + 1].kw === 'CHOOSE') {
        const ch = body[i + 1];
        out.push({ kind: x.kw, n: ((ch.args.find((a) => 'i' in a) || {}).i) || 1, of: ((ch.args.find((a) => 'l' in a) || {}).l || []).map(D.arg) });
      }
    }
    return out;
  }
  const schools = once('schools', () => D.all().filter((e) => e.type === 'School').map((e) => {
    const ob = D.block(e, 'STARTING_OUTFIT');
    const ab = D.block(e, 'SCHOOL_ABILITY');
    return {
      id: e.id, e, book: e.book, name: D.text(e, 'School Name') || e.name, clan: D.text(e, 'Clan'),
      roles: [].concat(D.val(e, 'Roles') || []), honor: D.val(e, 'Starting Honor'),
      rings: increases(D.prop(e, 'Ring Increase')), skills: increases(D.prop(e, 'Starting Skills')),
      techniques: startingTechniques(e), outfit: ob && ob.args[0] && ob.args[0].l ? ob.args[0].l.map(D.arg) : [],
      ability: ab ? D.arg(ab.args[0]) : null,
    };
  }).sort((a, b) => a.name.localeCompare(b.name)));
  // Path of Waves' regions and upbringings (Writ of the Wilds restates four of the upbringings)
  const regions = once('regions', () => D.all().filter((e) => D.prop(e, 'Region') && D.prop(e, 'Ring Increase')).map((e) => ({
    id: e.id, e, book: e.book, name: D.text(e, 'Region'), full: e.name,
    rings: increases(D.prop(e, 'Ring Increase')), skills: increases(D.prop(e, 'Skill Increase')), glory: D.val(e, 'Glory'),
  })));
  const upbringings = once('upb', () => D.all().filter((e) => /Upbringing$/.test(e.name) && D.prop(e, 'Status Modification')).map((e) => ({
    id: e.id, e, book: e.book, name: D.text(e, 'Upbringing') || e.name.replace(/ Upbringing$/, ''), full: e.name,
    rings: increases(D.prop(e, 'Ring Increase')), skills: increases(D.prop(e, 'Skill Increases')),
    status: signed(D.val(e, 'Status Modification')), coins: purseOf(e), items: itemsOf(e),
  })));
  // A mode offers what its own book states: Writ of the Wilds names three of the six regions and
  // four upbringings in its OPTIONS; Path of Waves offers every one it prints.
  function originSet(mode, n, list) {
    const q = mode === 'wow' ? questionSets().wow[n] : null;
    const bookId = mode === 'wow' ? 'writ-of-wilds' : 'path-of-waves';
    if (q && q.options.length) {
      const names = q.options.map((o) => norm(o.label));
      const mine = list.filter((x) => names.indexOf(norm(x.name)) !== -1);
      const own = mine.filter((x) => x.book === bookId);
      const pick = names.map((nm) => own.find((x) => norm(x.name) === nm) || mine.find((x) => norm(x.name) === nm)).filter(Boolean);
      if (pick.length) return pick;
    }
    return list.filter((x) => x.book === 'path-of-waves');
  }

  // Clan Views of Bushidō (Honor in Play): each Great Clan's paramount and lesser tenets
  const tenets = once('tenets', () => {
    const b = D.all(['core']).find((e) => e.name === 'Bushido' && e.file.endsWith('core-character.ttrpg'));
    const t = b && D.block(b, 'TENETS');
    return t ? (t.body || []).filter((p) => p.name).map((p) => ({ name: p.name, text: p.value, short: p.name.replace(/\s*\([^)]*\)\s*$/, '') })) : [];
  });
  const clanViews = once('views', () => {
    const h = D.all(['core']).find((e) => e.name === 'Honor in Play');
    const out = {};
    [['CLAN_PARAMOUNT_TENETS', 'paramount'], ['CLAN_LESSER_TENETS', 'lesser']].forEach(([kw, k]) => {
      pairs(h && D.block(h, kw)).forEach((r) => { (out[r.label] = out[r.label] || {})[k] = (r.text.match(/\^"([^"]+)"/g) || []).map((x) => x.slice(2, -1)); });
    });
    return out;
  });

  // advantages and disadvantages, by the type the corpus gives them
  const PEC = { distinction: 'Distinction', adversity: 'Adversity', passion: 'Passion', anxiety: 'Anxiety' };
  const peculiarities = (kind) => D.all().filter((e) => e.type === PEC[kind]).sort((a, b) => a.name.localeCompare(b.name));
  const pecStem = (s) => norm(s).replace(/\s*\((air|earth|fire|water|void)\)\s*$/, '');
  function peculiarityNamed(name, kinds) {
    const want = pecStem(name);
    const pool = (kinds || Object.keys(PEC)).reduce((a, k) => a.concat(peculiarities(k)), []);
    return pool.find((e) => pecStem(e.name) === want) || null;
  }
  const kindOf = (e) => Object.keys(PEC).find((k) => PEC[k] === e.type) || null;
  const isAdvantage = (e) => e && (e.type === 'Distinction' || e.type === 'Passion');

  // techniques, both encodings (L5RData.techniques), with their category's base word
  const techniques = once('tech', () => D.techniques().map((t) => Object.assign({}, t, { base: norm(t.category || '').replace(/^(air|earth|fire|water|void) /, '').replace(/s$/, '') })));
  const techniqueNamed = (n) => techniques().find((t) => norm(t.name) === norm(n)) || null;

  // items: everything the books price with a Rarity
  function itemKind(e) {
    if (D.prop(e, 'Base Damage') || D.prop(e, 'Deadliness')) return 'weapon';
    if (D.prop(e, 'Physical Resistance') || D.prop(e, 'Supernatural Resistance')) return 'armor';
    return 'item';
  }
  const items = once('items', () => D.all().filter((e) => typeof D.val(e, 'Rarity') === 'number' && e.name).map((e) => ({ id: e.id, e, name: e.name, rarity: D.val(e, 'Rarity'), kind: itemKind(e), book: e.book, group: (D.entity(e.parent) || {}).name || '' })).sort((a, b) => a.name.localeCompare(b.name)));
  const itemNamed = (n) => { const k = norm(String(n).replace(/\s*\([^)]*\)\s*$/, '')); return items().find((i) => norm(i.name) === k || norm(i.name) === k.replace(/s$/, '')) || null; };
  const qualities = once('qual', () => { const q = D.all(['core']).find((e) => e.name === 'Item Quality'); return q ? D.children(q.id).map((c) => c.name) : []; });

  // Path of Waves' Table 2–1: Sample Pasts (a file-level TABLE), and Writ of the Wilds' pasts and
  // ninjō, which it prints as rules `past_01_06_spiritual_troubles "Spiritual Troubles: …"`
  function fileTable(bookId, name) {
    let out = null;
    const walk = (list) => (list || []).forEach((b) => {
      if (!b || out) return;
      if (b.kw === 'TABLE' && b.args && b.args[0] && b.args[0].s === name) out = b;
      else if (b.body) walk(b.body);
    });
    D.chapters(bookId).forEach((c) => walk(c.blocks));
    return out;
  }
  function rolled(mode, n) {
    if ((n === 5 || n === 6) && mode === 'pow') {
      const name = n === 5 ? 'Sample Pasts' : 'Sample Ninjō';
      const t = fileTable('path-of-waves', name);
      if (!t) return null;
      // `ROLL "d100"` then `"01-06" "Name" "Text"` rows: the parser keeps the rows as the ROLL
      // line's own arguments, so the strings are read from both places, in order
      const roll = (t.body || []).find((x) => x.kw === 'ROLL');
      const s = [].concat(roll ? roll.args.slice(1).filter((a) => 's' in a).map((a) => a.s) : [], (t.body || []).filter((x) => 's' in x).map((x) => x.s));
      const rows = [];
      for (let i = 0; i + 2 < s.length; i += 3) rows.push({ range: s[i], name: s[i + 1], text: s[i + 2] });
      return { die: roll && roll.args[0] ? roll.args[0].s : 'd100', rows, source: name };
    }
    if (mode === 'wow' && (n === 5 || n === 6)) {
      const q = questionSets().wow[n];
      const key = n === 5 ? 'past' : 'ninjo';
      const rows = ((q && q.rules) || []).map((r) => {
        const m = new RegExp('^' + key + '_(\\d+)_(\\d+)_').exec(r.id);
        if (!m) return null;
        const c = /^([^:]+):\s*([\s\S]*)$/.exec(r.text);
        return { range: m[1] + '-' + m[2], name: c ? c[1] : r.text, text: c ? c[2] : '' };
      }).filter(Boolean);
      return rows.length ? { die: 'd100', rows, source: 'Writ of the Wilds' } : null;
    }
    return null;
  }

  // ── rolling a printed range: "1", "2-3", "01-06" ──
  function span(range) {
    const m = /^\s*0*(\d+)\s*(?:[-–—]\s*0*(\d+))?\s*$/.exec(String(range || ''));
    return m ? [parseInt(m[1], 10), parseInt(m[2] || m[1], 10)] : null;
  }
  const dieSides = (die) => { const m = /d(\d+)/i.exec(String(die || '')); return m ? parseInt(m[1], 10) : 10; };
  function rollOn(rows, die, rangeOf) {
    const n = 1 + Math.floor(Math.random() * dieSides(die));
    return { n, row: rows.find((r) => { const s = span(rangeOf(r)); return s && n >= s[0] && n <= s[1]; }) || null };
  }

  // ── the heritage tables: every HERITAGE_TABLE, however its rows are encoded ──
  // A table's rows are `1 ^"Name" DEF { … }` inline (the core) or `2-3 #hash ^"Name" DEF { … }`,
  // which the build files as a range (2, -3) and then the entity.
  function heritageEntry(name, body, lo, hi, table) {
    const kw = (k) => (body || []).find((b) => b.kw === k);
    const mods = {};
    ((kw('MODIFIERS') || {}).body || []).forEach((p) => { const v = signed(p.value); if (p.name && v != null) mods[p.name] = v; });
    const effect = ((kw('EFFECT') || {}).body || []).map((x) => x.s).filter(Boolean);
    const st = kw('SUB_TABLE');
    const s = st ? (st.body || []).filter((x) => 's' in x).map((x) => x.s) : [];
    const sub = [];
    for (let i = 0; i + 1 < s.length; i += 2) sub.push({ range: s[i], text: s[i + 1] });
    const desc = (table.rules || []).map(rule).find((r) => r.text.indexOf(name + ':') === 0);
    return { name, range: hi && hi !== lo ? lo + '-' + hi : String(lo), mods, effect, die: st && st.args[0] ? st.args[0].s : null, sub, description: desc ? desc.text.slice(name.length + 1).trim() : null };
  }
  const heritageTables = once('her', () => D.all().filter((e) => D.block(e, 'HERITAGE_TABLE')).map((t) => {
    const rows = [];
    let lo = null;
    let hi = null;
    (D.block(t, 'HERITAGE_TABLE').body || []).forEach((x) => {
      if (x.num != null && x.def) { rows.push(heritageEntry(x.args[0] ? x.args[0].c : '', x.body, x.num, null, t)); lo = hi = null; return; }
      if (x.num != null && x.num < 0) { hi = -x.num; return; }
      if (x.num != null) { lo = x.num; hi = null; return; }
      if (x.ent) { const e = D.entity(x.ent); if (e) rows.push(heritageEntry(e.name, e.blocks, lo, hi, t)); lo = hi = null; }
    });
    // the table's own introduction, not one of its entries' descriptions
    const intro = (t.rules || []).map(rule).find((r) => /heritages?$/.test(r.id) && !rows.some((e) => r.text.indexOf(e.name + ':') === 0));
    return { id: t.id, name: t.name, book: t.book, entries: rows, intro: intro ? intro.text : null };
  }).filter((t) => t.entries.length > 1).sort((a, b) => (a.book === 'core' ? 0 : 1) - (b.book === 'core' ? 0 : 1)));
  const heritageTable = (id) => heritageTables().find((t) => t.id === id) || null;

  // How a SUB_TABLE range reads, per REQUIRES' `sub` (default "skill", proved per range).
  const MARTIAL = ['Martial Arts [Melee]', 'Martial Arts [Ranged]', 'Martial Arts [Unarmed]'];
  function asSkill(text) {
    let t = refText(String(text || '').trim()).replace(/\.$/, '');
    const m = /^Gain\s*\+\s*1\s+(.+)$/i.exec(t);
    if (m) t = m[1].trim();
    if (t === 'Martial Arts [Choose One]') return { kind: 'skill', prompt: 'Martial art', options: MARTIAL };
    return isSkill(t) ? { kind: 'skill', prompt: 'Skill', skill: t } : null;
  }
  const SUB_READERS = {
    skill: asSkill,
    peculiarity: (t) => ({ kind: 'peculiarity', prompt: 'Advantage', name: refText(t) }),
    item: (t) => ({ kind: 'item', prompt: 'Item', name: refText(t), custom: (RULES.CUSTOM_ITEMS || []).indexOf(refText(t)) !== -1 }),
    item_category: () => null, item_name: () => null, technique_category: () => null, ring: () => null,
  };
  const specFor = (table, entry) => ((RULES.REQUIRES || {})[table.name] || {})[entry.name] || {};
  function heirloomKind(text) {
    const h = (RULES.HEIRLOOM || []).find((x) => new RegExp(x[0], 'i').test(String(text || '').trim()));
    return h ? h[1] : { type: '' };
  }
  // A requirement read from the sub-roll can only be answered after the roll: the range's own
  // text is the category, the ring or the heirloom.
  function resolveReq(r, sub, key) {
    const out = Object.assign({}, r, { key });
    const text = sub ? refText(sub.text) : '';
    if (r.kind === 'pick_one') { out.options = r.options.map((o, i) => resolveReq(o, sub, key + '.p' + i)); return out; }
    if (!sub && (r.category_from_sub || r.ring_from_sub || r.name_from_sub || r.to === 'from_sub')) { out.waiting = true; return out; }
    if (r.category_from_sub && r.kind === 'technique') { out.category = norm(text).replace(/s$/, ''); out.categoryLabel = text; }
    if (r.category_from_sub && r.kind === 'item') { const h = heirloomKind(text); out.type = h.type; out.free = h.free; out.categoryLabel = text; }
    if (r.ring_from_sub) out.ring = cap(norm(text));
    if (r.name_from_sub) out.name = text + (r.name_suffix || '');
    if (r.to === 'from_sub') out.to = [cap(norm(text))];
    return out;
  }
  // everything a heritage result asks of the sheet: the entry's own requirements, then the
  // second roll's (a range that reads as a skill, a peculiarity or an item)
  function heritageRequirements(table, entry, sub) {
    if (!table || !entry) return [];
    const spec = specFor(table, entry);
    const reader = SUB_READERS[spec.sub || 'skill'];
    const base = 'h.' + norm(entry.name).replace(/[^a-z0-9]+/g, '-');
    const own = (spec.requires || []).map((r, i) => resolveReq(r, sub, base + '.' + i));
    const fromSub = sub && reader ? [reader(sub.text)].filter(Boolean).map((r, i) => resolveReq(r, sub, base + '.s' + i)) : [];
    return own.concat(fromSub);
  }

  // ── the draft ──
  function blank() {
    return {
      v: 2, mode: 'core', name: '', personal: '', concept: '',
      clan: null, family: null, region: null, upbringing: null, origin: null, school: null, role: null,
      choices: {}, standout: null, ring_reassign: [], outfit: {},
      bushido: { paramount: null, lesser: null, attitude: null, skill: null, item: null },
      pec: { distinction: null, adversity: null, passion: null, anxiety: null }, subjects: {},
      a: {}, people: [{ name: '', text: '' }], item: null,
      heritage: { table: null, entry: null, sub: null, rolls: [] },
    };
  }
  const chosen = (c, key) => ((c.choices || {})[key] || []).slice();

  // ── the character the answers make ──
  function compute(c) {
    const mode = c.mode || 'core';
    const rings = {};
    RINGS.forEach((r) => (rings[r] = baseRing()));
    const skills = {};
    let honor = 0;
    let glory = 0;
    let status = 0;
    const coins = { koku: 0, bu: 0, zeni: 0 };
    const pending = [];
    const from = { rings: {}, skills: {} };
    const credit = (kind, k, by, source) => { if (k && by) (from[kind][k] = from[kind][k] || []).push({ by, source }); };
    const addRing = (r, by, source) => { if (rings[r] != null) { rings[r] += by; credit('rings', r, by, source); } };
    const addSkill = (s, by, source) => { if (!s) return; skills[s] = (skills[s] || 0) + by; credit('skills', s, by, source); };
    // a set of increases: its fixed ranks, then each CHOOSE the player has answered
    function apply(inc, key, source, kind) {
      const add = kind === 'rings' ? addRing : addSkill;
      Object.keys(inc.fixed).forEach((k) => add(k, inc.fixed[k], source));
      inc.choose.forEach((ch, i) => {
        const k = key + '.' + i;
        if (ch.clan) {
          const pick = chosen(c, k)[0];
          if (pick === 'none' && ch.fallback) {
            const f = chosen(c, k + '.f').filter((o) => ch.fallback.of.indexOf(o) !== -1).slice(0, ch.fallback.n);
            f.forEach((o) => add(o, ch.fallback.by, source));
            if (f.length < ch.fallback.n) pending.push({ type: kind === 'rings' ? 'ring' : 'skill', source, n: ch.fallback.n - f.length, of: ch.fallback.of });
            return;
          }
          const cl = clans().find((x) => x.id === pick);
          if (!cl) { pending.push({ type: 'clan', source, what: ch.clan }); return; }
          const g = kind === 'rings' ? cl.rings : cl.skills;
          Object.keys(g.fixed).forEach((x) => add(x, g.fixed[x], source + ' (' + cl.name + ')'));
          return;
        }
        const picked = chosen(c, k).filter((o) => ch.of.indexOf(o) !== -1).slice(0, ch.n);
        picked.forEach((o) => add(o, ch.by, source));
        if (picked.length < ch.n) pending.push({ type: kind === 'rings' ? 'ring' : 'skill', source, n: ch.n - picked.length, of: ch.of });
      });
    }
    let clan = null;
    let fam = null;
    let region = null;
    let upb = null;
    if (mode === 'core') {
      clan = clans().find((x) => x.id === c.clan) || null;
      if (clan) { apply(clan.rings, 'clan.r', clan.name + ' Clan', 'rings'); apply(clan.skills, 'clan.s', clan.name + ' Clan', 'skills'); if (typeof clan.status === 'number') status = clan.status; }
      fam = families().find((x) => x.id === c.family) || null;
      if (fam) {
        apply(fam.rings, 'family.r', fam.name, 'rings');
        apply(fam.skills, 'family.s', fam.name, 'skills');
        if (typeof fam.glory === 'number') glory = fam.glory;
        addCoins(coins, fam.coins);
        fam.items.forEach((it) => pending.push({ type: 'item', name: it, source: fam.name }));
      }
    } else {
      region = regions().find((x) => x.id === c.region) || null;
      if (region) { apply(region.rings, 'region.r', region.name + ' region', 'rings'); apply(region.skills, 'region.s', region.name + ' region', 'skills'); if (typeof region.glory === 'number') glory = region.glory; }
      const ot = originTypes().find((t) => t.key === c.origin) || originTypes()[0];
      if (ot) status = ot.status;
      upb = upbringings().find((x) => x.id === c.upbringing) || null;
      if (upb) {
        apply(upb.rings, 'upb.r', upb.name + ' upbringing', 'rings');
        apply(upb.skills, 'upb.s', upb.name + ' upbringing', 'skills');
        // every negative Status Modification is printed "(minimum 0)" where the book says so
        if (upb.status != null) status = Math.max(0, status + upb.status);
        addCoins(coins, upb.coins);
      }
    }
    const school = schools().find((x) => x.id === c.school) || null;
    if (school) {
      apply(school.rings, 'school.r', school.name, 'rings');
      apply(school.skills, 'school.s', school.name, 'skills');
      if (typeof school.honor === 'number') honor = school.honor;
    }
    if (c.standout && rings[c.standout] != null) addRing(c.standout, 1, 'Question 4');
    const a = c.a || {};
    // question 7: the glory or the skill
    const q7 = question(mode, 7);
    if (a.q7 === 'glory') glory += (mode === 'core' ? amount(summaryRow(7), 'glory') : amount(((q7 && q7.options[0]) || {}).text, 'glory')) || 0;
    if (a.q7 === 'skill') addSkill(a.q7skill, 1, 'Question 7');
    // question 8: devoted (+honor), or a skill; Path of Waves adds an item
    if (c.bushido.attitude === 'honor') {
      const q8 = alt(mode, 8);
      honor += (q8 ? amount((q8.options.find((o) => /honor/i.test(o.text)) || {}).text, 'honor') : amount((walkthrough(8) || {}).text, 'honor')) || 0;
    }
    if (c.bushido.attitude === 'skill') addSkill(c.bushido.skill, 1, 'Question 8');
    if (a.q13 === 'dis') addSkill(a.q13skill, 1, 'Question 13');
    if (mode === 'core') addSkill(a.q17skill, 1, 'Question 17');
    else addSkill(a.q18skill, 1, 'Question 18');

    // question 18: the heritage — its modifiers, and whatever the result obliges
    const her = heritageGrants(c, skills);
    honor += her.social.Honor;
    glory += her.social.Glory;
    status += her.social.Status;
    if (her.koku !== 1) ['koku', 'bu', 'zeni'].forEach((k) => (coins[k] *= her.koku));
    Object.keys(her.skills).forEach((k) => addSkill(k, her.skills[k], 'Question 18'));
    her.swaps.forEach((sw) => {
      if (rings[sw.from] != null && rings[sw.to] != null && sw.from !== sw.to && rings[sw.from] > 1 && rings[sw.to] < (sw.cap || ringCap())) {
        addRing(sw.from, -1, 'Question 18');
        addRing(sw.to, 1, 'Question 18');
      } else pending.push({ type: 'swap', from: sw.from, to: sw.to });
    });
    // the creation cap, after every increase: each move takes a rank off a ring above the cap
    (c.ring_reassign || []).forEach((mv) => {
      if (rings[mv.from] == null || rings[mv.to] == null || mv.from === mv.to) return;
      if (rings[mv.from] <= ringCap() || rings[mv.to] >= ringCap()) return;
      addRing(mv.from, -1, 'over the creation cap');
      addRing(mv.to, 1, 'moved from ' + mv.from);
    });
    return { mode, rings, skills, honor, glory, status, coins, coinLabel: coinLabel(coins), pending, from, clan, family: fam, region, upbringing: upb, school, heritage: her };
  }

  // what the heritage result puts on the sheet, from the entry plus the answers — nothing stored
  function heritageState(c) {
    const h = c.heritage || {};
    const table = heritageTable(h.table);
    const entry = table && table.entries.find((e) => e.name === h.entry) || null;
    const sub = entry && entry.sub.find((s) => s.range === h.sub) || null;
    return { table, entry, sub, reqs: heritageRequirements(table, entry, sub) };
  }
  const pick1 = (c, key) => chosen(c, key)[0] || null;
  function reqOpen(c, r) {
    if (r.waiting) return true;
    switch (r.kind) {
      case 'skill': return !r.skill && !pick1(c, r.key);
      case 'technique': return !pick1(c, r.key);
      case 'peculiarity':
        if (r.options) return !pick1(c, r.key);
        if (r.subject_options || r.subject_free) return !pick1(c, r.key + '.subject');
        return false;
      case 'item':
        if (r.name) return false;
        return !pick1(c, r.key + '.item') || (!!r.qualities && !pick1(c, r.key + '.quality'));
      case 'ring_swap':
        return r.optional ? false : !(pick1(c, r.key + '.from') && pick1(c, r.key + '.to'));
      case 'pick_one': {
        const p = pick1(c, r.key + '.pick');
        return p == null ? true : reqOpen(c, r.options[Number(p)]);
      }
      default: return false;
    }
  }
  function heritageOpen(c) {
    const st = heritageState(c);
    const out = st.reqs.filter((r) => reqOpen(c, r));
    if (st.entry && st.entry.sub.length && !st.sub) out.unshift({ kind: 'sub_roll', prompt: 'Second roll' });
    return out;
  }
  function heritageGrants(c) {
    const out = { skills: {}, swaps: [], techniques: [], peculiarities: [], gear: [], koku: 1, social: { Honor: 0, Glory: 0, Status: 0 } };
    if ((c.mode || 'core') !== 'core') return out;
    const st = heritageState(c);
    if (!st.entry) return out;
    Object.keys(st.entry.mods).forEach((k) => { if (out.social[k] != null) out.social[k] += st.entry.mods[k]; });
    function fold(r) {
      if (r.waiting) return;
      if (r.kind === 'pick_one') { const p = pick1(c, r.key + '.pick'); if (p != null) fold(r.options[Number(p)]); return; }
      if (r.kind === 'skill') { const s = r.skill || pick1(c, r.key); if (s) out.skills[s] = (out.skills[s] || 0) + 1; return; }
      if (r.kind === 'technique') { const t = pick1(c, r.key); if (t) out.techniques.push(t); return; }
      if (r.kind === 'peculiarity') {
        const n = r.options ? pick1(c, r.key) : r.name;
        if (!n) return;
        const subject = r.subject || pick1(c, r.key + '.subject');
        out.peculiarities.push({ name: n, subject: subject || null, source: 'Question 18' });
        return;
      }
      if (r.kind === 'item') {
        const n = r.name || pick1(c, r.key + '.item');
        if (!n) return;
        const note = [];
        if (r.define) note.push(r.define);
        if (r.held === false) note.push('lost — it exists somewhere in the world');
        if (r.heirloom) note.push(r.heirloom + ' heirloom');
        const q = pick1(c, r.key + '.quality');
        const gq = pick1(c, r.key + '.gm_quality');
        if (q) note.push('quality chosen by the player: ' + q);
        if (gq) note.push('quality chosen by the GM: ' + gq);
        out.gear.push({ name: n, note: note.join('; '), held: r.held !== false, open: reqOpen(c, r) });
        return;
      }
      if (r.kind === 'ring_swap') { const f = pick1(c, r.key + '.from'); const t = pick1(c, r.key + '.to'); if (f && t) out.swaps.push({ from: f, to: t, cap: r.cap }); return; }
      if (r.kind === 'money' && r.koku === 'double') out.koku = 2;
    }
    st.reqs.forEach(fold);
    return out;
  }

  // ── the outfit: printed with choices in it; a character owns things, not choices ──
  const OUTFIT_OPEN = /\bor\b|\brarity\b|\b(any|one)\s+(weapon|item|trinket)\b/i;
  function outfitItems(s) { return String(s).replace(/\([^)]*\)/g, '').split(/\s+and\s+/i).map((x) => x.trim()).filter(Boolean); }
  function outfitOffer(line) {
    const s = String(line);
    const m = /^(?:any\s+)?(one|two|three|\d+)\s+(weapon|item|trinket|armor)s?\s+of\s+rarity\s+(\d+)\s+or\s+lower/i.exec(s);
    if (m) return { kind: 'pick', count: WORDS[m[1].toLowerCase()] || Number(m[1]), rarity: Number(m[3]), type: m[2].toLowerCase() === 'trinket' ? 'item' : m[2].toLowerCase() };
    const d = /^daish[ōo]\s*\(([^)]*)\)/i.exec(s);
    if (d) {
      const parts = d[1].split(',').map((x) => x.trim());
      const alts = parts[0].split(/\s+or\s+/i).map((x) => x.trim());
      if (alts.length > 1) return { kind: 'either', options: alts.map((x) => [x].concat(parts.slice(1))) };
    }
    if (/\bor\b/i.test(s)) {
      const sides = s.replace(/\([^)]*\)/g, '').split(/\s+or\s+/i);
      if (sides.length >= 2) return { kind: 'either', options: sides.map(outfitItems) };
    }
    return { kind: 'free' };
  }
  function outfitLines(c, d) {
    const out = [];
    if (d.school) d.school.outfit.forEach((it) => out.push({ name: it, source: d.school.name + ' outfit', open: OUTFIT_OPEN.test(it) }));
    const up = d.upbringing;
    if (up) up.items.forEach((it) => out.push({ name: it, source: up.name + ' upbringing', open: false }));
    if (d.family) d.family.items.forEach((it) => out.push({ name: it, source: d.family.name, open: false }));
    return out;
  }
  function gear(c, d) {
    const out = [];
    const ch = c.outfit || {};
    outfitLines(c, d).forEach((g) => {
      if (g.open && ch[g.name] && ch[g.name].length) ch[g.name].forEach((it) => out.push({ name: it, note: g.source, from: g.name }));
      else out.push({ name: g.name, note: g.source, open: g.open });
    });
    const a = c.a || {};
    if (a.accName || a.acc) out.push({ name: a.accName || a.acc, note: a.accName ? a.acc : 'the accoutrement (question 14)' });
    if (a.prized) out.push({ name: a.prized, note: 'prized possession (question 14)' });
    if (c.bushido.item) out.push({ name: c.bushido.item, note: 'question 8' });
    if (c.item) out.push({ name: c.item, note: 'question 16' });
    d.heritage.gear.forEach((g) => out.push({ name: g.name, note: g.note, open: g.open, lost: !g.held }));
    return out;
  }
  const outfitOpen = (c, d) => outfitLines(c, d).filter((g) => g.open && !((c.outfit || {})[g.name] || []).length);

  // the school's starting techniques as picked, and the heritage's
  function techniqueList(c, d) {
    const out = [];
    if (d.school) d.school.techniques.forEach((t, i) => {
      if (t.fixed) out.push({ name: t.fixed, kind: t.kind, source: d.school.name });
      else chosen(c, 'school.t.' + i).filter((o) => t.of.indexOf(o) !== -1).slice(0, t.n).forEach((n) => out.push({ name: n, kind: t.kind, source: d.school.name }));
    });
    d.heritage.techniques.forEach((n) => out.push({ name: n, source: 'Question 18' }));
    return out;
  }
  // advantages and disadvantages held, with the question that granted each
  function peculiarityList(c, d) {
    const out = [];
    const add = (id, source) => { const e = id && D.entity(id); if (e) out.push({ id, name: e.name, e, kind: kindOf(e), adv: isAdvantage(e), source, subject: (c.subjects || {})[id] || null }); };
    add(c.pec.distinction, 'Question 9');
    add(c.pec.adversity, 'Question 10');
    add(c.pec.passion, 'Question 11');
    add(c.pec.anxiety, 'Question 12');
    add((c.a || {}).q13pick, 'Question 13');
    d.heritage.peculiarities.forEach((p) => {
      const e = peculiarityNamed(p.name);
      out.push({ id: e ? e.id : null, name: e ? e.name : p.name, e, kind: e ? kindOf(e) : null, adv: e ? isAdvantage(e) : true, source: p.source, subject: p.subject });
    });
    return out;
  }
  const withSubject = (name, subject) => (subject ? name.replace(/\s*\[[^\]]*\]/, ' ' + subject) : name);

  // ── the character file (system/l5r5e/sheet.js reads it) ──
  function toSheet(c) {
    const d = compute(c);
    const v = Sheet().blank();
    const mode = d.mode;
    v.Rings = Object.assign({}, d.rings);
    v.Skills = {};
    Object.keys(d.skills).forEach((k) => { if (d.skills[k]) v.Skills[k] = d.skills[k]; });
    if (d.clan) v.Clan = d.clan.name;
    if (d.family) v.Family = d.family.name;
    if (d.region) v.Region = d.region.name;
    if (d.upbringing) v.Upbringing = d.upbringing.name;
    if (mode !== 'core') { const ot = originTypes().find((t) => t.key === c.origin) || originTypes()[0]; if (ot) v.Clan = v.Clan || ot.label; }
    if (d.school) {
      v.School = d.school.name;
      v['School Rank'] = 1;
      v.Roles = c.role ? [c.role] : d.school.roles.slice();
      if (d.school.ability) v['School Ability'] = d.school.ability;
    }
    v.Honor = d.honor;
    v.Glory = d.glory;
    v.Status = d.status;
    v.Wealth = d.coinLabel !== '—' ? d.coinLabel : '';
    v.Techniques = techniqueList(c, d).map((t) => t.name);
    const pecs = peculiarityList(c, d);
    v.Advantages = pecs.filter((p) => p.adv).map((p) => withSubject(p.name, p.subject));
    v.Disadvantages = pecs.filter((p) => !p.adv).map((p) => withSubject(p.name, p.subject));
    v.Equipment = gear(c, d).map((g) => g.name + (g.lost ? ' (lost)' : ''));
    const a = c.a || {};
    v.Giri = mode === 'core' ? a.giri || '' : a.past || '';
    if (mode !== 'core' && a.pastName) v.Past = a.pastName;
    v['Ninjō'] = a.ninjo || '';
    v.Bushido = { 'Paramount Tenet': c.bushido.paramount || '', 'Less Significant Tenet': c.bushido.lesser || '' };
    if (d.heritage && c.heritage && c.heritage.entry && mode === 'core') {
      const st = heritageState(c);
      v.Heritage = c.heritage.entry + (st.sub ? ' — ' + refText(st.sub.text) : '');
    }
    const personal = (c.personal || '').trim();
    const fam = mode === 'core' && d.family ? d.family.name : '';
    v.Name = (c.name || '').trim() || (personal ? [fam, personal].filter(Boolean).join(' ') : '');
    // the narrative answers travel as fields named by their questions
    const words = { 4: a.standout, 5: mode === 'core' ? a.giri : a.past, 6: a.ninjo, 7: a.q7text, 9: a.accomplishment, 10: a.challenge, 11: a.peace, 12: a.fear,
      13: [a.mentor, a.mentorText].filter(Boolean).join(' — '), 14: mode === 'core' ? [a.impression, [a.accName, a.acc].filter(Boolean).join('. ')].filter(Boolean).join(' · ') : a.prizedText,
      15: a.stress, 16: (c.people || []).filter((p) => p.name || p.text).map((p) => [p.name, p.text].filter(Boolean).join(': ')).join(' · '),
      17: mode === 'core' ? a.parent : [a.q17prompt, a.group].filter(Boolean).join(' — '), 18: mode === 'core' ? a.heritageText : a.raised, 20: a.death };
    Object.keys(words).forEach((n) => { const q = question(mode, +n); if (q && words[n]) v[q.text] = words[n]; });
    return v;
  }

  return {
    RINGS, MODES, norm, refText, rule, reset, question, alt, hasRule, questionSets, summaryRow, walkthrough, amount, listedSkills,
    skillNames, skillGroups, isSkill, limit, ringCap, skillCap, originTypes, increases, label, coinLabel,
    clans, families, familiesOf, schools, regions, upbringings, originSet, tenets, clanViews,
    peculiarities, peculiarityNamed, kindOf, isAdvantage, PEC, techniques, techniqueNamed, items, itemNamed, qualities, rolled, span, rollOn,
    heritageTables, heritageTable, heritageState, heritageOpen, reqOpen, heirloomKind, asSkill, specFor,
    blank, chosen, compute, outfitLines, outfitOffer, outfitOpen, gear, techniqueList, peculiarityList, withSubject, toSheet,
  };
})();
