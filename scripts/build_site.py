#!/usr/bin/env python3
"""
build_site.py — generate The Fragile Peace from the Archivist export in ingest/
plus the hand-authored session files in sources/chronicle/.

    python3 scripts/build_site.py

Generated directories are wiped and rebuilt: chronicle/, party/, dramatis-personae/,
atlas/, lore/. Everything else (index.html, character/, play/, notes/, map/,
rokugan.css, assets/, README) is left alone.

Nothing in this script decides what Doji Setsuna knows. That is adjudicated by hand,
session by session, in sources/chronicle/*.md — see the `witnessed:` / `apart:` keys.
An NPC's page reveals only the sessions she was there for; the rest are masked, and
the masked bars carry no content at all, because we do not have it.
"""

import os, re, io, sys, html, shutil, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import archivist as A
from archivist import slugify, norm, rel, link_wikilinks, md_inline

ROOT = A.ROOT
BRAND = "The Fragile Peace"
FOOT = ('<footer class="foot"><span class="mark">&#10070;</span>'
        'The Fragile Peace &middot; Legend of the Five Rings</footer>')
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
         '<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;500;600;700'
         '&family=Cormorant:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500;1,600'
         '&family=EB+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&display=swap" rel="stylesheet">')

NAV = [("home", "Home", "index.html"),
       ("character", "Setsuna", "character/index.html"),
       ("party", "The Party", "party/index.html"),
       ("chronicle", "Chronicle", "chronicle/index.html"),
       ("dramatis", "Dramatis Personae", "dramatis-personae/index.html"),
       ("map", "Atlas", "map/index.html"),
       ("lore", "Lore", "lore/index.html"),
       ("notes", "Player Notes", "notes/index.html")]

CATDIR = {"npc": "dramatis-personae", "pc": "party", "location": "atlas",
          "faction": "lore/factions", "item": "lore/relics", "lore": "lore/documents"}
CATNAV = {"npc": "dramatis", "pc": "party", "location": "map",
          "faction": "lore", "item": "lore", "lore": "lore"}

# The four who are still at the table; everyone else in Characters/PCs is off stage.
CURRENT_PARTY = ["Doji Setsuna", "Bayushi Monban", "Shiba Midori", "Kakita Kazumi",
                 "Ikoma Tadayoshi"]

# Sessions 10-17 are a flashback three centuries back, played with different
# characters. Setsuna lived that arc as the memories of her ancestor Morozane.
# 17 belongs to it despite the export naming "Doji Setsuna" in it: the rider it
# calls Setsuna is mounted on Shiguro Chinmoku, which is Morozane's lion, and no
# present-day companion appears anywhere in the session.
FLASHBACK_PARTY = ["Matsu Morozane", "Kitsu Somalia", "Matsumura Zane"]
FLASHBACK_SESSIONS = set(range(10, 18))

# PCs with a live sheet under play/. Setsuna is built by the doji-setsuna repo;
# Morozane by scripts/build_morozane_sheet.py in this one.
PLAYABLE = {"Doji Setsuna": "play/setsuna.html",
            "Matsu Morozane": "play/morozane.html"}


def esc(s):
    return html.escape(s, quote=False)


def navbar(active, depth):
    p = "../" * depth
    out = ['<nav class="topnav"><span class="brand">%s</span>' % BRAND]
    for k, label, href in NAV:
        cls = []
        if k == "notes":
            cls.append("notes")
        if k == active:
            cls.append("active")
        out.append('<a href="%s%s"%s>%s</a>'
                   % (p, href, (' class="%s"' % " ".join(cls)) if cls else "", label))
    return "".join(out) + "</nav>"


