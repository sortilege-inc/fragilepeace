#!/usr/bin/env python3
"""M4's gate (F2): every version of every character on the VTT sheet against the old sheet it
replaced — the retired play/<sheet>.html's embedded `sheet-data` (the current sheet) and
`SHEET_HISTORY` (archived versions), kept verbatim in campaign/source/old-sheets/ when play/ was
removed — read from the BUILT layer (campaign/data/campaign.js; rebuild first), field by field.

    python3 campaign/source/check_sheets.py            # exit 0 = every field matches or is accounted for

Numbers, names and lists are compared as values. The old sheet's prose-only facts (a bond's partner
and rank, an affliction, a title's own wording, the "pending" notes, a companion) have no field in
ACTOR Samurai; each must appear, as text, somewhere in the character's entity — or be listed in
ACCOUNTED with the reason it is not carried. A difference that is neither is a FAIL.
"""
import glob
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(HERE, 'campaign/source'))
from check_cast import built, props  # noqa: E402

OLD = os.path.join(HERE, 'campaign/source/old-sheets')
# old sheet file → the layer's entity; an archived version by its label
ENTITY = {'setsuna': '#FPpcDojiSetsuna', 'harunobu': '#FPpcShinjoHarunobu', 'kuma': '#FPpcTonboKuma',
          'jujiro': '#FPpcAsahinaJujiro', 'anzu': '#FPpcShinjoAnzu', 'morozane': '#FPpcMatsuMorozane'}
HISTORY = {('anzu', 'chargen'): '#FPpcShinjoAnzuAtcharactercreation'}
SKILL = {'melee': 'Martial Arts [Melee]', 'ranged': 'Martial Arts [Ranged]', 'unarmed': 'Martial Arts [Unarmed]'}
COMES_WITH = {'School Ability', 'Mastery Ability', 'Title Ability'}   # carried by the School / Title
GOOD = {'Distinction', 'Passion'}
# a difference between the old sheet and the layer that is the layer being right: (sheet, field) → why.
# Each was traced to its source (2026-10-01); nothing here is a fact the layer drops.
CORPUS_SCHOOL = "the corpus's School entity, as check_cast proves; Foundry's own name is kept in As Recorded where it differs"
ACCOUNTED = {
    ('anzu', 'School'): CORPUS_SCHOOL, ('harunobu', 'School'): CORPUS_SCHOOL, ('jujiro', 'School'): CORPUS_SCHOOL,
    ('kuma', 'School'): CORPUS_SCHOOL, ('morozane', 'School'): CORPUS_SCHOOL, ('setsuna', 'School'): CORPUS_SCHOOL,
    ('jujiro', 'Ninjō'): "the live social.ninjo (\"find him a match\"); the retiring builder read the frozen twenty_questions answer (\"them\")",
    ('morozane', 'Advantages'): 'Ferocity is an Anxiety in the corpus (core-anxieties) and in Foundry; the retiring builder tagged it a Distinction',
    ('morozane', 'Disadvantages'): 'Ferocity is an Anxiety in the corpus (core-anxieties) and in Foundry; the retiring builder tagged it a Distinction',
    ('morozane', 'Titles'): 'Foundry holds the titles Gunso and Renowned Warrior; the retiring sheet showed them only as their title abilities',
    ('setsuna', 'Affliction'): 'healed some time ago (owner, 2026-10-01); the retired sheet still carried it',
    ('harunobu', 'Pending: Glory award outstanding for his part in the Unicor'): "resolved: the award is OWNER_RULINGS' +6 glory (owner, 2026-09-29), which the layer carries",
    ('harunobu', 'Pending: The glory, honour and status below are therefore p'): "resolved with the award above: the layer's glory is post-award",
}

