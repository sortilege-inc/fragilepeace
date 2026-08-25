#!/usr/bin/env python3
"""
build_harunobu_sheet.py — generate play/harunobu.html, the playable L5R5e sheet
for Shinjo Harunobu and his Moto Charger, Khar Baatar.

Harunobu is Doji Setsuna's husband: a Shinjo bushi trained in a Crab school, a
prisoner of the Lion from session 2 until Akodo Toturi freed him before session
48. The sheet runs on the same engine as hers — play/sheet.js, play/sheet.css,
play/l5rdata.js.

Rules text is never retyped. It comes from two sources:

  FOUNDRY  sources/foundry/fvtt-Actor-shinjo-harunobu.json
           sources/foundry/fvtt-Actor-khar-baatar.json
           the owner's Foundry VTT exports, pinned here so the build is
           reproducible. **Drop fresh exports over those files and re-run.**

  CORPUS   ~/Working/Titterpig DSL/titterpig-dsl-l5r5e/0.4/*.ttrpg
           the canonical L5R5e corpus, consulted only for gear the export
           carries without a stat line.

Unlike build_morozane_sheet.py this script authors almost no metadata. Harunobu's
export records `technique_type` on every technique, `peculiarity_type` on every
peculiarity and full stat blocks on his gear, so tags, rings and numbers are all
derived. The only hand-written things are display order and the roller hooks the
engine needs, which no export carries.

    python3 scripts/build_harunobu_sheet.py
"""

import glob
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FOUNDRY = os.path.join(ROOT, "sources", "foundry", "fvtt-Actor-shinjo-harunobu.json")
HORSE = os.path.join(ROOT, "sources", "foundry", "fvtt-Actor-khar-baatar.json")
OUT = os.path.join(ROOT, "play", "harunobu.html")
TEMPLATE = os.path.join(ROOT, "play", "setsuna.html")
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


def field(text):
    """Foundry textareas keep the editor's markdown. Flatten to sheet prose.

    His giri and ninjō are written as nested markdown lists with bold runs. The
    sheet renders one flowed block, so the bullets become sentences and the
    asterisks come off; nothing is dropped.
    """
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


def corpus_props(name, keys):
    """Named PROPERTIES off a gear DEF — used only where the export has no stats.

    Names are not unique across the corpus, so the block matching the most
    requested keys wins. Returns "" when the corpus does not carry the item,
    and the sheet then lists it by name with no numbers rather than inventing any.
    """
    src = corpus_text()
    best = []
    for m in re.finditer(r'\^"' + re.escape(name) + r'" DEF \{', src):
        depth, i = 0, m.end() - 1
        for j in range(i, len(src)):
            if src[j] == "{":
                depth += 1
            elif src[j] == "}":
                depth -= 1
                if depth == 0:
                    break
        body = src[m.start():j + 1]
        got = []
        for k in keys:
            km = re.search(r'\^"' + re.escape(k) + r'" (?:STRING "((?:[^"\\]|\\.)*)"|INTEGER (\d+))', body)
            if km:
                got.append("%s %s" % (k, km.group(1) or km.group(2)))
        if len(got) > len(best):
            best = got
    return " · ".join(best)


actor = json.load(open(FOUNDRY, encoding="utf-8"))
horse = json.load(open(HORSE, encoding="utf-8"))
sysd = actor["system"]
items = actor["items"]
by_name = {i["name"]: i for i in items}


def fdesc(name):
    if name not in by_name:
        sys.exit("foundry: item %r not in export" % name)
    return plain(by_name[name]["system"].get("description", ""))


# ------------------------------------------------------------ authored metadata
# Everything below is display order and engine hooks. Tags, rings, stats and
# rules text are all read from the export.

# technique_type → the label the sheet prints, in the order techniques are shown.
TECH_TAGS = [
    ("school_ability", "School Ability"),
    ("title_ability", "Title Ability"),
    ("shuji", "Shūji"),
    ("ritual", "Ritual"),
    ("kata", "Kata"),
    ("ninjutsu", "Ninjutsu"),
]
PECULIARITY_TAGS = {"distinction": "Distinction", "passion": "Passion",
                    "adversity": "Adversity", "anxiety": "Anxiety"}

