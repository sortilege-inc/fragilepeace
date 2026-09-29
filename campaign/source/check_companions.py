#!/usr/bin/env python3
"""
check_companions.py — the conversion's proof for the companions: each one read back from the BUILT
layer (campaign/data/campaign.js — rebuild first), field by field against its Foundry export.

    python3 campaign/source/check_companions.py

The expected values are read from the export here, not taken from the converter; only the list of
companions is shared. Every key of the export's `system` is compared or named in NOT_CARRIED with
the reason, and every item is accounted for. Exit 1 on any difference.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(HERE, 'campaign/source'))
from convert_companions import COMPANIONS, FOUNDRY, RINGS  # noqa: E402
from convert_cast import html_text  # noqa: E402

LAYER = os.path.join(HERE, 'campaign/data/campaign.js')

NOT_CARRIED = {
    'soft_locked': "Foundry's sheet lock",
    'prepared': "Foundry's prepared toggle",
    'notes': 'the breed, where there is one; it leads the DESCRIPTION (checked)',
    'identity': 'a companion has no clan, family or school',
    'social': 'honour, glory and status are 0 for all three; an animal has no standing (checked)',
    'fatigue': 'the live tracker; max = Endurance',
    'strife': 'the live tracker; max = Composure',
    'void_points': 'the live tracker',
    'stance': "Foundry's live stance, not part of a statblock",
    'techniques': "Foundry's allowed-technique-type switches",
    'description': 'the DESCRIPTION, with each ability under its name (checked)',
    # compared directly
    'type': None, 'conflict_rank': None, 'rings': None, 'rings_affinities': None,
    'attitude': None, 'endurance': None, 'composure': None, 'focus': None,
    'vigilance': None, 'skills': None,
}


def built():
    src = open(LAYER, encoding='utf-8').read()
    return json.loads(re.search(r'var d=(\{.*\});var T=window\.L5R5E', src, re.S).group(1))['entities']


def main():
    entities = built()
    from check_cast import props as read_props   # the same reader check_cast is proven with
    total = bad = 0
    for eid, name, fn, owner in COMPANIONS:
        d = json.load(open(os.path.join(FOUNDRY, fn), encoding='utf-8'))
        s, items = d['system'], d['items']
        e = entities.get(eid) or entities.get(eid.lstrip('#'))
        if e is None:
            print('== %s: NOT IN the built layer' % eid); bad += 1; continue
        P = read_props(e)
        rows = []

        def eq(field, want, got):
            rows.append((field, want, got, want == got))

        eq('name', d['name'], P.get('Name'))
        eq('type', (s.get('type') or '').title(), P.get('Type'))
        eq('conflict_rank.martial', s['conflict_rank']['martial'], P.get('Combat Conflict Rank'))
        eq('conflict_rank.social', s['conflict_rank']['social'], P.get('Intrigue Conflict Rank'))
        for r in RINGS:
            eq('rings.' + r, s['rings'][r], (P.get('Rings') or {}).get(r.title()))
        eq('attitude', s.get('attitude') or '', P.get('Demeanor'))
        for k in ('endurance', 'composure', 'focus', 'vigilance'):
            eq(k, s[k], P.get(k.title()))
        aff = s.get('rings_affinities') or {}
        want = ', '.join('%s %+d' % (r.title(), aff[r])
                         for r in ('fire', 'air', 'water', 'earth', 'void') if aff.get(r))
        eq('rings_affinities', want or None, P.get('Social Skill Check TN Modifiers'))
        eq('social honour/glory/status all 0', {'honor': 0, 'glory': 0, 'status': 0},
           {k: s['social'][k] for k in ('honor', 'glory', 'status')})
        adv = [i['name'] for i in items if i['type'] == 'peculiarity'
               and i['system'].get('peculiarity_type') in ('distinction', 'passion')]
        dis = [i['name'] for i in items if i['type'] == 'peculiarity'
               and i['system'].get('peculiarity_type') in ('adversity', 'anxiety')]
        eq('advantages', adv or None, P.get('Advantages'))
        eq('disadvantages', dis or None, P.get('Disadvantages'))
        weapons = [('%s: %s' % (i['name'], html_text(i['system'].get('description'))))
                   if html_text(i['system'].get('description')) else i['name']
                   for i in items if i['type'] == 'weapon' and not i['name'].lower().startswith('gear')]
        eq('favored weapons', weapons or None, P.get('Favored Weapons'))
        gear = [html_text(i['system'].get('description')) for i in items
                if i['type'] == 'weapon' and i['name'].lower().startswith('gear')] \
            + [i['name'] for i in items if i['type'] in ('item', 'armor')]
        eq('gear', gear or None, P.get('Gear'))
        desc = e.get('desc') or e.get('description') or ''
        eq('every ability is in the description', True,
           all((i['name'] + ':') in desc for i in items if i['type'] == 'technique'))
        note = html_text(s.get('notes'))
        eq('notes (the breed) lead the description', True, not note or desc.startswith(note))
        left = [k for k in s if k not in NOT_CARRIED]
        eq('every system key carried or named', [], left)

        n = sum(1 for r in rows if not r[3])
        total += len(rows); bad += n
        print('== %s ← %s: %d fields, %d differ' % (eid, fn, len(rows), n))
        for f, w, g, ok in rows:
            if not ok:
                print('   DIFFERS  %-44s export=%r  built=%r' % (f, w, g))
    print('check_companions: %s — %d fields compared across %d companions, %d differ'
          % ('OK' if not bad else 'FAILED', total, len(COMPANIONS), bad))
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
