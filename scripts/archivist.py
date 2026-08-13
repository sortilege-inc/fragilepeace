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
        self.local = False        # hand-authored under sources/entities/, not
                                  # drawn from the export; the builder says so
                                  # in a meta line rather than making every
                                  # entry announce it in its own prose

    def __repr__(self):
        return "<Page %s %r>" % (self.cat, self.title)


# Spellings that are simply wrong, and what they should read as. RENAMES (below)
# only relabels a page's *title*; these rewrite the prose, so a corrected name is
# corrected everywhere it is displayed rather than only on its own page. Applied
# once, at read time, to every source file — inside [[wikilinks]] as well as out,
# since every replacement resolves to the same page the old one did.
#
# Only outright errors belong here. Legitimate short forms and alternate names
# ("Lion" for Lion Clan, "Higuchi", the pen name "Hana no Ame") stay as written
# and are handled by ALIASES instead. scripts/verify_site.py fails the build if
# any of these reappears in the generated site.
#
# Do not prune the entries that no longer match anything. Once a misspelling has
# been corrected at the source, its pattern matches nothing by definition — and
# it is precisely that pattern which verify_site's `names` check iterates to
# keep the spelling from coming back in the next session's notes. A rule here
# that fires zero times is the gate working, not dead weight. As of 2026-08-13
# eleven of them are in that state.
CORRECTIONS = [
    # Owner 2026-08-12, corrected 2026-08-13: the family is Shosuro. "Shishoro"
    # is not a family name, and the owner's first call of "Shoshuro" was withdrawn
    # once the L5R5e corpus was checked — it uses Shosuro throughout and Shoshuro
    # never. This normalises every Scorpion of that family to one spelling.
    (r"\bShishoro\b", "Shosuro"),
    (r"\bShoshuro\b", "Shosuro"),
    # Owner 2026-08-12: the governor is Tetsuya. The export invents "Tetsuna".
    (r"\bMiya Tetsuna\b", "Miya Tetsuya"),
    # Owner 2026-08-12: Yui is the spelling.
    (r"\bKitsuyue\b", "Kitsu Yui"),
    (r"\bYue\b", "Yui"),
    # Owner 2026-08-12: Ryo and Ryu are one retainer, spelled Ryu.
    (r"\bRyo\b", "Ryu"),
    # Owner 2026-08-13: the rōnin watch commander on the Unicorn side of the
    # Rich Frog is Kaeru Haya. The record used both spellings freely — s30
    # introduces her as Haia, s31 runs the dawn operation as Haya, and s31's own
    # coda cites "Haia's report" about the missing sailors. Six mentions each,
    # and the export cannot settle it either (53 Haia to 51 Haya), so this is
    # the owner's call. The export has a file under each name; correcting the
    # title as well as the prose lets discover() merge them into one page rather
    # than leaving half her record on each.
    (r"\bKaeru Haia\b", "Kaeru Haya"),
    # The Unicorn general at the Snow Plain. The transcription never got his
    # name and the export files him five ways — as a person twice, as a faction
    # once, and in the titles of his letters and his camp. All of it is Shinjo
    # Kamo: the Characters entry describes the commander unseated from his horse
    # with his banner on the saddle, which is what Morozane did to him in s17,
    # and the other describes the hand and the chop on the disputed treaty.
    # Longest form first, so the bare name does not eat the others.
    (r"\bShinjuku Kamu\b", "Shinjo Kamo"),
    (r"\bShinjo Kamu\b", "Shinjo Kamo"),
    (r"\bShinjukamu\b", "Shinjo Kamo"),
    # Spacing and truncation, each of which built a second page.
    (r"\bIkoma Aku Yaku\b", "Ikoma Akuyaku"),
    (r"\bSlow Tide Harbor\b", "Slowtide Harbor"),
    (r"\bDran Merchant River\b", "Drowned Merchant River"),
    # "Asawa" is not a family of the Phoenix; the Isawa are.
    (r"\bAsawa Family\b", "Isawa Family"),
    # Morozane's lion, spelled three ways across the sources. Owner 2026-08-13:
    # the lion is Shigo no Chinmoku, which is also what his Foundry actor says.
    (r"\bShigo no Tomoku\b", "Shigo no Chinmoku"),
    (r"\bShiguro Chinmoku\b", "Shigo no Chinmoku"),
    # The 2026-04 session summaries against the export and the earlier record.
    (r"\bMiya Masato\b", "Miya Misato"),
    (r"\bDoji Shin\b", "Daidoji Shin"),
    (r"\bMoto Gaharis\b", "Moto Gaheris"),
    (r"\bMatsu Matsumaro\b", "Matsu Maro"),
    (r"\bMatsumaro\b", "Matsu Maro"),     # must follow the line above
    (r"\bAtoya\b", "Otoya"),
    # The 2026-04-27 notes. Owner 2026-08-13: "Cosmi" is Kakita Kazumi (Crane
    # courtier, and the one with medicine in the record), and "Komo Tadayoshi"
    # is Ikoma Tadayoshi, spoken for by another player in his absence.
    (r"\bKakita Cosmi\b", "Kakita Kazumi"),   # must precede the bare form
    (r"\bCosmi\b", "Kakita Kazumi"),
    (r"\bKomo Tadayoshi\b", "Ikoma Tadayoshi"),
    (r"\bMia Misato\b", "Miya Misato"),
    (r"\bLordy Ikoma\b", "Lord Ikoma"),
    # Both are Great Clan Champions whose names the 2026-04-13 notes garbled. The
    # L5R5e corpus has Altansarnai and Toturi; it has neither of the other forms.
    (r"\bShinjo Alt[ae]n?sar(?:i|nia)\b", "Shinjo Altansarnai"),
    # Session 48 names the jilted groom the record has only called Lord Ikoma.
    (r"\bIkoma Asakichi\b", "Ikoma Anakazu"),
    (r"\bLord Ikoma\b", "Ikoma Anakazu"),
    (r"\bShiro Hametsu\b", "Shosuro Hametsu"),
    (r"\bIde Subame\b", "Ide Subane"),
    # Owner 2026-08-13: the GM mispronounces him across several sessions; the
    # Lion strong-arm negotiator is Ikoma Ujiaki.
    # Scoped to the Ikoma: Setsuna's sheet quotes L5R fiction containing an
    # unrelated Ide Ujiyasu, and a bare rule would have corrupted it.
    (r"\bIkoma Ujiyasu\b", "Ikoma Ujiaki"),
    (r"\bKodo Totori\b", "Akodo Toturi"),
]
CORRECTIONS = [(re.compile(a), b) for a, b in CORRECTIONS]