def shell(url, title, desc, active, body, extra=""):
    depth = url.count("/")
    p = "../" * depth
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="icon" href="{p}assets/favicon.svg" type="image/svg+xml">
<title>{title}</title>
<meta name="description" content="{desc}">
{fonts}
<link rel="stylesheet" href="{p}rokugan.css">{extra}
</head>
<body>
{nav}
{body}
{foot}
</body>
</html>
""".format(p=p, title=esc(title), desc=esc(desc), fonts=FONTS, extra=extra,
           nav=navbar(active, depth), body=body, foot=FOOT)


def write(url, content):
    path = os.path.join(ROOT, url)
    d = os.path.dirname(path)
    if d and not os.path.isdir(d):
        os.makedirs(d)
    io.open(path, "w", encoding="utf-8").write(content)


# ------------------------------------------------------------------ session files

class Rewrite(object):
    """A hand-authored session file from sources/chronicle/."""

    def __init__(self, meta, sections):
        self.meta = meta
        self.sections = sections

    @property
    def narrative(self):
        return self.sections.get("narrative", "")

    @property
    def coda(self):
        return self.sections.get("setsuna", "")

    @property
    def epigraph(self):
        return self.meta.get("epigraph", "")

    def text(self):
        """Everything the rewrite says, for sessions the export does not cover."""
        return "\n".join([self.narrative, self.coda] +
                         ["[[%s]]" % n for n, _, u in self.learned() if not u])

    def names(self, key):
        v = self.meta.get(key, "")
        return [x.strip() for x in v.split(";") if x.strip()]

    def learned(self):
        """'## Learned' — one '- Name: what she took away' line per person.

        A name must resolve to a page, so that a typo cannot quietly become a
        knowledge line attached to nobody. Some people the record never names
        ("the ronin at the docks"), and those are still worth writing down —
        mark them '- Name (unpaged): ...' to say so deliberately.
        """
        out = []
        for line in self.sections.get("learned", "").splitlines():
            m = re.match(r"^-\s*([^:]+):\s*(.+)$", line.strip())
            if not m:
                continue
            name, text = m.group(1).strip(), m.group(2).strip()
            unpaged = name.endswith("(unpaged)")
            if unpaged:
                name = name[:-len("(unpaged)")].strip()
            out.append((name, text, unpaged))
        return out


class Interlude(object):
    """A stretch between sessions that was played but never recorded.

    Not a session and never given a session number — the count of what happened
    in it is not known. It sits in the chronicle where it belongs and says so.

        sources/chronicle/i41-the-road-north.md

            after: 41
            title: The Road North
            dates: 2026-03-02 to 2026-04-06
            ---
            ## Narrative
            ## Learned
            ## Setsuna
    """

    is_interlude = True

    def __init__(self, meta, sections, rw):
        self.meta = meta
        self.after = int(meta["after"])
        self.title = meta["title"]
        self.date = meta.get("dates", "")
        # Sorts between its neighbours and keys the ledger like a session, but
        # never renders as "Session N" — it is explicitly an unknown number of them.
        self.number = self.after + 0.5
        self.slug = "i%02d-%s" % (self.after, slugify(self.title))
        self.rw = rw
        self.recap = self.moments = self.timeline = ""


def _parse(raw):
    head, _, body = raw.partition("\n---\n")
    meta = {}
    for line in head.splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            meta[k.strip().lower()] = v.strip()
    sections, cur = {}, None
    for line in body.splitlines():
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            cur = m.group(1).strip().lower()
            sections[cur] = []
        elif cur:
            sections[cur].append(line)
    return meta, {k: "\n".join(v).strip() for k, v in sections.items()}


def load_interludes():
    d = os.path.join(ROOT, "sources", "chronicle")
    out = []
    if not os.path.isdir(d):
        return out
    for fn in sorted(os.listdir(d)):
        if not (fn.startswith("i") and fn.endswith(".md")):
            continue
        meta, sections = _parse(A.correct(io.open(os.path.join(d, fn), encoding="utf-8").read()))
        out.append(Interlude(meta, sections, Rewrite(meta, sections)))
    return out


def load_rewrites():
    """
    sources/chronicle/sNN-slug.md:

        session: 4
        witnessed: Matsu Koda; Shinjo Mono
        apart: Yushi Sama
        epigraph: ...
        ---
        ## Narrative
        ...
        ## Setsuna
        ...
    """
    d = os.path.join(ROOT, "sources", "chronicle")
    out = {}
    if not os.path.isdir(d):
        return out
    for fn in sorted(os.listdir(d)):
        if not (fn.startswith("s") and fn.endswith(".md")):
            continue   # iNN-*.md are interludes, loaded by load_interludes()
        raw = A.correct(io.open(os.path.join(d, fn), encoding="utf-8").read())
        head, _, body = raw.partition("\n---\n")
        meta = {}
        for line in head.splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                meta[k.strip().lower()] = v.strip()
        sections, cur = {}, None
        for line in body.splitlines():
            m = re.match(r"^##\s+(.+?)\s*$", line)
            if m:
                cur = m.group(1).strip().lower()
                sections[cur] = []
            elif cur:
                sections[cur].append(line)
        sections = {k: "\n".join(v).strip() for k, v in sections.items()}
        out[int(meta["session"])] = Rewrite(meta, sections)
    return out


def paras(text, url, reg):
    """Blank-line separated markdown paragraphs -> linked <p>."""
    out = []
    for block in re.split(r"\n\s*\n", text.strip()):
        block = block.strip()
        if not block:
            continue
        cls, tag = "", "p"
        if block.startswith("!lede "):
            block, cls = block[6:], ' class="lede"'
        elif block.startswith("!note "):
            # A standing caveat about the record itself, not about the fiction.
            block, cls, tag = block[6:], ' class="raw-note"', "div"
        body = link_wikilinks(md_inline(esc(block).replace("\n", " ")), url, reg)
        out.append("<%s%s>%s</%s>" % (tag, cls, body, tag))
    return "\n".join(out)


# ------------------------------------------------------------------ knowledge

class Ledger(object):
    """
    Who Setsuna dealt with, session by session. Built only from adjudicated
    session files — an un-adjudicated session is PENDING, never assumed.
    """
    KNOWN, REMEMBERED, APART, PENDING = "known", "remembered", "apart", "pending"

    def __init__(self, sessions, rewrites, reg):
        self.sessions = sessions
        self.rewrites = rewrites
        self.reg = reg
        self.state = collections.defaultdict(dict)   # page -> {session_no: state}
        self.learned = collections.defaultdict(dict) # page -> {session_no: line}
        self.unpaged = collections.defaultdict(list) # session_no -> [(name, line)]
        for s in sessions:
            rw = rewrites.get(s.number)
            appear = self.appearances(s)
            if rw is None:
                for pg in appear:
                    self.state[pg][s.number] = self.PENDING
                continue
            # The company tells each other what it learns, so the default is that
            # Setsuna ends the session knowing it. `unknown:` lists the exceptions —
            # what a companion deliberately kept to themselves.
            default = self.REMEMBERED if rw.meta.get("mode") == "flashback" else self.KNOWN
            kept = set()
            for n in rw.names("unknown"):
                pg = reg.get(norm(n))
                if pg is None:
                    raise KeyError("session %d: 'unknown:' names %r, which has no page"
                                   % (s.number, n))
                kept.add(pg)
            for name, line, unpaged in rw.learned():
                if unpaged:
                    self.unpaged[s.number].append((name, line))
                    continue
                pg = reg.get(norm(name))
                if pg is None:
                    raise KeyError("session %d: 'Learned' names %r, which has no page. "
                                   "Fix the spelling, or mark it '%s (unpaged)' if the "
                                   "record never names them." % (s.number, name, name))
                self.learned[pg][s.number] = line
            for pg in appear:
                self.state[pg][s.number] = self.APART if pg in kept else default

    def appearances(self, s):
        """Every entity page a session names.

        Normally that is read off the export's three source files. Sessions
        played after the export was pulled have none, so the hand-written
        rewrite is the only record and stands in for them.
        """
        rw = self.rewrites.get(s.number)
        texts = (s.recap, s.moments, s.timeline)
        if not any(t.strip() for t in texts) and rw is not None:
            texts = (rw.text(),)
        seen = set()
        for txt in texts:
            for m in A.LINK_RE.findall(txt):
                pg = self.reg.get(norm(m[0].strip()))
                if pg is not None:
                    seen.add(pg)
        return seen

    def for_page(self, pg):
        return sorted(self.state.get(pg, {}).items())

    def counts(self, pg):
        c = collections.Counter(self.state.get(pg, {}).values())
        return c[self.KNOWN], c[self.APART], c[self.PENDING], c[self.REMEMBERED]


# ------------------------------------------------------------------ entity pages

MASK_SLOTS = [("Motive", "why they act as they do"),
              ("Allegiance", "whom they truly answer to"),
              ("Capability", "what they can do under arms"),
              ("Standing with Setsuna", "what they would spend to help or harm her")]


def mask_bar(label, hint):
    return ('<div class="mask-row"><span class="mask-k">%s</span>'
            '<span class="mask-bar" title="%s" aria-label="not known"></span></div>'
            % (esc(label), esc(hint)))


def entity_body(p, reg, ledger, sessions_by_no):
    url = p.url
    known, apart, pending, remembered = ledger.counts(p)
    clan = p.clan or A.clan_of(p.title) or ""

    bits = []
    bits.append('<div class="wrap">')
    crumb = ('<p class="crumb"><a href="%s">Home</a><span class="sep">&#8250;</span>'
             '<a href="%s">%s</a><span class="sep">&#8250;</span>%s</p>'
             % (rel(url, "index.html"),
                rel(url, CATDIR[p.cat].split("/")[0] + "/index.html"),
                {"npc": "Dramatis Personae", "pc": "The Party", "location": "Gazetteer",
                 "faction": "Factions", "item": "Relics", "lore": "Documents"}[p.cat],
                esc(p.title)))
    bits.append(crumb)
    eyebrow = {"npc": "Dramatis Persona", "pc": "The Party", "location": "Gazetteer",
               "faction": "Faction", "item": "Relic", "lore": "Document"}[p.cat]
    sub = ('<p class="meta">%s</p>' % esc(clan)) if clan else ""
    if p.title in PLAYABLE:
        sub += ('<p style="margin-top:0.9rem"><a class="play-btn" href="%s">'
                'Open the sheet &amp; play</a></p>' % rel(url, PLAYABLE[p.title]))
    bits.append('<header class="masthead"><div class="eyebrow">%s</div><h1>%s</h1>%s</header>'
                % (eyebrow, esc(p.title), sub))
    bits.append('<div class="col">')

    if p.cat == "npc":
        lines = sorted(ledger.learned.get(p, {}).items())
        if lines:
            bits.append('<article class="panel"><h2>What is known</h2>')
            for no, line in lines:
                s = sessions_by_no[no]
                bits.append('<div class="learned"><a class="lr-s%s" href="%s">%s</a>'
                            '<span class="lr-t">%s</span></div>'
                            % (" lr-i" if s.is_interlude else "",
                               rel(url, "chronicle/%s.html" % s.slug),
                               "&#8212;" if s.is_interlude else "S%d" % no,
                               link_wikilinks(md_inline(esc(line)), url, reg)))
            bits.append('<p class="meta" style="margin-top:1rem">Each line is what she took '
                        'from the session it cites, and nothing else. The Archivist\'s own '
                        'account of this person is not reproduced here \u2014 it blends what she '
                        'saw with what she did not.</p>')
            bits.append("</article>")
        elif known:
            bits.append('<article class="panel"><h2>What is known</h2>'
                        '<p class="meta">She has been in a room with them, but nothing has '
                        'been set down yet.</p></article>')
        elif remembered:
            bits.append('<article class="panel remembered"><h2>Known by memory</h2>'
                        '<p class="meta">Setsuna never met this person. She carries them from '
                        'the memories of her ancestor <a class="ref" href="%s">Matsu Morozane</a>, '
                        'three centuries dead. What she holds is his, and it is that old.</p>'
                        "</article>" % rel(url, "party/matsu-morozane.html"))
        else:
            bits.append('<article class="panel unmet"><h2>Not met</h2>'
                        '<p class="meta">Setsuna has not met this person, and no companion has '
                        'brought word of them back to her. The record holds nothing she could '
                        'act on.</p></article>')
        bits.append('<article class="panel" style="margin-top:1.4rem"><h2>Encounters</h2>')
        rows = ledger.for_page(p)
        if not rows:
            bits.append('<p class="meta">No session names them.</p>')
        else:
            bits.append('<ul class="enc">')
            for no, st in rows:
                s = sessions_by_no[no]
                href = rel(url, "chronicle/%s.html" % s.slug)
                nm = "Between sessions" if s.is_interlude else "Session %d" % no
                if st in (Ledger.KNOWN, Ledger.REMEMBERED):
                    cls = "enc-k" if st == Ledger.KNOWN else "enc-r"
                    tail = esc(s.date) if st == Ledger.KNOWN else "remembered, not lived"
                    bits.append('<li class="%s"><a class="ref" href="%s">%s &middot; %s</a>'
                                '<span class="enc-t">%s</span></li>'
                                % (cls, href, nm, esc(s.title), tail))
                elif st == Ledger.PENDING:
                    bits.append('<li class="enc-p"><span class="enc-n">%s</span>'
                                '<span class="mask-bar short" aria-label="not yet transcribed"></span>'
                                '<span class="enc-t">not yet transcribed</span></li>' % nm)
                else:
                    bits.append('<li class="enc-a"><span class="enc-n">%s</span>'
                                '<span class="mask-bar" aria-label="not witnessed"></span>'
                                '<span class="enc-t">apart from her</span></li>' % nm)
            bits.append("</ul>")
        bits.append("</article>")
        bits.append('<article class="panel" style="margin-top:1.4rem"><h2>Not known</h2>'
                    '<p class="meta">Nothing lies behind these. They mark what the record '
                    'does not hold, so that a guess is never mistaken for a fact.</p>')
        for k, hint in MASK_SLOTS:
            bits.append(mask_bar(k, hint))
        bits.append("</article>")
    else:
        bits.append('<article class="panel">')
        bits.append(paras(p.raw, url, reg))
        bits.append("</article>")

    bits.append("</div></div>")
    return "\n".join(bits)


# ------------------------------------------------------------------ session pages

def entities_block(s, url, reg, rw=None):
    """The cast and ground a session names, grouped — the 'Entities' tab."""
    groups = collections.OrderedDict([("Characters", []), ("Locations", []),
                                      ("Factions", []), ("Relics", [])])
    gof = {"npc": "Characters", "pc": "Characters", "location": "Locations",
           "faction": "Factions", "item": "Relics", "lore": "Factions"}
    seen = set()
    texts = (s.recap, s.moments, s.timeline)
    if not any(t.strip() for t in texts) and rw is not None:
        texts = (rw.text(),)
    for txt in texts:
        for m in A.LINK_RE.findall(txt):
            pg = reg.get(norm(m[0].strip()))
            if pg is None or pg in seen:
                continue
            seen.add(pg)
            groups[gof[pg.cat]].append(pg)
    out = ['<h2>Entities named this session</h2>']
    for g, items in groups.items():
        if not items:
            continue
        out.append("<h3>%s</h3><ul class='tlist'>" % g)
        for pg in sorted(items, key=lambda x: x.title):
            out.append("<li><a class='ref' href='%s'>%s</a></li>"
                       % (rel(url, pg.url), esc(pg.title)))
        out.append("</ul>")
    return "\n".join(out)


def timeline_block(s, url, reg):
    """The export's nested timeline, rendered as arcs > scenes > beats."""
    out = ['<h2>Timeline</h2>']
    open_ul = False
    for line in s.timeline.splitlines():
        line = line.rstrip()
        if not line or line.startswith("# "):
            continue
        m3 = re.match(r"^###\s+(.*)$", line)
        m4 = re.match(r"^####\s+(.*)$", line)
        mb = re.match(r"^-\s+(.*)$", line)
        if m4:
            if open_ul:
                out.append("</ul>"); open_ul = False
            out.append("<h4 class='tl-scene'>%s</h4>"
                       % link_wikilinks(md_inline(esc(m4.group(1))), url, reg))
        elif m3:
            if open_ul:
                out.append("</ul>"); open_ul = False
            out.append("<h3 class='tl-arc'>%s</h3>"
                       % link_wikilinks(md_inline(esc(m3.group(1))), url, reg))
        elif mb:
            if not open_ul:
                out.append("<ul class='tl-beats'>"); open_ul = True
            out.append("<li>%s</li>"
                       % link_wikilinks(md_inline(esc(mb.group(1))), url, reg))
    if open_ul:
        out.append("</ul>")
    return "\n".join(out)


