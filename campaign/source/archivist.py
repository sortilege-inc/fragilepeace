"""
archivist.py — read the Obsidian/Archivist export in ingest/ into Page objects,
build the name registry (including short-form aliases), and resolve [[wikilinks]].

The export is the raw campaign pull. Nothing here decides what Setsuna knows;
that lives in the hand-authored session files under sources/chronicle/.
"""

import os, sys, re, io, html, unicodedata, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import cfg

SUP  = cfg.BASE          # …/fragile-peace-support
ROOT = cfg.ROOT          # sibling site repo (the GIT root — git show paths hang off this)
SITE = cfg.SITE          # where the generated pages live inside it (campaign/ since the VTT fork)
SRC = cfg.SRC            # the Archivist export, under archive/

CLANS = ["Crane", "Lion", "Unicorn", "Scorpion", "Dragon", "Phoenix", "Crab",
         "Mantis", "Badger", "Centipede", "Dragonfly", "Fox", "Tortoise"]

# Families, for reading a clan off a personal name.
FAMILY_CLAN = {
    "Doji": "Crane", "Kakita": "Crane", "Daidoji": "Crane", "Asahina": "Crane",
    "Matsu": "Lion", "Akodo": "Lion", "Ikoma": "Lion", "Kitsu": "Lion",
    "Shinjō": "Unicorn", "Shinjo": "Unicorn", "Ide": "Unicorn",
    "Utaku": "Unicorn", "Iuchi": "Unicorn",
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
    # 2026-09-13: "Shosuro Amaro" is the Scorpion who advised Shinjo Kamo at
    # the Snow Plain — i.e. Shosuro Amane, mis-transcribed. The export's own
    # Amaro page describes her as "an ancestor of the Scorpion Clan, renowned
    # for her role as an advisor to the Unicorn Clan", which is Amane's entire
    # description, and the count is 37 Amane against 5 Amaro. Must come after
    # the Shishoro/Shoshuro normalisation above.
    (r"\bShosuro Amaro\b", "Shosuro Amane"),
    # 2026-09-13: the Unicorn advocate is Ide TSUBAME. The export writes
    # "Subane" 149 times against 4 correct — but the transcriptions say Tsubame
    # 8 times out of 8, including from the guest player who voices her on the
    # 2025-09-22 recording, and Tsubame is a word (a swallow) where Subane is
    # not. Same dropped-consonant defect as "Okoto" for "Akodo".
    (r"\bIde Subane\b", "Ide Tsubame"),
    # 2026-09-13, from the correction pass: the party's Kitsu shugenja is KITSU
    # Ayoko, not "Kitsuko". The transcriptions say Kitsu Ayoko 27 times across 11
    # recordings against a single "Kitsuko" (2025-04-28). Kitsu is a real Lion
    # family and the canonical ancestor-speaking bloodline -- which is precisely
    # her role -- while Kitsuko is not a family at all; Shosuro Aishi says it out
    # loud on the 2025-10-06 recording ("that is only the provenance of the
    # Kitsu"), and the Castle of the Swift Sword is the seat of the Kitsu family.
    # Same dropped/added-syllable defect as Okoto/Akodo and Subane/Tsubame.
    # Reversible: delete this line and re-run build_site.
    (r"\bKitsuko Ayoko\b", "Kitsu Ayoko"),
    # Owner 2026-08-12: the governor is Tetsuya. The export invents "Tetsuna".
    (r"\bMiya Tetsuna\b", "Miya Tetsuya"),
    # Owner 2026-09-13, reversing the 2026-08-12 call: the spelling is YUE, and
    # there is no Katsuki Yui — it is the same person, filed by the export under
    # three names. The export agrees: 106 "Kitsu Yue" against 36 "Kitsu Yui" and
    # 14 "Katsuki Yui". The 2026-08-12 rule had been rewriting the majority
    # spelling into the minority one. Two-word forms first, so the bare rule
    # cannot strand "Katsuki Yue".
    (r"\bKatsuki Yui\b", "Kitsu Yue"),
    (r"\bKitsu Yui\b", "Kitsu Yue"),
    (r"\bKitsuyue\b", "Kitsu Yue"),
    (r"\bYui\b", "Yue"),
    # 2026-09-13, correcting session 12 against the 2025-06-09 recording. There
    # is no Matsumura Zane. It is the transcription mishearing "Matsu Morozane",
    # and the export built a SECOND PC page out of it — 41 mentions against 310.
    # The recording settles it in the general's own mouth: when Shinjo Kamo asks
    # who the man shouting at his horse is, Matsu Sakura answers "their name is
    # Matsu Morozane". Correcting the title as well as the prose merges the two
    # pages.
    (r"\bMatsumura Zane\b", "Matsu Morozane"),
    (r"\bMatsumura-san\b", "Matsu Morozane"),
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
    # 2026-09-13: the Imperial herald whose chop is first on the Snow Plain
    # treaty. The transcription runs the name together and the export filed the
    # page that way; it is Miya Mimoka, of the Miya heralds, as the other seven
    # Miya entries in the export make plain. Same defect as "Shinjukamu".
    (r"\bMiyamimoka\b", "Miya Mimoka"),
    # Spacing and truncation, each of which built a second page.
    (r"\bIkoma Aku Yaku\b", "Ikoma Akuyaku"),
    (r"\bSlow Tide Harbor\b", "Slowtide Harbor"),
    (r"\bDran Merchant River\b", "Drowned Merchant River"),
    # "Asawa" is not a family of the Phoenix; the Isawa are.
    (r"\bAsawa Family\b", "Isawa Family"),
    # Morozane's lion, spelled three ways across the sources. Owner 2026-08-13:
    # the lion is Shigo no Chinmoku, which is also what her Foundry actor says.
    # Owner 2026-09-13: the lion is FEMALE. The export calls her "he" throughout,
    # which never reaches a page — an NPC entry renders its session ledger, not
    # the Archivist prose — but it had leaked into the s11 rewrite. Jordan's own
    # usage on the recordings is she/her: "my pet lion who likes some horse
    # flanks, she's at my side" (2025-06-30), "my cat did very well… she got
    # embroiled after the duel was technically done" (2025-06-02).
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
    # 2026-09-13: the general holding Shinjo Harunobu, and Akodo Akihito's
    # father. There is no Okoto family — it is the transcription's rendering of
    # AKODO, which the export itself writes twice ("Akodo Sakuon") against
    # twenty of the mangled form. Kitsu Takeko calls him "my cousin, Akodo
    # Sakuon" on the 2025-09-01 recording and names Akihito as his son. The
    # ALIASES entry used to pin this the wrong way round, making the error the
    # page title; it now points at the corrected name.
    (r"\bOkoto Sakuon\b", "Akodo Sakuon"),
    (r"\bKodo Totori\b", "Akodo Toturi"),
    # Owner 2026-08-13: it was an abortion. The Archivist filed session 35 as
    # "Doji Setsuna's Miscarriage" and used the word twice in the entry, which
    # is wrong on the record's own evidence — she asked Shiba Midori for the
    # Terminating Tea, had the ingredients gathered, and drank it, and the
    # entry's own first clause is "your efforts were successful". A miscarriage
    # is something that happens to a woman; this is something she did. The word
    # appears in that one file and nowhere else in the sources.
    (r"you have indeed miscarried", "you have indeed aborted the pregnancy"),
    (r"\bMiscarriage successful\b", "Abortion successful"),
    # Owner 2026-08-26: the Unicorn family is spelled Shinjō, with the macron,
    # everywhere on this site. Before this the site ran 769 plain to 3 macron and
    # the L5R5e corpus writes Shinjo throughout, so this is a deliberate
    # house-style departure from the books rather than a correction toward them.
    #
    # Ordering matters: this runs last, after the Kamo and Altansarnai rules
    # above, whose replacements spell the family plainly. They produce
    # "Shinjo Kamo" and this rule then takes it to "Shinjō Kamo". Do not move it
    # up the list.
    #
    # Safe for URLs: slugify() normalises NFKD and drops combining marks, so
    # "Shinjō Harunobu" still slugs to shinjo-harunobu and no link moves.
    (r"\bShinjo\b", "Shinjō"),
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
    # 2026-09-14 audit of export-invented identifications. Each of these is one
    # person the export split into two pages by mis-hearing the name, leaving a
    # thin duplicate that carried an appearance the real page should have had.
    # Merged rather than dropped, so any content on the duplicate survives; each
    # also needs its ALIASES entry below, because the prose still links the old
    # title. Verified against the canonical page's own sessions in every case.
    "Lady Takeko": "Kitsu Takeko",        # empty page beside Takeko's six sessions
    "Torunako": "Akodo Toronoko",         # Snow Plain arc, s10/s12/s17
    "Mantis Captain": "Captain Kubota",
    "Lady Matsu": "Matsu Tsuko",   # named since s31; the role page is empty

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
    # "Hana no Ame" -> "Tonbo Higuchi" removed 2026-09-14: that rename is what
    # produced the merged page. Both of the novelist's export pages are now
    # superseded by sources/entities/Shinjo Higuchi.md instead.
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
    # Owner 2026-08-13. See the note in CORRECTIONS: she sought the tea out and
    # drank it, and the Archivist's own entry opens "your efforts were
    # successful". The title was the Archivist's word, not the table's.
    "Doji Setsuna's Miscarriage": "Doji Setsuna’s Abortion",
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
    # Both were filed as NPCs by an export that predates their being played.
    # Tonbo Kuma was run by Setsuna's player in session 57 and is at the table;
    # Shinjo Harunobu has been played since his parole in 58. Owner's ruling,
    # 2026-09-28: both are playable characters. They also need CURRENT_PARTY in
    # build_site.py to reach The Party rather than the off-stage group.
    ("npc", "Tonbo Kuma"): "pc",
    ("npc", "Shinjo Harunobu"): "pc",

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
# Appearances the export asserts and the recordings do not support.
#
# A session's cast is read off the export's recap/moments/timeline, so removing
# a fabricated identification from the prose does not remove the person from the
# session: their page goes on listing it as one they were in. Every fabrication
# the correction pass struck out left exactly that residue. Keyed by session
# number, holding page titles to drop from that session's cast.
#
# Each entry is a ruling recorded in CORRECTION-PASS.md. Nothing goes here to
# tidy an inconvenience — only where the recording is checked and silent.
MISREAD_APPEARANCES = {
    # s27: the record made the Lion at the teahouse "the same Matsu Koda who
    # duelled Kakita Kazumi at Loyalty Castle". Koda is nowhere in the
    # 2025-11-10 recording, and Kazumi is not in the session at all.
    27: {"Matsu Koda"},
    # s28: the record had Isawa Kaede accusing Iuchi Minoru's practice of caging
    # spirits. The 2025-11-17 recording has Minoru quote an unnamed MALE Isawa;
    # the Archivist completed the family name to the famous Kaede, who in this
    # corpus is the Lion Champion's betrothed and was not there.
    28: {"Isawa Kaede"},
    # s36: the note under the shuriken is two characters in dark blue ink
    # reading "Turn back", and nothing else. The Archivist read a trailing
    # aside on the 2026-01-12 recording as a signature and linked it to Aoi,
    # a Kitsu of a vassal family met once at the Border Waystation in s5.
    # "Aoi" appears in exactly one of the 73 recordings, and it is s5.
    36: {"Aoi"},
    # s19: the hostile exchange over the journals was with the War College
    # QUARTERMASTER, whom the 2025-09-01 recording never names. Akodo Atsushi is
    # a different Lion, whose own entry puts him at a tea house with Kitsu
    # Takeko. The scene is in the record; the name was not in the recording.
    19: {"Akodo Atsushi"},
    # s33: the export believed Tonbo Higuchi was the possessed novelist and so
    # placed him in the exorcism. He is Tonbo Kuma's go opponent, met once in
    # s32 and excused from the board. The novelist is Shinjo Higuchi.
    33: {"Tonbo Higuchi"},
}

SUPERSEDED_BY_LOCAL = {
    "Asawa Family",
    # Owner pass 2026-09-13, against the 2025-06-02 recording. The export
    # entry names the officer who challenged Morozane as General Shinjo
    # Kamo and gives the challenge to Bayushi Monban. Both are wrong: the
    # officer challenged Morozane, and the Lion spent the whole day failing
    # to identify any Unicorn commander — that was the objective, and it
    # went unmet. The Shinjo Kamo page keeps its own account.
    "Unicorn Officer",
    # 2026-09-14, correction pass at s37. The export's "Tonbo Higuchi" page is
    # two people in one: the man excused from Tonbo Kuma's go board (he/him)
    # and the possessed novelist in the purple dress (she/her). The local page
    # keeps only the man; the novelist is Shinjo Higuchi and has her own.
    "Tonbo Higuchi",
    # 2026-09-14: two more split identities whose canonical page is LOCAL, so a
    # rename would collide with the duplicate check. Dropped here; ALIASES routes
    # the old titles. Both export pages are empty placeholders.
    "Onohime",
    "Okoto Totori",
    # "Lady Matsu" is an empty placeholder; the recordings use "Lady Matsu" and
    # "Lady Daimyo Matsu" for Matsu Tsuko, who has a local page with content.
    "Lady Matsu",
    # The export's "City Between the Rivers" opens by calling it "also known as
    # the City of the Rich Frog". It is not: the 2025-11-10 recording routes the
    # party FROM the City of the Rich Frog TO it, and on toward the Golden Yurts.
    # Replaced by a local page that says what the recording says.
    "City Between the Rivers",
    # The export's "First Enemy Blood" faction page is a summary of the s24
    # arbitration -- diamond mines, forgery, "least of the Bayushi" -- filed
    # under a phrase that appears nowhere in it, and it repeats the invented
    # mines claim the pass already struck. The phrase is Monban's, it is a form
    # of address, and the local page records the usage without settling it.
    "First Enemy Blood",
    # The novelist's two export pages -- one under her pen name, one under a
    # garbled given name -- both replaced by the local Shinjo Higuchi page.
    "Hana no Ame",
    "Shinjo Higoichi",
    # The same export filed the governor's niece twice, once by name and once
    # by her relationship to him. ALIASES points the relationship at the name.
    "Miya’s Niece",
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
    d = cfg.ENTITIES
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
    # 2026-09-13: LEFT ALONE DELIBERATELY. The page title is the transcription
    # stuttering — 28 "Emperor Hantei Hantei" in the export against 5 of this
    # quadrupled form — but the export FILE for him is corrupt in a way a
    # rename makes worse: its body opens "[[[[Emperor Hantei Hantei]] Hantei
    # Hantei]] Hantei Hantei Hantei Hantei…", nested brackets around a run of
    # repeated words. Any CORRECTIONS rule that rewrites the long form fires
    # inside those nested links and multiplies them. Fixing this needs the
    # export entry repaired, not a regex. Logged in CORRECTION-PASS.md.
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
    # Session 53 gave the Unicorn's advisor a name. Her page was titled by
    # her role because the record had not supplied one; s52 still links her
    # that way, so the old title stays pointed at the new one.
    "The Unicorn's Iuchi Advisor": "Iuchi Yukiko",
    "The Unicorn’s Iuchi Advisor": "Iuchi Yukiko",
    "General Shinjo Kamo": "Shinjo Kamo",
    "General Matsu Sakura": "Matsu Sakura",
    "Katsuki Kage": "Kitsuki Kaage",
    "Katsuki": "Kitsuki Kaage",
    "Katsuki Wataru": "Kitsuki Wataru",
    # The export writes the Akodo family as "Okoto" in places.
    "Okoto Sakuon": "Akodo Sakuon",
    "Okoto Kayamayako": "Akodo Kayamayako",
    # Owner's ruling 2026-08-12: Miya Tetsuya is the governor and there is
    # no Miya Amaya — the export invented her across 12 references.
    "Governor Miya Amaya": "Governor Miya Tetsuya",
    "Miya Amaya": "Governor Miya Tetsuya",
    "Miya Tetsuya": "Governor Miya Tetsuya",
    "Aishi": "Shosuro Aishi",
    "the Lady of Decay": "Lady of Decay",
    "Daimyo Shosuro": "Shosuro Hametsu",
    # the five merges made above, so prose still linking the old titles resolves
    "Onohime": "Onahime",
    "Okoto Totori": "Akodo Toturi",
    "Lady Takeko": "Kitsu Takeko",
    "Torunako": "Akodo Toronoko",
    "Mantis Captain": "Captain Kubota",
    "Lady Matsu": "Matsu Tsuko",
    # 2026-09-14, correction pass at s37: the export filed the governor's niece
    # as her own NPC as well as under her name. The 2026-02-02 recording has
    # Miya Tetsuya calling Misato "my niece" throughout and the party moving
    # between the two forms in one breath. One person, two pages.
    "Miya's Niece": "Miya Misato",
    "Miya’s Niece": "Miya Misato",
    # The trader has no page of his own; the export files his premises.
    "Hideyoshi Aki": "Hideyoshi Aki’s Counting House And Warehouse",
    # 2026-09-14: corrected at s37, finishing the s33 ruling. The novelist is
    # SHINJO Higuchi; Tonbo Higuchi is Tonbo Kuma's go opponent from s32. The
    # export merged them onto one page -- its text describes a man excused from
    # a go board AND a possessed woman in a purple dress -- and these aliases
    # were still routing every Hana no Ame link to the wrong person after the
    # s33 prose was fixed. Correcting the prose without the alias table left the
    # links pointing where they always had.
    "Hana no Ame": "Shinjo Higuchi",
    "Hanano Ame": "Shinjo Higuchi",
    "Shinjo Higoichi": "Shinjo Higuchi",
    "Higuchi": "Shinjo Higuchi",
    # Morozane's lion, which the sources spell three ways: the export has both
    # "Shiguro Chinmoku" and "Shigo no Tomoku" as separate NPC files, and his
    # Foundry actor calls it "Shigo no Chinmoku". Merged onto the first, which
    # is the page that exists. Worth renaming once the owner picks one.
    "Diamond Mines": "Old Diamond Mines",
    # Owner's ruling 2026-09-13, reversing 2026-08-12: YUE is the correct
    # spelling, and the export's "Kitsu Yui" and "Katsuki Yui" are the same
    # person. Pinned rather than left to the fuzzy pass, so the merge is a
    # decision and not a guess. See CORRECTIONS for the rewrite.
    "Yue": "Kitsu Yue",
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
