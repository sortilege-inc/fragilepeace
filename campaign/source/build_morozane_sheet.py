#!/usr/bin/env python3
"""
build_morozane_sheet.py — generate play/morozane.html, the playable L5R5e sheet
for Matsu Morozane and his lion.

Morozane is the character the owner played through the Snow Plain flashback
(sessions 10-16), and Doji Setsuna's own Lion ancestor. The sheet runs on the
same engine as hers — play/sheet.js, play/sheet.css, play/l5rdata.js.

Rules text is never retyped. It comes verbatim from two sources:

  FOUNDRY  sources/foundry/fvtt-Actor-matsu-morozane.json
           his Foundry VTT export, pinned here so the build is reproducible.
           Rings, skills, derived stats, social standing, and the description
           blocks for everything the export carries. **Drop a fresh export over
           that file and re-run to pick up sheet changes.**

  CORPUS   ~/Sortilege/Titterpig/DSL/titterpig-dsl-l5r5e/0.5/*.ttrpg
           the canonical L5R5e corpus, for the six techniques and the gear stats
           the export omits. Searched across files, since his techniques come
           from core, Fields of Victory, and two clan school books.

Everything this script authors itself is metadata the engine needs and neither
source carries: display order, tags, and roller activation hooks.

    python3 scripts/build_morozane_sheet.py
"""

import html
import json
import os
import re
import sys
import glob

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from config import cfg

SUP  = cfg.BASE          # …/fragile-peace-support
ROOT = cfg.ROOT          # sibling site repo
FOUNDRY = os.path.join(cfg.FOUNDRY_DIR, "fvtt-Actor-matsu-morozane.json")
TEMPLATE = os.path.join(ROOT, "play", "setsuna.html")
OUT = os.path.join(ROOT, "play", "morozane.html")
CORPUS_DIR = cfg.DSL_L5R5E


# ---------------------------------------------------------------- extraction
def plain(markup):
    """Foundry stores descriptions as HTML. Flatten to the plain text the sheet wants."""
    if not markup:
        return ""
    s = re.sub(r"<br\s*/?>", "\n", markup)
    s = re.sub(r"</p>|</div>|</h[1-6]>|</tr>", "\n\n", s)
    s = re.sub(r"</li>", "\n", s)
    s = re.sub(r"<li[^>]*>", "• ", s)
    s = re.sub(r"</td>\s*<td[^>]*>", " — ", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s)
    s = s.replace("• - ", "• ").replace("•  ", "• ")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r" *\n *", "\n", s)
    return re.sub(r"\n{3,}", "\n\n", s).strip()


_CORPUS = None


def corpus_text():
    """Every .ttrpg in the corpus, concatenated once."""
    global _CORPUS
    if _CORPUS is None:
        parts = []
        for p in sorted(glob.glob(os.path.join(CORPUS_DIR, "*.ttrpg"))):
            parts.append(open(p, encoding="utf-8").read())
        _CORPUS = "\n".join(parts)
    return _CORPUS


def _blocks(name):
    """Every DEF block carrying this name, braces balanced.

    Names are not unique across the corpus. "Nagae Yari" is both a weapon (in
    Fields of Victory's mechanics) and a cohort upgrade (in its mass-battle
    rules); taking the first match prints "Applies To One cohort" as a weapon
    stat. Callers pick the block that actually carries the keys they want.
    """
    src = corpus_text()
    out = []
    for m in re.finditer(r'\^"' + re.escape(name) + r'" DEF \{', src):
        depth, i = 0, m.end() - 1
        for j in range(i, len(src)):
            if src[j] == "{":
                depth += 1
            elif src[j] == "}":
                depth -= 1
                if depth == 0:
                    out.append(src[m.start():j + 1])
                    break
    return out


def _block(name):
    blocks = _blocks(name)
    if not blocks:
        sys.exit("corpus: %r not found under %s" % (name, CORPUS_DIR))
    return blocks[0]


def unquote(s):
    r"""Corpus escapes -> text: \" and \n, then the ^"Name" reference carets.

    One pass, not chained replaces, or a `\n` paragraph break in a corpus string
    reaches the sheet as the two characters it prints literally.
    """
    s = re.sub(r"\\(.)", lambda m: {"n": "\n", "t": "\t", "r": "\r"}.get(m.group(1), m.group(1)), s, flags=re.S)
    return re.sub(r'\^"([^"]*)"', r"\1", s)


