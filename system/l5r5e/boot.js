// system/l5r5e/boot.js — the table and the player's page read the adventure and the sheet
// synchronously when they start (engine/vtt.js, engine/play.js), but this corpus's books load on
// demand. So those pages load the core (the Samurai ACTOR, the dice) and the campaign's
// adventure book first, then the engine page named in data-page. The engine is left as it is.
(function () {
  const me = document.currentScript;
  const page = me && me.getAttribute('data-page');
  const D = window.L5RData;
  const mod = ((window.VttState && window.VttState.state.campaign) || {}).modules || [];
  const books = ['core'].concat(mod.map((mid) => (D.moduleList().find((m) => m.id === mid) || {}).book).filter(Boolean));
  D.ensure(books).then(() => {
    const s = document.createElement('script');
    s.src = page;
    document.body.appendChild(s);
  });
})();
