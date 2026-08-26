#!/usr/bin/env python3
"""
build_jujiro_sheet.py — generate play/jujiro.html, the playable L5R5e sheet for
Asahina Jūjirō.

Jūjirō is an Asahina Artificer: a Crane shugenja-artisan, Master Artisan by the
gift of the Imperial consort Shiba Ayame, and the father of the pregnancy Doji
Setsuna terminated. The sheet runs on the same engine as hers and Harunobu's —
play/sheet.js, play/sheet.css, play/l5rdata.js.

Rules text is never retyped. It comes from two sources:

  FOUNDRY  sources/foundry/fvtt-Actor-asahina-jujiro.json
           the owner's Foundry VTT export, pinned here so the build is
           reproducible. **Drop a fresh export over that file and re-run.**

  CORPUS   ~/Working/Titterpig DSL/titterpig-dsl-l5r5e/0.4/*.ttrpg
           the canonical L5R5e corpus.

The corpus does far more work here than it does for Harunobu. **Every
`description` field in this export is empty** — Foundry dropped the compendium
text on import — so a sheet built from the export alone would carry no rules at
all. Activation, Effects and Opportunities for every technique, and the Effect
block for every peculiarity, are lifted verbatim out of the corpus DEFs. Nothing
is paraphrased and nothing is invented; where the corpus does not carry an item
(the Boon of Benten omamori), the entry stays bare but for the owner's own note.

    python3 scripts/build_jujiro_sheet.py
"""

import glob
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FOUNDRY = os.path.join(ROOT, "sources", "foundry", "fvtt-Actor-asahina-jujiro.json")
OUT = os.path.join(ROOT, "play", "jujiro.html")
TEMPLATE = os.path.join(ROOT, "play", "setsuna.html")
CORPUS_DIR = os.path.expanduser("~/Working/Titterpig DSL/titterpig-dsl-l5r5e/0.4")


# ---------------------------------------------------------------- extraction
# Foundry's compendium text uses a private-use glyph for the opportunity symbol
# where the rest of the book writes "(op)". Left alone it reaches the page as a
# missing-glyph box in the middle of a rules sentence.
PUA = {"\uf3b3": "(op)"}


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


def unesc(s):
    r"""Corpus strings escape their quotes and mark cross-references as ^"Name".

    Unescape first, then drop the reference carets, so ^\"Silhouette\" arrives as
    plain Silhouette rather than as markup the sheet would render literally.
    """
    s = s.replace('\\"', '"').replace("\\\\", "\\")
    return re.sub(r'\^"([^"]*)"', r"\1", s)


def corpus_block(name):
    """The body of the DEF block for `name`, preferring one that carries rules text.

    A handful of names appear in more than one book (Path to Inner Peace is in
    both core-techniques and the Children of the Five Winds GM tools). The block
    that actually defines the technique is the one with ACTIVATION or EFFECT(S)
    in it; ties go to the longer body.

    Apostrophes are matched either way round. Foundry writes the typographic
    U+2019 (Reflections of P’an Ku, Benten’s Blessing) and the corpus writes the
    ASCII one, so a literal match finds neither book's version of half this
    character's sheet.
    """
    src = corpus_text()
    pat = r'\^"' + "['\u2019]".join(re.escape(p) for p in re.split(r"['\u2019]", name)) + r'" DEF \{'
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
        score = (sum(k in body for k in ("ACTIVATION", "EFFECTS", "EFFECT {", "EFFECT \"")),
                 len(body))
        if score > best_score:
            best, best_score = body, score
    return best


def corpus_strings(body, key):
    """`KEY "…"` or `KEY { "…" "…" }` → the list of strings, unescaped.

    Returns [] when the key is absent, which is a real answer: Artisan's
    Appraisal genuinely has no EFFECTS block because it is an opportunity spend.
    """
    m = re.search(r"\b" + key + r'\s*(\{|")', body)
    if not m:
        return []
    if m.group(1) == '"':
        q = re.match(r'"((?:[^"\\]|\\.)*)"', body[m.end() - 1:])
        return [unesc(q.group(1))] if q else []
    depth, end = 0, len(body)
    for j in range(m.end() - 1, len(body)):
        if body[j] == "{":
            depth += 1
        elif body[j] == "}":
            depth -= 1
            if depth == 0:
                end = j
                break
    return [unesc(x) for x in re.findall(r'"((?:[^"\\]|\\.)*)"', body[m.end():end])]