def session_page(s, prev, nxt, rewrites, reg):
    url = "chronicle/%s.html" % s.slug
    rw = rewrites.get(s.number)
    bits = ['<div class="wrap">',
            '<p class="crumb"><a href="../index.html">Home</a><span class="sep">&#8250;</span>'
            '<a href="index.html">Chronicle</a><span class="sep">&#8250;</span>%s</p>' % esc(s.title),
            '<header class="masthead"><div class="eyebrow">%s</div>'
            % ("Between Sessions" if s.is_interlude else "Session"),
            '<h1>%s</h1><p class="meta">%s<span class="sep">&middot;</span>%s</p></header>'
            % (esc(s.title),
               "An unrecorded stretch" if s.is_interlude else "Session %d" % s.number,
               esc(s.date)),
            '<div class="col"><article class="panel">']

    # Sessions played after the export was pulled have no Archivist timeline.
    has_tl = bool(s.timeline.strip())
    labels = ['<label for="ct-chr">Chronicle</label>']
    if has_tl:
        labels.append('<label for="ct-tl">Timeline</label>')
    labels.append('<label for="ct-ent">Entities</label>')
    tabs = ['<div class="chron-tabs">'
            '<input type="radio" id="ct-chr" name="ct" checked>'
            '<input type="radio" id="ct-tl" name="ct">'
            '<input type="radio" id="ct-ent" name="ct">'
            '<div class="tab-labels">%s</div>' % "".join(labels)]

    tabs.append('<div class="tab-panel tp-chr">')
    if rw:
        if rw.epigraph:
            tabs.append('<p class="epigraph">%s</p>'
                        % link_wikilinks(md_inline(esc(rw.epigraph)), url, reg))
        tabs.append(paras(rw.narrative, url, reg))
        if rw.coda:
            tabs.append('<h3 class="sec-h">Setsuna</h3>')
            tabs.append(paras(rw.coda, url, reg))
    else:
        tabs.append('<div class="raw-note"><b>Not yet rewritten.</b> What follows is the '
                    'Archivist\'s own summary, passed through unedited. It is a machine '
                    'account of the session and has not been checked against the table.</div>')
        body = re.sub(r"^#\s+.*$", "", s.recap, count=1, flags=re.M)
        tabs.append(paras(body, url, reg))
    tabs.append("</div>")

    tabs.append('<div class="tab-panel tp-tl">%s</div>'
                % (timeline_block(s, url, reg) if has_tl else ""))
    tabs.append('<div class="tab-panel tp-ent">%s</div>' % entities_block(s, url, reg, rw))
    tabs.append("</div>")
    bits.append("\n".join(tabs))
    bits.append("</article>")

    pager = ['<div class="pager">']
    pager.append('<a class="ref" href="%s.html">&#8249; %s</a>' % (prev.slug, esc(prev.title))
                 if prev else "<span></span>")
    pager.append('<a class="ref" href="%s.html">%s &#8250;</a>' % (nxt.slug, esc(nxt.title))
                 if nxt else "<span></span>")
    pager.append("</div>")
    bits.append("\n".join(pager))
    bits.append("</div></div>")

    desc = ("The Fragile Peace between sessions, %s." % s.date if s.is_interlude
            else "Session %d of The Fragile Peace, played %s." % (s.number, s.date))
    return shell(url, "%s — The Fragile Peace" % s.title, desc, "chronicle", "\n".join(bits))


