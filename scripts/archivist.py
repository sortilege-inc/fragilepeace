"""
archivist.py — read the Obsidian/Archivist export in ingest/ into Page objects,
build the name registry (including short-form aliases), and resolve [[wikilinks]].

The export is the raw campaign pull. Nothing here decides what Setsuna knows;
that lives in the hand-authored session files under sources/chronicle/.
"""

import os, re, io, html, unicodedata, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "ingest", "The Fragile Peace-obsidian-export",
                   "The Fragile Peace - Archivist")

CLANS = ["Crane", "Lion", "Unicorn", "Scorpion", "Dragon", "Phoenix", "Crab",
         "Mantis", "Badger", "Centipede", "Dragonfly", "Fox", "Tortoise"]

# Families, for reading a clan off a personal name.
FAMILY_CLAN = {
    "Doji": "Crane", "Kakita": "Crane", "Daidoji": "Crane", "Asahina": "Crane",
    "Matsu": "Lion", "Akodo": "Lion", "Ikoma": "Lion", "Kitsu": "Lion",
    "Shinjo": "Unicorn", "Ide": "Unicorn", "Utaku": "Unicorn", "Iuchi": "Unicorn",
    "Moto": "Unicorn", "Otaku": "Unicorn",
    "Bayushi": "Scorpion", "Shosuro": "Scorpion", "Shoshuro": "Scorpion",
    "Soshi": "Scorpion", "Yogo": "Scorpion",
    "Togashi": "Dragon", "Mirumoto": "Dragon", "Agasha": "Dragon", "Kitsuki": "Dragon",
    "Shiba": "Phoenix", "Asako": "Phoenix", "Isawa": "Phoenix", "Kaito": "Phoenix",
    "Hida": "Crab", "Hiruma": "Crab", "Kuni": "Crab", "Kaiu": "Crab",
    "Miya": "Imperial", "Seppun": "Imperial", "Otomo": "Imperial",
    "Tonbo": "Dragonfly", "Kaeru": "Ronin",
}


def slugify(s):
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.replace("’", "").replace("'", "")
    s = re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").lower()
    return s or "x"


def norm(s):
    """Comparison key: casefolded, punctuation-flattened."""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", s.replace("’", "'").lower()).strip()


class Page(object):
    def __init__(self, cat, title, raw, srcpath):
        self.cat = cat            # npc | pc | location | faction | item | lore
        self.title = title
        self.raw = raw
        self.srcpath = srcpath
        self.url = None           # root-relative, set by the builder
        self.aliases = set()
        self.clan = ""            # override; otherwise read off the family name

    def __repr__(self):
        return "<Page %s %r>" % (self.cat, self.title)


def _read(p):
    return io.open(p, encoding="utf-8").read()


# The export's filenames are not always the correct name. Owner's ruling
# 2026-08-12: "Shishoro" is not a Scorpion family; the family is Shoshuro.
# Left-hand side is the export's filename stem, right-hand side is what the
# site should call the person.
RENAMES = {
    "Shishoro Aishi": "Shoshuro Aishi",
    "Shosuro Aishi": "Shoshuro Aishi",
    # The export files the governor three ways — with and without the title,
    # and as "Miya Tetsuna" in session 29, where it calls them the governor
    # outright. Owner confirmed Tetsuya is the governor.
    "Miya Tetsuya": "Governor Miya Tetsuya",
    "Miya Tetsuna": "Governor Miya Tetsuya",
    # Owner's ruling 2026-08-12: Ryo and Ryu are one retainer, spelled Ryu.
    "Ryo": "Ryu",
    # Owner's ruling 2026-08-12: Hana no Ame is Tonbo Higuchi's pen name.
    # One person, filed by the export under both.
    "Hana no Ame": "Tonbo Higuchi",
    "Higuchi": "Tonbo Higuchi",
}


def discover():
    """Load every entity file in the export, under their corrected names."""
    pages = []
    for sub, cat in [("Characters/PCs", "pc"), ("Characters/NPCs", "npc"),
                     ("Locations", "location"), ("Factions", "faction"),
                     ("Items", "item"), ("Journals", "lore")]:
        d = os.path.join(SRC, sub)
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if not fn.endswith(".md"):
                continue
            title = fn[:-3]
            pages.append(Page(cat, RENAMES.get(title, title),
                              _read(os.path.join(d, fn)),
                              os.path.join(d, fn)))

    # A rename can collapse two files onto one person. Merge rather than lose one.
    merged, out = {}, []
    for pg in pages:
        key = (pg.cat, norm(pg.title))
        if key in merged:
            merged[key].raw += "\n\n" + pg.raw
            continue
        merged[key] = pg
        out.append(pg)
    return out