def corpus_def(name):
    """A technique DEF rendered as sheet text — activation, effects, opportunities.

    The corpus spells techniques two ways. Core books use the block constructs
    (ACTIVATION "..." / EFFECTS "..." / OPPORTUNITIES { ... }); the supplements —
    Fields of Victory among them — use flat properties (^"Activation" STRING "...").
    Read both, or five of Morozane's six corpus techniques come out empty.
    """
    body = _block(name)
    out = []

    def prop(key):
        m = re.search(r'\^"' + key + r'" STRING "((?:[^"\\]|\\.)*)"', body)
        return unquote(m.group(1)) if m else None

    act = re.search(r'ACTIVATION "((?:[^"\\]|\\.)*)"', body)
    act = unquote(act.group(1)) if act else prop("Activation")
    if act:
        out.append("Activation: " + act)

    eff = re.search(r'EFFECTS "((?:[^"\\]|\\.)*)"', body)
    eff = unquote(eff.group(1)) if eff else (prop("Effect") or prop("Effects"))
    if eff:
        out.append("Effects: " + eff)

    opp = re.search(r"OPPORTUNITIES \{(.*?)\n\s*\}", body, re.S)
    if opp:
        for line in re.findall(r'"((?:[^"\\]|\\.)*)"', opp.group(1)):
            out.append(unquote(line))
    elif prop("Opportunities"):
        out.append(prop("Opportunities"))

    if not out:
        sys.exit("corpus: %r produced no text" % name)
    return "\n\n".join(out)


# The corpus does not name these the way a sheet does, and it does not write
# them all as scalars. Getting either wrong makes a value that IS there read as
# absent, which is how this sheet published swords with no damage and armour
# with no resistances: the reader asked for "Damage" where core writes "Base
# Damage", for "Physical" where it writes "Physical Resistance", and knew only
# STRING and INTEGER where Qualities is a LIST OF STRING.
PROP_KEYS = {
    "category": ["Category"],
    "skill": ["Skill"],
    "range": ["Range"],
    # Core writes "Base Damage"; Fields of Victory writes "Damage".
    "damage": ["Base Damage", "Damage"],
    "deadliness": ["Deadliness"],
    "grips": ["Grips"],
    "qualities": ["Qualities"],
    "rarity": ["Rarity"],
    "physical": ["Physical Resistance", "Physical"],
    "supernatural": ["Supernatural Resistance", "Supernatural"],
}


def _prop(body, key):
    """One PROPERTY value — STRING, INTEGER or LIST OF STRING — or None.

    The list form is the one that bites. 0.5 writes

        ^"Qualities" LIST OF STRING ["Ceremonial", "Razor-Edged"]

    and a reader that knows only STRING and INTEGER reports the key as absent
    rather than failing, so the quality never reaches the page and nothing says
    so. The optional hash and type name before the bracket are §5d's hash-bound
    list body, tolerated here so a corpus that adopts it does not go quiet.
    """
    m = re.search(r'\^"' + re.escape(key) + r'" (STRING|INTEGER|LIST OF STRING)', body)
    if not m:
        return None
    kind, rest = m.group(1), body[m.end():]
    if kind == "STRING":
        q = re.match(r'\s*"((?:[^"\\]|\\.)*)"', rest)
        return unquote(q.group(1)) if q else None
    if kind == "INTEGER":
        q = re.match(r"\s*(-?\d+)", rest)
        return int(q.group(1)) if q else None
    q = re.match(r'\s*(?:#\S+\s*)?(?:\^"[^"]*"\s*)?\[(.*?)\]', rest, re.S)
    return [unquote(x) for x in re.findall(r'"((?:[^"\\]|\\.)*)"', q.group(1))] if q else None


def corpus_props(name, want):
    """The sheet's fields for a piece of gear, read off its corpus DEF.

    `want` is sheet field names; PROP_KEYS maps each to the spellings the corpus
    actually uses. Returns {} when the corpus does not carry this gear at all —
    the card then shows the name and prose, rather than a number invented here.
    Where a name is ambiguous the block answering the most fields wins: Nagae
    Yari is both a weapon and a line in a mass-battle rarity table.
    """
    best = {}
    for body in _blocks(name):
        got = {}
        for want_key in want:
            for key in PROP_KEYS[want_key]:
                v = _prop(body, key)
                if v is not None:
                    got[want_key] = v
                    break
        if len(got) > len(best):
            best = got
    if not best:
        MISSING.append(name)
    return best


