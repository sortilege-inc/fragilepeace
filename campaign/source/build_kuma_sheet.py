#!/usr/bin/env python3
"""
build_kuma_sheet.py — generate play/kuma.html, the playable L5R5e sheet for
Tonbo Kuma and the water kami he calls up.

Kuma is a guest, not a member of the party: Setsuna's player ran him for session
57 while Setsuna herself was absent, and the owner's ruling (2026-09-26) is that
he does not recur. The sheet exists so that session can be replayed and checked
against the record, not because he is coming back. He is deliberately *not* on
the character chooser for that reason, and his bar carries no Bio link because
he has no entity page.

Rules text is never retyped. It comes verbatim from three sources:

  FOUNDRY  archive/foundry-export/fvtt-Actor-tonbo-kuma.json
           his Foundry VTT export (2026-09-21). Rings, skills, derived stats,
           social standing, XP, gear numbers, and the rules text for every
           technique and peculiarity — this export, unusually, carries all of
           it. **Drop a fresh export over that file and re-run.**

  KAMI     archive/foundry-export/fvtt-Actor-tonbo-kuma-manifest-water-kami.json
           the Adversary actor for the kami Rise, Water summons. Morozane's lion
           had to be transcribed from screenshots; this one is a real export, so
           the companion card is read rather than typed.

  CORPUS   ~/Sortilege/Titterpig/DSL/titterpig-dsl-l5r5e/0.5/*.ttrpg
           the canonical L5R5e corpus, consulted only for the gear descriptions.
           Foundry stores gear by reference and strips the prose on export, so
           every one of his eleven possessions comes out of Foundry with numbers
           and no text.

Everything this script authors itself is the one thing neither source carries:
the action type of each technique's roller button. The TN, skill and ring of
every button are read from the export and then **cross-checked against the
Activation line the book prints**, and a disagreement is fatal rather than
published.

    python3 scripts/build_kuma_sheet.py
"""

import glob
import html
import json
import os
import re
import sys

# Retired 2026-10-01 (campaign/PLAN.md M4): play/ is gone and the character is on the VTT sheet,
# built from campaign/dsl/ by convert_cast.py, which carries what only this builder held
# (FROM_THE_OLD_SHEETS, OWNER_RULINGS, CORRECTIONS; check_sheets.py proves it). Kept as provenance.
sys.exit('build_kuma_sheet.py is retired: play/ was removed at M4 (fragile-peace/campaign/PLAN.md); the sheet is built by campaign/source/convert_cast.py')

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from config import cfg

SUP = cfg.BASE           # …/fragile-peace-support
ROOT = cfg.ROOT          # sibling site repo
FOUNDRY = os.path.join(cfg.FOUNDRY_DIR, "fvtt-Actor-tonbo-kuma.json")
KAMI = os.path.join(cfg.FOUNDRY_DIR, "fvtt-Actor-tonbo-kuma-manifest-water-kami.json")
OUT = os.path.join(ROOT, "play", "kuma.html")
TEMPLATE = os.path.join(ROOT, "play", "setsuna.html")
CORPUS_DIR = cfg.DSL_L5R5E


# ---------------------------------------------------------------- extraction
# Foundry's compendium text uses a private-use glyph for the opportunity symbol
# where the rest of the book writes "(op)". Left alone it reaches the page as a
# missing-glyph box in the middle of a rules sentence.
PUA = {"": "(op)"}


def plain(markup):
    """Foundry stores descriptions as HTML. Flatten to the plain text the sheet wants."""
    if not markup:
        return ""
    for bad, good in PUA.items():
        markup = markup.replace(bad, good)
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


def field(text):
    """Foundry textareas keep the editor's markdown. Flatten to sheet prose."""
    s = text or ""
    s = re.sub(r"\*\*(.*?)\*\*", r"\1", s, flags=re.S)
    s = re.sub(r"^\s*\d+\.\s*", "", s, flags=re.M)
    s = re.sub(r"^\s*[-•]\s*", "", s, flags=re.M)
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{2,}", "\n", s)
    return "\n".join(l.strip() for l in s.split("\n") if l.strip())


_CORPUS = None