# Roller hooks, keyed by technique name. The engine reads these to offer an
# activation button; no export carries them, so each one is checked against the
# corpus rather than guessed at.
#
# Only techniques that are *independently activated on their own check* belong
# here. Great Anvil's Measure and Tactical Assessment are (op) spends on somebody
# else's action — a Guard or Reinforce, and an Initiative check — and giving them
# a roller button invites a check that the rules never call for. Warrior's Resolve
# takes no check at all. All three are deliberately absent.
ACTIVATION = {
    # "Once per scene as a Support action, you may make a TN 5 Command (Void) check
    # targeting your cohort or a number of characters who can hear you up to your
    # ranks in Meditation. Reduce TN to 2 if all targets are in Confining or
    # Entangling terrain."
    "Battle of No Escape": {"actionType": "Support action", "punct": ":", "tn": 5,
                            "skill": "command", "ring": "void",
                            "note": "TN 2 if all targets are in Confining or Entangling "
                                    "terrain. Reaches your cohort, or characters who can "
                                    "hear you up to your ranks in Meditation ({med})."},
    "Fortress of Necessity": {"actionType": "Support action", "punct": ":", "tn": 3,
                              "skill": "command", "ring": "earth"},
}

# Per-scene limits on the techniques that carry one.
USES = {
    "Battle of No Escape": {"max": 1, "per": "Scene"},
    "Warrior’s Resolve": {"max": 1, "per": "Scene"},
}

# Techniques that spend a resource instead of rolling. Core p. 178: "Once per
# scene, as a Support action, you may spend 1 Void point to recover. Effects:
# Remove fatigue equal to your honor rank." No check is involved, so this is a
# button rather than an activation.
USE = {
    "Warrior’s Resolve": {"label": "Support action", "voidCost": 1,
                          "fatigueRemove": "honorRank",
                          "uses": {"max": 1, "per": "Scene"},
                          "note": "No check. Removes fatigue equal to your honor rank "
                                  "({n})."},
}

# Anxieties drive the engine's strife buttons; distinctions and adversities drive
# its advantage/disadvantage rerolls. Two each, per the core rules.
ADV = {"kind": "advantage", "max": 2}
DIS = {"kind": "disadvantage", "max": 2, "successOnly": True, "mustMax": True}
PECULIARITY_HOOKS = {
    "Bishamon’s Blessing": {"reroll": dict(ADV, approach="water")},
    "Indomitable Will": {"reroll": dict(ADV, approach="earth")},
    "Glorious Deeds": {"strife": -3},
    "Fukurokujin’s Curse": {"reroll": dict(DIS, approach="fire")},
    "Belligerent": {"strife": 3},
    "Superstition": {"strife": 3},
}

WEAPON_KEYS = ["Category", "Skill", "Range", "Damage", "Deadliness", "Rarity", "Qualities"]
ARMOR_KEYS = ["Physical", "Supernatural", "Rarity", "Qualities"]

# Items the export carries with no rules text of their own. What they are comes
# from the owner's character notes; nothing mechanical is invented, and where the
# notes say nothing the entry stays bare.
GEAR_NOTES = {
    "Scroll of Battle Tactics": "School issue. The Hida Battle Leader starting outfit includes "
                                "“several scrolls of battle tactics”, and he still carries them.",
    "Three Victories":"A calligraphy scroll, penned by Akodo Masanari and given to him as the "
                       "Lion half of a pact of brotherhood: “Victory over the enemy. "
                       "Victory over oneself. Victory over fate.” Masanari meant it as a "
                       "question — whether Harunobu pursues his own path or merely follows "
                       "orders. Harunobu's half of the exchange was an iron mon cut from a "
                       "fallen section of the Kaiu Wall he had defended.",
}


# ------------------------------------------------------------------- assembly
def qualities(it):
    return [p["name"] for p in it["system"].get("properties", []) if p.get("name")]