SKILL_KEYS = {"Martial Arts [Melee]": "melee", "Martial Arts [Ranged]": "ranged",
              "Martial Arts [Unarmed]": "unarmed"}


MISSING = []


actor = json.load(open(FOUNDRY, encoding="utf-8"))
by_name = {i["name"]: i for i in actor["items"]}
sysd = actor["system"]


def fdesc(name):
    if name not in by_name:
        sys.exit("foundry: item %r not in export" % name)
    return plain(by_name[name]["system"].get("description", ""))


# ------------------------------------------------------------ authored metadata
# Order: school ability, title abilities, shuji, ritual, kata.
# `src: "corpus"` marks the six the Foundry export omits but the live sheet shows
# (screenshots supplied by the owner, 2026-08-12) — pulled verbatim from the corpus.
TECHNIQUES = [
    {"name": "One with the Pride", "tag": "School Ability", "ring": "water"},
    {"name": "Gunso", "tag": "Title Ability", "ring": "air", "src": "title"},
    {"name": "Renowned Warrior", "tag": "Title Ability", "ring": "fire", "src": "title"},

    {"name": "Call the Wild", "tag": "Shūji", "ring": "water"},
    {"name": "Lightning Raid", "tag": "Shūji", "ring": "fire"},
    {"name": "Righteous Example", "tag": "Shūji", "ring": "earth"},
    {"name": "Rallying Cry", "tag": "Shūji", "ring": "fire", "src": "corpus"},
    {"name": "Touchstone of Courage", "tag": "Shūji", "ring": "earth", "src": "corpus"},

    {"name": "Beseech Shinjo's Empathy", "tag": "Ritual", "ring": "water"},

    {"name": "Warrior’s Resolve", "tag": "Kata"},
    {"name": "Shattering Tide Style", "tag": "Kata", "src": "corpus"},
    {"name": "Battle in the Mind", "tag": "Kata", "src": "corpus"},
    {"name": "Heartpiercing Strike", "tag": "Kata", "src": "corpus"},
    {"name": "Striking as Fire", "tag": "Kata", "src": "corpus"},
]

PECULIARITIES = [
    {"name": "Animal Bond", "kind": "Distinction"},
    {"name": "Glorious Deeds", "kind": "Distinction"},
    {"name": "Famously Lucky", "kind": "Distinction"},
    {"name": "Generosity", "kind": "Passion"},
    {"name": "Ferocity", "kind": "Passion"},
    {"name": "Belligerent", "kind": "Adversity"},
    {"name": "Lost Arm or Lost Hand", "kind": "Adversity"},
]

# The export carries no stat block for his gear, so the numbers come from the
# corpus and the name is the join. Anything the corpus does not carry is listed
# plainly rather than guessed at.
WEAPON_PROPS = ["category", "skill", "range", "damage", "deadliness", "grips",
                "qualities", "rarity"]
ARMOR_PROPS = ["physical", "supernatural", "qualities", "rarity"]

GEAR = [
    {"name": "Nagae Yari", "props": WEAPON_PROPS},
    {"name": "Katana", "props": WEAPON_PROPS},
    {"name": "Wakizashi", "props": WEAPON_PROPS},
    {"name": "Tessen", "props": WEAPON_PROPS},
    {"name": "Ashigaru Armor", "props": ARMOR_PROPS},
    {"name": "Traveling Clothes", "props": ARMOR_PROPS},
    {"name": "Traveling pack", "props": []},
]

# Morozane's lion is an Adversary-type actor, not a character, and the owner
# supplied it as screenshots rather than an export. Transcribed here and marked
# as such — replace with a real export when one exists. The Foundry actor spells
# it "Shigo no Chinmoku", and so does the site (owner 2026-08-13).
COMPANION = {
    "name": "Shigo no Chinmoku",
    "kind": "Lion · Animal Bond companion",
    "note": "Transcribed from the owner's Foundry screenshots (2026-08-12), not "
            "from an export. Verify before leaning on the numbers.",
    "threat": {"combat": 6, "intrigue": 1},
    "demeanor": "Opportunistic",
    "rings": {"earth": 2, "air": 4, "water": 3, "fire": 1, "void": 1},
    "derived": {"endurance": 7, "composure": 11, "focus": 5, "vigilance": 3},
    "trackers": {"fatigue": {"max": 7}, "strife": {"max": 10},
                 "void": {"max": 1, "start": 1}},
    "tnMods": "Earth 0 · Air 0 · Water +2 · Fire −2 · Void 0",
    "skillGroups": {"artisan": 0, "martial": 3, "scholar": 0, "social": 0, "trade": 0},
    "ability": "Pouncing Predator / Savage Mauling",
}