def corpus_prop(body, key):
    """`^"Key" STRING "value"` → value, unescaped.

    Techniques write their rules as bare `ACTIVATION "…"` keys; titles write
    theirs as named PROPERTIES. Reading a title with corpus_strings() returns the
    literal " STRING " between the two quoted runs, which is how the first build
    of this file put `STRING` on the page as the name of a title ability.
    """
    m = re.search(r'\^"' + re.escape(key) + r'" STRING "((?:[^"\\]|\\.)*)"', body)
    return unesc(m.group(1)) if m else ""


def rules_text(name):
    """Activation / Effects / Opportunities for a technique, verbatim from the corpus."""
    body = corpus_block(name)
    if not body:
        return ""
    parts = []
    for label, key in (("Activation", "ACTIVATION"), ("Effects", "EFFECTS")):
        vals = corpus_strings(body, key)
        if vals:
            parts.append("%s: %s" % (label, "\n\n".join(vals)))
    opps = corpus_strings(body, "OPPORTUNITIES")
    if opps:
        parts.append("Opportunities:\n" + "\n".join("• " + o for o in opps))
    return "\n\n".join(parts)


def effect_text(name):
    """The EFFECT block of a peculiarity, verbatim from the corpus."""
    body = corpus_block(name)
    return "\n\n".join(corpus_strings(body, "EFFECT")) if body else ""


def school_free_techniques(school, owned):
    """Technique names this school grants at character creation, from the corpus.

    The Asahina Artificer block reads:

        STARTING_TECHNIQUES {
            INVOCATION CHOOSE 3 [Blessed Wind, Armor of Radiance, Inari's Blessing,
                                 Reflections of P'an Ku, Token of Memory]
            RITUAL "Commune with the Spirits"
            RITUAL "Cleansing Rite"
        }

    The rituals are granted outright; the invocations are whichever of the choose
    list the character actually owns. Needed because the export prices all five
    as 3 XP purchases made at rank 2, which is 15 XP the character never spent.
    """
    body = corpus_block(school)
    m = re.search(r"STARTING_TECHNIQUES \{(.*?)\n(\s*)\}", body, re.S)
    if not m:
        return set()
    block = m.group(1)
    # Compare on a normalised key: the corpus writes P'an Ku with an ASCII
    # apostrophe and the export writes P’an Ku with a typographic one, and a
    # literal match silently leaves that invocation priced as a purchase.
    def key(x):
        return x.replace("\u2019", "'")
    have = {key(n): n for n in owned}
    free = set()
    for name in re.findall(r'RITUAL \^"([^"]+)"', block):
        if key(name) in have:
            free.add(have[key(name)])
    for _kind, n, lst in re.findall(r'(\w+) CHOOSE (\d+) \[([^\]]*)\]', block):
        picks = [have[key(x)] for x in re.findall(r'\^"([^"]+)"', lst) if key(x) in have]
        free |= set(picks[:int(n)])
    return free


actor = json.load(open(FOUNDRY, encoding="utf-8"))
sysd = actor["system"]
items = actor["items"]
tq = sysd["twenty_questions"]


# ------------------------------------------------------------ authored metadata
# Display order and engine hooks. Tags, rings, TNs and stats are read from the
# export; rules prose is read from the corpus. Only what neither carries is here.

TECH_TAGS = [
    ("school_ability", "School Ability"),
    ("title_ability", "Title Ability"),
    ("invocation", "Invocation"),
    ("ritual", "Ritual"),
    ("shuji", "Shūji"),
]
PECULIARITY_TAGS = {"distinction": "Distinction", "passion": "Passion",
                    "adversity": "Adversity", "anxiety": "Anxiety"}

