// system/l5r5e/ops.js — the ops Legend of the Five Rings adds to the engine's, registered with
// the same call and shared the same way (engine/ops.js). Loaded by the browser after
// engine/ops.js, and imported by the Worker beside it, so the room applies the very same
// functions.
//
//   cast   { [sceneId]: [entityIds] }   who the GM has put in a scene of an adventure, beyond
//                                       the NPCs its .arc names there — drawn from any book's
//                                       NPCs (the Cast panel)
//   party[].versions                    archived copies of a character (archivePartyVersion)
//   npcConditions { [entityId]: [names] } an NPC's conditions, the GM's (setNpcConditions)
//   gmNotes, arc, threads, encounters, gm   the GM's own pack state (setGmNotes …, setGm), never
//                                       shared and never sent to the room (opts.local)
(function (root, factory) {
  if (typeof module !== 'undefined' && module.exports) module.exports = factory(require('../../engine/ops.js'));
  else factory(root.VttOps);
})(typeof self !== 'undefined' ? self : this, function (Ops) {
  Ops.shared(['cast']);

  Ops.register('setSceneCast', (s, sceneId, ids) => {
    if (!s.cast) s.cast = {};
    s.cast[sceneId] = (ids || []).slice();
  });

  // A party member's archived versions (the sheet's version history): a copy of the character
  // and its trackers, appended, never edited. A player may archive their own character.
  Ops.register('archivePartyVersion', (s, id, version) => {
    const m = (s.party || []).find((x) => x.id === id);
    if (!m || !version || !version.id) return;
    if (!m.versions) m.versions = [];
    if (!m.versions.some((x) => x.id === version.id)) m.versions.push(version);
  }, (s, me, a) => a[0] === me);

  // An advancement (the player's Advancement page): the character as it was is archived as a
  // version, the advanced character becomes the current one, and the XP record moves with it.
  // adv = { version: { id, label, date, character, live }, character, live }. A player may
  // advance their own character.
  Ops.register('advancePartyMember', (s, id, adv) => {
    const m = (s.party || []).find((x) => x.id === id);
    if (!m || !adv || !adv.character || !adv.version || !adv.version.id) return;
    if (!m.versions) m.versions = [];
    if (!m.versions.some((x) => x.id === adv.version.id)) m.versions.push(adv.version);
    m.character = adv.character;
    if (adv.live) m.live = Object.assign({}, m.live || {}, adv.live);
  }, (s, me, a) => a[0] === me);

  // An NPC's conditions, as the GM marks them (the Inspector): { [entityId]: [names] }. Shared, so a
  // player engaged with the NPC sees them with their rules text (Portents O7).
  Ops.shared(['npcConditions']);
  Ops.register('setNpcConditions', (s, id, list) => {
    if (!s.npcConditions) s.npcConditions = {};
    s.npcConditions[id] = (list || []).slice();
  });

  // The GM's own pack state (Portents M6, O8): free notes, the arc, open threads, saved encounters.
  // Never shared: no player may send them, none is in a player's view, and none is forwarded.
  const gmOnly = () => null;
  // the GM's own keys are never shared, so their ops never go to the session's room either
  const LOCAL = { local: true };
  Ops.register('setGmNotes', (s, text) => { s.gmNotes = String(text || ''); }, null, gmOnly, LOCAL);
  Ops.register('setArc', (s, list) => { s.arc = JSON.parse(JSON.stringify(list || [])); }, null, gmOnly, LOCAL);
  Ops.register('setThreads', (s, list) => { s.threads = JSON.parse(JSON.stringify(list || [])); }, null, gmOnly, LOCAL);
  Ops.register('setEncounters', (s, list) => { s.encounters = JSON.parse(JSON.stringify(list || [])); }, null, gmOnly, LOCAL);
  // the GM's own material (system/l5r5e/gm-text.js): gm[where] is a list of sections, or a note
  Ops.register('setGm', (s, where, value) => {
    if (!s.gm) s.gm = {};
    s.gm[String(where)] = JSON.parse(JSON.stringify(value == null ? null : value));
  }, null, gmOnly, LOCAL);

  return Ops;
});