def corpus_text():
    global _CORPUS
    if _CORPUS is None:
        _CORPUS = "\n".join(open(p, encoding="utf-8").read()
                            for p in sorted(glob.glob(os.path.join(CORPUS_DIR, "*.ttrpg"))))
    return _CORPUS


_ESCAPES = {"n": "\n", "t": "\t", "r": "\r"}


def unesc(s):
    r"""Corpus escapes -> text: \" and \n, then the ^"Name" reference carets.

    One pass, not chained replaces, or a `\n` paragraph break in a corpus string
    reaches the sheet as the two characters it prints literally.
    """
    s = re.sub(r"\\(.)", lambda m: _ESCAPES.get(m.group(1), m.group(1)), s, flags=re.S)
    return re.sub(r'\^"([^"]*)"', r"\1", s)


def corpus_block(name):
    """The body of the DEF block for `name`, preferring one that carries prose.

    Apostrophes are matched either way round: Foundry writes the typographic
    U+2019 and the corpus writes the ASCII one.
    """
    src = corpus_text()
    pat = r'\^"' + "['’]".join(re.escape(p) for p in re.split(r"['’]", name)) + r'" DEF \{'
    best, best_score = "", (-1, -1)
    for m in re.finditer(pat, src):
        depth, end = 0, len(src)
        for j in range(m.end() - 1, len(src)):
            if src[j] == "{":
                depth += 1
            elif src[j] == "}":
                depth -= 1
                if depth == 0:
                    end = j + 1
                    break
        body = src[m.start():end]
        score = (1 if '^"Description"' in body else 0, len(body))
        if score > best_score:
            best, best_score = body, score
    return best


def corpus_prop(body, key):
    """`^"Key" STRING "value"` → value, unescaped."""
    m = re.search(r'\^"' + re.escape(key) + r'" STRING "((?:[^"\\]|\\.)*)"', body)
    return unesc(m.group(1)) if m else ""


NO_CORPUS = []


def gear_text(name):
    """The corpus's own Description for a piece of gear.

    Foundry stores gear by reference and drops the prose on export, so without
    this every possession on the sheet is a bare name and a row of numbers.
    Anything the corpus does not carry is recorded in NO_CORPUS and listed with
    its numbers only, rather than described from memory.
    """
    text = corpus_prop(corpus_block(name), "Description")
    if not text:
        NO_CORPUS.append(name)
    return text


# ------------------------------------------------------------ authored metadata
TECH_TAGS = [
    ("school_ability", "School Ability"),
    ("invocation", "Invocation"),
    ("ritual", "Ritual"),
    ("shuji", "Shūji"),
]
PECULIARITY_TAGS = {"distinction": "Distinction", "passion": "Passion",
                    "adversity": "Adversity", "anxiety": "Anxiety"}

# Roller hooks. The TN, skill and ring of every button are read from the export
# and cross-checked against the Activation line below it by the audit further
# down — a mismatch is fatal. Only the action type is authored here, because it
# is the one part of the activation neither the export nor a corpus field holds.
ACTION_TYPE = {
    # "As a Movement and Scheme action, you may make a TN 2 Theology (water)
    #  check targeting one position containing a body of water at range 0–1."
    "Dominion of Suijin": "Movement & Scheme",
    # "As a Scheme action, …"
    "Reflections of P’an Ku": "Scheme action",
    # "As a downtime activity, …"
    "Cleansing Rite": "Downtime",
    "Divination": "Downtime",
    # "As a downtime activity or Support action, you may make a TN 1 Theology
    #  check using (air), (earth), (fire), (water), or (void)…"
    #
    # No ring in the line: the caster picks one. The button opens on Void because
    # that is what the export records, the card states the freedom, and the ring
    # audit exempts this technique by name. Change the ring before rolling.
    "Commune with the Spirits": "Downtime or Support",
    # "As a Support action, …"
    "Heart of the Water Dragon": "Support action",
    "Rise, Water": "Support action",
    # "As a Scheme action, …"
    "By the Light of the Lord Moon": "Scheme action",
    # "Once per game session at the start of a scene, or as a Support action, …"
    #
    # Deliberately no `uses` tracker. The once-per-session clause governs the
    # start-of-scene use; the Support action is not obviously limited by it, and
    # a tracker here would enforce on the sheet a restriction the sentence does
    # not clearly impose.
    "Eyes Up!": "Start of scene or Support",
    # "As a Movement and Support action, …"
    "Slippery Maneuvers": "Movement & Support",
    # "As a Movement action, …"
    "Call Upon the Wind": "Movement action",
    # "Once per game session, as a downtime activity using a tea set, …"
    "Tea Ceremony": "Downtime",
}