def chronicle_index(entries, rewrites):
    url = "chronicle/index.html"
    sessions = [e for e in entries if not e.is_interlude]
    done = sum(1 for s in sessions if s.number in rewrites)
    rows = []
    for s in entries:
        rw = rewrites.get(s.number)
        state = "" if rw else '<span class="chip raw">raw</span>'
        if s.number in FLASHBACK_SESSIONS:
            state += '<span class="chip back">three centuries back</span>'
        if s.is_interlude:
            state += '<span class="chip gap">no record</span>'
        rows.append(
            '<a class="chron-row%s%s" href="%s.html"><span class="cn">%s</span>'
            '<span class="ct">%s</span>%s<span class="cd">%s</span></a>'
            % ("" if rw else " is-raw", " is-gap" if s.is_interlude else "",
               s.slug,
               "Between" if s.is_interlude else "Session %d" % s.number,
               esc(s.title), state, esc(s.date)))
    body = """<div class="wrap">
<p class="crumb"><a href="../index.html">Home</a><span class="sep">&#8250;</span>Chronicle</p>
<header class="masthead"><div class="eyebrow">The Record of Play</div>
<h1>Chronicle</h1>
<p class="sub">Session by session &mdash; the tale as it is told at the table.</p></header>
<div class="flourish"></div>
<div class="col">
<p class="epigraph">A peace is a document before it is a fact. Every clause in it is a place where it can fail.</p>
<p class="meta">%d sessions, %s 2025 to %s 2026. %d rewritten; the rest carry the Archivist's
machine summary until they are.</p>
<div class="chron">%s</div>
</div>
</div>""" % (len(sessions), sessions[0].date[:7], sessions[-1].date[:7], done, "\n".join(rows))
    return shell(url, "Chronicle — The Fragile Peace",
                 "The record of play, session by session.", "chronicle", body)


