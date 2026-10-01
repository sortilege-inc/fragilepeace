#!/usr/bin/env python3
"""
convert_companions.py — one-way conversion of the cast's companions into the campaign's DSL layer,
as instances of the corpus's ^"NPC".

    python3 campaign/source/convert_companions.py

The characters are instances of ACTOR "Samurai" (convert_cast.py). Their companions are not
characters: Foundry exports them as `npc` actors of type minion or adversary, and the corpus's own
statblocks for such things extend ^"NPC" with a fixed, small set of properties. This writes them in
exactly that set — the one a survey of the corpus's 149 NPC blocks gives — and nothing else:

    Type · Combat/Intrigue Conflict Rank · Rings · Demeanor · Social Skill Check TN Modifiers ·
    Endurance · Composure · Focus · Vigilance · Skills · Advantages · Disadvantages ·
    Favored Weapons · Gear

Honour, glory and status are on 117 of those 149 and are omitted here, because all three companions
record 0 for each: a horse has no standing, and printing three zeros would assert otherwise.

An NPC block has no property for a special ability — in the books that text is prose — so each
companion's abilities are written into its DESCRIPTION, under their own names, verbatim from the
export. ^"Companion Of" points at the character whose companion it is, which is the one thing the
retiring sheets showed that the corpus's own shape has nowhere to put.

Anything that does not resolve stops the conversion — nothing is dropped silently.
"""
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(HERE, 'campaign/source'))
from convert_cast import q, html_text, FOUNDRY  # noqa: E402

NPC = '#t4540de6f35155c46f41f0 ^"NPC"'
OUT = os.path.join(HERE, 'campaign/dsl/fragile-peace-companions.actor')

# (id, name, export, the character it belongs to as (id, name))
COMPANIONS = [
    ('#FPnpcKharBaatar', 'Khar Baatar', 'fvtt-Actor-khar-baatar.json',
     ('#FPpcShinjoHarunobu', 'Shinjō Harunobu')),
    ('#FPnpcKurige', 'Kurige', 'fvtt-Actor-kurige.json',
     ('#FPpcShinjoAnzu', 'Shinjō Anzu')),
    ('#FPnpcManifestWaterKami', "Tonbo Kuma's Manifest Water Kami",
     'fvtt-Actor-tonbo-kuma-manifest-water-kami.json', ('#FPpcTonboKuma', 'Tonbo Kuma')),
]

# A companion with no export: transcribed by the retiring build_morozane_sheet.py from the owner's
# Foundry screenshots (2026-08-12), and found missing by M4's check against the old sheet. Its numbers
# are that transcription's, as the old sheet showed them; its two abilities are named there and their
# text is the corpus's Hunting Cat's (core, p. 327), verbatim. Replace with a real export when one lands.
TRANSCRIBED = [
    ('#FPnpcShigoNoChinmoku', 'Shigo no Chinmoku', ('#FPpcMatsuMorozane', 'Matsu Morozane'), [
        '^"Name" STRING "Shigo no Chinmoku" FIXED',
        '^"Type" STRING "Adversary" FIXED',
        '^"Companion Of" #FPpcMatsuMorozane ^"Matsu Morozane"',
        '^"Combat Conflict Rank" INTEGER 6',
        '^"Intrigue Conflict Rank" INTEGER 1',
        '^"Rings" DEF { ^"Air" INTEGER 4 ^"Earth" INTEGER 2 ^"Fire" INTEGER 1 ^"Water" INTEGER 3 ^"Void" INTEGER 1 }',
        '^"Demeanor" STRING "Opportunistic"',
        '^"Social Skill Check TN Modifiers" STRING "Water +2, Fire -2"',
        '^"Endurance" INTEGER 7', '^"Composure" INTEGER 11', '^"Focus" INTEGER 5', '^"Vigilance" INTEGER 3',
        '^"Skills" LIST OF STRING ["Martial 3"]',
    ], "Lion · Animal Bond companion. Transcribed from the owner's Foundry screenshots (2026-08-12), not "
       "from an export. Verify before leaning on the numbers.\n\n"
       "Pouncing Predator: A hunting cat is a silhouette 3 creature. When performing an Attack action check "
       "against an unaware or Prone target, it may spend (op) as follows: (op): The target suffers the "
       "Disoriented condition.\n\n"
       "Savage Mauling: Disoriented targets cannot defend against damage dealt by a hunting cat."),
]
ADVANTAGE_TYPES, DISADVANTAGE_TYPES = {'distinction', 'passion'}, {'adversity', 'anxiety'}
RINGS = ('air', 'earth', 'fire', 'water', 'void')


def tn_mods(aff):
    """The corpus writes these as "Fire +2, Earth -2" — only the rings that modify anything."""
    parts = ['%s %+d' % (r.title(), aff[r]) for r in ('fire', 'air', 'water', 'earth', 'void')
             if aff.get(r)]
    return ', '.join(parts)