# Per-session limits stated in the activation text rather than in any field.
USES = {
    "Tea Ceremony": {"max": 1, "per": "Session"},
}

# His school ability prints no Activation line — it is a reaction, and its TN is
# not a constant: "a TN 5 Theology check, with the TN being reduced by a number
# equal to your school rank (to a minimum of 1)". The button therefore carries a
# label instead of a number and leaves the roller's TN to the player, the same
# way Jūjirō's Cloak of Night does. Exempt from the audit by name.
TN_LABEL = {
    "May the Spirits Show the Path": {"actionType": "Reaction · once per scene", "punct": " —",
                                      "tnLabel": "5 − school rank", "skill": "theology",
                                      "ring": "void"},
}

# Peculiarities the engine can hook: anxieties drive its strife buttons,
# distinctions and adversities its advantage/disadvantage rerolls. Two dice each,
# per the core rules. The approach ring is the export's own `ring` field.
ADV = {"kind": "advantage", "max": 2}
DIS = {"kind": "disadvantage", "max": 2, "successOnly": True, "mustMax": True}
PECULIARITY_HOOKS = {
    "Famously Lucky": {"reroll": dict(ADV, approach="void")},
    "Precise Memory": {"reroll": dict(ADV, approach="earth")},
    "Ally: Miya Tetsua": {"reroll": dict(ADV, approach="water")},
    "Benten’s Curse": {"reroll": dict(DIS, approach="air")},
    "Omen of Bad Luck": {"strife": 3},
}


# ------------------------------------------------------------------- assembly
actor = json.load(open(FOUNDRY, encoding="utf-8"))
sysd = actor["system"]
items = actor["items"]


def qualities(it):
    return [p["name"] for p in it["system"].get("properties", []) if p.get("name")]


def printed_activation(text):
    """(tn, skill, ring) exactly as the book's Activation line states them.

    Returns None when the technique prints no Activation line at all, which is a
    real answer for a reaction like May the Spirits Show the Path.
    """
    m = re.search(r"Activation:\s*(.+?)(?:\n|$)", text)
    if not m:
        return None
    line = m.group(1)
    tn = re.search(r"TN (\d+)", line)
    skill = re.search(r"TN \d+ ([A-Z][A-Za-z]+)(?: skill)?", line)
    ring = re.search(r"TN \d+ [A-Z][A-Za-z]+(?: skill)? \((air|earth|fire|water|void)\)", line)
    return (int(tn.group(1)) if tn else None,
            skill.group(1).lower() if skill else None,
            ring.group(1) if ring else None)


def technique(it):
    s = it["system"]
    text = plain(s.get("description", ""))
    t = {"name": it["name"], "tag": dict(TECH_TAGS)[s["technique_type"]], "text": text}
    if s.get("ring"):
        t["ring"] = s["ring"]
    if it["name"] in TN_LABEL:
        t["activation"] = dict(TN_LABEL[it["name"]])
    elif it["name"] in ACTION_TYPE:
        t["activation"] = {"actionType": ACTION_TYPE[it["name"]], "punct": ",",
                           "tn": int(s["difficulty"]), "skill": s["skill"], "ring": s["ring"]}
    if it["name"] in USES:
        t["uses"] = USES[it["name"]]
    return t


# The export misspells the governor. The chronicle, his own entity page and every
# other page on this site say Miya Tetsuya; only this actor says Tetsua, so the
# sheet was the one place publishing it wrong. Corrected here and reported on
# stderr the moment an export lands with the name already right, so this can go.
NAME_FIXES = {"Ally: Miya Tetsua": "Ally: Miya Tetsuya"}