def correct(text):
    for rx, repl in CORRECTIONS:
        text = rx.sub(repl, text)
    return text


def _read(p):
    return correct(io.open(p, encoding="utf-8").read())


# The export's filenames are not always the correct name. Left-hand side is the
# export's filename stem, right-hand side is what the site should call the
# person. A rename here relabels the *title* only, and merges two export files
# onto one page — use CORRECTIONS above to fix a spelling in the prose.
RENAMES = {
    "Shishoro Aishi": "Shosuro Aishi",
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
    # Morozane's lion has an export file under each of its spellings. Merged by
    # title rather than by alias, so there is one page and not two.
    "Shigo no Tomoku": "Shigo no Chinmoku",
    "Shiguro Chinmoku": "Shigo no Chinmoku",
    # Session 47 names Monban's lord: the Shosuro daimyo is Shosuro Hametsu,
    # Bayushi Kachiko's brother. The export only ever calls him by his title.
    "Daimyo Shoshuro": "Shosuro Hametsu",
    # The export duplicated two people outright, suffixing the second file.
    "The Emperor (2)": "The Emperor",
    "Asahina Nao (2)": "Asahina Nao",
    # The governor's residence on Central Island, filed five times under five
    # names. Every one of them describes the same building: an island in the
    # middle of the river at the City of the Rich Frog, the home of Governor
    # Miya Tetsuya. The chronicle links it as the Governor's Mansion.
    "Governor’s Palace": "Governor’s Mansion",
    "Governor’s Manor": "Governor’s Mansion",
    "Governor’s residence": "Governor’s Mansion",
    "Miya Governor’s Palace": "Governor’s Mansion",
    # Short form and full name of one institution inside the Castle of the
    # Swift Sword.
    "War College": "Akodo War College",
    # The mines under the hill at the Snow Plain, which the chronicle calls the
    # Old Diamond Mines throughout.
    "Diamond Mines": "Old Diamond Mines",
    "diamond mines": "Old Diamond Mines",
    # The spirit and the box it was sealed into are one being. It negotiated in
    # session 33; it belongs with the people, not the relics.
    "The Ifrit": "Ifrit",
}

# Pages the export filed under the wrong kind, keyed by (export folder's cat,
# file stem) and mapped to the cat they should have had.
#
# discover() merges by (cat, title), so two files describing one thing under
# two different kinds build two pages no matter how the titles are corrected —
# the Ifrit was a "person" in Characters and a "relic" in Items, and Shinjo
# Kamo was a person and a faction at once. Recategorising before the merge
# collapses them. Applied to the file as the export names it, before RENAMES.
RECAT = {
    ("faction", "Shinjuku Kamu"): "npc",     # a man, not a body
    ("item", "The Ifrit"): "npc",            # the spirit, not its box
    ("item", "diamond mines"): "location",   # a place, not a possession
    ("faction", "War College"): "location",  # somewhere the party toured
    ("faction", "Akodo War College"): "location",
}

