#!/usr/bin/env python3
"""
convert_cast.py — one-way conversion of the cast's Foundry sheets into the campaign's DSL layer, as
instances of the corpus's ACTOR "Samurai".

    python3 campaign/source/convert_cast.py

Adapted from The Bushi Oni's convert_pcs.py, which is the same job on the same system; what is this
campaign's own is SHEETS, the aliases and the layer header.

The record is campaign/source/foundry/: the Foundry `l5r5e` actor exports, copied BYTE FOR BYTE from
fragile-peace-support/archive/foundry-export/ and, for Setsuna, from her own generator's sources.
SHEETS below names which export is each character's current sheet and which are archived versions.

campaign/dsl/fragile-peace-cast.actor carries each sheet in every field the Samurai ACTOR declares, in the
corpus's pregen conventions (Portents' convert_norikage.py): skills as "Name N" strings, techniques,
advantages, disadvantages, titles and bonds as references to the corpus's own entities by hash
(corpus_index.py finds the root DEF of a name), gear as names. What the sheet adds: the stance, the XP
spent and its ledger, and — where Foundry's name for an item is not the corpus's (a specifier such as
"Dark Secret (In love with …)", a clan suffix such as "(Crab)") — the Foundry name verbatim in
^"As Recorded", so nothing the table wrote is lost. School abilities (and a title's ability) come with
the School (and the Title), as in Portents. An archived sheet is its own DEF, ^"Version Of" the current.
Two layers: the players' characters (SHEETS → campaign/dsl/) and the GM's (GM_SHEETS → campaign/dsl-gm/).

Anything that does not resolve stops the conversion — nothing is dropped silently.
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(HERE, 'campaign/source'))
from corpus_index import load, resolve  # noqa: E402
# The site's house corrections (owner rulings on names, and its orthography: "Shinjō"), applied to what
# the table wrote — family, ninjō, giri, description, notes — and never to a book's own names (a
# technique, the XP ledger's item names) or to Foundry's name for the actor, kept verbatim as a record.
# verify_site.py states the same rule for the old sheets: authored data the house way, quoted text exact.
from archivist import correct as house  # noqa: E402

SAMURAI = '#L5R003xY4zA6bC8dE0fG2hI ^"Samurai"'
TECH, ADV, DIS = '#L5R350fG9hI1jK3lM5nO7p ^"Technique"', '#L5R263hI5jK7lM9nO1pQ3r ^"Advantage"', '#L5R264sT6uV8wX0yZ2aB4c ^"Disadvantage"'
TITLE, BOND = '#L5R463nO5pQ7rS9tU1vW3x ^"Title"', '#L5R262wX4yZ6aB8cD0eF2g ^"Bond"'
FOUNDRY = os.path.join(HERE, 'campaign/source/foundry')

# (id, the name the character goes by, [(export, version label or None for the current sheet)])
# The players' characters — layer campaign/dsl/, book "The Bushi Oni".
SHEETS = [
    # The three who are at the table now, then the three who are playable and are not.
    ('#FPpcDojiSetsuna', 'Doji Setsuna', [('fvtt-Actor-doji-setsuna.json', None),
                                          ('fvtt-Actor-doji-setsuna-prev-2026-08-10.json', 'Foundry export · 10 Aug 2026')]),
    ('#FPpcBayushiMonban', 'Bayushi Monban', []),   # no export yet — see MISSING below
    ('#FPpcShinjoHarunobu', 'Shinjō Harunobu', [('fvtt-Actor-shinjo-harunobu.json', None)]),
    ('#FPpcTonboKuma', 'Tonbo Kuma', [('fvtt-Actor-tonbo-kuma.json', None)]),
    ('#FPpcAsahinaJujiro', 'Asahina Jūjirō', [('fvtt-Actor-asahina-jujiro.json', None)]),
    # Anzu's creation snapshot is a version of her, the way Taigen's December sheet is of his.
    ('#FPpcShinjoAnzu', 'Shinjō Anzu', [('fvtt-Actor-shinjo-anzu.json', None),
                                        ('fvtt-Actor-shinjo-anzu-chargen.json', 'At character creation')]),
    # Setsuna's ancestor, played through the Snow Plain flashback (sessions 10-16).
    ('#FPpcMatsuMorozane', 'Matsu Morozane', [('fvtt-Actor-matsu-morozane.json', None)]),
]
# Characters the campaign plays that no Foundry export in the archive covers. Named here rather than
# left to be noticed: the layer is the cast, and a silent omission is the failure this whole file
# exists to prevent.
MISSING = {'#FPpcBayushiMonban': 'Shiba Midori and Bayushi Monban are other players\' characters; '
                                 'no Foundry export of either is in this campaign\'s archive.'}
SHEETS = [x for x in SHEETS if x[2]]
# The GM's characters (owner, 2026-09-26: full sheets like the PCs, tracked apart) — the six pregens of
# 2025-10-27, a layer of their own, campaign/dsl-gm/, its own book "The Bushi Oni — GM characters".
# Foundry names them with their XP and title ("Hiruma Kaede 74 XP (Gunsō, Rank 3)"); the entity is
# named as the person and Foundry's name is kept verbatim in ^"Foundry Name".
GM_SHEETS = []   # this campaign keeps no separate GM layer: everything on the site is the table's
# (sheets, the .actor file, EXTENSION id, its NAME, what the file's header says)
LAYERS = [
    (SHEETS, 'campaign/dsl/fragile-peace-cast.actor', 'FragilePeace_Cast', 'The Fragile Peace — the cast', '0.1.1',
     'The cast: instances of the Samurai ACTOR in the corpus\'s pregen conventions.'),
]

# What the owner has ruled and no Foundry export carries yet. Applied on top of the export's own
# value, as the arithmetic rather than as a number, so it retires itself: when an export arrives
# already carrying the ruled value the build says so on stderr and the entry can be deleted, and an
# export carrying a third value stops the conversion rather than being quietly overwritten.
#
# This exists because the sheet it replaces had one. Harunobu's award lived only in the retiring
# builder, and converting the export without it would have dropped it silently — which is the whole
# failure this layer is supposed to make impossible.
OWNER_RULINGS = {
    ('#FPpcShinjoHarunobu', 'Glory'): {
        'before': 49, 'after': 55,
        'why': 'a major glory award for his conduct in the war, +6, awarded out of play at his '
               'capture (owner, 2026-09-29; campaign/CORRECTION-PASS.md)',
    },
    # Foundry's giri stops mid-sentence and holds no fuller copy; the owner supplied the ending, so
    # what is published is the export's own words finished, not rewritten. It lived only in the
    # retiring build_kuma_sheet.py (GIRI_COMPLETED) until M4's check against the old sheet found it.
    ('#FPpcTonboKuma', 'Giri'): {
        'before': "To represent the Dragon Clan's interests in ",
        'after': "To represent the Dragon Clan's interests in the City of the Rich Frog.",
        'why': 'the ending supplied by the owner, 2026-09-26 (build_kuma_sheet.py)',
    },
}

# Corrections to an export's own text, each with the evidence for it, applied as a replacement so that
# an export which already carries the corrected text passes through untouched.
CORRECTIONS = {
    # The export spells her horse two ways; its own notes and the owner's dossier both say Kogarashi
    # (the retiring doji-setsuna/build/build_sheet.py made the same fix).
    ('#FPpcDojiSetsuna', 'Ninjō'): {'replace': ('Kogorashi', 'Kogarashi'),
                                    'why': 'the horse is Kogarashi in the notes and the dossier'},
}


def ruled(pid, field, value):
    """The owner's value for a field, where they have ruled one (or a recorded correction applies);
    otherwise the export's."""
    c = CORRECTIONS.get((pid, field))
    if c:
        old, new = c['replace']
        if old in value:
            return value.replace(old, new)
        print('  CORRECTIONS (%s %s) found no %r — the export may be fixed; delete the entry'
              % (pid, field, old), file=sys.stderr)
        return value
    r = OWNER_RULINGS.get((pid, field))
    if not r:
        return value
    if value == r['before']:
        return r['after']
    if value == r['after']:
        print('  OWNER_RULINGS (%s %s) is no longer needed — the export carries %r itself'
              % (pid, field, r['after']), file=sys.stderr)
        return value
    raise Unresolved('%s %s is %r in the export, neither the pre-ruling %r nor the ruled %r: %s'
                     % (pid, field, value, r['before'], r['after'], r['why']))