# Roller hooks. Each is transcribed from the corpus ACTIVATION line quoted above
# it, and every TN, skill and ring below is cross-checked against the export's
# own `difficulty`/`skill`/`ring` fields by the audit further down — a mismatch
# is fatal rather than published.
#
# Artisan's Appraisal is deliberately absent. It is an (op) spend on somebody
# else's Artisan/Performance/Games check, not an action of its own, and giving it
# a button would invite a roll the rules never call for. Spiritual Artisan is a
# passive school ability for the same reason.
ACTIVATION = {
    # "As a Support action, make a TN 2 Theology (Fire) check targeting one set
    #  of armor at range 0-1."
    "Armor of Radiance": {"actionType": "Support action", "punct": ",", "tn": 2,
                          "skill": "theology", "ring": "fire"},
    # "As a Scheme action, make a TN 2 Theology (Water) check targeting one item
    #  at range 0-1."
    "Reflections of P’an Ku": {"actionType": "Scheme action", "punct": ",", "tn": 2,
                               "skill": "theology", "ring": "water"},
    # "As a Scheme action, make a TN 2 Theology (Air) check targeting one
    #  position at range 0-1."
    "Token of Memory": {"actionType": "Scheme action", "punct": ",", "tn": 2,
                        "skill": "theology", "ring": "air"},
    # "As a Scheme and Support action, make a Theology (Air) check targeting one
    #  object or character at range 0-1. TN equals the target's Silhouette."
    #
    # No fixed TN: the export's `difficulty: 2` is the system's default, not this
    # invocation's number, so the button carries a label instead and the audit
    # below exempts it by name.
    "Cloak of Night": {"actionType": "Scheme & Support", "punct": ",",
                       "tnLabel": "silhouette", "skill": "theology", "ring": "air"},
    # "As a Support action, make a TN 2 Theology (Water) check targeting yourself
    #  or another character at range 0-2."
    "Path to Inner Peace": {"actionType": "Support action", "punct": ",", "tn": 2,
                            "skill": "theology", "ring": "water"},
    # "Once per game session, as a downtime activity using a tea set, make a TN 2
    #  Performance (Void) check targeting yourself and a number of other
    #  characters up to your ranks in Culture…"
    "Tea Ceremony": {"actionType": "Downtime", "punct": ",", "tn": 2,
                     "skill": "performance", "ring": "void"},
    # "As a downtime activity, make a TN 3 Theology (Void) check targeting up to
    #  five characters…"
    "Cleansing Rite": {"actionType": "Downtime", "punct": ",", "tn": 3,
                       "skill": "theology", "ring": "void"},
    # "As a downtime activity or Support action, make a TN 1 Theology check using
    #  Air, Earth, Fire, Water, or Void…"
    #
    # The ring is the caster's choice; the button opens on Void because that is
    # what the export records, and the Activation line on the card states the
    # freedom. Change the ring in the roller before rolling.
    "Commune with the Spirits": {"actionType": "Downtime or Support", "punct": ",", "tn": 1,
                                 "skill": "theology", "ring": "void"},
}

# Per-session limits carried in the corpus activation text rather than any field.
USES = {
    "Tea Ceremony": {"max": 1, "per": "Session"},
}

# Anxieties drive the engine's strife buttons; distinctions and adversities drive
# its advantage/disadvantage rerolls. Two dice each, per the core rules.
ADV = {"kind": "advantage", "max": 2}
DIS = {"kind": "disadvantage", "max": 2, "successOnly": True, "mustMax": True}
PECULIARITY_HOOKS = {
    "Benten’s Blessing": {"reroll": dict(ADV, approach="air")},
    "Charity": {"strife": -3},
    "Bitter Betrothal": {"reroll": dict(DIS, approach="water")},
    "Incurable Illness": {"reroll": dict(DIS, approach="earth")},
    "Claustrophobia": {"strife": 3},
}

# Items the export carries with no rules text, and which the corpus does not
# define either. What they are comes from the owner's own answers to the twenty
# questions; nothing mechanical is invented.
GEAR_NOTES = {
    "Omamori (Boon of Benten)": "A gift from Shiba Ayame after Otosan Uchi — a charm of "
                                "the Fortune of Arts and Romantic Love, given by the one "
                                "person at court who knows why it is funny.",
}


# ------------------------------------------------------------------- assembly
def qualities(it):
    return [p["name"] for p in it["system"].get("properties", []) if p.get("name")]


def technique(it):
    s = it["system"]
    t = {"name": it["name"], "tag": dict(TECH_TAGS)[s["technique_type"]],
         "text": plain(s.get("description", "")) or rules_text(it["name"])}
    if s.get("ring"):
        t["ring"] = s["ring"]
    if it["name"] in ACTIVATION:
        t["activation"] = dict(ACTIVATION[it["name"]])
    if it["name"] in USES:
        t["uses"] = USES[it["name"]]
    return t


def peculiarity(it):
    s = it["system"]
    p = {"name": it["name"], "tag": PECULIARITY_TAGS[s["peculiarity_type"]],
         "ring": s.get("ring", ""),
         "text": plain(s.get("description", "")) or effect_text(it["name"])}
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
        # Unlike Harunobu's, this export carries the armour numbers itself.
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
    text = plain(s.get("description", "")) or GEAR_NOTES.get(it["name"], "")
    if text:
        g["text"] = text
    return g


def all_items(src):
    """Every item, including the advancements and techniques a title owns.

    Display only. The XP audit below reads top level, because a title's `xp_used`
    already sums its children and walking both would double-count them.
    """
    for i in src:
        yield i
        if i["type"] == "title":
            for sub in i["system"].get("items", []):
                yield sub


def ordered(kind):
    return [i for i in all_items(items) if i["type"] == kind]


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