def fields(d, owner):
    s = d['system']
    items = d['items']
    P = ['^"Name" STRING %s FIXED' % q(d['name']),
         '^"Type" STRING %s FIXED' % q((s.get('type') or '').title()),
         '^"Companion Of" %s ^"%s"' % owner,
         '^"Combat Conflict Rank" INTEGER %d' % s['conflict_rank']['martial'],
         '^"Intrigue Conflict Rank" INTEGER %d' % s['conflict_rank']['social'],
         '^"Rings" DEF { %s }' % ' '.join(
             '^"%s" INTEGER %d' % (r.title(), s['rings'][r]) for r in RINGS),
         '^"Demeanor" STRING %s' % q(s.get('attitude') or '')]
    mods = tn_mods(s.get('rings_affinities') or {})
    if mods:
        P.append('^"Social Skill Check TN Modifiers" STRING %s' % q(mods))
    for k in ('endurance', 'composure', 'focus', 'vigilance'):
        P.append('^"%s" INTEGER %d' % (k.title(), s[k]))

    skills = []
    for grp, sk in (s.get('skills') or {}).items():
        if isinstance(sk, dict):
            best = max([v.get('rank') if isinstance(v, dict) else v for v in sk.values()] or [0])
            if best:
                skills.append('%s %d' % (grp.title(), best))
    if skills:
        P.append('^"Skills" LIST OF STRING [%s]' % ', '.join(q(x) for x in sorted(skills)))

    adv = [i['name'] for i in items if i['type'] == 'peculiarity'
           and i['system'].get('peculiarity_type') in ADVANTAGE_TYPES]
    dis = [i['name'] for i in items if i['type'] == 'peculiarity'
           and i['system'].get('peculiarity_type') in DISADVANTAGE_TYPES]
    for i in items:
        if i['type'] == 'peculiarity' and i['system'].get('peculiarity_type') not in (
                ADVANTAGE_TYPES | DISADVANTAGE_TYPES):
            raise SystemExit('%s: peculiarity %r of no known kind (%s)'
                             % (d['name'], i['name'], i['system'].get('peculiarity_type')))
    if adv:
        P.append('^"Advantages" LIST OF STRING [%s]' % ', '.join(q(x) for x in adv))
    if dis:
        P.append('^"Disadvantages" LIST OF STRING [%s]' % ', '.join(q(x) for x in dis))

    weapons, gear = [], []
    for i in items:
        if i['type'] != 'weapon':
            continue
        txt = html_text(i['system'].get('description'))
        # Foundry carries this actor's armour in a weapon item named "Gear (equipped)"
        (gear if i['name'].lower().startswith('gear') else weapons).append(
            txt if i['name'].lower().startswith('gear') else
            ('%s: %s' % (i['name'], txt) if txt else i['name']))
    gear += [i['name'] for i in items if i['type'] in ('item', 'armor')]
    if weapons:
        P.append('^"Favored Weapons" LIST OF STRING [%s]' % ', '.join(q(x) for x in weapons))
    if gear:
        P.append('^"Gear" LIST OF STRING [%s]' % ', '.join(q(x) for x in gear))

    # everything left must be accounted for, or the conversion has dropped something
    known = {'peculiarity', 'weapon', 'item', 'armor', 'technique'}
    left = [(i['type'], i['name']) for i in items if i['type'] not in known]
    if left:
        raise SystemExit('%s: items of no known type: %s' % (d['name'], left))
    return P


def description(d):
    """The actor's own description, then each ability under its name — all verbatim."""
    parts = []
    # Foundry's `notes` is where this campaign records a horse's breed — Khar Baatar's says
    # "Moto Charger.", which is not a Rokugani pony and matters. An NPC block has no field for it,
    # so it leads the description.
    note = html_text(d['system'].get('notes'))
    if note:
        parts.append(note)
    own = html_text(d['system'].get('description'))
    if own:
        parts.append(own)
    for i in d['items']:
        if i['type'] != 'technique':
            continue
        txt = html_text(i['system'].get('description'))
        if not txt:
            raise SystemExit('%s: ability %r has no text' % (d['name'], i['name']))
        parts.append('%s: %s' % (i['name'], txt))
    # a peculiarity with text of its own says what it does; one without is named in its list only
    for i in d['items']:
        if i['type'] == 'peculiarity':
            txt = html_text(i['system'].get('description'))
            if txt:
                parts.append('%s: %s' % (i['name'], txt))
    return '\n\n'.join(parts)


def main():
    blocks = []
    for eid, name, fn, owner in COMPANIONS:
        d = json.load(open(os.path.join(FOUNDRY, fn), encoding='utf-8'))
        if d['name'] != name:
            raise SystemExit('%s: the export is named %r' % (name, d['name']))
        P = fields(d, owner)
        desc = description(d)
        blocks.append('    # From foundry/%s.\n    %s ^"%s" DEF {\n        EXTENDS %s\n'
                      '        PROPERTIES {\n%s\n        }\n%s    }\n'
                      % (fn, eid, name, NPC,
                         '\n'.join('            ' + p for p in P),
                         ('        DESCRIPTION %s\n' % q(desc)) if desc else ''))
    for eid, name, owner, P, desc in TRANSCRIBED:
        blocks.append('    # Transcribed (no export): the retiring build_morozane_sheet.py.\n    %s ^"%s" DEF {\n        EXTENDS %s\n'
                      '        PROPERTIES {\n%s\n        }\n        DESCRIPTION %s\n    }\n'
                      % (eid, name, NPC, '\n'.join('            ' + p for p in P), q(desc.replace('\\n', '\n'))))
    body = ('EXTENSION "FragilePeace_Companions" {\n'
            '    NAME "The Fragile Peace — the companions"\n'
            '    VERSION "0.1.1"\n'
            '    SPEC_VERSION "0.5"\n'
            '    RELEASE_DATE "2026-09-29"\n'
            '    DEPENDS_ON "L5R5e_Core_Core"\n\n'
            '    # The horses and the summoned kami, as instances of the corpus\'s ^"NPC" — the shape\n'
            '    # its own 149 statblocks use. Converted from campaign/source/foundry/ (the Foundry\n'
            '    # exports, byte for byte) by campaign/source/convert_companions.py;\n'
            '    # campaign/source/check_companions.py reads the built layer back against them.\n\n'
            + '\n'.join(blocks) + '}\n')
    open(OUT, 'w', encoding='utf-8').write(body)
    print('wrote campaign/dsl/%s: %d companions' % (os.path.basename(OUT), len(blocks)))


if __name__ == '__main__':
    main()