demark = lambda s: re.sub(r'(^|\s)(\d+\.|-)\s', ' ', str(s).replace('**', ''))
fold = lambda s: re.sub(r'\s+([,.;:])', r'\1', re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', str(s))).replace('’', "'").replace('‘', "'").replace('“', '"').replace('”', '"'))).strip()
low = lambda s: fold(s).lower()


def load(f):
    d = json.load(open(f, encoding='utf-8'))
    h = f.replace('.sheet.json', '.history.json')
    return d, (json.load(open(h, encoding='utf-8')) if os.path.exists(h) else [])


def skills_of(x):
    """The layer writes skills as "Name N" strings (the corpus's pregen convention)."""
    if isinstance(x, dict):
        return {k: v for k, v in x.items() if v}
    out = {}
    for item in x or []:
        m = re.match(r'^(.*\S)\s+(\d+)$', str(item))
        if m and int(m.group(2)):
            out[m.group(1)] = int(m.group(2))
    return out


def alltext(p):
    out = []
    def walk(x):
        if isinstance(x, dict):
            for k, v in x.items(): out.append(str(k)); walk(v)
        elif isinstance(x, list):
            for v in x: walk(v)
        elif x is not None: out.append(str(x))
    walk(p)
    return low(' '.join(out))


def compare(sheet, old, ent, ents):
    p = props(ent)
    text = alltext(p)
    rows = []   # (field, old, new, ok, note)

    def eq(field, a, b, note=''):
        rows.append((field, a, b, a == b, note))

    def carried(field, needle):
        n = low(needle)
        rows.append((field, needle, 'in the entity' if n in text else '—', n in text, ''))

    eq('Name', old['name'], p.get('Name'))
    eq('Clan', old['clan'], p.get('Clan'))
    eq('Family', old['family'], p.get('Family'))
    eq('School', low(old['school']), low(p.get('School') or ''))
    eq('School Rank', old['rank'], p.get('School Rank'))
    eq('Rings', {k.capitalize(): v for k, v in old['rings'].items()}, p.get('Rings'))
    for k in ('endurance', 'composure', 'focus', 'vigilance'):
        if k in (old.get('derived') or {}):
            eq(k.capitalize(), old['derived'][k], p.get(k.capitalize()))
    if ((old.get('trackers') or {}).get('void') or {}).get('max') is not None:
        eq('Void Points', old['trackers']['void']['max'], p.get('Void Points'))
    if old.get('stance'):
        eq('Stance', old['stance'].capitalize(), p.get('Stance'))
    for k in ('honor', 'glory', 'status'):
        eq(k.capitalize(), (old.get('social') or {}).get(k), p.get(k.capitalize()))
    eq('Skills', {SKILL.get(k, k.capitalize()): v for k, v in old['skills'].items() if v},
       skills_of(p.get('Skills')))
    b = old.get('bushido') or {}
    eq('Bushido', {'Paramount Tenet': b.get('paramount'), 'Less Significant Tenet': b.get('less')}, p.get('Bushido'))
    if b.get('register'):
        carried('Bushido register', b['register'])
    # Foundry's Markdown (**bold**, "1." and "-" lists) is formatting, not content
    eq('Ninjō', fold(demark(old.get('ninjo') or '')), fold(demark(p.get('Ninjō') or '')))
    eq('Giri', fold(demark(old.get('giri') or '')), fold(demark(p.get('Giri') or '')))
    eq('Techniques', sorted(low(t['name']) for t in old['techniques'] if t.get('tag') not in COMES_WITH),
       sorted(low(t) for t in p.get('Techniques') or []))
    for t in old['techniques']:
        if t.get('tag') == 'Title Ability':
            rows.append(('Title ability ' + t['name'], 'with its title', 'titles: ' + ', '.join(p.get('Titles') or []),
                         bool(p.get('Titles')), 'comes with the title'))
    rec = {low(x) for x in p.get('As Recorded') or []}
    def named(want, have):
        """The old names against the layer's: a name the corpus prints as a template ("Paragon of a
        Bushidō Tenet", "Scorn of [One Group]", "Advisor") matches when the table's own wording is in
        ^"As Recorded"; what is left over on each side is the difference."""
        want, have = sorted(want), list(have)
        miss = [w for w in want if w not in have and w not in rec]
        for w in want:
            if w in have:
                have.remove(w)
            elif w in rec:   # carried as recorded; its template entry is the one it fills
                tpl = next((h for h in have if h not in want), None)
                if tpl: have.remove(tpl)
        return miss, sorted(h for h in have if h not in want)
    for field, want, have in (
            ('Advantages', [low(x['name']) for x in old['peculiarities'] if x.get('tag') in GOOD], [low(x) for x in p.get('Advantages') or []]),
            ('Disadvantages', [low(x['name']) for x in old['peculiarities'] if x.get('tag') not in GOOD], [low(x) for x in p.get('Disadvantages') or []]),
            ('Titles', [low(t['name']) for t in old['titles']], [low(t) for t in p.get('Titles') or []])):
        miss, extra = named(want, have)
        rows.append((field, miss, extra, not miss and not extra, ''))
    equip = [low(x) for x in p.get('Equipment') or []]
    mounts = [low(x.split(':')[0]) for x in p.get('Mounts') or []]
    eq('Gear', sorted(low(g['name']) for g in old['gear']), sorted([x for x in equip if not re.search(r'\b(zeni|koku|bu)\b', x)] + mounts))
    if old.get('money'):
        eq('Money', low(old['money']), next((x for x in equip if re.search(r'\b(zeni|koku|bu)\b', x)), None))
    for bd in old.get('bonds') or []:
        rows.append(('Bond', bd.get('type'), ', '.join(p.get('Bonds') or []), bool(p.get('Bonds')), ''))
        carried('Bond partner', bd['name'])
        carried('Bond rank', 'rank ' + str(bd.get('rank')))
    for a in old.get('afflictions') or []:
        carried('Affliction', a['name'])
    for x in old.get('pending') or []:
        carried('Pending: ' + fold(x)[:50], fold(x)[:60])
    c = old.get('companion')
    if c:
        mine = [e for e in ents.values() if (props(e).get('Companion Of') or '') == ent['id']]
        rows.append(('Companion', c['name'], ', '.join(e['name'] for e in mine) or '—', any(low(e['name']) == low(c['name']) for e in mine), ''))
    return rows


def main():
    ents = built('campaign/data/campaign.js')
    fails = total = acc = 0
    for f in sorted(glob.glob(os.path.join(OLD, '*.sheet.json'))):
        sheet = os.path.basename(f)[:-len('.sheet.json')]
        cur, hist = load(f)
        pairs = [('current', cur, ENTITY[sheet])] + [(h['id'], h['data'], HISTORY.get((sheet, h['id']))) for h in hist]
        for vid, old, eid in pairs:
            print('== %s (%s) → %s' % (sheet, vid, eid))
            if not eid or eid not in ents:
                print('   FAIL no entity for this version'); fails += 1; continue
            for field, a, b, ok, note in compare(sheet, old, ents[eid], ents):
                total += 1
                why = ACCOUNTED.get((sheet, vid, field)) or ACCOUNTED.get((sheet, field))
                if ok:
                    continue
                if why:
                    acc += 1
                    print('   accounted  %s: %s — %s' % (field, json.dumps(a, ensure_ascii=False)[:90], why))
                    continue
                fails += 1
                print('   FAIL %s\n        old: %s\n        new: %s' % (field, json.dumps(a, ensure_ascii=False)[:300], json.dumps(b, ensure_ascii=False)[:300]))
    print('%s: %d fields across %d sheets — %d differ, %d accounted for' % ('PASS' if not fails else 'FAIL', total, len(glob.glob(os.path.join(OLD, '*.sheet.json'))), fails, acc))
    sys.exit(1 if fails else 0)


if __name__ == '__main__':
    main()
