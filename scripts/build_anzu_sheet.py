#!/usr/bin/env python3
"""
build_anzu_sheet.py — generate play/anzu.html, the playable L5R5e sheet for
Shinjō Anzu.

Anzu is Shinjō Harunobu's older sister: a Shinjō raised into the Iuchi Meishōdō
Master school, an Artisan rather than a Shugenja, who binds spirits into objects
rather than calling on them. She is not a campaign PC and does not appear in the
chronicle; this sheet exists so the owner can push the build around.

**She is still mid-character-creation**, and that is what makes this script
different from Harunobu's and Jūjirō's. Her Foundry actor has nothing applied —
every ring is 1, every skill 0, honour/glory/status 0, `items` empty — because
the twenty-questions wizard has not been committed to the sheet yet. So the
numbers here are *derived from the chargen record* rather than read off the
live fields, and the script says so on every run.

The moment the wizard is applied in Foundry, the live values take over on their
own: each derived block below prefers the export whenever the export is not
still at its blank default. Re-export over the pinned file and re-run.

  FOUNDRY  sources/foundry/fvtt-Actor-shinjo-anzu.json
  CORPUS   ~/Working/Titterpig DSL/titterpig-dsl-l5r5e/0.4/*.ttrpg

    python3 scripts/build_anzu_sheet.py
"""

import glob
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FOUNDRY = os.path.join(ROOT, "sources", "foundry", "fvtt-Actor-shinjo-anzu.json")
CHARGEN = os.path.join(ROOT, "sources", "foundry", "fvtt-Actor-shinjo-anzu-chargen.json")
OUT = os.path.join(ROOT, "play", "anzu.html")
HORSE = os.path.join(ROOT, "sources", "foundry", "fvtt-Actor-kurige.json")
TEMPLATE = os.path.join(ROOT, "play", "setsuna.html")
CORPUS_DIR = os.path.expanduser("~/Working/Titterpig DSL/titterpig-dsl-l5r5e/0.4")

RINGS = ("air", "earth", "fire", "water", "void")


def house(s):
    """The site's spelling of the Unicorn family, applied to authored text only.

    Foundry and the l5r5e books both write Shinjo; this site standardises on
    Shinjō. Never run this over technique, item or peculiarity descriptions —
    those are reproduced exactly as printed.
    """
    return s.replace("Shinjo", "Shinjō")


# ---------------------------------------------------------------- extraction
PUA = {"": "(op)"}


def plain(markup):
    if not markup:
        return ""
    for bad, good in PUA.items():
        markup = markup.replace(bad, good)
    s = re.sub(r"<br\s*/?>", "\n", markup)
    s = re.sub(r"</p>|</div>|</h[1-6]>|</tr>", "\n\n", s)
    s = re.sub(r"<li[^>]*>", "• ", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s)
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r" *\n *", "\n", s)
    return re.sub(r"\n{3,}", "\n\n", s).strip()


_CORPUS = None


def corpus_text():
    global _CORPUS
    if _CORPUS is None:
        _CORPUS = "\n".join(open(p, encoding="utf-8").read()
                            for p in sorted(glob.glob(os.path.join(CORPUS_DIR, "*.ttrpg"))))
    return _CORPUS


def unesc(s):
    s = s.replace('\\"', '"').replace("\\\\", "\\")
    return re.sub(r'\^"([^"]*)"', r"\1", s)


def _namepat(name):
    """Match a corpus name with either apostrophe. Foundry and the books disagree."""
    return "['’]".join(re.escape(p) for p in re.split(r"['’]", name))


def corpus_block(name):
    """Body of the DEF for `name`, preferring the one that carries rules text."""
    src = corpus_text()
    best, best_score = "", (-1, -1)
    for m in re.finditer(r'\^"' + _namepat(name) + r'" DEF \{', src):
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
        score = (sum(k in body for k in ("ACTIVATION", "EFFECTS", "EFFECT")), len(body))
        if score > best_score:
            best, best_score = body, score
    return best


def corpus_strings(body, key):
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
    m = re.search(r'\^"' + re.escape(key) + r'" (?:STRING "((?:[^"\\]|\\.)*)"|INTEGER (-?\d+))', body)
    if not m:
        return ""
    return unesc(m.group(1)) if m.group(1) is not None else m.group(2)


def rules_text(name):
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