def peculiarity(it):
    s = it["system"]
    p = {"name": NAME_FIXES.get(it["name"], it["name"]),
         "tag": PECULIARITY_TAGS[s["peculiarity_type"]],
         "ring": s.get("ring", ""), "text": plain(s.get("description", ""))}
    p.update(PECULIARITY_HOOKS.get(it["name"], {}))
    return p


def gear(it):
    s = it["system"]
    g = {"name": it["name"]}
    if it["type"] == "weapon":
        g.update(kind="Weapon", category=s.get("category", ""), skill=s.get("skill", ""),
                 range=str(s.get("range", "")), damage=s.get("damage"),
                 deadliness=s.get("deadliness"))
        grips = [x for x in (s.get("grip_1"), s.get("grip_2")) if x and x != "N/A"]
        if grips:
            g["grips"] = " · ".join(grips)
    elif it["type"] == "armor":
        g["kind"] = "Armour"
        for k in ("physical", "supernatural"):
            v = s.get("armor", {}).get(k)
            if v not in (None, ""):
                g[k] = int(v)
    else:
        g["kind"] = "Item"
    q = qualities(it)
    if q:
        g["qualities"] = q
    if s.get("rarity") not in (None, "", "0"):
        g["rarity"] = int(s["rarity"])
    text = plain(s.get("description", "")) or gear_text(it["name"])
    if text:
        g["text"] = text
    return g


def ordered(kind):
    return [i for i in items if i["type"] == kind]


tech_order = {t: n for n, (t, _) in enumerate(TECH_TAGS)}
techniques = [technique(i) for i in
              sorted(ordered("technique"),
                     key=lambda i: (tech_order[i["system"]["technique_type"]], i["name"]))]
pec_order = {"distinction": 0, "passion": 1, "adversity": 2, "anxiety": 3}
peculiarities = [peculiarity(i) for i in
                 sorted(ordered("peculiarity"),
                        key=lambda i: (pec_order[i["system"]["peculiarity_type"]], i["name"]))]
gear_list = [gear(i) for i in
             sorted([i for i in items if i["type"] in ("weapon", "armor", "item")],
                    key=lambda i: ({"weapon": 0, "armor": 1, "item": 2}[i["type"]], i["name"]))]

rings = {k: (v["rank"] if isinstance(v, dict) else v) for k, v in sysd["rings"].items()}
# Ranks, flat and as plain integers. The engine reads `S.skills[name]` as a
# number in three places — the skill list, the roller's die count, and the
# specialisation lookups — so a {"rank": n, "group": g} record here renders as
# [object Object] and rolls as NaN. Morozane's sheet had exactly that defect.
flat_skills = {}
for grp, sk in sysd["skills"].items():
    if not isinstance(sk, dict):
        continue
    for n, v in sk.items():
        r = v.get("rank") if isinstance(v, dict) else v
        if isinstance(r, int) and r > 0:
            flat_skills[n] = r


# ------------------------------------------------------------------- companion
def build_companion():
    """The manifest water kami, read from its own Adversary export.

    Rise, Water summons it, so it belongs on this sheet the way Morozane's lion
    belongs on his — but that lion had to be transcribed from screenshots, and
    this one is a real export, so nothing here is typed from memory.
    """
    k = json.load(open(KAMI, encoding="utf-8"))
    s = k["system"]
    by_name = {i["name"]: i for i in k["items"]}

    ability = ""
    for i in k["items"]:
        if i["type"] == "technique":
            ability = "%s — %s" % (i["name"], plain(i["system"].get("description", "")))
            break

    # The card has no slot for a spirit's weapons, armour or peculiarities, and
    # they are the part a player actually reaches for mid-scene. Folded into the
    # note verbatim rather than dropped.
    lines = []
    for i in k["items"]:
        if i["type"] == "weapon":
            d = plain(i["system"].get("description", ""))
            if d:
                nm = i["name"] if i["name"] != "Gear (equipped)" else "Gear"
                lines.append("%s — %s." % (nm, d.rstrip(".")))
    pecs = [i["name"] for i in k["items"] if i["type"] == "peculiarity"]
    if pecs:
        lines.append("Peculiarities: %s — neither the export nor the corpus carries "
                     "rules text for them." % ", ".join(pecs))
    lines.append("Summoned by Rise, Water. Read from his Foundry export, 2026-09-21.")

    aff = s.get("rings_affinities") or {}
    tn_mods = " · ".join("%s %s" % (r.capitalize(), ("+%d" % aff[r]) if aff[r] > 0
                                    else ("−%d" % -aff[r]) if aff[r] < 0 else "0")
                         for r in ("earth", "air", "water", "fire", "void") if r in aff)

    comp = {
        "name": k["name"],
        "kind": "Manifest Water Kami · Adversary",
        "threat": {"combat": s["conflict_rank"]["martial"],
                   "intrigue": s["conflict_rank"]["social"]},
        "demeanor": s.get("attitude", ""),
        "rings": {r: (v["rank"] if isinstance(v, dict) else v) for r, v in s["rings"].items()},
        "derived": {k2: s[k2] for k2 in ("endurance", "composure", "focus", "vigilance")},
        "ability": ability,
        "note": " ".join(lines),
    }
    if tn_mods:
        comp["tnMods"] = tn_mods
    return comp