# ------------------------------------------------------------------- assembly
def technique(meta):
    src = meta.get("src")
    if src == "corpus":
        text = corpus_def(meta["name"])
    else:
        text = fdesc(meta["name"])
    out = {"name": meta["name"], "tag": meta["tag"], "text": text}
    if "ring" in meta:
        out["ring"] = meta["ring"]
    if src == "title":
        out["kind"] = "title"
    for k in ("activation", "uses", "use"):
        if k in meta:
            out[k] = meta[k]
    return out


def peculiarity(meta):
    # `tag`, not `kind`: entry() renders p.tag, so these cards published with no
    # Distinction/Passion/Adversity label at all until 2026-09-26.
    return {"name": meta["name"], "tag": meta["kind"], "text": fdesc(meta["name"])}


def gear(meta):
    """One possession, in the shape the sheet engine actually reads.

    His export carries no numbers for any of it, so everything but the name and
    the description comes from the corpus. Whatever the corpus genuinely does not
    carry is simply absent — the card then shows the name and the prose, which is
    honest, rather than a number this script made up. The audit below makes sure
    "genuinely" is not the reader's word for its own blind spot.
    """
    props = corpus_props(meta["name"], meta["props"]) if meta["props"] else {}
    item = by_name.get(meta["name"])
    g = {"name": meta["name"]}
    if meta["props"] is ARMOR_PROPS:
        g["kind"] = "Armour"
    elif meta["props"]:
        g["kind"] = "Weapon"
    else:
        g["kind"] = "Item"
    for k in ("category", "range", "damage", "deadliness", "grips"):
        if k in props:
            g[k] = str(props[k])
    for k in ("physical", "supernatural", "rarity"):
        if k in props:
            g[k] = int(props[k])
    if "skill" in props:
        g["skill"] = SKILL_KEYS.get(props["skill"], props["skill"].lower())
    if props.get("qualities"):
        g["qualities"] = list(props["qualities"])
    text = fdesc(meta["name"]) if item else ""
    if text:
        g["text"] = text
    return g


rings = {k: (v["rank"] if isinstance(v, dict) else v) for k, v in sysd["rings"].items()}

flat_skills = {}
for grp, sk in sysd["skills"].items():
    if not isinstance(sk, dict):
        continue
    for n, v in sk.items():
        r = v.get("rank") if isinstance(v, dict) else v
        if isinstance(r, int) and r > 0:
            # A plain integer, as the other four sheets emit. The engine reads
            # `S.skills[name]` as a number in three places — the skill list, the
            # roller's die count, and the specialisation lookups — so a
            # {"rank": n, "group": g} record rendered as [object Object] and
            # rolled as NaN. It did, on this sheet, until 2026-09-26.
            flat_skills[n] = r

SHEET = {
    "id": "morozane",
    "name": actor["name"],
    "clan": sysd["identity"]["clan"],
    "family": sysd["identity"]["family"],
    "school": sysd["identity"]["school"],
    "role": sysd["identity"]["roles"],
    "rank": sysd["identity"]["school_rank"],
    # Local, like the other four. It was hot-linked from the owner's Forge VTT
    # account, which made it the only image on a published site depending on a
    # third party staying up and the account staying paid. The file is the same
    # one, fetched once and converted; the export's own `img` is left untouched.
    # Kept square rather than cropped to the 3:4 the other portraits use, because
    # Morozane shares the frame with Shigo no Chinmoku and 3:4 loses the lion.
    "portrait": "../assets/morozane.webp",
    "rings": {r: rings[r] for r in ("air", "earth", "fire", "water", "void")},
    "derived": {"endurance": sysd["endurance"], "composure": sysd["composure"],
                "focus": sysd["focus"], "vigilance": sysd["vigilance"]},
    "trackers": {"strife": {"max": sysd["strife"]["max"]},
                 "fatigue": {"max": sysd["fatigue"]["max"]},
                 "void": {"max": sysd["void_points"]["max"],
                          "start": sysd["void_points"]["max"]}},
    "stance": sysd["stance"],
    "social": {k: sysd["social"][k] for k in ("honor", "glory", "status")},
    "skills": flat_skills,
    # His export records no tenets, ninjō or giri — carried through as empty
    # rather than invented. The sheet drops the card when they are all blank.
    "bushido": {"paramount": sysd["social"]["bushido_tenets"]["paramount"],
                "less": sysd["social"]["bushido_tenets"]["less_significant"]},
    "ninjo": sysd["social"]["ninjo"],
    "giri": sysd["social"]["giri"],
    "money": "%d zeni" % sysd["zeni"],
    "techniques": [technique(t) for t in TECHNIQUES],
    "peculiarities": [peculiarity(p) for p in PECULIARITIES],
    "gear": [gear(g) for g in GEAR],
    "titles": [], "bonds": [],
    "afflictions": [{"name": "Fire Ring damaged",
                     "text": plain(sysd.get("notes", "")) or "Fire Ring damaged: +3 difficulty."}],
    "companion": COMPANION,
}