# ------------------------------------------------------------ authored bridge
# The chargen wizard stores its technique and equipment picks as bare compendium
# IDs from the owner's own module, and the actor's `items` array is still empty,
# so there is nothing on the export to read names off. These are transcribed
# from the character-creation screen and are used ONLY while `items` is empty —
# the moment the wizard is applied, the real items win and this list is ignored.
CHARGEN_TECHNIQUES = [
    ("The Way of Names", "school_ability", "void"),
    ("Jurōjin's Balm", "invocation", "earth"),
    ("The Rushing Wave", "invocation", "water"),
    ("Commune with the Spirits", "ritual", "void"),
    ("Ancestry Unearthed", "shuji", "earth"),
]
CHARGEN_OUTFIT = ["Ceremonial Clothes", "Traveling Clothes", "Wakizashi",
                  "Horsebow", "Calligraphy Set", "Traveling Pack"]

TECH_TAGS = {"school_ability": "School Ability", "invocation": "Invocation",
             "ritual": "Ritual", "shuji": "Shūji", "inversion": "Inversion"}
PECULIARITY_TAGS = {"distinction": "Distinction", "passion": "Passion",
                    "adversity": "Adversity", "anxiety": "Anxiety"}

# Two dice each, per the core rules.
ADV = {"kind": "advantage", "max": 2}
DIS = {"kind": "disadvantage", "max": 2, "successOnly": True, "mustMax": True}
PECULIARITY_HOOKS = {
    "Famously Reliable": {"reroll": dict(ADV, approach="earth")},
    "Skilled Midwife": {"reroll": dict(ADV, approach="fire")},
    "Hot Pot": {"strife": -3},
    "Encompassing Duty": {"reroll": dict(DIS, approach="earth")},
    "Conspiracy": {"strife": 3},
}

# Roller hooks, each transcribed from the corpus ACTIVATION quoted above it and
# cross-checked against it by the audit below.
#
# Ancestry Unearthed is deliberately absent: it is an (op) spend on a Scholar or
# Social (Earth) check she is already making, not an action of its own.
ACTIVATION = {
    # "As a Support action, make a TN 1 Theology (Earth) check targeting one
    #  character at range 0-1."
    "Jurōjin's Balm": {"actionType": "Support action", "punct": ",", "tn": 1,
                       "skill": "theology", "ring": "earth"},
    # "As a Movement action, make a TN 2 Theology (Water) check targeting one
    #  character at range 0-1. Must have a large source of water nearby."
    "The Rushing Wave": {"actionType": "Movement action", "punct": ",", "tn": 2,
                         "skill": "theology", "ring": "water"},
    # "As a downtime activity or Support action, make a TN 1 Theology check
    #  using Air, Earth, Fire, Water, or Void…" — the ring is her choice; the
    #  button opens on Void and the card states the freedom.
    "Commune with the Spirits": {"actionType": "Downtime or Support", "punct": ",", "tn": 1,
                                 "skill": "theology", "ring": "void"},
    # "Once per session, immediately after an action of great consequence, TN 2
    #  Theology (Void), target that character at range 0-3." An Inversion, which
    #  her school does not teach — it came with the heritage.
    "Sight beyond Existence": {"actionType": "After a consequential action", "punct": ",",
                               "tn": 2, "skill": "theology", "ring": "void"},

    # --- bought on the way to Rank 4 -------------------------------------
    # "As a Support action, make a TN 2 Theology (Water) check to spread one
    #  chosen persistent invocation effect across targets equal to your Water
    #  Ring at range 0-1."
    "Sympathetic Energies": {"actionType": "Support action", "punct": ",", "tn": 2,
                             "skill": "theology", "ring": "water"},
    # "As a downtime activity, make a TN 3 Theology (Void) check targeting up to
    #  five characters to remove spiritual contaminants…"
    "Cleansing Rite": {"actionType": "Downtime", "punct": ",", "tn": 3,
                       "skill": "theology", "ring": "void"},
    # "As a Movement action, make a TN 5 Theology (Water) check targeting
    #  yourself and characters up to your Water Ring at range 1-4."
    "Hands of the Tides": {"actionType": "Movement action", "punct": ",", "tn": 5,
                           "skill": "theology", "ring": "water"},
    # "As a Support action, make a TN 2 Theology (Earth) check targeting
    #  characters up to your Earth Ring at range 0-2."
    "Courage of Seven Thunders": {"actionType": "Support action", "punct": ",", "tn": 2,
                                  "skill": "theology", "ring": "earth"},
    # "As a Support action, make a TN 6 Theology (Earth) check targeting one
    #  position that includes dirt, clay or stone at range 0-3."
    "Rise, Earth": {"actionType": "Support action", "punct": ",", "tn": 6,
                    "skill": "theology", "ring": "earth"},

    # Dazzling Performance is deliberately absent: it is a (fire)(op) spend on an
    # Artisan, Games or Performance (Fire) check she is already making.
}