# ninjō is filled in this export and read live.
NINJO = field(sysd["social"]["ninjo"])

# giri is not: the export's field stops mid-phrase at "…the Dragon Clan's
# interests in ", and Foundry holds no fuller copy. The owner supplied the
# ending (2026-09-26), so what is published is the export's own words finished,
# not rewritten. This defers the moment an export lands whose giri completes its
# own sentence, and says so loudly if the export ever says something else.
GIRI_COMPLETED = "To represent the Dragon Clan's interests in the City of the Rich Frog."


def _giri(raw):
    def norm(x):
        return re.sub(r"\s+", " ", x).strip().rstrip(".").lower().replace("\u2019", "'")
    live = field(raw)
    if not live or norm(GIRI_COMPLETED).startswith(norm(live)):
        return GIRI_COMPLETED
    print("NOTE: the export's giri is no longer the phrase the owner completed; "
          "publishing the export verbatim: %r" % live, file=sys.stderr)
    return live


GIRI = _giri(sysd["social"]["giri"])

SHEET = {
    "id": "kuma",
    "name": actor["name"],
    "clan": sysd["identity"]["clan"],
    "family": sysd["identity"]["family"],
    "school": sysd["identity"]["school"],
    "role": sysd["identity"]["roles"],
    "rank": sysd["identity"]["school_rank"],
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
    "bushido": {"paramount": sysd["social"]["bushido_tenets"]["paramount"],
                "less": sysd["social"]["bushido_tenets"]["less_significant"]},
    "ninjo": NINJO,
    "giri": GIRI,
    "money": "%d zeni" % sysd["zeni"],
    "techniques": techniques,
    "peculiarities": peculiarities,
    "gear": gear_list,
    "titles": [], "bonds": [], "afflictions": [],
    "companion": build_companion(),
}


# ---------------------------------------------------------------------- audits
fatal = []