def discover_local():
    """Entity pages the export does not hold.

    The export is a snapshot. Sessions played after it introduce people and
    places it has never heard of — Karahaya, who put a scar across the party's
    yojimbo, is in none of its 543 files. Those live in sources/entities/ as

        cat: npc
        clan: Ronin
        ---
        prose (used for non-npc pages; npc pages are built from the ledger)

    and are merged into the same registry, so they link and are linked like
    anything else.
    """
    d = os.path.join(ROOT, "sources", "entities")
    pages = []
    if not os.path.isdir(d):
        return pages
    for fn in sorted(os.listdir(d)):
        if not fn.endswith(".md"):
            continue
        raw = _read(os.path.join(d, fn))
        head, _, body = raw.partition("\n---\n")
        meta = {}
        for line in head.splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                meta[k.strip().lower()] = v.strip()
        pg = Page(meta.get("cat", "npc"), fn[:-3], body.strip(),
                  os.path.join(d, fn))
        pg.clan = meta.get("clan", "")
        pages.append(pg)
    return pages


# ------------------------------------------------------------------ sessions

SESSION_RE = re.compile(r"^(.*?)\s*-\s*Session\s*(\d+)\s*-\s*([\d-]+)$")
DATED_RE = re.compile(r"^(.*?)\s*-\s*([\d]{4}-[\d]{2}-[\d]{2})$")


class Session(object):
    def __init__(self, key, title, number, date):
        self.key = key            # the export's filename stem, joins the 3 folders
        self.title = title
        self.number = number
        self.date = date
        self.recap = ""
        self.moments = ""
        self.timeline = ""
        self.slug = None
        self.rewrite = None       # loaded from sources/chronicle/
        self.is_interlude = False

    def __repr__(self):
        return "<Session %s %r>" % (self.number, self.title)


def discover_sessions():
    """
    39 sessions: 33 carry an explicit 'Session N', 6 later ones carry only a date.
    The dated-only ones continue the numbering in date order.
    """
    d = os.path.join(SRC, "Recaps")
    found = []
    for fn in sorted(os.listdir(d)):
        if not fn.endswith(".md") or fn == "World Summary.md":
            continue
        key = fn[:-3]
        m = SESSION_RE.match(key)
        if m:
            found.append(Session(key, m.group(1).strip(), int(m.group(2)), m.group(3)))
            continue
        m = DATED_RE.match(key)
        if m:
            found.append(Session(key, m.group(1).strip(), None, m.group(2)))
            continue
        raise ValueError("unparsed recap filename: %r" % fn)

    numbered = sorted([s for s in found if s.number], key=lambda s: s.number)
    dated = sorted([s for s in found if not s.number], key=lambda s: s.date)
    nxt = (numbered[-1].number if numbered else 0) + 1
    for s in dated:
        s.number = nxt
        nxt += 1

    sessions = sorted(numbered + dated, key=lambda s: s.number)
    for s in sessions:
        s.slug = "s%02d-%s" % (s.number, slugify(s.title))
        s.recap = _read(os.path.join(SRC, "Recaps", s.key + ".md"))
        for fld, folder in [("moments", "Moments"), ("timeline", "Timeline")]:
            p = os.path.join(SRC, folder, s.key + ".md")
            if os.path.exists(p):
                setattr(s, fld, _read(p))
    return sessions


# ------------------------------------------------------------------ registry