USES = {"Sight beyond Existence": {"max": 1, "per": "Session"}}

# Provenance notes. Sight beyond Existence is not something Anzu learned: it is a
# meishōdō talisman she carries, from the Spirit Companion heritage (Children of
# the Five Winds) — "Ancestor made an agreement with a spirit… Know one
# additional meishōdō talisman (roll d10 for ring… 9-10 Void). Select rank 1
# invocation. You can perform that invocation even if it is not normally allowed
# by your school."
#
# The table sends a tenth of its rolls to a Void invocation, and the game has
# none — Air 18, Earth 18, Fire 16, Water 16, Void 0 across the whole corpus — so
# the owner substituted a rank 1 Void inversion, which is the nearest legal
# object. That is why an Inversion sits on the sheet of a school that forbids
# them.
#
# Note also that the talisman does NOT count against the number of meishōdō she
# can sustain under The Way of Names (one, at school rank 1) — she did not bind
# it, an ancestor did. The corpus's conversion of the Spirit Companion entry is
# truncated and stops before that clause; the printed book carries it. Do not
# "correct" this back from the corpus text.
PROVENANCE = {
    "Sight beyond Existence":
        "A meishōdō talisman, not a learned technique — the spirit an ancestor "
        "bargained with, and incredibly rare. Held under the Spirit Companion "
        "heritage, which lets her perform it though her school does not teach "
        "inversions. It does not count against the meishōdō she can sustain "
        "under The Way of Names.",
}

WEAPON_KEYS = ["Category", "Skill", "Range", "Base Damage", "Deadliness", "Rarity", "Price"]