# 1. Derived stats are formulae. If an export ever drifts from them, say so.
d = SHEET["derived"]
for k, want in (("endurance", (rings["earth"] + rings["fire"]) * 2),
                ("composure", (rings["earth"] + rings["water"]) * 2),
                ("focus", rings["fire"] + rings["air"]),
                ("vigilance", -(-(rings["air"] + rings["water"]) // 2))):
    if d[k] != want:
        fatal.append("derived: %s is %s, formula gives %s" % (k, d[k], want))

# 2. Every roller button against the Activation line the book prints. The export
#    fields drive the button; this proves they agree with the printed rule.
RING_EXEMPT = {"Commune with the Spirits"}   # the caster chooses the ring
for it in ordered("technique"):
    t = next(x for x in techniques if x["name"] == it["name"])
    a = t.get("activation")
    if not a or "tn" not in a:
        continue
    printed = printed_activation(plain(it["system"].get("description", "")))
    if printed is None:
        fatal.append("%s: has a roller button but prints no Activation line" % it["name"])
        continue
    tn, skill, ring = printed
    if tn is not None and tn != a["tn"]:
        fatal.append("%s: export TN %s, book prints TN %s" % (it["name"], a["tn"], tn))
    if skill is not None and skill != a["skill"]:
        fatal.append("%s: export skill %s, book prints %s" % (it["name"], a["skill"], skill))
    if ring is not None and ring != a["ring"]:
        fatal.append("%s: export ring %s, book prints %s" % (it["name"], a["ring"], ring))
    elif ring is None and it["name"] not in RING_EXEMPT:
        fatal.append("%s: no ring in the printed Activation line" % it["name"])

# 3. XP. `system.xp_spent` is 0 in this export and is not maintained, so the
#    spend is summed from the items and checked against xp_total instead.
XP_ADV = sum(i["system"].get("xp_used", 0) for i in ordered("advancement"))
XP_TECH = sum(i["system"].get("xp_used", 0) for i in ordered("technique"))
XP_TOTAL = sysd["xp_total"]
if XP_ADV + XP_TECH != XP_TOTAL:
    fatal.append("xp: advancements %d + techniques %d = %d, export total is %d"
                 % (XP_ADV, XP_TECH, XP_ADV + XP_TECH, XP_TOTAL))

if fatal:
    for line in fatal:
        print("FATAL: %s" % line, file=sys.stderr)
    sys.exit(1)

blob = json.dumps(SHEET, indent=2, ensure_ascii=False)
if "</script" in blob:
    sys.exit("sheet data would close the script tag")


# ------------------------------------------------------------------------ emit
tpl = open(TEMPLATE, encoding="utf-8").read()
i = tpl.find('<script id="sheet-data" type="application/json">')
j = tpl.find("</script>", i)
if i < 0 or j < 0:
    sys.exit("template: could not find the sheet-data block in %s" % TEMPLATE)

head = tpl[:i]
head = head.replace("Doji Setsuna — Character Sheet", "Tonbo Kuma — Character Sheet")
head = head.replace("Generated by fragile-peace-support/doji-setsuna/build/build_sheet.py",
                    "Generated by fragile-peace-support/scripts/build_kuma_sheet.py")
# No Bio link: he has no entity page, and a dead link is worse than no link.
head = head.replace('<a href="../character/setsuna.html">&lsaquo; Bio</a>\n', "")
if "&lsaquo; Bio" in head:
    sys.exit("template: the Bio link moved; it would publish as a dead link")
page = (head
        + '<script id="sheet-data" type="application/json">\n' + blob + "\n"
        + tpl[j:])
open(OUT, "w", encoding="utf-8").write(page)

print("wrote %s" % OUT)
print("  rank    %d  ·  xp %d/%d spent — advancements %d, techniques %d"
      % (SHEET["rank"], XP_ADV + XP_TECH, XP_TOTAL, XP_ADV, XP_TECH))
print("  rings   " + "  ".join("%s %d" % (r.capitalize(), rings[r])
                               for r in ("air", "earth", "fire", "water", "void")))
print("  derived " + "  ".join("%s %d" % (k, d[k])
                               for k in ("endurance", "composure", "focus", "vigilance")))
print("  social  honour %d  glory %d  status %d"
      % (sysd["social"]["honor"], sysd["social"]["glory"], sysd["social"]["status"]))
print("  skills  %d ranked" % len(flat_skills))
print("  techniques %d (%d with a roller hook)  gear %d  peculiarities %d"
      % (len(techniques), sum(1 for t in techniques if t.get("activation")),
         len(gear_list), len(peculiarities)))
print("  companion  %s" % SHEET["companion"]["name"])
if NO_CORPUS:
    print("  no corpus description for: %s (listed with their numbers only)"
          % ", ".join(sorted(set(NO_CORPUS))))
for _bad in NAME_FIXES:
    if not any(i["name"] == _bad for i in items):
        print("  NAME_FIXES no longer needed for %r — the export spells it correctly" % _bad,
              file=sys.stderr)
if GIRI == GIRI_COMPLETED and field(sysd["social"]["giri"]) != GIRI_COMPLETED:
    print("  giri: the export still stops mid-phrase; publishing the owner's completion",
          file=sys.stderr)