# ------------------------------------------------------------------ index pages

def initial(t):
    t = re.sub(r"^(The|A)\s+", "", t)
    return t[0].upper() if t else "?"


def people_index(pages, ledger, url, active, title, eyebrow, sub, groups):
    """groups: list of (heading, blurb, [pages])."""
    bits = ['<div class="wrap">',
            '<p class="crumb"><a href="../index.html">Home</a>'
            '<span class="sep">&#8250;</span>%s</p>' % esc(title),
            '<header class="masthead"><div class="eyebrow">%s</div><h1>%s</h1>'
            '<p class="sub">%s</p></header>' % (eyebrow, esc(title), sub),
            '<div class="flourish"></div>', '<div class="col">']
    for heading, blurb, items in groups:
        if not items:
            continue
        bits.append('<h2 class="group-h">%s</h2>' % esc(heading))
        if blurb:
            bits.append('<p class="group-sub">%s</p>' % blurb)
        bits.append('<div class="roster">')
        for p in items:
            k, a, pend, rem = ledger.counts(p)
            clan = p.clan or A.clan_of(p.title) or ""
            if k:
                state, note = "met", "known from %d session%s" % (k, "" if k == 1 else "s")
            elif rem:
                state, note = "remembered", "by memory only"
            elif pend:
                state, note = "pending", "not yet transcribed"
            else:
                state, note = "unmet", "no word of them"
            bits.append(
                '<a class="rost %s%s" href="%s"><span class="ro-n">%s</span>'
                '<span class="ro-c">%s</span><span class="ro-s">%s</span></a>'
                % (state, " playable" if p.title in PLAYABLE else "",
                   rel(url, p.url), esc(p.title), esc(clan),
                   esc("playable" if p.title in PLAYABLE else note)))
        bits.append("</div>")
    bits.append("</div></div>")
    return shell(url, "%s — The Fragile Peace" % title, sub, active, "\n".join(bits))


