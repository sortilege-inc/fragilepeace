/* The players' live sheets, imported ONCE from the retired play/ pages' own storage (campaign/PLAN.md
   M4, F10; the pattern is Portents & Fortunes' campaign/site/import-old-sheet.js). Each old page kept its
   character's state in this browser's localStorage under pf-sheet-<sheet> and its roll log under
   pf-log-<sheet>; this page is the same origin, so it can read them. When a party member built from one
   of the characters below has not taken them yet, they become its live values and log, and the member
   is marked `importedFrom` — nothing is read twice, and the old keys are left as they are.

   Honor, glory and status: every old save carries all three, touched or not. One is taken only where
   the save differs from what the old sheet printed — that is, where the player changed it in play —
   so a stale save cannot undo a later ruling (Harunobu's 49, the pre-award glory, is a printed value
   too). Loaded at the gm and play stages (engine/config.js). */
(function () {
  // the character's entity → its old page's id, and every standing the old page ever printed
  var SHEETS = {
    '#FPpcDojiSetsuna': { sheet: 'setsuna', printed: { honor: [69], glory: [71], status: [60] } },
    '#FPpcShinjoHarunobu': { sheet: 'harunobu', printed: { honor: [55], glory: [55, 49], status: [35] } },
    '#FPpcTonboKuma': { sheet: 'kuma', printed: { honor: [30], glory: [35], status: [30] } },
    '#FPpcAsahinaJujiro': { sheet: 'jujiro', printed: { honor: [60], glory: [78], status: [35] } },
    '#FPpcShinjoAnzu': { sheet: 'anzu', printed: { honor: [40], glory: [46], status: [33] } },
    '#FPpcMatsuMorozane': { sheet: 'morozane', printed: { honor: [20], glory: [55], status: [45] } },
  };
  var cap = function (s) { return String(s || '').replace(/\b\w/g, function (c) { return c.toUpperCase(); }); };
  function read(k) { try { return JSON.parse(localStorage.getItem(k) || 'null'); } catch (e) { return null; } }
  // the old sheet's state, in the VTT's live terms
  function liveOf(st, printed) {
    var p = {};
    if (st.strife != null) p.Strife = st.strife;
    if (st.fatigue != null) p.Fatigue = st.fatigue;
    if (st['void'] != null) p.voidPoints = st['void'];
    if (st.stance) p.stance = cap(st.stance);
    ['honor', 'glory', 'status'].forEach(function (k) {
      if (st[k] != null && (printed[k] || []).indexOf(st[k]) === -1) p[cap(k)] = st[k];
    });
    if (Array.isArray(st.conditions) && st.conditions.length) p.conditions = st.conditions.slice();
    if (st.inConflict && st.conflictType) p.conflict = { type: cap(String(st.conflictType).replace(/[-_]/g, ' ')), initiative: null, engaged: [] };
    var eq = {};
    if (st.equipWeapon) { eq.weapons = {}; eq.weapons[st.equipWeapon] = { state: 'readied' }; }
    if (st.equipArmor) eq.armor = st.equipArmor;
    if (eq.weapons || eq.armor) p.equip = eq;
    return p;
  }
  // an old log entry as one line of the new log (its dice are not the VTT's record, its outcome is)
  function lineOf(e) {
    if (e.kind && e.text) return e.text.replace(/<[^>]+>/g, '');
    var bits = [e.skillLabel || null, e.ring ? '(' + cap(e.ring) + (e.ringN != null ? ' ' + e.ringN : '') + ')' : null, e.tn != null ? 'TN ' + e.tn : null].filter(Boolean).join(' ');
    var res = e.su != null ? e.su + ' success' + (e.su === 1 ? '' : 'es') + (e.op ? ' · ' + e.op + ' opportunity' : '') + (e.strifeApplied ? ' · ' + e.strifeApplied + ' strife' : '') + (e.pass != null ? ' — ' + (e.pass ? 'succeeds' : 'fails') : '') : '';
    return [bits, res, e.source ? 'via ' + e.source : null, e.note ? '“' + e.note + '”' : null].filter(Boolean).join(' · ');
  }
  function run() {
    var State = window.VttState, S = State && State.state;
    if (!S || !Array.isArray(S.party)) return;
    var me = window.VttSession && window.VttSession.current && window.VttSession.current();
    var myId = me && me.info && me.info.memberId;
    if (me && me.info && me.info.role === 'player' && !myId) return;   // a player imports only once they have claimed
    S.party.forEach(function (m) {
      var src = (m.source && m.source.id) || ((m.character || {})._source || {}).id;
      var old = SHEETS[src];
      if (!old || (m.live || {}).importedFrom) return;
      if (myId && m.id !== myId) return;           // a player takes only their own
      var KEY = 'pf-sheet-' + old.sheet, LOGKEY = 'pf-log-' + old.sheet;
      var st = read(KEY);
      if (!st) return;
      var p = liveOf(st, old.printed);
      p.importedFrom = { key: KEY, at: new Date().toISOString() };
      State.commit('setPartyLive', [m.id, p]);
      var log = read(LOGKEY) || [];
      var t0 = Date.now();
      log.slice().reverse().forEach(function (e, i) {   // the old log is newest first
        State.commit('appendLog', [{ at: new Date(t0 + i).toISOString(), kind: 'event', who: m.name, memberId: m.id, text: lineOf(e), why: 'the old sheet' + (e.when ? ', ' + e.when : '') }]);
      });
      State.commit('appendLog', [{ at: new Date(t0 + log.length).toISOString(), kind: 'event', who: m.name, memberId: m.id,
        text: 'Imported from the old sheet: ' + Object.keys(p).filter(function (k) { return k !== 'importedFrom'; }).join(', ') + (log.length ? '; ' + log.length + ' log entries' : ''), why: 'import' }]);
    });
  }
  window.addEventListener('load', function () {
    setTimeout(run, 400);
    // a character added to the party after the page loaded takes its save at once (Portents' import
    // ran at load only: its character was already in the party); run() acts once per member
    if (window.VttBus) ['state:remote', 'state:changed'].forEach(function (ev) { window.VttBus.on(ev, function () { setTimeout(run, 0); }); });
  });
})();