# The school ability carries no DEF of its own in the corpus — it lives inside the
# Asahina Artificer school block as a SCHOOL_ABILITY. Pull it from there so the
# card is not the one entry on the sheet with no text.
_school = corpus_block("Asahina Artificer")
for t in techniques:
    if not t["text"] and t["tag"] == "School Ability":
        nm = "['\u2019]".join(re.escape(p) for p in re.split(r"['\u2019]", t["name"]))
        m = re.search(r'SCHOOL_ABILITY "' + nm + r'" \{\s*"((?:[^"\\]|\\.)*)"',
                      corpus_text())
        if m:
            t["text"] = unesc(m.group(1))

# The one title. Its ability is not an item in this export the way Harunobu's is,
# so the name and effect come from the corpus DEF instead.
titles = []
for it in ordered("title"):
    s = it["system"]
    body = corpus_block(it["name"])
    ability = corpus_prop(body, "Title Ability")
    titles.append({
        "name": it["name"],
        "state": "Invested — %d of %d XP" % (s.get("xp_used", 0), s.get("xp_cost", 0)),
        "ability": ability,
        "abilityText": corpus_prop(body, "Title Ability Effect"),
        "curriculum": [x["name"] for x in s.get("items", [])],
        "text": plain(s.get("description", "")),
    })

# ninjō and giri live in the twenty-questions record, not in the live social
# fields — `system.social.ninjo` and `system.social.giri` are both empty strings
# in this export. Prefer the live field the moment it is filled, so a future
# export that sets it wins without a code change.
NINJO = field(sysd["social"]["ninjo"]) or field(tq["step6"]["social_ninjo"])
GIRI = field(sysd["social"]["giri"]) or field(tq["step5"]["social_giri"])

# Jūjirō is non-binary. The pronoun correction reached the twenty-questions
# record but not `system.social.ninjo`, which is the field actually published,
# so the site was misgendering them. The owner has since fixed it in Foundry;
# this stands in until an export carrying the fix lands, and reports itself as
# redundant the moment one does. Delete it then.
NINJO_STALE, NINJO_FIXED = "find him a match", "find them a match"
if NINJO_STALE in NINJO:
    NINJO = NINJO.replace(NINJO_STALE, NINJO_FIXED)
    print("  note: ninjō pronoun corrected in-flight — the export still reads "
          "%r in system.social.ninjo" % NINJO_STALE)
else:
    print("  note: export carries the ninjō pronoun fix; the in-flight "
          "correction in this script is now redundant and can be deleted")

# The live field and the chargen record are allowed to differ — Setsuna's tenets
# do, on purpose. But when they differ only in a pronoun it is a half-applied
# edit, so say so on every build rather than shipping the stale one silently.
for label, live, rec in (("ninjō", NINJO, field(tq["step6"]["social_ninjo"])),
                         ("giri", GIRI, field(tq["step5"]["social_giri"]))):
    if live and rec and live != rec:
        print("  note: %s differs between the live field and the twenty-questions "
              "record; the live field is being published" % label)

# The export's `name` carries a Foundry working label ("Asahina Jûjirô (50 XP)")
# and circumflexes where the site uses macrons, so the display name is set here.
PORTRAIT = "jujiro.webp"
_have_portrait = os.path.exists(os.path.join(ROOT, "assets", PORTRAIT))

SHEET = {
    "id": "jujiro",
    "name": "Asahina Jūjirō",
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
    "titles": titles,
    "bonds": [],
    "afflictions": [],
}

# The engine skips the portrait block entirely when the key is absent, so an
# asset that is not on disk yet leaves a clean card rather than a broken image.
# Drop assets/jujiro.webp in place and re-run; no code change needed.
if _have_portrait:
    SHEET["portrait"] = "../assets/" + PORTRAIT

# --------------------------------------------------------------------- audits
# Nothing below changes the sheet. Each one refuses to publish numbers that do
# not add up, rather than quietly shipping them.

# 1. Every roller hook is checked against the export's own fields. `difficulty`
#    on Cloak of Night is the system default rather than its real TN, which the
#    corpus states as the target's silhouette, so that one name is exempt.
TN_EXEMPT = {"Cloak of Night"}
by_name = {i["name"]: i for i in all_items(items)}
for name, act in ACTIVATION.items():
    s = by_name[name]["system"]
    if act.get("ring") and s.get("ring") and act["ring"] != s["ring"]:
        sys.exit("activation %s: ring %s, export says %s" % (name, act["ring"], s["ring"]))
    if act.get("skill") and s.get("skill") and act["skill"] != s["skill"]:
        sys.exit("activation %s: skill %s, export says %s" % (name, act["skill"], s["skill"]))
    if name not in TN_EXEMPT and act.get("tn") is not None and s.get("difficulty"):
        if int(act["tn"]) != int(s["difficulty"]):
            sys.exit("activation %s: TN %s, export says %s"
                     % (name, act["tn"], s["difficulty"]))

