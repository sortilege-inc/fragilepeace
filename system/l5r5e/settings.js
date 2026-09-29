// system/l5r5e/settings.js — the GM's Settings pane: one section per feature that needs this
// browser's own configuration (the AI suggestions' key, the lore server's address and token). A feature
// adds its section with L5RSettings.section({ id, render(container, redraw) }); everything a
// section saves is its own, in this browser's localStorage, and never enters the pack or a session.
window.L5RSettings = (function () {
  const sections = [];
  const section = (s) => { if (!sections.some((x) => x.id === s.id)) sections.push(s); };
  function renderPane(container) {
    const { el } = window.VttRender;
    const draw = () => {
      container.innerHTML = '';
      container.appendChild(el('h4', {}, ['Settings']));
      container.appendChild(el('p', { class: 'muted small' }, ['Saved in this browser only — not in the pack, not shared with the table.']));
      sections.forEach((s) => { const box = el('div', { class: 'paper settings-section' }); container.appendChild(box); s.render(box, draw); });
    };
    draw();
  }
  if (window.VttPanels) window.VttPanels.register('settings', { label: 'Settings', render: renderPane });

  // The public site's book tabs (engine/site.js): off on an instance unless turned on — here, for
  // this browser only. Nobody else's view of the site changes.
  const CFG = window.VttConfig || {};
  const BOOKS_KEY = (CFG.storagePrefix || 'sortilege-vtt') + ':site-books';
  section({ id: 'site-books', render: (box, redraw) => {
    const { el } = window.VttRender;
    let on = !!CFG.siteBooks;
    try { const v = localStorage.getItem(BOOKS_KEY); if (v !== null) on = v === '1'; } catch (e) { /* default */ }
    box.appendChild(el('div', { class: 'guidance-k' }, ['The books on the site']));
    box.appendChild(el('p', { class: 'muted small' }, ['Whether the site shows the books’ own text — the shelf, the lore, adventures and search. Off, the schools, techniques, NPCs, characters, the creator and the dice still show, and a link to one entry still opens it. This setting is for this browser only; other visitors see the site’s default (' + (CFG.siteBooks ? 'on' : 'off') + ').']));
    box.appendChild(el('label', { class: 'set-row' }, [
      el('input', { type: 'checkbox', checked: on || null, onchange: (ev) => { try { localStorage.setItem(BOOKS_KEY, ev.target.checked ? '1' : '0'); } catch (e) { /* private mode */ } redraw(); } }),
      ' Show the books on the site, in this browser',
    ]));
  } });
  return { section };
})();