def list_index(pages, url, active, title, eyebrow, sub, intro):
    by_letter = collections.OrderedDict()
    for p in sorted(pages, key=lambda x: norm(x.title)):
        by_letter.setdefault(initial(p.title), []).append(p)
    bits = ['<div class="wrap">',
            '<p class="crumb"><a href="../index.html">Home</a>'
            '<span class="sep">&#8250;</span>%s</p>' % esc(title),
            '<header class="masthead"><div class="eyebrow">%s</div><h1>%s</h1>'
            '<p class="sub">%s</p></header>' % (eyebrow, esc(title), sub),
            '<div class="flourish"></div><div class="col">',
            '<p class="intro" style="margin-bottom:1.4rem">%s</p>' % intro]
    for letter, items in by_letter.items():
        bits.append('<h2 class="group-h">%s</h2><ul class="tlist">' % letter)
        for p in items:
            bits.append("<li><a class='ref' href='%s'>%s</a></li>"
                        % (rel(url, p.url), esc(p.title)))
        bits.append("</ul>")
    bits.append("</div></div>")
    return shell(url, "%s — The Fragile Peace" % title, sub, active, "\n".join(bits))


# ------------------------------------------------------------------ main

GENERATED = ["chronicle", "party", "dramatis-personae", "atlas", "lore"]