# What the retiring play/ sheets showed that no Foundry export carries: each builder's own constants,
# verbatim, found by M4's check against the old sheets (campaign/source/check_sheets.py). Properties
# the Samurai ACTOR does not declare; the sheet lists them with the biography. The current sheet only.
#   Setsuna — from fragile-peace-support/doji-setsuna/build/build_sheet.py (the owner's dossier):
#   the standing Void wound, the register of her bushidō, her horse, and what is "in hand, unspent".
#   Anzu — from build_anzu_sheet.py: what the sheet is for.
FROM_THE_OLD_SHEETS = {
    '#FPpcDojiSetsuna': [
        ('Afflictions', ['Void Wound — severe, partially healed: Sustained during the termination. '
                         'Increases the TN of Void-stance and Void-skill checks rather than reducing pool '
                         'capacity. It has persisted across the whole arc of the campaign and does not clear '
                         'on a scene reset.']),
        ('Bushido Register', 'Rigid acquiescence'),
        ('Mounts', ['Kogarashi: A white Utaku steed with a silver mane and tail — lean, swift, always '
                    'poised. A wedding gift from the Shinjō family, and the one being to whom her warmth '
                    'flows unmediated. Her distinctive Utaku breeding marks Setsuna at distance to any '
                    'Unicorn who sees her.']),
        ('In Hand, Unspent', ['Two boons, owed by the Lion. Unspent and unspecified, taken in the tent at '
                              'session 53 when they were left choosing between giving ground and owing her.',
                              'Next Social skill check against Miya Satoshi: TN −4, to a minimum of TN 1. '
                              'Worth spending on a Social (Water) check so Shallow Waters can buy his ninjō '
                              'at two opportunities.']),
    ],
    '#FPpcShinjoAnzu': [
        ('Not a Campaign Character', 'Shinjō Anzu does not appear in the chronicle and is not played. She is '
                                     "Shinjō Harunobu's older sister, and this sheet exists to try the build."),
    ],
}