# Export files that a hand-authored sources/entities page replaces outright.
#
# The builder's normal rule is that the export wins a title collision, which is
# right when the collision is an accident. It is wrong when the export's entry
# is a misspelling of a real thing and the local page is the corrected one:
# "Asawa Family" is not a family of the Phoenix, the Isawa are, and correcting
# the name would otherwise build a second Isawa Family page out of machine
# prose beside the written one. Anything worth keeping from the export entry is
# folded into the local page before its name goes in here.
SUPERSEDED_BY_LOCAL = {
    "Asawa Family",
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
            stem = fn[:-3]
            if stem in SUPERSEDED_BY_LOCAL:
                continue
            # correct() the title too, so a spelling fix does not need its own
            # RENAMES entry as well — RENAMES is for retitling and merging.
            title = correct(RENAMES.get(stem, stem))
            pages.append(Page(RECAT.get((cat, stem), cat), title,
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
        pg = Page(meta.get("cat", "npc"), correct(fn[:-3]), body.strip(),
                  os.path.join(d, fn))
        pg.clan = meta.get("clan", "")
        pg.local = True
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
    "Swift Sword Castle": "Castle of the Swift Sword",
    "Governor’s Manor": "Governor’s Mansion",
    "Governor’s residence": "Governor’s Mansion",
    # RENAMES moves the page but leaves prose still linking the old title, so
    # every merged name needs its alias here as well as its rename above.
    "Governor’s Palace": "Governor’s Mansion",
    "Miya Governor’s Palace": "Governor’s Mansion",
    "War College": "Akodo War College",
    "Virtuous Contemplation": "Garden Of Virtuous Contemplation",
    "The Ifrit": "Ifrit",
    "Efreet": "Ifrit",
    "General Shinjo Kamo": "Shinjo Kamo",
    "General Matsu Sakura": "Matsu Sakura",
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
    "Aishi": "Shosuro Aishi",
    "the Lady of Decay": "Lady of Decay",
    "Daimyo Shosuro": "Shosuro Hametsu",
    # The trader has no page of his own; the export files his premises.
    "Hideyoshi Aki": "Hideyoshi Aki’s Counting House And Warehouse",
    "Hana no Ame": "Tonbo Higuchi",
    "Hanano Ame": "Tonbo Higuchi",
    "Higuchi": "Tonbo Higuchi",
    # Morozane's lion, which the sources spell three ways: the export has both
    # "Shiguro Chinmoku" and "Shigo no Tomoku" as separate NPC files, and his
    # Foundry actor calls it "Shigo no Chinmoku". Merged onto the first, which
    # is the page that exists. Worth renaming once the owner picks one.
    "Diamond Mines": "Old Diamond Mines",
    # Owner's ruling 2026-08-12: Yui is the correct spelling; the export's
    # "Kitsu Yue" (94 instances) is the same person. Pinned rather than left
    # to the fuzzy pass, so the merge is a decision and not a guess.
    "Yui": "Kitsu Yui",
    # Session 41's notes spell the governor's niece "Miya Masato". The export has
    # a Miya Misato (16, the niece, carries the writ) and a separate Doji Masato
    # (Crane, married to Doji Miho) — the woman in the tower says "tell your
    # uncle", so it is Misato. Pinned so the two never collapse into each other.
    # Same session shortens Daidoji Shin. The export runs 81 "Daidoji Shin" to
    # 4 "Doji Shin", and has no Doji Shin page.
    # The 2026-04-06 summary and the 2026-04-13 record disagree on two new names.
    # The later document is the more careful one — it carries a participants
    # table, the GM's name and transcript timestamps, and it independently gets
    # Miya Misato and Ikoma Tadayoshi right where the earlier one does not — so
    # its spellings win and the earlier ones are kept as aliases.
    # Setsuna's scribe, on the road with her since session 1. The 2026-04-13
    # record spells him "Atoya"; session 1 and the export both say Otoya.
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
    otherwise the plain display text. Never emits a broken href.

    An unresolved link used to render as a dotted "not yet chronicled" span. The
    Archivist invents links freely — [[kitchen]], [[guest quarters]], [[47 Lion
    soldiers]] — and none of those is a thing anyone will ever write a page for,
    so the marker promised a page that was never coming and put a help cursor on
    the word "kitchen". Owner 2026-08-13: drop them. They still count in the
    build report, which is where an unresolved link is actually worth knowing
    about.
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
        return html.escape(display)
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
