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

  CORPUS   ~/Working/Titterpig DSL/titterpig-dsl-l5r5e/0.4/*.ttrpg
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
ROOT = os.path.dirname(HERE)
FOUNDRY = os.path.join(ROOT, "sources", "foundry", "fvtt-Actor-matsu-morozane.json")
TEMPLATE = os.path.join(ROOT, "play", "setsuna.html")
OUT = os.path.join(ROOT, "play", "morozane.html")
CORPUS_DIR = os.path.expanduser("~/Working/Titterpig DSL/titterpig-dsl-l5r5e/0.4")


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
    return re.sub(r'\^\\"([^"]*)\\"', r"\1", s).replace('\\"', '"')


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


def corpus_props(name, keys):
    """Named PROPERTIES off a gear DEF, in the order asked for.

    Returns "" when the corpus does not carry this piece of gear at all — the
    sheet then lists it by name with no numbers, rather than inventing any.
    Where a name is ambiguous, the block matching the most requested keys wins.
    """
    def harvest(body):
        out = []
        for k in keys:
            m = re.search(r'\^"' + re.escape(k) + r'" (?:STRING "((?:[^"\\]|\\.)*)"|INTEGER (\d+))', body)
            if m:
                out.append("%s %s" % (k, unquote(m.group(1)) if m.group(1) else m.group(2)))
        return out

    best = []
    for body in _blocks(name):
        got = harvest(body)
        if len(got) > len(best):
            best = got
    if not best:
        MISSING.append(name)
    return " · ".join(best)


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
GEAR = [
    {"name": "Nagae Yari", "props": ["Category", "Skill", "Range", "Damage",
                                     "Deadliness", "Rarity", "Qualities"]},
    {"name": "Katana", "props": ["Category", "Skill", "Range", "Damage",
                                 "Deadliness", "Rarity", "Qualities"]},
    {"name": "Wakizashi", "props": ["Category", "Skill", "Range", "Damage",
                                    "Deadliness", "Rarity", "Qualities"]},
    {"name": "Tessen", "props": ["Category", "Skill", "Range", "Damage",
                                 "Deadliness", "Rarity", "Qualities"]},
    {"name": "Ashigaru Armor", "props": ["Physical", "Supernatural", "Rarity", "Qualities"]},
    {"name": "Traveling Clothes", "props": ["Physical", "Supernatural", "Rarity", "Qualities"]},
    {"name": "Traveling pack", "props": []},
]

# Morozane's lion is an Adversary-type actor, not a character, and the owner
# supplied it as screenshots rather than an export. Transcribed here and marked
# as such — replace with a real export when one exists. The Foundry actor spells
# it "Shigo no Chinmoku"; the site spells it Shiguro Chinmoku, per
# archivist.CORRECTIONS, so that one name is used everywhere.
COMPANION = {
    "name": "Shiguro Chinmoku",
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
    return {"name": meta["name"], "kind": meta["kind"], "text": fdesc(meta["name"])}


def gear(meta):
    stats = corpus_props(meta["name"], meta["props"]) if meta["props"] else ""
    item = by_name.get(meta["name"])
    equipped = bool(item and item["system"].get("equipped"))
    return {"name": meta["name"], "stats": stats, "equipped": equipped,
            "text": fdesc(meta["name"]) if item else ""}


rings = {k: (v["rank"] if isinstance(v, dict) else v) for k, v in sysd["rings"].items()}

flat_skills = {}
for grp, sk in sysd["skills"].items():
    if not isinstance(sk, dict):
        continue
    for n, v in sk.items():
        r = v.get("rank") if isinstance(v, dict) else v
        if isinstance(r, int) and r > 0:
            flat_skills[n] = {"rank": r, "group": grp}

SHEET = {
    "id": "morozane",
    "name": actor["name"],
    "clan": sysd["identity"]["clan"],
    "family": sysd["identity"]["family"],
    "school": sysd["identity"]["school"],
    "role": sysd["identity"]["roles"],
    "rank": sysd["identity"]["school_rank"],
    # Hot-linked from Foundry rather than copied in, matching how the Caul site
    # sources its portraits. Swap for a local asset if the Forge URL ever moves.
    "portrait": actor["img"],
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
head = head.replace('<a href="../character/index.html">Characters</a>',
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
