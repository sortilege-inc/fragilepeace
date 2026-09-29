// system/l5r5e/dice.js — Roll & Keep, read from the corpus.
//
// The dice are the corpus's: `^"Ring Die"` and `^"Skill Die"` print their FACES (6 and 12
// numbered rows, each face a run of symbols — "(op) (st)"), `^"Dice Symbols"` prints the four
// symbols and the RESOLUTION_ORDER, `^"Check"` prints the six STEPS (the book's Summary of a Check, p. 23), `^"Target Number"` the
// DIFFICULTY_SCALE. Nothing about a face is typed here; the numbers the rules state only in
// prose are named constants below, each citing its sentence.
//
// A roll is a state the player acts on, as at the table: roll the pool (step 3), apply the
// advantages and disadvantages that reroll dice (step 4), choose kept dice up to the limit
// (step 5) — nothing is ever kept for the player — roll a bonus die for each kept (ex), then
// resolve (step 6), receiving the strife the player settles on. Every die first rolled, every
// reroll and explosion is carried into the log with the roll.
// The art is the owner's (assets/art/dice), one face per symbol run: ring_ot is a Ring die
// showing (op) (st).
window.L5RDice = (function () {
  const D = window.L5RData;
  const { el, esc } = window.VttRender;

  // ── the numbers the rules state only in prose, each citing the corpus's own sentence ──
  // "The player must choose at least one die to keep, and can choose to keep a maximum up to the
  //  value of the ring the character used for the check." — Check, RULES keep_limit_equals_ring_value
  //  (Step 5: Choose Kept Dice, p. 24)
  const KEEP_LIMIT_IS_RING = true;
  // "a character may spend 1 Void point to roll one additional Ring die (ring) and subsequently
  //  keep one additional die during Step 5: Choose Kept Dice." — Void Points, USES: Seize the Moment
  const SEIZE_THE_MOMENT = { extraRingDice: 1, extraKept: 1, cost: 1 };
  // "For each (ex) symbol, the player rolls one additional die of the same type as the one
  //  containing the (ex) symbol. After rolling a die this way, the player chooses whether it will
  //  be kept (on top of their current results) or dropped." — Dice Symbols, RULES (ex) (p. 24)
  const EXPLOSION = { sameType: true, keptApart: true };
  // No default: "Finally, the GM selects a target number of successes (commonly referred to as a
  // TN)." — Target Number, RULES gm_sets_target_number (Step 2, p. 22). The corpus once carried a
  // rule "default_tn_is_two"; the book has no such rule (TN 2 is only "An average task" among the
  // sample TNs), and it was removed. Until a TN is chosen, the roller shows "TN ?".
  const DEFAULT_TN = null;
  // "…the character making the check rolls one additional (skill) per assisting character who has
  //  1 or more ranks of the skill in use, and one additional (ring) per assisting character who has
  //  0 ranks in the skill in use." — Assistance, RULES helper_rolls_skill_or_ring_die; "Then, during
  //  Step 5: Choose Kept Dice, a character making a check with assistance may keep up to 1
  //  additional die per assisting character." — main_keeps_plus_one_per_helper (p. 26)
  const ASSISTANCE = { skilled: 'skill', unskilled: 'ring', extraKeptEach: 1 };
  // Rerolls happen at Step 4, before any die is kept: "Modify Rolled Dice: The GM and player apply
  // any effects that modify the dice, such as advantages and disadvantages that cause rerolls." —
  // Check, STEPS 4. "Each advantage and disadvantage can be applied only once per check by any
  // character." — Advantage, RULES each_applies_once_per_check. How many dice each rerolls is
  // read from its rule (rerollRule below), not typed here.

  const SYMBOLS = ['ex', 'su', 'op', 'st'];
  const TYPES = { ring: 'Ring Die', skill: 'Skill Die' };

  // ── the faces, read from the corpus ──
  let faceCache = null;
  function faces() {
    if (faceCache) return faceCache;
    const out = {};
    Object.keys(TYPES).forEach((t) => {
      const e = D.named(TYPES[t], 'core');
      const fb = e && D.block(e, 'FACES');
      out[t] = (fb ? fb.body || [] : []).filter((r) => 'num' in r).map((r) => {
        const txt = r.args[0] ? r.args[0].s : '';
        const sym = { ex: 0, su: 0, op: 0, st: 0 };
        (txt.match(/\((ex|su|op|st)\)/g) || []).forEach((m) => sym[m.slice(1, 3)]++);
        const code = SYMBOLS.filter((k) => sym[k]).map((k) => ({ ex: 'e', su: 's', op: 'o', st: 't' }[k])).join('');
        return { num: r.num, text: txt, sym, key: t + '_' + (code || 'blank') };
      });
    });
    if (out.ring.length && out.skill.length) faceCache = out;
    return out;
  }
  // the symbols the corpus names, and their definitions, verbatim
  function symbolDefs() {
    const e = D.named('Dice Symbols', 'core');
    const b = e && D.block(e, 'SYMBOL_DEFINITIONS');
    return b ? (b.body || []).filter((p) => p.name).map((p) => ({ name: p.name, text: p.value })) : [];
  }
  function resolutionOrder() {
    const e = D.named('Dice Symbols', 'core');
    const b = e && D.block(e, 'RESOLUTION_ORDER');
    return b && b.args[0] && b.args[0].l ? b.args[0].l.map((a) => a.s) : [];
  }
  function checkSteps() {
    const e = D.named('Check', 'core');
    const b = e && D.block(e, 'STEPS');
    return b ? (b.body || []).filter((r) => 'num' in r).map((r) => ({ n: r.num, text: r.args[0] ? r.args[0].s : '' })) : [];
  }
  function difficulty() {
    const e = D.named('Target Number', 'core');
    const b = e && D.block(e, 'DIFFICULTY_SCALE');
    return b ? (b.body || []).filter((r) => 'num' in r).map((r) => ({ tn: r.num, text: r.args[0] ? r.args[0].s : '' })) : [];
  }

  // a core rule by its slug, as the book prints it — "Distinction: The player chooses up to 2 dice
  // to reroll." (Advantage, RULES distinction_reroll_two_dice)
  const ruleCache = {};
  function rule(slug) {
    if (ruleCache[slug]) return ruleCache[slug];
    let hit = null;
    D.all(['core']).some((e) => (e.rules || []).some((r) => {
      if (String(r.text).split(/\s/)[0] !== slug) return false;
      hit = { text: window.L5REntity.ruleText(r.text), entity: e.name, id: r.id };
      return true;
    }));
    if (hit) ruleCache[slug] = hit;
    return hit;
  }
  // the number of dice a distinction or an adversity rerolls, from its rule: "up to 2 dice",
  // "must choose 2 dice with results containing (su) or (ex) symbols"
  const REROLL_RULES = { distinction: 'distinction_reroll_two_dice', adversity: 'adversity_effect' };
  function rerollRule(kind) {
    const r = rule(REROLL_RULES[kind]);
    const m = r && r.text && /(\d+) dice/.exec(r.text);
    return m ? { dice: parseInt(m[1], 10), text: r.text } : null;
  }

  const rand = (n) => Math.floor(Math.random() * n);
  function rollDie(type, bonus) {
    const f = faces()[type];
    const face = f[rand(f.length)];
    return { id: Math.random().toString(36).slice(2, 9), type, face: face.num, key: face.key, sym: Object.assign({}, face.sym), text: face.text, kept: false, bonus: !!bonus, exploded: false };
  }

  // ── a roll ──
  // opts: { ring (name), ringValue, skill (name|null), skillRank, tn, void, assistSkilled,
  //         assistUnskilled, concealed, label, source, note }
  function roll(opts) {
    const o = Object.assign({ ringValue: 1, skillRank: 0, tn: DEFAULT_TN, void: false, assistSkilled: 0, assistUnskilled: 0 }, opts || {});
    const ringDice = o.ringValue + (o.void ? SEIZE_THE_MOMENT.extraRingDice : 0) + (ASSISTANCE.unskilled === 'ring' ? o.assistUnskilled : 0);
    const skillDice = o.skillRank + (ASSISTANCE.skilled === 'skill' ? o.assistSkilled : 0);
    const dice = [];
    for (let i = 0; i < ringDice; i++) dice.push(rollDie('ring'));
    for (let i = 0; i < skillDice; i++) dice.push(rollDie('skill'));
    return { opts: o, dice, limit: keepLimit(o), resolved: null, strife: null, at: new Date().toISOString(),
      initial: dice.map((d) => d.key), events: [], applied: [] };
  }
  const keepLimit = (o) => (KEEP_LIMIT_IS_RING ? o.ringValue : 0) + (o.void ? SEIZE_THE_MOMENT.extraKept : 0)
    + ((o.assistSkilled || 0) + (o.assistUnskilled || 0)) * ASSISTANCE.extraKeptEach;
  const keptBase = (r) => r.dice.filter((d) => d.kept && !d.bonus).length;
  const successDie = (d) => d.sym.su + d.sym.ex > 0;
  const anyKept = (r) => r.dice.some((d) => d.kept);
  function toggleKeep(r, id) {
    const d = r.dice.find((x) => x.id === id);
    if (!d || r.resolved) return false;
    if (d.kept) {
      if (d.exploded) return false;              // its bonus die is already rolled
      d.kept = false;
      return true;
    }
    if (!d.bonus && keptBase(r) >= r.limit) return false;
    d.kept = true;
    return true;
  }
  // a kept (ex) rolls one more die of its type, which may itself be kept or dropped
  function explode(r, id) {
    const d = r.dice.find((x) => x.id === id);
    if (!d || !d.kept || !d.sym.ex || d.exploded || r.resolved) return null;
    d.exploded = true;
    const nd = rollDie(d.type, true);
    nd.from = d.id;
    r.dice.splice(r.dice.indexOf(d) + 1 + r.dice.filter((x) => x.from === d.id).length, 0, nd);
    r.events.push({ kind: 'explode', type: d.type, from: d.key, to: nd.key });
    return nd;
  }
  // A reroll mode: { id, label, kind: 'distinction' | 'adversity' | 'other', dice, text }.
  // An adversity must reroll that many dice showing (su) or (ex) — all of them, if fewer show.
  const rerollNeed = (r, mode) => (mode.kind === 'adversity' ? Math.min(mode.dice, r.dice.filter((d) => !d.bonus && successDie(d)).length) : 0);
  function canMark(r, mode, d) {
    if (r.resolved || anyKept(r) || d.bonus) return false;
    if (mode.kind === 'adversity' && !successDie(d)) return false;
    return true;
  }
  const applied = (r, mode) => r.applied.some((a) => a.id === mode.id);
  function reroll(r, ids, mode) {
    if (r.resolved || anyKept(r) || !ids.length) return false;
    if (mode.kind !== 'other' && applied(r, mode)) return false;
    const dice = ids.map((id) => r.dice.find((x) => x.id === id)).filter((d) => d && canMark(r, mode, d));
    if (mode.kind === 'adversity' ? dice.length !== rerollNeed(r, mode) : mode.dice != null && dice.length > mode.dice) return false;
    dice.forEach((d) => {
      const nd = rollDie(d.type);
      r.events.push({ kind: 'reroll', type: d.type, from: d.key, to: nd.key, via: mode.label });
      Object.assign(d, { face: nd.face, key: nd.key, sym: nd.sym, text: nd.text });
    });
    if (mode.kind !== 'other') r.applied.push({ id: mode.id, label: mode.label, kind: mode.kind });
    return true;
  }
  // Step 6: the kept dice's symbols, in the corpus's order
  function tally(r) {
    const t = { ex: 0, su: 0, op: 0, st: 0 };
    r.dice.filter((d) => d.kept).forEach((d) => SYMBOLS.forEach((k) => (t[k] += d.sym[k])));
    const successes = t.su + t.ex;                // "(ex) Counts as (su)"
    const tn = r.opts.tn;
    return { symbols: t, successes, opportunity: t.op, strife: t.st, tn, success: tn == null ? null : successes >= tn, bonus: tn == null ? null : Math.max(0, successes - tn), unexploded: r.dice.filter((d) => d.kept && d.sym.ex && !d.exploded).length };
  }
  // Bonus successes an ability adds to a check that succeeds ("if you succeed, add additional
  // bonus successes equal to your school rank") — [{ successes, label }], from the roller's owner
  function withExtra(t, extra) {
    const n = (extra || []).reduce((a, x) => a + (x.successes || 0), 0);
    if (!n) return t;
    return Object.assign({}, t, { successes: t.successes + n, bonus: t.bonus == null ? null : t.bonus + n, extra: extra });
  }
  // `strife`: what the character receives — the kept (st) unless the player and GM settle on less
  function resolve(r, strife, extra) {
    r.extra = extra || [];
    r.resolved = withExtra(tally(r), r.extra);
    r.strife = strife == null ? r.resolved.strife : Math.max(0, Math.min(r.resolved.strife, strife));
    return r.resolved;
  }

  // ── the look ──
  const artBase = () => (document.querySelector('base') ? '' : '') + 'assets/art/';
  function faceImg(d, cls) {
    return el('img', { class: 'face ' + (cls || ''), src: artBase() + 'dice/' + d.key + '.svg', alt: d.text || 'blank', title: (d.type === 'ring' ? 'Ring die: ' : 'Skill die: ') + (d.text || 'Blank') });
  }
  // (op) (su) (ex) (st) (ring) (skill), a lowercase ring (air)…(void), a technique mark (kata)
  const GLYPH = { op: '◈', su: '❁', ex: '❉', st: '▲' };
  const RINGS = ['air', 'earth', 'fire', 'water', 'void'];
  function symbolsHtml(escaped) {
    return escaped
      .replace(/\((op|su|ex|st)\)/g, (m, k) => '<span class="sym ' + k + '" title="' + m + '">' + GLYPH[k] + '</span>')
      .replace(/\((air|earth|fire|water|void)\)/g, (m, r) => '<img class="ring-ico" src="' + artBase() + 'rings/' + r + '.svg" alt="' + m + '" title="' + m + '">')
      .replace(/\((ring|skill)\)/g, (m, k) => '<span class="sym die-' + k + '" title="' + m + '">' + (k === 'ring' ? '⬢' : '⬟') + '</span>')
      .replace(/\((kata|kiho|kihō|shuji|shūji|invocation|ritual|maho|mahō|ninjutsu|mantra)\)/g, (m, k) => '<span class="sym tech" title="' + m + '">' + k + '</span>');
  }
  const ringIcon = (ring, cls) => el('img', { class: 'ring-ico ' + (cls || ''), src: artBase() + 'rings/' + String(ring).toLowerCase() + '.svg', alt: ring, title: ring });

  function summary(t) {
    const bits = [];
    bits.push(t.successes + (t.successes === 1 ? ' success' : ' successes'));
    if (t.opportunity) bits.push(t.opportunity + ' opportunity');
    if (t.strife) bits.push(t.strife + ' strife');
    let verdict = '';
    if (t.success === true) verdict = 'succeeds' + (t.bonus ? ' with ' + t.bonus + ' bonus success' + (t.bonus === 1 ? '' : 'es') : '');
    else if (t.success === false) verdict = 'fails by ' + (t.tn - t.successes);
    return { text: bits.join(' · '), verdict };
  }

  // A roller: the controls, the tray, the result. `opts.onResolve(roll)` logs it; `opts.preset`
  // fills ring / values / skill (a sheet's or an NPC's); `opts.fixed` hides the value inputs.
  // A character's roller also takes `opts.rerolls(ring)` — the reroll modes its advantages and
  // disadvantages give on a check of that ring — `opts.onConceal()` when the GM conceals the TN,
  // `opts.onAdversityFailed(roll, applied)` for an adversity on a check whose TN was never set,
  // `opts.strifeDefault(tally)` for the strife a kept (st) gives (a stance may change it), and
  // `opts.extra(roll, tally)` for bonus successes an ability adds to a successful check. A check
  // set up from a technique carries it as `source` (its name, id and category) into the log.
  // `opts.notes(roll, tally)` → lines shown under the tally and logged with the check (a Strike's
  // damage, an initiative value, a critical strike's severity); `opts.opportunities(roll)` → the
  // spends the check's (op) may buy, [{ group, text }], shown once (op) is kept, ticked to log.
  // A set-up may carry a `tag` ({ kind: 'strike' | 'initiative' | 'crit', … }) for those two.
  const OTHER = { id: 'other', label: 'Other reroll', kind: 'other', dice: null, text: 'A reroll a technique, an ability or the GM grants: mark the dice it names.' };
  // − value + for a number input the page keeps (hidden) as the value's home: a phone's player
  // taps, never types a number
  function stepper(inp, min, max, label) {
    const out = el('b', { class: 'step-v' }, [String(inp.value || min)]);
    const go = (d) => {
      const n = Math.max(min, Math.min(max, (parseInt(inp.value || String(min), 10) || min) + d));
      inp.value = n; out.textContent = String(n);
      inp.dispatchEvent(new Event('input', { bubbles: true }));
    };
    inp.hidden = true;
    return el('span', { class: 'stepper' }, [label ? el('span', { class: 'step-k' }, [label]) : null,
      el('button', { class: 'step', type: 'button', 'aria-label': 'less', onclick: () => go(-1) }, ['−']), out,
      el('button', { class: 'step', type: 'button', 'aria-label': 'more', onclick: () => go(1) }, ['+']), inp]);
  }
  // a checkbox shown as a button that is on or off
  function toggle(box, label) {
    box.hidden = true;
    const b = el('button', { class: 'toggle' + (box.checked ? ' on' : ''), type: 'button', 'aria-pressed': box.checked ? 'true' : 'false', onclick: () => {
      box.checked = !box.checked;
      box.dispatchEvent(new Event('change', { bubbles: true }));
      b.classList.toggle('on', box.checked); b.setAttribute('aria-pressed', box.checked ? 'true' : 'false');
    } }, [label]);
    b.sync = () => { b.classList.toggle('on', box.checked); b.setAttribute('aria-pressed', box.checked ? 'true' : 'false'); };
    return el('span', {}, [b, box]);
  }

  function roller(opts) {
    const o = opts || {};
    const compact = !!o.compact;   // the player's page: taps, not typed numbers; no explanations
    const p = Object.assign({ ring: 'Air', ringValue: 2, skill: null, skillRank: 1, tn: DEFAULT_TN, void: false }, o.preset || {});
    let current = null;
    let mode = null;            // the reroll being marked
    let marks = [];
    let concealGranted = false; // the Void point a concealed TN gives, once per roll set up
    const box = el('div', { class: 'roller' });
    const tray = el('div', { class: 'tray' });
    const rerollBar = el('div', { class: 'reroll-bar' });
    const result = el('div', { class: 'roll-result' });
    const ringPick = el('div', { class: 'ring-pick' });
    const ringValue = el('input', { class: 'text num small', type: 'number', min: 1, max: 5, value: p.ringValue, title: 'Ring value' });
    const skillRank = el('input', { class: 'text num small', type: 'number', min: 0, max: 5, value: p.skillRank, title: 'Skill ranks' });
    const tn = el('select', { class: 'scope tiny', title: 'Target number' });
    tn.appendChild(el('option', { value: '' }, ['TN ?']));
    difficulty().forEach((d) => tn.appendChild(el('option', { value: d.tn, title: d.text, selected: d.tn === p.tn || null }, ['TN ' + d.tn])));
    const voidBox = el('input', { type: 'checkbox', checked: p.void || null });
    const assistSkilled = el('input', { class: 'text num small', type: 'number', min: 0, max: 9, value: 0, title: 'Assisting characters with 1 or more ranks in the skill: each adds a Skill die and a kept die' });
    const assistUnskilled = el('input', { class: 'text num small', type: 'number', min: 0, max: 9, value: 0, title: 'Assisting characters with 0 ranks in the skill: each adds a Ring die and a kept die' });
    const concealBox = el('input', { type: 'checkbox' });
    const note = el('input', { class: 'text small note', type: 'text', placeholder: 'what this check is for…' });
    concealBox.addEventListener('change', () => {
      if (concealBox.checked && !concealGranted && o.onConceal) {
        concealGranted = true;
        o.onConceal();
      }
    });
    function drawRings() {
      ringPick.innerHTML = '';
      ['Air', 'Earth', 'Fire', 'Water', 'Void'].forEach((r) => {
        ringPick.appendChild(el('button', { class: 'ring-btn' + (p.ring === r ? ' on' : ''), type: 'button', title: r, onclick: () => {
          p.ring = r;
          if (o.ringsOf) ringValue.value = o.ringsOf(r);
          drawRings();
          if (compact) drawDice();
        } }, [ringIcon(r), el('span', {}, [r])]));
      });
    }
    const int = (inp, min) => Math.max(min, parseInt(inp.value || String(min), 10) || min);
    function values() {
      return { ring: p.ring, ringValue: int(ringValue, 1), skill: p.skill, skillRank: int(skillRank, 0), tn: tn.value === '' ? null : parseInt(tn.value, 10), void: voidBox.checked,
        assistSkilled: int(assistSkilled, 0), assistUnskilled: int(assistUnskilled, 0), concealed: concealBox.checked, label: o.label || null,
        source: p.source || null, sourceId: p.sourceId || null, sourceType: p.sourceType || null, tag: p.tag || null };
    }
    const modes = () => (o.rerolls ? o.rerolls(current ? current.opts.ring : p.ring) : []).concat([OTHER]);
    function drawRerolls() {
      rerollBar.innerHTML = '';
      const r = current;
      if (!r || r.resolved || anyKept(r)) return;
      // a disadvantage whose ring is the check's: the table's call, prompted, never applied for it
      if (!r.dismissed) r.dismissed = [];
      modes().filter((m) => m.prompt && !applied(r, m) && r.dismissed.indexOf(m.id) === -1).forEach((m) => rerollBar.appendChild(el('div', { class: 'chiprow tight prompt' }, [
        el('span', { class: 'small' }, ['⚠ ', symbolsSpan(m.label), ' — its ring is this check’s: does it apply? The GM’s call.']),
        el('button', { class: 'btn tiny', type: 'button', onclick: () => { mode = m; marks = []; drawTray(); } }, ['Apply']),
        el('button', { class: 'btn ghost tiny', type: 'button', onclick: () => { r.dismissed.push(m.id); r.events.push({ kind: 'dismissed', via: m.label }); drawTray(); } }, ['Dismiss']),
      ])));
      rerollBar.appendChild(el('div', { class: 'chiprow tight' }, [el('span', { class: 'tray-k' }, ['Reroll']), modes().map((m) => {
        const used = m.kind !== 'other' && applied(r, m);
        return el('button', { class: 'btn ghost tiny rr ' + m.kind + (mode && mode.id === m.id ? ' on' : ''), type: 'button', disabled: used || null,
          title: (m.text || '') + (used ? ' — applied on this check' : ''), onclick: () => { mode = mode && mode.id === m.id ? null : m; marks = []; drawTray(); } },
        [symbolsSpan(m.label), m.dice != null ? el('span', { class: 'muted' }, [' · ' + (m.kind === 'adversity' ? rerollNeed(r, m) : 'up to ' + m.dice)]) : null]);
      })]));
      if (!mode) return;
      const need = mode.kind === 'adversity' ? rerollNeed(r, mode) : null;
      const ok = mode.kind === 'adversity' ? marks.length === need : marks.length > 0 && (mode.dice == null || marks.length <= mode.dice);
      rerollBar.appendChild(el('div', { class: 'chiprow tight' }, [
        el('span', { class: 'muted small' }, [mode.kind === 'adversity' ? (need ? 'Mark the ' + need + ' ' + (need === 1 ? 'die' : 'dice') + ' showing (su) or (ex) it rerolls.' : 'No die shows (su) or (ex): nothing to reroll.') : mode.kind === 'distinction' ? 'Mark up to ' + mode.dice + (mode.dice === 1 ? ' die' : ' dice') + ' to reroll.' : 'Mark the dice to reroll.']),
        el('button', { class: 'btn tiny', type: 'button', disabled: ok ? null : true, onclick: () => {
          if (reroll(r, marks, mode)) { mode = null; marks = []; drawTray(); }
        } }, ['Reroll ' + marks.length + ' ' + (marks.length === 1 ? 'die' : 'dice')]),
        mode.kind === 'adversity' && !need ? el('button', { class: 'btn ghost tiny', type: 'button', onclick: () => { r.applied.push({ id: mode.id, label: mode.label, kind: mode.kind }); mode = null; drawTray(); } }, ['Apply it anyway']) : null,
      ]));
    }
    function clickDie(r, d) {
      if (mode) {
        if (!canMark(r, mode, d)) return;
        const i = marks.indexOf(d.id);
        if (i !== -1) marks.splice(i, 1);
        else if (mode.kind === 'adversity' ? marks.length < rerollNeed(r, mode) : mode.dice == null || marks.length < mode.dice) marks.push(d.id);
        drawTray();
        return;
      }
      if (toggleKeep(r, d.id)) drawTray();
    }
    function drawTray() {
      tray.innerHTML = '';
      result.innerHTML = '';
      drawRerolls();
      if (!current) return;
      const r = current;
      ['ring', 'skill'].forEach((type) => {
        const group = r.dice.filter((d) => d.type === type);
        if (!group.length) return;
        tray.appendChild(el('div', { class: 'tray-row' }, [
          el('span', { class: 'tray-k' }, [type === 'ring' ? 'Ring dice' : 'Skill dice']),
          group.map((d) => {
            const node = el('button', { class: 'die ' + d.type + (d.kept ? ' kept' : '') + (d.bonus ? ' bonus' : '') + (marks.indexOf(d.id) !== -1 ? ' marked' : ''), type: 'button', title: (d.text || 'Blank') + (d.bonus ? ' — the bonus die of an (ex)' : ''), onclick: () => clickDie(r, d) }, [faceImg(d)]);
            if (d.kept && d.sym.ex && !d.exploded && !r.resolved) node.appendChild(el('span', { class: 'explode', title: 'Roll the bonus die this (ex) gives', onclick: (ev) => { ev.stopPropagation(); explode(r, d.id); drawTray(); } }, ['❉ +1']));
            return node;
          }),
        ]));
      });
      const base = tally(r);
      const extra = !r.resolved && o.extra ? o.extra(r, base) : (r.extra || []);
      const t = r.resolved || withExtra(base, extra);
      const s = summary(t);
      if (r.opts.source) result.appendChild(el('div', { class: 'muted small' }, ['via ' + r.opts.source + (r.opts.sourceType ? ' (' + r.opts.sourceType + ')' : '')]));
      (t.extra || []).forEach((x) => result.appendChild(el('div', { class: 'small extra' }, ['+' + x.successes + ' bonus success' + (x.successes === 1 ? '' : 'es') + ' — ' + x.label])));
      result.appendChild(el('div', { class: 'tally' }, [
        el('span', { class: 'muted small' }, ['kept ' + keptBase(r) + ' of ' + r.limit + (!compact && r.dice.some((d) => d.bonus) ? ' (+ bonus dice)' : '') + ' · ']),
        el('b', {}, [s.text]),
        s.verdict ? el('span', { class: 'verdict ' + (t.success ? 'ok' : 'fail') }, [' — ' + s.verdict]) : null,
        t.unexploded ? el('span', { class: 'muted small' }, [' · ' + t.unexploded + ' kept (ex) not yet rolled']) : null,
      ]));
      const notes = r.resolved ? (r.notes || []) : (o.notes ? o.notes(r, t) : []);
      notes.forEach((n) => result.appendChild(el('div', { class: 'small roll-note' }, [symbolsSpan(n)])));
      if (!r.resolved && t.opportunity && o.opportunities) {
        if (!r.spends) r.spends = [];
        const list = o.opportunities(r);
        if (list.length) result.appendChild(el('details', { class: 'opps' }, [
          el('summary', { class: 'small' }, ['Spend ' + t.opportunity + ' (op) — ' + list.length + ' options for this check' + (r.spends.length ? ' · ' + r.spends.length + ' chosen' : '')]),
          list.map((x) => el('label', { class: 'opp small' }, [
            el('input', { type: 'checkbox', checked: r.spends.indexOf(x.text) !== -1 || null, onchange: (ev) => { const i = r.spends.indexOf(x.text); if (ev.target.checked && i === -1) r.spends.push(x.text); if (!ev.target.checked && i !== -1) r.spends.splice(i, 1); } }),
            el('span', { class: 'muted' }, [' ' + x.group + ' · ']), symbolsSpan(x.text),
          ])),
        ]));
      }
      if (!r.resolved) {
        const dflt = o.strifeDefault ? o.strifeDefault(t, r) : t.strife;
        const shown = r.strifeChosen != null ? Math.min(r.strifeChosen, t.strife) : Math.min(dflt, t.strife);
        const strife = el('input', { class: 'text num small', type: 'number', min: 0, max: t.strife, value: shown, title: 'The strife the character receives: the kept (st), unless the player and GM settle on less',
          oninput: (ev) => { r.strifeChosen = Math.max(0, parseInt(ev.target.value || '0', 10) || 0); } });
        const keepHint = compact ? 'Tap the dice you keep.' : 'Click dice to keep them — nothing is kept for you.';
        const strifeUi = compact ? (t.strife ? stepper(strife, 0, t.strife, 'Strife taken') : null) : el('label', { class: 'small' }, ['Strife received ', strife, el('span', { class: 'muted' }, [' of ' + t.strife + ' (st) kept'])]);
        result.appendChild(el('div', { class: 'chiprow tight' }, [
          anyKept(r) ? strifeUi : el('span', { class: 'muted small' }, [keepHint]),
          el('button', { class: 'btn tiny', type: 'button', disabled: anyKept(r) ? null : true, onclick: () => {
            r.note = note.value.trim() || null;
            resolve(r, r.strifeChosen != null ? r.strifeChosen : dflt, extra);
            r.notes = o.notes ? o.notes(r, r.resolved) : [];
            p.source = p.sourceId = p.sourceType = p.tag = null;   // the next check is the player's own again
            // what was set up for this check does not carry to the next
            concealGranted = false;
            concealBox.checked = false;
            assistSkilled.value = 0;
            assistUnskilled.value = 0;
            note.value = '';
            if (compact) {
              box.querySelectorAll('.roller-controls.compact .step-v').forEach((x) => { x.textContent = '0'; });
              voidBox.checked = false;
              box.querySelectorAll('.roller-controls.compact .toggle').forEach((x) => x.sync && x.sync());
              startTn();
              box.refresh();
            }
            drawTray();
            if (o.onResolve) o.onResolve(r);
          } }, ['Resolve']),
        ]));
      } else {
        result.appendChild(el('div', { class: 'muted small' }, ['resolved' + (o.onResolve ? ' and logged' : '') + (r.strife !== r.resolved.strife ? ' · strife received ' + r.strife + ' of ' + r.resolved.strife : '')]));
        // an adversity on a check whose TN was never set: whether it failed is the table's to say
        const open = r.resolved.success == null && o.onAdversityFailed ? r.applied.filter((a) => a.kind === 'adversity' && !a.claimed) : [];
        if (open.length) result.appendChild(el('div', { class: 'chiprow tight' }, open.map((a) => el('button', { class: 'btn ghost tiny', type: 'button', onclick: () => { a.claimed = true; o.onAdversityFailed(r, a); drawTray(); } }, ['It failed: +1 Void point (' + a.label + ')']))));
      }
    }
    const rollBtn = el('button', { class: 'btn', type: 'button', onclick: () => {
      // compact: a hidden TN is the GM's concealing it, and the Void point it gives comes with the roll
      if (compact && tn.value === '' && o.onConceal && !concealGranted) { concealBox.checked = true; concealBox.dispatchEvent(new Event('change')); }
      current = roll(values()); mode = null; marks = []; drawTray();
    } }, ['Roll']);
    // compact, top to bottom: what it is for, the TN, the dice it comes to, the ring, the skill,
    // Void, assistance, Roll across the bottom. The TN is chosen for each check (a technique or an
    // initiative sets its own); Roll waits for it.
    // o.defaultTn: the TN a check starts at on this page (the player's page: 2), and returns to after
    // each resolve; without one, each check waits for its TN to be chosen
    const startTn = () => { if (compact && o.defaultTn != null) { tn.value = String(o.defaultTn); tnChosen = true; } else tnChosen = false; };
    let tnChosen = false;
    const tnPick = el('div', { class: 'tn-pick' });
    const drawTn = () => {
      tnPick.innerHTML = '';
      tnPick.appendChild(el('span', { class: 'step-k' }, ['TN']));
      const on = (x) => tnChosen && tn.value === x;
      tnPick.appendChild(el('button', { class: 'tn-btn hidden-tn' + (on('') ? ' on' : ''), type: 'button', onclick: () => { tn.value = ''; tnChosen = true; drawTn(); drawDice(); } }, ['Hidden']));
      difficulty().map((d) => String(d.tn)).forEach((x) => tnPick.appendChild(el('button', { class: 'tn-btn' + (on(x) ? ' on' : ''), type: 'button', onclick: () => { tn.value = x; tnChosen = true; drawTn(); drawDice(); } }, [x])));
    };
    const diceLine = el('div', { class: 'roll-dice-count' });
    const drawDice = () => {
      const v = values();
      const ringN = v.ringValue + (v.void ? SEIZE_THE_MOMENT.extraRingDice : 0) + (ASSISTANCE.unskilled === 'ring' ? v.assistUnskilled : 0);
      const skillN = v.skillRank + (ASSISTANCE.skilled === 'skill' ? v.assistSkilled : 0);
      diceLine.innerHTML = '';
      diceLine.appendChild(el('b', {}, [ringN + ' ring + ' + skillN + ' skill ' + (ringN + skillN === 1 ? 'die' : 'dice')]));
      diceLine.appendChild(el('span', { class: 'muted' }, [' · keep ' + keepLimit(v)]));
      rollBtn.disabled = compact && !tnChosen ? true : null;
      rollBtn.textContent = compact && !tnChosen ? 'Choose the TN' : 'Roll';
    };
    // the skill, chosen here (o.skills: { groups: [{ name, skills: [name] }], have: { name: rank } }):
    // each group under its name, its skills with their ranks as dots; tapped, a skill is the check's,
    // tapped again the check is the ring's alone
    const skillList = el('div', { class: 'skill-list', role: 'listbox', 'aria-label': 'Skill' });
    const drawSkills = () => {
      if (!o.skills) return;
      const sk = o.skills();
      skillList.innerHTML = '';
      sk.groups.forEach((g) => {
        skillList.appendChild(el('div', { class: 'sg-h' }, [g.name]));
        g.skills.forEach((k) => {
          const n = Math.max(0, Math.min(5, sk.have[k] || 0));
          const on = p.skill === k;
          skillList.appendChild(el('button', { class: 'sk-row' + (on ? ' on' : ''), type: 'button', role: 'option', 'aria-selected': on ? 'true' : 'false',
            onclick: () => box.set(on ? { skill: null, skillRank: 0 } : { skill: k, skillRank: sk.have[k] || 0 }) }, [
            el('span', { class: 'sk-n' }, [k]), el('span', { class: 'sk-dots', 'aria-label': n + ' of 5' }, ['●'.repeat(n) + '○'.repeat(5 - n)]),
          ]));
        });
      });
    };
    const voidRow = el('div', { class: 'roll-row' });
    const assistRow = (inp, label) => el('div', { class: 'roll-row' }, [el('span', { class: 'roll-row-k' }, [label]), stepper(inp, 0, 9)]);
    if (compact) {
      note.placeholder = 'What is this roll for?';
      voidRow.appendChild(el('span', { class: 'roll-row-k' }, ['Void point · +1 ring die, +1 kept']));
      voidRow.appendChild(toggle(voidBox, 'Spend'));
      box.appendChild(el('div', { class: 'roller-controls compact' }, [
        note, tnPick, diceLine, ringPick, o.skills ? skillList : null, voidRow,
        assistRow(assistSkilled, 'Skilled assistance'), assistRow(assistUnskilled, 'Unskilled assistance'),
        rollBtn, ringValue, skillRank, tn, concealBox]));
      ringValue.hidden = true; skillRank.hidden = true; tn.hidden = true; concealBox.hidden = true;
      [assistSkilled, assistUnskilled].forEach((x) => x.addEventListener('input', drawDice));
      voidBox.addEventListener('change', drawDice);
    }
    // what may change between draws of the page: the Void points to spend, the skills' ranks
    box.refresh = () => {
      if (!compact) return;
      const can = !o.voidAvailable || o.voidAvailable() > 0;
      voidRow.hidden = !can;
      if (!can && voidBox.checked) { voidBox.checked = false; }
      voidRow.querySelectorAll('.toggle').forEach((b) => b.sync && b.sync());
      drawSkills(); drawTn(); drawDice();
    };
    if (compact) { startTn(); drawRings(); box.refresh(); }
    drawRings();
    if (!compact) box.appendChild(el('div', { class: 'roller-controls' }, [
      ringPick,
      el('label', { class: 'small', hidden: o.fixed || null }, ['Ring ', ringValue]),
      el('label', { class: 'small', hidden: o.fixed || null }, [(p.skill ? p.skill + ' ' : 'Skill ') , skillRank]),
      tn,
      el('label', { class: 'small', title: 'Seize the Moment: spend 1 Void point to roll one additional Ring die and keep one additional die' }, [voidBox, ' Void point']),
      rollBtn,
    ]));
    if (!compact) box.appendChild(el('div', { class: 'roller-controls more' }, [
      el('label', { class: 'small', title: 'Assistance (p. 26): each assisting character with ranks in the skill adds a Skill die, each without adds a Ring die, and each adds a kept die' }, ['Assisting: skilled ', assistSkilled]),
      el('label', { class: 'small' }, ['unskilled ', assistUnskilled]),
      o.onConceal ? el('label', { class: 'small', title: 'After the GM conceals the TN of a check from the players, the character gains 1 Void point (Void Points, p. 297)' }, [concealBox, ' TN concealed (+1 Void point)']) : null,
      note,
    ]));
    box.appendChild(tray);
    box.appendChild(rerollBar);
    box.appendChild(result);
    box.set = (patch) => {
      // a set-up that names no technique is not one
      if (!patch || !('source' in patch)) p.source = p.sourceId = p.sourceType = p.tag = null;
      Object.assign(p, patch || {});
      if (patch && patch.ringValue != null) ringValue.value = patch.ringValue;
      if (patch && patch.skillRank != null) skillRank.value = patch.skillRank;
      if (patch && patch.tn !== undefined) tn.value = patch.tn == null ? '' : patch.tn;
      drawRings();
      const lab = skillRank.parentNode;
      if (!compact && lab && lab.firstChild) lab.firstChild.textContent = (p.skill ? p.skill + ' ' : 'Skill ');
      if (compact) { if (patch && patch.tn !== undefined) tnChosen = true; drawSkills(); drawTn(); drawDice(); }
    };
    box.current = () => current;
    box.skill = () => p.skill || null;   // the check's skill
    box.roll = () => { if (!rollBtn.disabled) rollBtn.click(); };   // a Roll elsewhere on the page (the player's tab bar)
    return box;
  }
  const symbolsSpan = (text) => el('span', { html: symbolsHtml(esc(text)) });

  // one log line: a resolved roll with how it came to be, or an event on a character
  const logDie = (type, key) => el('img', { class: 'logdie', src: artBase() + 'dice/' + key + '.svg', alt: key, title: (type === 'ring' ? 'Ring die ' : 'Skill die ') + key });
  function logLine(entry, opts) {
    const compact = !!(opts && opts.compact);
    if (entry.kind === 'event') return el('div', { class: 'roll-line event' }, [
      el('span', { class: 'roll-who' }, [entry.who || '']),
      el('span', {}, [entry.text || '']),
      entry.why ? el('span', { class: 'muted small' }, [entry.why]) : null,
    ]);
    if (entry.kind !== 'roll') return el('div', { class: 'roll-line' }, [el('span', { class: 'roll-who' }, [entry.kind || 'note']), entry.text || JSON.stringify(entry)]);
    const t = entry.tally || {};
    const s = summary(t);
    const chips = [];
    if (entry.limit != null && !compact) chips.push(el('span', { class: 'logchip' + (entry.keptFewer ? ' warn' : '') }, ['kept ' + entry.keptBase + ' of ' + entry.limit + (entry.keptFewer ? ' — fewer than allowed' : '')]));
    if (entry.assistSkilled) chips.push(el('span', { class: 'logchip' }, ['assisted: ' + entry.assistSkilled + ' skilled']));
    if (entry.assistUnskilled) chips.push(el('span', { class: 'logchip' }, ['assisted: ' + entry.assistUnskilled + ' unskilled']));
    if (entry.concealed) chips.push(el('span', { class: 'logchip' }, ['TN concealed']));
    if (entry.strifeRolled != null && entry.strifeApplied !== entry.strifeRolled) chips.push(el('span', { class: 'logchip warn' }, ['strife received ' + entry.strifeApplied + ' of ' + entry.strifeRolled]));
    (entry.applied || []).forEach((a) => chips.push(el('span', { class: 'logchip' }, [symbolsSpan(a.label)])));
    (entry.extra || []).forEach((x) => chips.push(el('span', { class: 'logchip' }, ['+' + x.successes + ' ' + x.label])));
    (entry.notes || []).forEach((n) => chips.push(el('span', { class: 'logchip note' }, [symbolsSpan(n)])));
    (entry.spends || []).forEach((n) => chips.push(el('span', { class: 'logchip' }, ['spent ', symbolsSpan(n)])));
    const events = (entry.events || []).map((ev) => el('div', { class: 'log-ev' }, [
      ev.kind === 'dismissed' ? el('span', { class: 'muted small' }, ['⚠ dismissed: ' + ev.via]) : [el('span', { class: 'muted small' }, [ev.kind === 'reroll' ? '↻ ' + (ev.via || 'reroll') : '❉ explodes']), logDie(ev.type, ev.from), el('span', { class: 'muted' }, ['→']), logDie(ev.type, ev.to)],
    ]));
    const first = (entry.initial || []).length ? el('div', { class: 'log-ev' }, [el('span', { class: 'muted small' }, ['rolled']), entry.initial.map((k) => logDie(k.split('_')[0], k))]) : null;
    return el('div', { class: 'roll-line' + (t.success === true ? ' ok' : t.success === false ? ' fail' : '') }, [
      el('span', { class: 'roll-who' }, [[entry.who, entry.what].filter(Boolean).join(' · ')]),
      el('span', { class: 'roll-dice' }, (entry.kept || []).map((k) => logDie(String(k).split('_')[0], k))),
      el('span', { class: 'roll-sum' }, [s.text + (s.verdict ? ' — ' + s.verdict : '')]),
      entry.note ? el('span', { class: 'muted small' }, ['“' + entry.note + '”']) : null,
      entry.source ? el('span', { class: 'muted small' }, ['via ' + entry.source + (entry.sourceType ? ' (' + entry.sourceType + ')' : '')]) : null,
      chips.length ? el('div', { class: 'logchips' }, chips) : null,
      !compact && (first || events.length) ? el('details', { class: 'log-prov' }, [el('summary', { class: 'muted small' }, ['how it was rolled']), first, events]) : null,
    ]);
  }
  // what a resolved roll leaves in the log: the check, every die first rolled, each reroll and
  // explosion, the dice kept, and the strife the character received
  function logEntry(r, who) {
    const o = r.opts;
    const t = r.resolved || tally(r);
    const kb = keptBase(r);
    return {
      at: new Date().toISOString(), kind: 'roll', mode: 'check', who: who || null,
      what: [o.skill, o.ring ? '(' + o.ring + ' ' + o.ringValue + ')' : null, o.tn != null ? 'TN ' + o.tn : null, o.void ? 'Void point' : null].filter(Boolean).join(' ') || (o.label || 'check'),
      kept: r.dice.filter((d) => d.kept).map((d) => d.key), tally: t,
      note: r.note || null, source: o.source || null, initial: r.initial.slice(), events: r.events.slice(),
      applied: r.applied.map((a) => ({ label: a.label, kind: a.kind })),
      limit: r.limit, keptBase: kb, keptFewer: kb < r.limit,
      assistSkilled: o.assistSkilled || 0, assistUnskilled: o.assistUnskilled || 0, concealed: !!o.concealed,
      sourceId: o.sourceId || null, sourceType: o.sourceType || null, extra: (r.extra || []).map((x) => ({ successes: x.successes, label: x.label })),
      notes: (r.notes || []).slice(), spends: (r.spends || []).slice(), tag: o.tag || null,
      strifeRolled: t.strife, strifeApplied: r.strife == null ? t.strife : r.strife,
    };
  }

  return {
    DEFAULT_TN, SEIZE_THE_MOMENT, EXPLOSION, ASSISTANCE, faces, symbolDefs, resolutionOrder, checkSteps, difficulty,
    rule, rerollRule, roll, toggleKeep, explode, reroll, rerollNeed, tally, resolve, summary, keepLimit,
    roller, faceImg, ringIcon, symbolsHtml, logLine, logEntry, esc, stepper, toggle,
  };
})();
