// engine/config.js — where things are. The one file a deployment edits.
window.VttConfig = {
  system: 'l5r5e',
  title: 'Legend of the Five Rings',
  channel: 'sortilege-vtt-l5r5e',        // BroadcastChannel name (same-machine windows)
  storagePrefix: 'sortilege-vtt-l5r5e',  // localStorage key prefix
  dataGlobal: 'L5R5E',                   // the global data/*.js registers into
  // The pages, relative to the site root; the gm/ pages carry <base href="../"> so every
  // path stays root-relative.
  pages: { site: './', gm: 'gm/', table: 'gm/vtt.html', play: 'gm/play.html' },
  // what a fresh browser opens on until a campaign is created or restored: no adventure is
  // picked (the Adventure panel offers the sixteen), no book beyond what a view asks for.
  // An instance may add `seed: 'campaign/pack/seed.json'` — a pack that fills what its campaign
  // has never had: a whole key, an entry (by id) in a list, a field (engine/state.js seed). What
  // the GM has set, changed or removed is never touched.
  // An instance may also name the Notes pane's document (system/l5r5e/gm-panes.js):
  //   notes: { src: 'campaign/docs/state.html', title: '…', class: 'pf-doc' }
  // a .html src is the instance's own fragment, inserted as it is; anything else reads as Markdown.
  // (The family standard is the GM's material in the GM tabs, in the pack — PLAYBOOK.md — so a
  // Notes document is for an instance that has not moved there yet.)
  defaultCampaign: { name: 'A new campaign', modules: [], books: [] },
  // the three panels the GM page opens on (engine/app.js)
  defaultSlots: ['adventure', 'party', 'inspector'],
  // Instance knobs, all off here:
  //   ownAdventure: { title } — the campaign is its own adventure: its arc (Scenes) is what the
  //     table, the cast and the current scene follow (system/l5r5e/table.js); pair it with
  //     hidePanes: ['adventure'].
  //   hidePanes: [ids] — GM panels the instance leaves out (engine/panels.js).
  //   gmGate: { title, text, enter, leave } — the warning in front of /gm/ (engine/app.js).
  //   siteBooks — whether the public site shows the books' tabs; an instance leaves it off, and
  //     the GM turns them on per browser in Settings (engine/site.js).
  siteBooks: true,
  // The Worker that holds player sessions. Served from localhost the app talks to
  // `wrangler dev`; deployed, to the URL below. Empty = sessions disabled until the owner
  // deploys (PLAN.md D3).
  // An instance (a campaign repo forked from this VTT) declares its own scripts here — its
  // data layer, site tabs, GM panels and styles — and engine/instance.js loads them at the
  // stages the upstream pages mark. Upstream declares none. Shape: engine/instance.js.
  instance: null,
  worker: {
    deployed: '',
    local: 'http://localhost:8792',
  },
};
window.VttConfig.workerUrl = /^(localhost|127\.0\.0\.1)$/.test(location.hostname) ? window.VttConfig.worker.local : window.VttConfig.worker.deployed;