# Items Foundry files under the wrong type. The value is the entity that actually grants the
# ability; the sheet must be holding it for the item to be skipped as coming with it.
MISCLASSIFIED = {'Voice of Authority': 'Emerald Magistrate'}

MARTIAL = {'melee': 'Martial Arts [Melee]', 'ranged': 'Martial Arts [Ranged]', 'unarmed': 'Martial Arts [Unarmed]'}
# Foundry's name → the corpus's, where they differ by more than a clan suffix, a specifier or the apostrophe:
# a spelling, a case, a " Bond" suffix, or a table's fill-in of an entry the corpus prints as a template
ALIAS = {'Sword Saint': 'Sword-Saint', 'Lover': 'Lover Bond', 'Gunsō': 'Gunso',
         'Wanderers Fellowship': 'Wanderers Fellowship Bond', 'Protector and Ward': 'Protector and Ward Bond',
         'One Within the Void': 'One within the Void',
         'Paragon of Courage': 'Paragon of a Bushidō Tenet', 'Disdain for Compassion': 'Disdain for a Bushidō Tenet',
         'Support of Brotherhood of Shinsei': 'Support of [One Group]', 'Blackmail on Akodo Nobuhiko': 'Blackmail on [Name]',
         # This campaign's own. Each is the table's filling-in of an entry the corpus prints as a
         # template, so the reference is to the template and ^"As Recorded" keeps what was written.
         # "Scorn of Kakita is correct" — owner, 2026-09-26, over a Foundry rename to the bare template.
         'Scorn of Kakita': 'Scorn of [One Group]',
         'Paragon of Courtesy': 'Paragon of a Bushidō Tenet',
         # Emerald Empire p.249 prints the title as the bare "Advisor"; Foundry carries the
         # appointment in the name.
         'Personal Advisor to Imperial Envoy Miya Misato': 'Advisor',
         'Personal Advisor to Miya Misato': 'Advisor',
         # a capital the corpus does not use
         'Beware The Smallest Mouse': 'Beware the Smallest Mouse',
         'Ally: Miya Tetsua': 'Ally [Name]',
         }