def technique(it):
    s = it["system"]
    t = {"name": it["name"], "tag": dict(TECH_TAGS)[s["technique_type"]],
         "text": plain(s.get("description", ""))}
    if s.get("ring"):
        t["ring"] = s["ring"]
    if it["name"] in ACTIVATION:
        act = dict(ACTIVATION[it["name"]])
        note = act.pop("note", None)
        t["activation"] = act
        if note:
            t["text"] = note.replace("{med}", str(
                sysd["skills"]["martial"].get("meditation", 0))) + "\n\n" + t["text"]
    if it["name"] in USES:
        t["uses"] = USES[it["name"]]
    if it["name"] in USE:
        t["use"] = USE[it["name"]]
    return t


def peculiarity(it):
    s = it["system"]
    p = {"name": it["name"], "tag": PECULIARITY_TAGS[s["peculiarity_type"]],
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
        stats = corpus_props(it["name"], ARMOR_KEYS)
        g["kind"] = "Armour"
        for k in ("Physical", "Supernatural"):
            m = re.search(k + r" (\d+)", stats)
            if m:
                g[k.lower()] = int(m.group(1))
    else:
        g["kind"] = "Item"
    q = qualities(it)
    if q:
        g["qualities"] = q
    if s.get("rarity") not in (None, "", "0"):
        g["rarity"] = int(s["rarity"])
    text = plain(s.get("description", "")) or GEAR_NOTES.get(it["name"], "")
    if text:
        g["text"] = text
    return g


def all_items(src):
    """Every item, including the ones a title owns.

    A title's own `system.items` holds the advancements and techniques bought
    through it, and they are items the character genuinely has — Righteous
    Example and Heartpiercing Strike are both paid for and both invisible to a
    pass that only walks `actor["items"]`. The title card listing them under
    Curriculum is what made them look accounted for.

    Used for display only. The XP pass below deliberately keeps reading top level,
    because a title's `xp_used` already sums its children and walking both would
    total 116 against an `xp_total` of 100.
    """
    for i in src:
        yield i
        if i["type"] == "title":
            for sub in i["system"].get("items", []):
                yield sub


def ordered(kind, key=None):
    out = [i for i in all_items(items) if i["type"] == kind]
    return sorted(out, key=key) if key else out


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

rings = sysd["rings"]
flat_skills = {k: v for grp in sysd["skills"].values() for k, v in grp.items() if v}

# The reciprocal of the bond on Setsuna's sheet. A GM grant at rank 1, costing
# nothing, so it sits outside the XP ledger entirely — bond XP counts toward
# neither school curriculum nor title progress in any case.
#
# Prefer a bond item off the export, so the two sheets stay in step from one
# source; the constant below is the stand-in until an export carrying it lands.
SETSUNA_BOND = {
    "name": "Doji Setsuna",
    "type": "Wife (Lover)",
    "rank": 1,
    "ability": "With You, the Storm Subsides",
    "abilityText": "At end of scene involving lover or reminders of them, call upon bond "
                   "to remove additional strife equal to bond rank.",
    "use": {"label": "End of scene · call upon the bond", "strifeRemove": "bondRank",
            "note": "Removes additional strife equal to your bond rank ({n})."},
    "text": "Samurai are expected to place romantic love below their obligations to family "
            "and clan — but the human heart is not so easily confined. Many samurai who "
            "fall in love keep their relationship secret, while others are more overt.\n\n"
            "A lover seeks to spend time with you, writes letters to you, and is willing "
            "to assist you in ways that do not require publicly acknowledging your bond — "
            "giving you information key to pursuing a desired goal, encouraging you to "
            "pursue your personal interests, helping you to deal with emotions you usually "
            "must keep to yourself — and they expect you to do the same.\n\n"
            "Generally, your lover's allies do not acknowledge your relationship. Some "
            "might be favorably disposed to you covertly if you make their ally happy (and "
            "unfavorably disposed if you make them unhappy), while others might be jealous "
            "of the attention you receive. Your lover's enemies might target you to attempt "
            "to gain leverage over your lover.\n\n"
            "If your bond rank is 3 or higher, a lover is more overt about your "
            "relationship, allowing them to assist you more publicly — such as giving you "
            "letters of introduction to officials above your status, allowing you to use "
            "their name to pursue your goals, and even helping you directly — and they "
            "expect the same from you.",
}

bonds = []
for it in items:
    if it["type"] != "bond":
        continue
    s = it["system"]
    b = {"name": it["name"], "rank": s.get("rank", 1),
         "text": plain(s.get("description", ""))}
    if it["name"] == SETSUNA_BOND["name"]:
        b = dict(SETSUNA_BOND, **{k: v for k, v in b.items() if v})
    bonds.append(b)
if not any(b["name"] == SETSUNA_BOND["name"] for b in bonds):
    bonds.append(SETSUNA_BOND)

# The one title he holds. Its ability is a technique in its own right in the
# export, so the card points at that entry rather than restating the text.
titles = []
for it in ordered("title"):
    s = it["system"]
    ability = next((x["name"] for x in items
                    if x["type"] == "technique"
                    and x["system"].get("technique_type") == "title_ability"), "")
    titles.append({
        "name": it["name"],
        "state": "Invested — %d of %d XP" % (s.get("xp_used", 0), s.get("xp_cost", 0)),
        "ability": ability,
        "abilityText": plain(by_name[ability]["system"]["description"]) if ability else "",
        "curriculum": [x["name"] for x in s.get("items", [])],
        "text": plain(s.get("description", "")),
    })

# Khar Baatar is a real Foundry NPC export, not a transcription: a Moto Charger,
# minion type, ridden rather than commanded. The engine's companion card takes
# the same shape as Morozane's lion.
hs = horse["system"]
COMPANION = {
    "name": horse["name"],
    "kind": "Moto Charger · mount",
    "threat": {"combat": hs["conflict_rank"]["martial"],
               "intrigue": hs["conflict_rank"]["social"]},
    "demeanor": hs.get("attitude", ""),
    "rings": {r: hs["rings"][r] for r in ("air", "earth", "fire", "water", "void")},
    "derived": {"endurance": hs["endurance"], "composure": hs["composure"],
                "focus": hs["focus"], "vigilance": hs["vigilance"]},
    "tnMods": " · ".join("%s %+d" % (r.title(), hs["rings_affinities"][r])
                         for r in ("earth", "air", "water", "fire", "void")),
    "skillGroups": hs["skills"],
    "ability": " · ".join(
        "%s (%s)" % (i["name"], i["system"]["peculiarity_type"].title())
        if i["type"] == "peculiarity" else i["name"]
        for i in horse["items"] if i["type"] in ("technique", "peculiarity")),
}

# The companion card renders name/kind/threat/demeanor/rings/derived/skillGroups/
# tnMods/ability/note and nothing else, so what matters in play goes in `note`
# rather than in keys the engine would silently drop: his hooves profile, and the
# Loyal Steed text — which is really a rule about *Harunobu*, since the bonuses
# land on the rider.
#
# One wrinkle to know about: the actor was built by duplicating a Rokugani Pony
# and relabelling it. Mechanically the Moto Charger conversion is applied
# correctly — Willful, Brute Strength and Masterful Fighter are exactly the
# corpus's picks, and Tireless Runner is gone — but the *prose* it inherited
# still says "Rokugani pony". The breed line below is the corpus's own Moto
# Charger text, so the card describes the horse it actually is; the export's
# rules text follows verbatim and is not edited.
_note = [corpus_props("Moto Charger", ["Description"]).replace("Description ", "")]
_hooves = next((i for i in horse["items"] if i["type"] == "weapon"), None)
if _hooves:
    w = _hooves["system"]
    _note.append("%s — Range %s · Damage %s · Deadliness %s"
                 % (_hooves["name"], w.get("range", "?"), w.get("damage", "?"),
                    w.get("deadliness", "?")))
_steed = next((i for i in horse["items"] if i["name"] == "Loyal Steed"), None)
if _steed:
    _note.append(plain(_steed["system"].get("description", "")))
COMPANION["note"] = "\n\n".join(x for x in _note if x)

# Standing notices, shown at the top of both the sheet and the dossier. These are
# table facts the export cannot carry: awards the GM has said are owed but has not
# yet set. Delete the entry the moment the number lands on the sheet — a banner
# that outlives its award is worse than no banner.
PENDING_LABEL = "Awaiting the GM"
PENDING = [
    "<b>Glory award outstanding</b> for his part in the Unicorn/Lion conflict and "
    "his captivity as a prisoner of the Lion — and possibly honour or status with "
    "it. The GM has yet to set the figure; expected next session.",
    "The glory, honour and status below are therefore <b>pre-award</b>. Do not "
    "spend or stake against a number that is about to move.",
]

SHEET = {
    "id": "harunobu",
    "name": actor["name"],
    "clan": sysd["identity"]["clan"],
    "family": sysd["identity"]["family"],
    "school": sysd["identity"]["school"],
    "role": sysd["identity"]["roles"],
    "rank": sysd["identity"]["school_rank"],
    "portrait": "../assets/harunobu.webp",
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
    "ninjo": field(sysd["social"]["ninjo"]),
    "giri": field(sysd["social"]["giri"]),
    "money": "%d zeni" % sysd["zeni"],
    "techniques": techniques,
    "peculiarities": peculiarities,
    "gear": gear_list,
    "titles": titles,
    "bonds": bonds,
    "afflictions": [],
    "companion": COMPANION,
    "pendingLabel": PENDING_LABEL,
    "pending": PENDING,
}

# XP has to be counted off the item tree, not read off `system.xp_spent` — that
# summary field is left at 0 in this export and believing it would say he has
# spent nothing. Count top-level items only: a title's `xp_used` is already the
# sum of the advancements and techniques nested inside it, so recursing turns
# Harunobu's 100 into 116.
xp_adv = sum(i["system"].get("xp_used") or 0 for i in items if i["type"] == "advancement")
xp_tech = sum(i["system"].get("xp_used") or 0 for i in items if i["type"] == "technique")
xp_title = sum(i["system"].get("xp_used") or 0 for i in items if i["type"] == "title")
xp_spent = xp_adv + xp_tech + xp_title
xp_total = sysd.get("xp_total", 0)
if xp_spent != xp_total:
    sys.exit("xp: tree accounts for %d of %d — reconcile before publishing "
             "(advancements %d, techniques %d, titles %d)"
             % (xp_spent, xp_total, xp_adv, xp_tech, xp_title))

# Derived stats follow from the rings; if an export ever drifts, say so loudly
# rather than publishing numbers that do not add up.
d = SHEET["derived"]
for key, want in [("endurance", (rings["earth"] + rings["fire"]) * 2),
                  ("composure", (rings["earth"] + rings["water"]) * 2),
                  ("focus", rings["fire"] + rings["air"]),
                  ("vigilance", -(-(rings["air"] + rings["water"]) // 2))]:
    if d[key] != want:
        sys.exit("derived %s: export says %d, rings give %d" % (key, d[key], want))

blob = json.dumps(SHEET, indent=2, ensure_ascii=False)
if "</script" in blob:
    sys.exit("sheet data would close the script tag")

# The page frame is taken from Setsuna's sheet so the two stay identical but for
# their data — same engine, same stylesheet, same bar.
page = open(TEMPLATE, encoding="utf-8").read()
page = page.replace("Doji Setsuna — Character Sheet", "Shinjo Harunobu — Character Sheet")
page = page.replace('<a href="../character/setsuna.html">&lsaquo; Bio</a>',
                    '<a href="../character/harunobu.html">&lsaquo; Bio</a>')
page = re.sub(r'(<script id="sheet-data" type="application/json">\n).*?(\n</script>)',
              lambda m: m.group(1) + blob + m.group(2), page, flags=re.S)
page = page.replace("Generated by build/build_sheet.py in ~/Working/doji-setsuna — edit that, not this.",
                    "Generated by scripts/build_harunobu_sheet.py — edit that, not this.")
open(OUT, "w", encoding="utf-8").write(page)

print("wrote %s" % OUT)
print("  techniques    %d" % len(SHEET["techniques"]))
print("  peculiarities %d" % len(SHEET["peculiarities"]))
print("  gear          %d" % len(SHEET["gear"]))
print("  titles %d  companion %s" % (len(SHEET["titles"]), COMPANION["name"]))
print("  skills ranked %d" % len(SHEET["skills"]))
print("  xp %d/%d spent — advancements %d, techniques %d, title %d"
      % (xp_spent, xp_total, xp_adv, xp_tech, xp_title))
