/* campaign/site/site.js — the campaign's site tabs (campaign/PLAN.md M5), loaded at the `site` stage
   (engine/config.js), before engine/site.js first renders. The old site's 517 pages are documents under
   campaign/docs/, one per old page at its old path (campaign/source/to_docs.py); each tab is one section of
   the old site, and a tab's path names a document in it: #chronicle/s42-midnight-tea is
   campaign/docs/chronicle/s42-midnight-tea.html. A path whose last segment is not a document is an anchor in
   the one before it (#pcs/setsuna/timeline). campaign/docs/manifest.js lists the documents; ROUTE and
   resolve() are mirrored, and every link in every document checked against them, by
   campaign/source/check_docs.py. A document is drawn into a `.fp-doc` element, the one
   campaign/site/campaign.css is scoped to; the map and the roster filters are functions it calls after. */
(function () {
  var DOCS = {};
  (window.FP_DOCS || []).forEach(function (p) { DOCS[p] = true; });
  var cache = {};

  function fetchDoc(path) {
    if (!cache[path]) cache[path] = fetch('campaign/docs/' + path).then(function (r) {
      if (!r.ok) throw new Error('campaign/docs/' + path + ': ' + r.status);
      return r.text();
    });
    return cache[path];
  }

  // a tab → its section of the old site
  var ROUTE = { fp: '', pcs: 'character', party: 'party', chronicle: 'chronicle', personae: 'dramatis-personae',
    atlas: 'atlas', rokugan: 'lore', notes: 'notes' };
  var join = function (parts) { return parts.filter(function (p) { return p !== ''; }).join('/'); };

  // tab + path → { doc, anchor }, or null: the longest run of the path that is a document, then at most
  // one more segment, an id in it. The Atlas tab is the map; its gazetteer is #atlas/gazetteer.
  function resolve(tab, parts) {
    if (tab === 'atlas' && !parts.length) return { doc: 'map/index.html', anchor: null };
    if (tab === 'atlas' && parts[0] === 'gazetteer') return parts.length <= 2 ? { doc: 'atlas/index.html', anchor: parts[1] || null } : null;
    var base = ROUTE[tab];
    for (var k = parts.length; k >= 0; k--) {
      var head = parts.slice(0, k);
      var cands = (k ? [join([base].concat(head)) + '.html'] : []).concat([join([base].concat(head, ['index.html']))]);
      for (var i = 0; i < cands.length; i++) {
        if (DOCS[cands[i]]) {
          var rest = parts.slice(k);
          return rest.length <= 1 ? { doc: cands[i], anchor: rest[0] || null } : null;
        }
      }
    }
    return null;
  }

  // the styles a document's old page used (campaign/source/scope_css.py GROUPS): the four character
  // dossiers carried their own and nothing else; every other page used the site's (rokugan.css)
  var OWN = { 'character/setsuna.html': 'setsuna', 'character/harunobu.html': 'harunobu',
    'character/jujiro.html': 'jujiro', 'character/anzu.html': 'anzu' };

  // what a document needs once it is drawn: the old pages' own scripts, as functions
  var AFTER = {
    'map/index.html': function () { window.FP.map(); },
    'dramatis-personae/index.html': function (host) { window.FP.roster(host); },
  };

  function docTab(tab) {
    return function (main, path) {
      var host = document.createElement('div');
      host.className = 'fp-doc fp-tab';
      host.innerHTML = '<p class="fp-reading">Reading…</p>';
      main.appendChild(host);
      var r = resolve(tab, path || []);
      if (!r) { host.textContent = 'Nothing in the record at this address.'; return; }
      fetchDoc(r.doc).then(function (html) {
        if (!host.isConnected) return;
        host.className = 'fp-doc fp-tab ' + (OWN[r.doc] ? 'fp-own-' + OWN[r.doc] : 'fp-site');
        host.innerHTML = html;
        if (AFTER[r.doc]) AFTER[r.doc](host);
        var at = r.anchor && host.querySelector('#' + CSS.escape(r.anchor));
        if (at) at.scrollIntoView();
      }).catch(function (e) { host.textContent = 'Could not read ' + r.doc + ' (' + e.message + ').'; });
    };
  }

  // the old site's nav, in its order; ids that leave the VTT's own (characters, lore) alone
  var tabs = [
    { id: 'fp', label: 'The Fragile Peace' },
    { id: 'pcs', label: 'The Characters' },   // the page's own title; the VTT has a "Characters" of its own
    { id: 'party', label: 'The Party' },
    { id: 'chronicle', label: 'Chronicle' },
    { id: 'personae', label: 'Dramatis Personae' },
    { id: 'atlas', label: 'Atlas' },
    { id: 'rokugan', label: 'Lore' },
    { id: 'notes', label: 'Player Notes' },
  ];
  tabs.forEach(function (t) { t.render = docTab(t.id); t.group = 'campaign'; });
  // the campaign's tabs first: the site opens on the campaign; the menu draws a line after them
  window.VttSiteTabs = tabs.concat(window.VttSiteTabs || []);
})();