# What ^"As Recorded" should say where the Foundry name itself is wrong. The site spells the
# governor Miya Tetsuya everywhere — chronicle, entity page, every session since 55 — and only this
# actor says Tetsua; recording the misspelling verbatim would publish it (campaign/CORRECTION-PASS.md,
# 2026-09-28, the same fix the retiring sheet carried).
AS_RECORDED_FIX = {'Ally: Miya Tetsua': 'Ally: Miya Tetsuya'}
# Foundry's school name (less " School" and a "[Clan]") → the corpus's
SCHOOL_ALIAS = {'Shoshuro Shadoweaver': 'Shosuro Shadowweaver',
                # Foundry drops the macrons the corpus prints.
                'Iuchi Meishodo Master': 'Iuchi Meishōdō Master'}
ADVANTAGE_TYPES, DISADVANTAGE_TYPES = {'distinction', 'passion'}, {'adversity', 'anxiety'}
COMES_WITH = {'school_ability', 'mastery_ability', 'title_ability'}
GEAR = {'weapon', 'armor', 'item'}


def q(s):
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n') + '"'


def corpus_name(name):
    """The corpus's name for a Foundry item name: apostrophe, then a trailing (Clan) / [spec] / ": spec" off."""
    n = name.replace('\u2019', "'").strip()
    if n in ALIAS:
        return ALIAS[n]
    base = re.sub(r'\s*(\([^)]*\)|\[[^\]]*\])$', '', n)
    base = base.split(':')[0].strip()
    return ALIAS.get(base, base)


def html_text(h):
    """Foundry's rich text as plain text: one line per paragraph (or <br>), tags off, entities decoded, empty lines dropped."""
    import html
    parts = re.split(r'</p>|<br\s*/?>', h or '')
    lines = [html.unescape(re.sub(r'<[^>]+>', '', x)).strip() for x in parts]
    return '\n'.join(x for x in lines if x)


def school_name(s):
    n = re.sub(r'\s+School$', '', re.sub(r'\s*\[[^\]]*\]$', '', s.strip()))
    return SCHOOL_ALIAS.get(n, n)


class Unresolved(Exception):
    pass


def ref(D, kind, name):
    n = corpus_name(name) if kind != 'raw' else name
    h, why = resolve(D, n)
    if not h:
        # a specifier the corpus spells in the name itself (e.g. "Ally [Name]", "Dark Secret (Void)")
        h2, _ = resolve(D, name.replace('\u2019', "'"))
        if h2:
            return h2, name.replace('\u2019', "'")
        raise Unresolved('%s: %s' % (name, why))
    return h, n