# Kurige — her Shinjo Courser, a real Foundry NPC export rather than a
# transcription. Same companion-card shape as Harunobu's Khar Baatar.
#
# One wrinkle inherited from the same place his was: the actor was built by
# duplicating a Rokugani Pony, so its `description` still reads "There were
# horses in Rokugan before the Unicorn Clan returned with their foreign-bred
# steeds…" — which is the pony's text, not a courser's. The breed line below is
# the corpus's own Shinjo Courser entry, so the card describes the horse it
# actually is; nothing from the export is edited.
horse = json.load(open(HORSE, encoding="utf-8"))
hs = horse["system"]
_hbody = corpus_block("Shinjo Courser")
COMPANION = {
    "name": horse["name"],
    "kind": "Shinjō Courser · mount",
    "threat": {"combat": hs["conflict_rank"]["martial"],
               "intrigue": hs["conflict_rank"]["social"]},
    "demeanor": hs.get("attitude", ""),
    "rings": {r: hs["rings"][r] for r in RINGS},
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
# The card renders only the keys above plus `note`, so anything else that
# matters in play goes in the note rather than in a key the engine would drop.
_note = [corpus_prop(_hbody, "Description")]
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


def build(actor):
    """Assemble one SHEET dict from one Foundry export.

    Called twice: once for the live sheet and once for the character-creation
    snapshot that feeds the version selector. Everything it reads comes from the
    actor passed in, so the two never share state.
    """
    notes = []
    sysd = actor["system"]
    items = actor["items"]
    tq = sysd["twenty_questions"]
    notes = []
    
    
    # ------------------------------------------------------- derive from chargen
    def q(step, key, default=None):
        return tq.get(step, {}).get(key, default)
    
    
    def derived_rings():
        """Base 1 in every ring, plus each chargen step's increase.
    
        Steps 1, 2 and 4 grant one ring each; step 3 (the school) grants two. The
        wizard records the chosen element per step, so the whole spread is
        reconstructable without the sheet having been applied.
        """
        r = {k: 1 for k in RINGS}
        for step, keys in (("step1", ("ring",)), ("step2", ("ring",)),
                           ("step3", ("ring1", "ring2")), ("step4", ("ring",))):
            for k in keys:
                v = (q(step, k) or "").lower()
                if v in r:
                    r[v] += 1
        return r
    
    
    def derived_skills():
        """Every skill rank the chargen record grants, summed by name."""
        s = {}
        picks = [("step1", "skill"), ("step2", "skill1"), ("step2", "skill2"),
                 ("step3", "skill1"), ("step3", "skill2"), ("step3", "skill3"),
                 ("step3", "skill4"), ("step3", "skill5"),
                 ("step7", "skill"), ("step8", "skill"), ("step13", "skill"),
                 ("step17", "skill"), ("step18", "skill")]
        for step, key in picks:
            v = (q(step, key) or "").strip().lower()
            if v and v != "none":
                s[v] = s.get(v, 0) + 1
        return s
    
    
    def derived_social():
        return {
            "honor": int(q("step3", "social_honor") or 0) + int(q("step8", "social_add_honor") or 0)
                     + int(q("step18", "heritage_add_honor") or 0),
            "glory": int(q("step2", "social_glory") or 0) + int(q("step7", "social_add_glory") or 0)
                     + int(q("step18", "heritage_add_glory") or 0),
            "status": int(q("step1", "social_status") or 0)
                      + int(q("step18", "heritage_add_status") or 0),
        }
    
    
    live_rings = sysd["rings"]
    live_skills = {k: v for grp in sysd["skills"].values() for k, v in grp.items() if v}
    live_social = {k: sysd["social"][k] for k in ("honor", "glory", "status")}
    
    # A freshly generated actor sits at 1 in every ring and 0 everywhere else. That
    # is distinguishable from any real character, so it is a safe test for "the
    # wizard has not been applied yet".
    UNAPPLIED = all(v == 1 for v in live_rings.values()) and not live_skills
    
    if UNAPPLIED:
        rings, skills, social = derived_rings(), derived_skills(), derived_social()
        notes.append("live sheet is blank — rings, skills and standing derived from "
                     "the twenty-questions record")
    else:
        rings, skills, social = live_rings, live_skills, live_social
    
    derived = {"endurance": (rings["earth"] + rings["fire"]) * 2,
               "composure": (rings["earth"] + rings["water"]) * 2,
               "focus": rings["fire"] + rings["air"],
               "vigilance": -(-(rings["air"] + rings["water"]) // 2)}
    if not UNAPPLIED:
        for k, want in derived.items():
            if sysd.get(k) != want:
                sys.exit("derived %s: export says %s, rings give %d" % (k, sysd.get(k), want))
    
    
    
    
    def school_ability_text(school, name):
        m = re.search(r'SCHOOL_ABILITY "' + _namepat(name) + r'" \{(.*?)\n\s*\}',
                      corpus_block(school) or corpus_text(), re.S)
        return "\n\n".join(unesc(x) for x in re.findall(r'"((?:[^"\\]|\\.)*)"', m.group(1))) if m else ""
    
    
    SCHOOL = re.sub(r"\s+School$", "", sysd["identity"]["school"] or "") or "Iuchi Meishōdō Master"
    
    if items:
        techniques = [{"name": i["name"],
                       "tag": TECH_TAGS.get(i["system"].get("technique_type"), "Technique"),
                       "ring": i["system"].get("ring", ""),
                       "text": plain(i["system"].get("description", "")) or rules_text(i["name"])}
                      for i in items if i["type"] == "technique"]
        gear_names = [i["name"] for i in items if i["type"] in ("weapon", "armor", "item")]
        _pec_order = {"distinction": 0, "passion": 1, "adversity": 2, "anxiety": 3}
        peculiarities = []
        for i in sorted((x for x in items if x["type"] == "peculiarity"),
                        key=lambda x: (_pec_order[x["system"]["peculiarity_type"]], x["name"])):
            ps = i["system"]
            pec = {"name": i["name"], "tag": PECULIARITY_TAGS[ps["peculiarity_type"]],
                   "ring": ps.get("ring", ""),
                   "text": plain(ps.get("description", "")) or effect_text(i["name"])}
            pec.update(PECULIARITY_HOOKS.get(i["name"], {}))
            peculiarities.append(pec)
    else:
        notes.append("actor has no items — techniques and outfit taken from the "
                     "character-creation screen")
        peculiarities = []
        techniques = []
        for name, kind, ring in CHARGEN_TECHNIQUES:
            text = school_ability_text(SCHOOL, name) if kind == "school_ability" else rules_text(name)
            techniques.append({"name": name, "tag": TECH_TAGS[kind], "ring": ring, "text": text})
        gear_names = list(CHARGEN_OUTFIT)
    
    def akey(n):
        return n.replace("\u2019", "'")
    
    
    _ACT = {akey(k): v for k, v in ACTIVATION.items()}
    _USES = {akey(k): v for k, v in USES.items()}
    for t in techniques:
        if akey(t["name"]) in _ACT:
            t["activation"] = dict(_ACT[akey(t["name"])])
        if akey(t["name"]) in _USES:
            t["uses"] = dict(_USES[akey(t["name"])])
        if t["name"] in PROVENANCE:
            t["text"] = PROVENANCE[t["name"]] + "\n\n" + t["text"]
    
    gear = []
    for name in gear_names:
        g = {"name": name, "kind": "Item"}
        body = corpus_block(name)
        if body and corpus_prop(body, "Category"):
            g.update(kind="Weapon", category=corpus_prop(body, "Category"),
                     skill=corpus_prop(body, "Skill").replace("Martial Arts [Ranged]", "ranged")
                                                     .replace("Martial Arts [Melee]", "melee").lower(),
                     range=corpus_prop(body, "Range"),
                     damage=corpus_prop(body, "Base Damage"),
                     deadliness=corpus_prop(body, "Deadliness"))
            qs = corpus_strings(body, "Qualities")
            if qs:
                g["qualities"] = qs
        r = corpus_prop(body, "Rarity") if body else ""
        if r:
            g["rarity"] = int(r)
        gear.append(g)
    
    
    SHEET = {
        "id": "anzu",
        "name": "Shinjō Anzu",
        "clan": sysd["identity"]["clan"] or q("step1", "clan") or "Unicorn",
        # The family field is blank on the export, but step 2 records the Shinjo
        # entry item for item — Fire-or-Water, Sentiment +1, Survival +1, Glory 44,
        # Wealth 8 — and she is Harunobu's sister.
        # Authored character data takes the house spelling; the quoted book
        # text further down the sheet is reproduced exactly as printed.
        "family": house(sysd["identity"]["family"] or q("step2", "family") or "Shinjō"),
        "school": SCHOOL,
        "role": sysd["identity"]["roles"] or q("step3", "roles") or "Artisan",
        "rank": sysd["identity"]["school_rank"] or 1,
        "rings": {k: rings[k] for k in RINGS},
        "derived": derived,
        "trackers": {"strife": {"max": derived["composure"]},
                     "fatigue": {"max": derived["endurance"]},
                     "void": {"max": rings["void"], "start": rings["void"]}},
        "stance": sysd["stance"],
        "social": social,
        "skills": skills,
        "bushido": {"paramount": sysd["social"]["bushido_tenets"]["paramount"]
                                 or q("step8", "tenet_paramount") or "",
                    "less": sysd["social"]["bushido_tenets"]["less_significant"]
                            or q("step8", "tenet_less_significant") or ""},
        "ninjo": house(sysd["social"]["ninjo"] or q("step6", "social_ninjo") or ""),
        "giri": house(sysd["social"]["giri"] or q("step5", "social_giri") or ""),
        "money": ("%d koku" % int(q("step2", "wealth") or 0)) if not sysd.get("zeni")
                 else "%d zeni" % sysd["zeni"],
        "techniques": techniques,
        "peculiarities": peculiarities,
        "gear": gear,
        "titles": [],
        "bonds": [],
        "afflictions": [],
    }
    
    # The engine skips the portrait block when the key is absent, so the sheet stays
    # clean until the asset exists. Drop assets/anzu.webp in place and re-run.
    if os.path.exists(os.path.join(ROOT, "assets", "anzu.webp")):
        SHEET["portrait"] = "../assets/anzu.webp"
    
    # Standing notice: this sheet is a work in progress and should say so on its face.
    UNANSWERED = [n for n in range(4, 21)
                  if not any((tq.get("step%d" % n) or {}).get(k)
                             for k in ("stand_out", "social_giri", "social_ninjo",
                                       "clan_relations", "bushido", "success", "difficulty",
                                       "calms", "worries", "most_learn", "first_sight",
                                       "stress", "relations", "parents_pov", "heritage_name",
                                       "death", "firstname"))]
    # The standing notice always carries the "not a campaign character" line, since
    # this sheet sits on the chooser page beside three characters who are. The
    # creation-in-progress line joins it only while questions remain unanswered.
    SHEET["pendingLabel"] = "Not a campaign character"
    SHEET["pending"] = [
        "Shinjō Anzu does not appear in the chronicle and is not played. She is "
        "Shinjō Harunobu's older sister, and this sheet exists to try the build.",
    ]
    if UNANSWERED:
        SHEET["pendingLabel"] = "Character creation in progress"
        SHEET["pending"].insert(0,
            "<b>Questions %s are unanswered.</b> Rings, skills and standing below are "
            "derived from the answers so far."
            % ", ".join(str(n) for n in UNANSWERED))
    # Per-sheet audits: a silent corpus miss would ship an empty card, and a
    # sheet with no skills means the record could not be read at all.
    for t in techniques + peculiarities:
        if not t["text"]:
            sys.exit("no rules text for %r — corpus lookup failed" % t["name"])
    if sum(skills.values()) == 0:
        sys.exit("no skills derived — neither the export nor the chargen record is readable")

    return SHEET, notes


actor = json.load(open(FOUNDRY, encoding="utf-8"))
SHEET, notes = build(actor)
SHEET["companion"] = COMPANION

# The character-creation sheet is kept as a read-only snapshot in the version
# selector, which is what window.SHEET_HISTORY is for. Anzu is the first
# character on the site to use it: she went from Rank 1 and 0 XP to Rank 4 and
# 104 in one step, and the sheet she was built as is worth being able to look at.
# The snapshot carries no companion — it is a record of the sheet, not the ordu.
_cg, _ = build(json.load(open(CHARGEN, encoding="utf-8")))
_cg.pop("pending", None)
_cg.pop("pendingLabel", None)
HISTORY = [{"id": "chargen", "label": "Character creation", "date": "Rank 1 · 0 XP",
            "data": _cg}]
# --------------------------------------------------------------------- audits
for name, act in ACTIVATION.items():
    body = corpus_block(name)
    src_act = (corpus_strings(body, "ACTIVATION") or [""])[0]
    m = re.search(r"TN (\d+) ([A-Z][A-Za-z ]*?) \((Air|Earth|Fire|Water|Void)\)", src_act)
    if m:
        want = (int(m.group(1)), m.group(2).strip().lower(), m.group(3).lower())
        got = (act.get("tn"), act.get("skill"), act.get("ring"))
        if want != got:
            sys.exit("activation %s: %r but corpus says %r" % (name, got, want))

blob = json.dumps(SHEET, indent=2, ensure_ascii=False)
if "</script" in blob:
    sys.exit("sheet data would close the script tag")

page = open(TEMPLATE, encoding="utf-8").read()
page = page.replace("Doji Setsuna — Character Sheet", "Shinjō Anzu — Character Sheet")
page = page.replace('<a href="../character/setsuna.html">&lsaquo; Bio</a>',
                    '<a href="../character/anzu.html">&lsaquo; Bio</a>')
page = re.sub(r'(<script id="sheet-data" type="application/json">\n).*?(\n</script>)',
              lambda m: m.group(1) + blob + m.group(2), page, flags=re.S)
page = page.replace("Generated by build/build_sheet.py in ~/Working/doji-setsuna — edit that, not this.",
                    "Generated by scripts/build_anzu_sheet.py — edit that, not this.")
hblob = json.dumps(HISTORY, indent=2, ensure_ascii=False)
if "</script" in hblob:
    sys.exit("history data would close the script tag")
page = page.replace("<script>window.SHEET_HISTORY = window.SHEET_HISTORY || [];</script>",
                    "<script>window.SHEET_HISTORY = " + hblob + ";</script>")
open(OUT, "w", encoding="utf-8").write(page)

print("wrote %s" % OUT)
for n in notes:
    print("  note: %s" % n)
print("  rank    %s  ·  xp %s" % (SHEET["rank"], actor["system"]["xp_total"]))
print("  rings   %s" % "  ".join("%s %d" % (k.title(), SHEET["rings"][k]) for k in RINGS))
print("  derived endurance %(endurance)d  composure %(composure)d  focus %(focus)d  "
      "vigilance %(vigilance)d" % SHEET["derived"])
print("  social  honour %(honor)d  glory %(glory)d  status %(status)d" % SHEET["social"])
print("  skills  %s" % ", ".join("%s %d" % (k.title(), v)
                                 for k, v in sorted(SHEET["skills"].items())))
print("  techniques %d (%d with a roller hook)  gear %d  peculiarities %d"
      % (len(SHEET["techniques"]),
         sum(1 for t in SHEET["techniques"] if t.get("activation")),
         len(SHEET["gear"]), len(SHEET["peculiarities"])))
print("  companion %s (%s)" % (COMPANION["name"], COMPANION["kind"]))
for h in HISTORY:
    print("  snapshot  %-22s rank %s  %d techniques  %d skills"
          % (h["label"], h["data"]["rank"], len(h["data"]["techniques"]), len(h["data"]["skills"])))