# 2. Every technique and peculiarity must have arrived with rules text. The
#    export supplies none, so a silent corpus miss would ship an empty card.
for t in techniques + peculiarities:
    if not t.get("text"):
        sys.exit("no rules text for %r — corpus lookup failed" % t["name"])

# 3. XP off the item tree. `system.xp_spent` is a separate summary field and is
#    not where this data lives, so the ledger is rebuilt from the items. Top
#    level only: a title's `xp_used` already sums its children.
#
#    Starting techniques are discounted. The export prices the school's five
#    chargen grants as 3 XP purchases apiece, which is 15 XP the character never
#    spent; the free set is derived from the corpus rather than listed here, so
#    the discount goes to zero by itself once the export stops charging for them.
FREE_TECH = school_free_techniques(
    re.sub(r"\s+School$", "", sysd["identity"]["school"]),
    {i["name"] for i in items if i["type"] == "technique"})
xp_free = sum(int(i["system"].get("xp_used") or 0)
              for i in items if i["type"] == "technique" and i["name"] in FREE_TECH)
xp_adv = sum(int(i["system"].get("xp_used") or 0) for i in items if i["type"] == "advancement")
xp_tech = sum(int(i["system"].get("xp_used") or 0)
              for i in items if i["type"] == "technique" and i["name"] not in FREE_TECH)
xp_title = sum(int(i["system"].get("xp_used") or 0) for i in items if i["type"] == "title")
xp_spent = xp_adv + xp_tech + xp_title
xp_total = sysd.get("xp_total", 0)
if xp_spent != xp_total:
    sys.exit("xp: tree accounts for %d of %d — reconcile before publishing "
             "(advancements %d, techniques %d, titles %d)"
             % (xp_spent, xp_total, xp_adv, xp_tech, xp_title))

# 4. Derived stats follow from the rings.
d = SHEET["derived"]
for key, want in [("endurance", (rings["earth"] + rings["fire"]) * 2),
                  ("composure", (rings["earth"] + rings["water"]) * 2),
                  ("focus", rings["fire"] + rings["air"]),
                  ("vigilance", -(-(rings["air"] + rings["water"]) // 2))]:
    if d[key] != want:
        sys.exit("derived %s: export says %d, rings give %d" % (key, d[key], want))

# 5. A title with no ability name is a failed corpus lookup, not a title.
for t in titles:
    if not t["ability"] or not t["abilityText"]:
        sys.exit("title %r: ability lookup failed (%r)" % (t["name"], t["ability"]))

blob = json.dumps(SHEET, indent=2, ensure_ascii=False)
if "</script" in blob:
    sys.exit("sheet data would close the script tag")

# The page frame is taken from Setsuna's sheet so all three stay identical but
# for their data — same engine, same stylesheet, same bar.
page = open(TEMPLATE, encoding="utf-8").read()
page = page.replace("Doji Setsuna — Character Sheet", "Asahina Jūjirō — Character Sheet")
page = page.replace('<a href="../character/setsuna.html">&lsaquo; Bio</a>',
                    '<a href="../character/jujiro.html">&lsaquo; Bio</a>')
page = re.sub(r'(<script id="sheet-data" type="application/json">\n).*?(\n</script>)',
              lambda m: m.group(1) + blob + m.group(2), page, flags=re.S)
page = page.replace("Generated by build/build_sheet.py in ~/Working/doji-setsuna — edit that, not this.",
                    "Generated by scripts/build_jujiro_sheet.py — edit that, not this.")
open(OUT, "w", encoding="utf-8").write(page)

print("wrote %s" % OUT)
print("  techniques    %d  (%d with a roller hook)"
      % (len(techniques), sum(1 for t in techniques if t.get("activation"))))
print("  peculiarities %d" % len(peculiarities))
print("  gear          %d" % len(gear_list))
print("  titles %d  bonds %d" % (len(titles), len(SHEET["bonds"])))
print("  skills ranked %d" % len(flat_skills))
print("  xp %d/%d spent — advancements %d, techniques %d, title %d"
      % (xp_spent, xp_total, xp_adv, xp_tech, xp_title))
if FREE_TECH:
    print("  free at chargen: %s%s"
          % (", ".join(sorted(FREE_TECH)),
             " (export charged %d XP for these — discounted)" % xp_free if xp_free else ""))