# Hand-curated aliases for targets the export spells differently from its own
# filenames, or refers to by a description. Left-hand side is the [[link text]];
# right-hand side must be an exact page title. Anything not listed and not caught
# by the fuzzy pass renders as a dotted "not yet chronicled" span.
ALIASES = {
    "Emperor Hantei": "Emperor Hantei Hantei Hantei Hantei",
    "Emperor Hantei Hantei": "Emperor Hantei Hantei Hantei Hantei",
    "Emperor": "Emperor Hantei Hantei Hantei Hantei",
    "Emerald Magistrate": "Emerald Magistrates",
    "Magistrates": "Emerald Magistrates",
    "Dragonlands": "Dragon Lands",
    "Imperial House": "Imperial Houses",
    "The Burning Sands": "Burning Sands",
    "Snow Plains": "Snow Plain",
    "Battle of Snow Plains": "Battle of the Snow Plains",
    "Docks": "The Docks",
    "Teahouse": "Teahouse With No Name",
    "Hall of Scribes": "Ikoma Hall of Scribes",
    "Ikoma House Of Scribes": "Ikoma Hall of Scribes",
    "Ikoma Hall Of Scribes": "Ikoma Hall of Scribes",
    "Ide delegation": "Ide Family",
    "Crane Quarters": "Crane Couple’s Guest Quarters",
    "Crane Guest Rooms": "Crane Couple’s Guest Quarters",
    "Crane Couple's Quarters": "Crane Couple’s Guest Quarters",
    "Monban's Room": "Bayushi Monban’s Room",
    "Slowtide Harbor": "Slow Tide Harbor",
    "Swift Sword Castle": "Castle of the Swift Sword",
    "Governor’s Manor": "Governor’s Mansion",
    "Governor’s residence": "Governor’s Mansion",
    "Virtuous Contemplation": "Garden Of Virtuous Contemplation",
    "The Ifrit": "Ifrit",
    "Efreet": "Ifrit",
    "General Shinjo Kamu": "Shinjo Kamo",
    "Shinjo Kamu": "Shinjo Kamo",
    "General Matsu Sakura": "Matsu Sakura",
    "Doji Shin": "Daidoji Shin",
    "Katsuki Kage": "Kitsuki Kaage",
    "Katsuki": "Kitsuki Kaage",
    "Katsuki Wataru": "Kitsuki Wataru",
    # The export writes the Akodo family as "Okoto" in places.
    "Akodo Sakuon": "Okoto Sakuon",
    "Okoto Kayamayako": "Akodo Kayamayako",
    # Owner's ruling 2026-08-12: Miya Tetsuya is the governor and there is
    # no Miya Amaya — the export invented her across 12 references.
    "Governor Miya Amaya": "Governor Miya Tetsuya",
    "Miya Amaya": "Governor Miya Tetsuya",
    "Miya Tetsuya": "Governor Miya Tetsuya",
    "Shishoro Aishi": "Shoshuro Aishi",
    "Shosuro Aishi": "Shoshuro Aishi",
    "Aishi": "Shoshuro Aishi",
    "the Lady of Decay": "Lady of Decay",
    "Ryo": "Ryu",
    # The trader has no page of his own; the export files his premises.
    "Hideyoshi Aki": "Hideyoshi Aki’s Counting House And Warehouse",
    "Hana no Ame": "Tonbo Higuchi",
    "Hanano Ame": "Tonbo Higuchi",
    "Higuchi": "Tonbo Higuchi",
    # Morozane's lion, which the sources spell three ways: the export has both
    # "Shiguro Chinmoku" and "Shigo no Tomoku" as separate NPC files, and his
    # Foundry actor calls it "Shigo no Chinmoku". Merged onto the first, which
    # is the page that exists. Worth renaming once the owner picks one.
    "Shigo no Tomoku": "Shiguro Chinmoku",
    "Shigo no Chinmoku": "Shiguro Chinmoku",
    "Diamond Mines": "Old Diamond Mines",
    # Owner's ruling 2026-08-12: Yui is the correct spelling; the export's
    # "Kitsu Yue" (94 instances) is the same person. Pinned rather than left
    # to the fuzzy pass, so the merge is a decision and not a guess.
    "Kitsu Yue": "Kitsu Yui",
    "Kitsuyue": "Kitsu Yui",
    "Yue": "Kitsu Yui",
    # Session 41's notes spell the governor's niece "Miya Masato". The export has
    # a Miya Misato (16, the niece, carries the writ) and a separate Doji Masato
    # (Crane, married to Doji Miho) — the woman in the tower says "tell your
    # uncle", so it is Misato. Pinned so the two never collapse into each other.
    "Miya Masato": "Miya Misato",
    # Same session shortens Daidoji Shin. The export runs 81 "Daidoji Shin" to
    # 4 "Doji Shin", and has no Doji Shin page.
    "Doji Shin": "Daidoji Shin",
}

# Names that look like entities but are common nouns or one-off props; never link.
NEVER_LINK = {
    "family", "kitchen", "tail", "quack", "proprietor", "the proprietor",
    "elderly proprietor", "his niece", "imperials", "local police officer",
    "ronin officer", "new henchman", "hq", "post road station", "pond area",
    "guest quarters", "teahouse",
}