def fields(D, d, archived=False, pid=None):
    s = d['system']; idn = s['identity']; so = s['social']
    techs, adv, dis, titles, bonds, recorded, ledger, gear = [], [], [], [], [], [], [], []
    for it in d['items']:
        t, si, nm = it['type'], it['system'], it['name']
        used = si.get('xp_used') or 0
        if used:
            ledger.append('%d · %s · rank %s' % (used, nm, si.get('bought_at_rank')))
        if t == 'technique':
            if si.get('technique_type') in COMES_WITH:
                continue
            h, cn = ref(D, 'technique', nm); techs.append('%s ^"%s"' % (h, cn))
        elif t == 'peculiarity':
            h, cn = ref(D, 'peculiarity', nm)
            k = si.get('peculiarity_type')
            if k in ADVANTAGE_TYPES: adv.append('%s ^"%s"' % (h, cn))
            elif k in DISADVANTAGE_TYPES: dis.append('%s ^"%s"' % (h, cn))
            else: raise Unresolved('%s: a peculiarity of no known kind (%s)' % (nm, k))
        elif t == 'title':
            h, cn = ref(D, 'title', nm); titles.append('%s ^"%s"' % (h, cn))
            # the title's own As Recorded before its items', in the order the sheet holds them
            if cn != nm.replace('\u2019', "'"):
                recorded.append(AS_RECORDED_FIX.get(nm, nm))
                cn = nm.replace('\u2019', "'")
            # A technique bought through a title is the title's own item (`system.items`), not a
            # top-level one — the character has it all the same. Its XP is already in the title's
            # xp_used, so only the technique itself is taken; the title's advancements are skipped.
            subs = si.get('items') or []
            for sub in (subs.values() if isinstance(subs, dict) else subs):
                if sub.get('type') != 'technique' or (sub.get('system') or {}).get('technique_type') in COMES_WITH:
                    continue
                sh, scn = ref(D, 'technique', sub['name']); techs.append('%s ^"%s"' % (sh, scn))
                if scn != sub['name'].replace('\u2019', "'"):
                    recorded.append(AS_RECORDED_FIX.get(sub['name'], sub['name']))
        elif t == 'bond':
            # A bond is named for the person it is with — "Doji Setsuna", "Shinjō Harunobu" — and
            # the corpus entity is the KIND of bond, which Foundry keeps separately as
            # bond_type ("Wife (Lover)", "Husband (Lover)"). Resolve by the kind and let the
            # person's name be what ^"As Recorded" carries. Aliasing each spouse by name would
            # work today and quietly rewrite any future item that happens to share a character's
            # name.
            kind = re.sub(r'^.*\(([^)]*)\).*$', r'\1', si.get('bond_type') or '').strip() or (si.get('bond_type') or '')
            h, cn = ref(D, 'bond', nm if resolve(D, nm)[0] else '%s Bond' % kind)
            bonds.append('%s ^"%s"' % (h, cn))
        elif t in GEAR:
            gear.append(nm); continue
        elif t == 'advancement':
            continue
        elif t == 'signature_scroll':
            # Foundry's item type is wrong here (owner, 2026-09-29). Voice of Authority is not a
            # signature scroll: it is the TITLE_ABILITY of the corpus's Emerald Magistrate, word
            # for word. A title ability comes with its Title, as a school ability does with its
            # School, so it is skipped — but only once the sheet is shown to hold the title that
            # grants it, or a misfiled item could vanish off a character who never had it.
            grant = MISCLASSIFIED.get(nm)
            if not grant:
                raise Unresolved('%s: an item Foundry types %s, with no entry in MISCLASSIFIED'
                                 % (nm, t))
            if not any(i['type'] == 'title' and i['name'] == grant for i in d['items']):
                raise Unresolved('%s comes with the title %r, which this sheet does not hold'
                                 % (nm, grant))
            continue
        else:
            raise Unresolved('%s: an item of no known type (%s)' % (nm, t))
        if cn != nm.replace('\u2019', "'"):
            recorded.append(AS_RECORDED_FIX.get(nm, nm))
    sch = school_name(idn['school'])
    if not resolve(D, sch)[0]:
        raise Unresolved('school %s → %s: not in the corpus' % (idn['school'], sch))
    if re.sub(r'\s+School$', '', re.sub(r'\s*\[[^\]]*\]$', '', idn['school'].strip())) != sch:
        recorded.append(idn['school'])
    skills = []
    for grp in s['skills'].values():
        for k, v in grp.items():
            if v:
                skills.append('%s %d' % (MARTIAL.get(k, k.title()), v))
    # Older exports in this campaign's archive (Setsuna's, Morozane's) carry only `zeni` and no
    # `money` record at all; newer ones carry both. Absent is zero, and the line below adds the two
    # together, so neither shape loses a coin.
    m = {k: (v or 0) for k, v in (s.get('money') or {}).items()}
    money = [x for x in ('%d koku' % m.get('koku', 0), '%d bu' % m.get('bu', 0), '%d zeni' % (m.get('zeni', 0) + (s.get('zeni') or 0))) if not x.startswith('0 ')]
    r = s['rings']
    P = [
        '^"Name" STRING %s FIXED' % q(NAME),
    ] + (['^"Foundry Name" STRING %s' % q(d['name'])] if d['name'] != NAME else []) + [
        '^"Clan" STRING %s FIXED' % q(idn['clan']),
        '^"Family" STRING %s FIXED' % q(house(idn['family'])),
        '^"School" STRING %s' % q(sch),
        '^"School Rank" INTEGER %d' % idn['school_rank'],
        '^"Roles" LIST OF STRING [%s]' % ', '.join(q(x.strip()) for x in idn['roles'].split(',') if x.strip()),
        '^"Rings" DEF { ' + ' '.join('^"%s" INTEGER %d' % (k.title(), r[k]) for k in ('air', 'earth', 'fire', 'water', 'void')) + ' }',
        '^"Honor" INTEGER %d' % ruled(pid, 'Honor', so['honor']),
        '^"Glory" INTEGER %d' % ruled(pid, 'Glory', so['glory']),
        '^"Status" INTEGER %d' % ruled(pid, 'Status', so['status']),
        '^"Endurance" INTEGER %d' % s['endurance'], '^"Composure" INTEGER %d' % s['composure'],
        '^"Focus" INTEGER %d' % s['focus'], '^"Vigilance" INTEGER %d' % s['vigilance'],
        '^"Void Points" INTEGER %d' % s['void_points']['max'],
        '^"Ninjō" STRING %s' % q(house(ruled(pid, 'Ninjō', so['ninjo']))),
        '^"Giri" STRING %s' % q(house(ruled(pid, 'Giri', so['giri']))),
        '^"Skills" LIST OF STRING [%s]' % ', '.join(q(x) for x in skills),
        '^"Techniques" LIST OF %s [%s]' % (TECH, ', '.join(techs)),
        '^"Advantages" LIST OF %s [%s]' % (ADV, ', '.join(adv)),
        '^"Disadvantages" LIST OF %s [%s]' % (DIS, ', '.join(dis)),
    ]
    if titles: P.append('^"Titles" LIST OF %s [%s]' % (TITLE, ', '.join(titles)))
    if bonds: P.append('^"Bonds" LIST OF %s [%s]' % (BOND, ', '.join(bonds)))
    P += [
        '^"Equipment" LIST OF STRING [%s]' % ', '.join(q(x) for x in gear + money),
        '^"Bushido" DEF { ^"Paramount Tenet" STRING %s ^"Less Significant Tenet" STRING %s }' % (q(so['bushido_tenets']['paramount']), q(so['bushido_tenets']['less_significant'])),
        '^"Experience" INTEGER %d' % s['xp_total'],
        # what the sheet adds to the ACTOR's fields
        '^"Experience Spent" INTEGER %d' % sum((it['system'].get('xp_used') or 0) for it in d['items']),
    ]
    if ledger: P.append('^"Experience Ledger" LIST OF STRING [%s]' % ', '.join(q(x) for x in ledger))
    P.append('^"Stance" STRING %s' % q(s['stance'].title()))
    for key, label in (('description', 'Description'), ('notes', 'Notes')):
        if html_text(s[key]):
            P.append('^"%s" STRING %s' % (label, q(house(html_text(s[key])))))
    if archived:
        P += ['^"Strife" INTEGER %d' % s['strife']['value'], '^"Fatigue" INTEGER %d' % s['fatigue']['value']]
    if recorded: P.append('^"As Recorded" LIST OF STRING [%s]' % ', '.join(q(x) for x in recorded))
    if not archived:
        for k, v in FROM_THE_OLD_SHEETS.get(pid, []):
            P.append('^"%s" %s' % (k, ('LIST OF STRING [%s]' % ', '.join(q(x) for x in v)) if isinstance(v, list) else 'STRING ' + q(v)))
    return P