def main():
    exported = A.discover()
    local = A.discover_local()
    have = {norm(p.title) for p in exported}
    for p in local:
        if norm(p.title) in have:
            raise KeyError("sources/entities/%s.md duplicates an export page; the "
                           "export's copy is authoritative" % p.title)
    pages = exported + local
    sessions = A.discover_sessions()
    for p in pages:
        p.url = "%s/%s.html" % (CATDIR[p.cat], slugify(p.title))
    reg = A.build_registry(pages)

    # fuzzy pass over whatever the curated map missed
    unres = collections.Counter()
    for s in sessions:
        for t in (s.recap, s.moments, s.timeline):
            link_wikilinks(t, "x.html", reg, unres)
    for p in pages:
        link_wikilinks(p.raw, p.url, reg, unres)
    fuzzy = []
    A.add_fuzzy_aliases(reg, set(unres.keys()), log=fuzzy)

    rewrites = load_rewrites()

    # Sessions played after the export was pulled exist only as hand-written
    # files, and carry their own title and date in front matter.
    have = {s.number for s in sessions}
    for no in sorted(set(rewrites) - have):
        rw = rewrites[no]
        for k in ("title", "date"):
            if not rw.meta.get(k):
                raise KeyError("session %d is not in the export, so its file must "
                               "carry a '%s:' line" % (no, k))
        s = A.Session(None, rw.meta["title"], no, rw.meta["date"])
        s.slug = "s%02d-%s" % (no, A.slugify(s.title))
        sessions.append(s)
    sessions.sort(key=lambda s: s.number)

    # Interludes are stretches that were played but never recorded. They take a
    # ledger key between their neighbours and are otherwise ordinary entries.
    interludes = load_interludes()
    for iv in interludes:
        rewrites[iv.number] = iv.rw
    entries = sorted(sessions + interludes, key=lambda e: e.number)

    ledger = Ledger(entries, rewrites, reg)
    by_no = {e.number: e for e in entries}

    for d in GENERATED:
        p = os.path.join(ROOT, d)
        if os.path.isdir(p):
            shutil.rmtree(p)

    n = 0
    # ---- sessions and interludes, in one prev/next chain
    for i, e in enumerate(entries):
        write("chronicle/%s.html" % e.slug,
              session_page(e, entries[i - 1] if i else None,
                           entries[i + 1] if i + 1 < len(entries) else None,
                           rewrites, reg)); n += 1
    write("chronicle/index.html", chronicle_index(entries, rewrites)); n += 1

    # ---- entity pages
    for p in pages:
        write(p.url, shell(p.url, "%s — The Fragile Peace" % p.title,
                           A.strip_wikilinks(p.raw).strip().replace("\n", " ")[:180],
                           CATNAV[p.cat], entity_body(p, reg, ledger, by_no))); n += 1

    npcs = [p for p in pages if p.cat == "npc"]
    pcs = {p.title: p for p in pages if p.cat == "pc"}
    current = [pcs[t] for t in CURRENT_PARTY if t in pcs]
    ancestral = [pcs[t] for t in FLASHBACK_PARTY if t in pcs]
    placed = set(CURRENT_PARTY) | set(FLASHBACK_PARTY)
    offstage = sorted((p for t, p in pcs.items() if t not in placed),
                      key=lambda x: norm(x.title))

    write("party/index.html", people_index(
        pages, ledger, "party/index.html", "party", "The Party",
        "Those Setsuna Travels With",
        "Those who hold the road now, and those who walked part of it.",
        [("At the table", "The company as it stands.", current),
         ("The ancestral company",
          "Sessions 10&ndash;17 are not the present. They run three centuries back, on the "
          "Snow Plain, and the table played its own forebears through them &mdash; Setsuna "
          "living the memories of <b>Matsu Morozane</b>, her Lion ancestor. What she took "
          "from that arc she remembers rather than witnessed, and the site marks it so. "
          "It is no longer only memory: the present war has come back to that same ground, "
          "and settled it the same way &mdash; Lion against Unicorn, one commander killing "
          "the other in single combat, a field of Lion dead afterwards. Setsuna has now "
          "been on the <a class='ref' href='../atlas/snow-plain.html'>Snow Plain</a> twice, "
          "and is the only person in the column who knows it settled nothing the first time.",
          ancestral),
         ("Off stage", "Walked with the party and are no longer at the table. "
                       "What they did is still in the record.", offstage)])); n += 1

    met = sorted((p for p in npcs if ledger.counts(p)[0]), key=lambda x: norm(x.title))
    unmet = sorted((p for p in npcs if not ledger.counts(p)[0]), key=lambda x: norm(x.title))
    write("dramatis-personae/index.html", people_index(
        pages, ledger, "dramatis-personae/index.html", "dramatis", "Dramatis Personae",
        "The Cast", "Everyone the record names. What is legible is what Setsuna was "
        "there for; the rest is masked, and there is nothing behind the mask.",
        [("Known to her", "She has dealt with these, or a companion brought word back. Knowing of someone is enough to be listed here \u2014 it does not mean she has met them.", met),
         ("Named only", "The record carries them, but nothing has reached her. Their pages are "
                        "mask and outline until a session brings them within her hearing.", unmet)])); n += 1

    locs = [p for p in pages if p.cat == "location"]
    facs = [p for p in pages if p.cat == "faction"]
    items = [p for p in pages if p.cat == "item"]
    docs = [p for p in pages if p.cat == "lore"]

    write("atlas/index.html", list_index(
        locs, "atlas/index.html", "map", "Gazetteer", "Atlas of Rokugan",
        "The ground the embassy has crossed.",
        "Every place the record names. Find them on the "
        "<a class='ref' href='../map/index.html'>map of Rokugan</a>.")); n += 1

    lore_body = """<div class="wrap">
<p class="crumb"><a href="../index.html">Home</a><span class="sep">&#8250;</span>Lore</p>
<header class="masthead"><div class="eyebrow">The Emerald Empire</div>
<h1>Lore of Rokugan</h1>
<p class="sub">The world beneath the chronicle &mdash; its clans and families, the things
they carry, and the code by which a samurai is measured.</p></header>
<div class="flourish"></div>
<div class="col">
<div class="grid">
<a class="card" href="factions/index.html"><span class="cat">Factions</span><h3>Clans &amp; Families</h3><p>%d bodies the record names &mdash; Great Clans, families, units, and the companies met on the road.</p></a>
<a class="card" href="relics/index.html"><span class="cat">Relics</span><h3>Things Carried</h3><p>%d items, documents, poisons and talismans that have turned a scene.</p></a>
<a class="card" href="../atlas/index.html"><span class="cat">Gazetteer</span><h3>Places</h3><p>%d places, from Otosan Uchi to the Snow Plain.</p></a>
</div>
<article class="panel" style="margin-top:1.6rem" id="bushido">
<h2>Bushid&#333;</h2>
<p>The code names the virtues by which a samurai's life is measured &mdash; among them
Sincerity, Duty and Loyalty, Compassion, Courage, Courtesy, Honor, and Righteousness.
Few hold all of them perfectly at once, and a samurai's character is usually legible in
which tenet they hold <em>paramount</em> and which they hold <em>least</em>.</p>
</article>
<article class="panel" style="margin-top:1.4rem" id="celestial-order">
<h2>The Celestial Order</h2>
<p>Heaven, Earth, and the mortal realm are bound in one order, watched over by Lord Sun
and Lady Moon and the Fortunes and kami between them. Omens are read as that order's
language, and the reading belongs to theologians, shugenja, and monks, who serve the
Empire as its interpreters of Heaven's will.</p>
</article>
</div></div>""" % (len(facs), len(items), len(locs))
    write("lore/index.html", shell("lore/index.html", "Lore — The Fragile Peace",
                                   "The Emerald Empire — clans, families, relics and places.",
                                   "lore", lore_body)); n += 1

    write("lore/factions/index.html", list_index(
        facs, "lore/factions/index.html", "lore", "Factions", "Lore",
        "Clans, families, units and companies.",
        "Every body the record names, from the Great Clans down to a band of "
        "ronin hired for one night.")); n += 1
    write("lore/relics/index.html", list_index(
        items, "lore/relics/index.html", "lore", "Relics", "Lore",
        "Things carried, given, stolen and used.",
        "Items, documents, poisons and talismans that have turned a scene.")); n += 1
    if docs:
        write("lore/documents/index.html", list_index(
            docs, "lore/documents/index.html", "lore", "Documents", "Lore",
            "Set-down accounts.", "Longer pieces kept whole.")); n += 1

    # ---- report
    unres2 = collections.Counter()
    tot = 0
    for s in sessions:
        for t in (s.recap, s.moments, s.timeline):
            link_wikilinks(t, "x.html", reg, unres2); tot += len(A.LINK_RE.findall(t))
    for p in pages:
        link_wikilinks(p.raw, p.url, reg, unres2); tot += len(A.LINK_RE.findall(p.raw))

    print("pages written        : %d" % n)
    written = sum(1 for s in sessions if s.number in rewrites)
    print("sessions             : %d (%d rewritten, %d raw), %d interlude(s)"
          % (len(sessions), written, len(sessions) - written, len(interludes)))
    print("entities             : %s"
          % ", ".join("%s %d" % (c, sum(1 for p in pages if p.cat == c))
                      for c in ["npc", "pc", "location", "faction", "item", "lore"]))
    print("fuzzy aliases        : %d" % len(fuzzy))
    print("wikilinks            : %d, unresolved %d (%.1f%%)"
          % (tot, sum(unres2.values()), 100.0 * sum(unres2.values()) / tot))
    print("NPCs met by Setsuna  : %d of %d" % (len(met), len(npcs)))


if __name__ == "__main__":
    main()