def add_fuzzy_aliases(reg, targets, cutoff=0.88, log=None):
    """
    The export misspells its own names (Akoto Akihito, Shishuro Amane,
    Ikoma Akiyaku, Kitsuko Ayako). Map an unresolved target onto a real title
    when the match is close and unambiguous. Every alias is logged for audit.
    """
    import difflib
    keys = [k for k in reg.keys()]
    for t in sorted(targets):
        n = norm(t)
        if n in reg or n in NEVER_LINK or len(n) < 6:
            continue
        m = difflib.get_close_matches(n, keys, n=2, cutoff=cutoff)
        if len(m) == 1 or (len(m) == 2 and reg[m[0]] is reg[m[1]]):
            reg[n] = reg[m[0]]
            if log is not None:
                log.append((t, reg[m[0]].title))


def build_registry(pages):
    """
    Map every name a [[wikilink]] might use onto a Page.
    Exact titles win; short forms are added only when unambiguous.
    """
    reg = {}
    for p in pages:
        reg[norm(p.title)] = p

    # clan short forms: [[Lion]] -> Lion Clan
    for c in CLANS:
        tgt = reg.get(norm(c + " Clan"))
        if tgt and norm(c) not in reg:
            reg[norm(c)] = tgt
            tgt.aliases.add(c)

    # family short forms: [[Kitsu]] -> Kitsu Family
    for p in list(pages):
        if p.cat == "faction" and p.title.endswith(" Family"):
            short = p.title[:-len(" Family")]
            if norm(short) not in reg:
                reg[norm(short)] = p
                p.aliases.add(short)

    # personal short forms: [[Setsuna]] -> Doji Setsuna, when exactly one match
    people = [p for p in pages if p.cat in ("npc", "pc")]
    by_token = collections.defaultdict(list)
    for p in people:
        parts = p.title.split()
        if len(parts) >= 2:
            by_token[norm(parts[-1])].append(p)
    for tok, cands in by_token.items():
        if len(cands) == 1 and tok not in reg:
            reg[tok] = cands[0]
            cands[0].aliases.add(tok)

    # curated aliases last, so they win over any short-form guess
    for frm, to in ALIASES.items():
        tgt = reg.get(norm(to))
        if tgt is None:
            raise KeyError("ALIASES target has no page: %r" % to)
        reg[norm(frm)] = tgt
        tgt.aliases.add(frm)
    return reg


# ------------------------------------------------------------------ linking

def rel(from_url, to_url):
    """Relative href between two root-relative urls."""
    a = from_url.strip("/").split("/")[:-1]
    b = to_url.strip("/").split("/")
    i = 0
    while i < len(a) and i < len(b) - 1 and a[i] == b[i]:
        i += 1
    return "/".join([".."] * (len(a) - i) + b[i:])


LINK_RE = re.compile(r"\[\[([^\]|]+?)(?:\|([^\]]*))?\]\]")


def link_wikilinks(text, cur_url, reg, unresolved=None):
    """
    [[Target]] / [[Target|Display]] -> <a class="ref"> when the target has a page,
    otherwise a dotted 'not yet chronicled' span. Never emits a broken href.
    """
    def sub(m):
        target = m.group(1).strip()
        display = (m.group(2) or target).strip()
        p = reg.get(norm(target))
        if p and p.url:
            return '<a class="ref" href="%s">%s</a>' % (
                html.escape(rel(cur_url, p.url), quote=True), html.escape(display))
        if unresolved is not None:
            unresolved[target] += 1
        return '<span class="ref-open" title="not yet chronicled">%s</span>' % html.escape(display)
    return LINK_RE.sub(sub, text)


def strip_wikilinks(text):
    return LINK_RE.sub(lambda m: (m.group(2) or m.group(1)).strip(), text)


# ------------------------------------------------------------------ markdown

def md_inline(s):
    """Bold/italic/code only — the export uses nothing else inline."""
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\*\w])\*(?!\s)(.+?)(?<!\s)\*(?![\*\w])", r"<em>\1</em>", s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    return s


def escape_keep_links(s):
    """Escape HTML, but leave [[wikilinks]] intact for a later pass."""
    return html.escape(s, quote=False)


def clan_of(name):
    fam = name.split()[0] if name.split() else ""
    return FAMILY_CLAN.get(fam)