def block(h, name, P, comment):
    return '    # %s\n    %s ^"%s" DEF {\n        EXTENDS %s\n        PROPERTIES {\n%s\n        }\n    }\n' % (
        comment, h, name, SAMURAI, '\n'.join('            ' + p for p in P))


NAME = None


def main():
    global NAME
    D = load()
    only = sys.argv[1:]          # pilot: convert_pcs.py '#BOpcKitsukiHasumi'
    errors, wrote = [], []
    for sheets, out, ext, title, version, about in LAYERS:
        blocks = []
        for pid, name, versions in sheets:
            if only and pid not in only:
                continue
            NAME = name
            for f, label in versions:
                d = json.load(open(os.path.join(FOUNDRY, f), encoding='utf-8'))
                try:
                    if label is None:
                        blocks.append(block(pid, name, fields(D, d, pid=pid), 'The current sheet: foundry/%s.' % f))
                    else:
                        # This campaign's exports are not all named <name>.<date>.json — some carry
                        # the date in the stem (…-prev-2026-08-10.json) and some carry none at all
                        # (…-anzu-chargen.json, which is a state rather than a date). Take a date
                        # where the filename has one, and build the suffix from the label itself
                        # rather than assuming it splits on ' · '.
                        md = re.search(r'(\d{4}-\d{2}-\d{2})', f)
                        date = md.group(1) if md else ''
                        short = label.split(' · ')[1] if ' · ' in label else label
                        suffix = date.replace('-', '') or re.sub(r'[^A-Za-z0-9]', '', short)
                        P = ['^"Version Of" %s ^"%s"' % (pid, name), '^"Version Label" STRING %s' % q(label)]
                        if date:
                            P.append('^"Version Date" STRING %s' % q(date))
                        P += fields(D, d, archived=True, pid=pid)
                        blocks.append(block(pid + suffix, '%s (%s)' % (name, short), P, 'Archived: foundry/%s.' % f))
                except Unresolved as e:
                    errors.append('%s (%s): %s' % (name, f, e))
        if blocks:
            wrote.append((out, ext, title, version, about, blocks))
    if errors:
        print('\n'.join('UNRESOLVED ' + e for e in errors)); sys.exit(1)
    for out, ext, title, version, about, blocks in wrote:
        text = '''EXTENSION "%s" {
    NAME "%s"
    VERSION "%s"
    SPEC_VERSION "0.5"
    RELEASE_DATE "2026-09-26"
    DEPENDS_ON "L5R5e_Core_Core"

    # %s Converted from
    # campaign/source/foundry/ (the Foundry exports, byte for byte) by campaign/source/convert_pcs.py;
    # campaign/source/check_pcs.py reads the built layer back against them field by field.

%s}
''' % (ext, title, version, about, '\n'.join(blocks))
        path = os.path.join(HERE, out)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, 'w', encoding='utf-8').write(text)
        print('wrote %s: %d sheets' % (out, len(blocks)))


if __name__ == '__main__':
    main()