# Gear the corpus defines must arrive with its numbers. A key the corpus spells
# differently, or writes as a list, reads as absent rather than as an error —
# which is exactly how every sword on this sheet published with no damage and
# both suits of armour with no resistance. Fail the build instead of the page.
for _g in SHEET["gear"]:
    if _g["kind"] == "Weapon" and not all(k in _g for k in ("damage", "deadliness", "skill")):
        sys.exit("corpus: %s is a weapon with no %s — check the property names"
                 % (_g["name"], ", ".join(k for k in ("damage", "deadliness", "skill")
                                          if k not in _g)))
    if _g["kind"] == "Armour" and "physical" not in _g:
        sys.exit("corpus: %s is armour with no physical resistance" % _g["name"])

# Rings are derived; if the export ever drifts from the formulae, say so loudly.
d = SHEET["derived"]
checks = [("endurance", (rings["earth"] + rings["fire"]) * 2),
          ("composure", (rings["earth"] + rings["water"]) * 2),
          ("focus", rings["fire"] + rings["air"]),
          ("vigilance", -(-(rings["air"] + rings["water"]) // 2))]
bad = [(k, d[k], w) for k, w in checks if d[k] != w]
if bad:
    for k, got, want in bad:
        print("DERIVED MISMATCH: %s is %s, formula gives %s" % (k, got, want), file=sys.stderr)
    sys.exit(1)

blob = json.dumps(SHEET, indent=2, ensure_ascii=False)
if "</script" in blob:
    sys.exit("sheet data would close the script tag")

# ------------------------------------------------------------------- emit
tpl = open(TEMPLATE, encoding="utf-8").read()
i = tpl.find('<script id="sheet-data" type="application/json">')
j = tpl.find("</script>", i)
if i < 0 or j < 0:
    sys.exit("template: could not find the sheet-data block in %s" % TEMPLATE)

head = tpl[:i]
head = head.replace("Doji Setsuna — Character Sheet",
                    "Matsu Morozane — Character Sheet")
head = head.replace('<a href="../character/setsuna.html">&lsaquo; Bio</a>',
                    '<a href="../party/matsu-morozane.html">&lsaquo; Bio</a>')
# He is on the chooser page now, so the bar keeps the Characters link the other
# four sheets carry rather than replacing it. The Party and the cross-link to
# Setsuna's sheet are appended, since his bio lives under party/ and the two
# sheets are the same battle seen from opposite ends.
head = head.replace('<a href="../character/index.html">Characters</a>',
                    '<a href="../character/index.html">Characters</a>'
                    '<a href="../party/index.html">The Party</a>'
                    '<a href="setsuna.html">Setsuna &rsaquo;</a>')
page = (head
        + '<script id="sheet-data" type="application/json">\n' + blob + "\n"
        + tpl[j:])
open(OUT, "w", encoding="utf-8").write(page)

print("wrote %s" % OUT)
print("  techniques    %d (%d from corpus)"
      % (len(SHEET["techniques"]), sum(1 for t in TECHNIQUES if t.get("src") == "corpus")))
print("  peculiarities %d" % len(SHEET["peculiarities"]))
print("  gear          %d" % len(SHEET["gear"]))
print("  skills ranked %d" % len(SHEET["skills"]))
print("  companion     %s" % SHEET["companion"]["name"])
if MISSING:
    print("  no corpus stats for: %s (listed by name only)" % ", ".join(sorted(set(MISSING))))
