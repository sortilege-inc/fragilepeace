#!/usr/bin/env python3
"""
check_cast.py — the conversion's proof for the cast: each sheet, read back from the BUILT layer
(campaign/data/campaign.js — rebuild first), field by field against its Foundry export in
campaign/source/foundry/.

    python3 campaign/source/check_cast.py            # every sheet in convert_cast.SHEETS
    python3 campaign/source/check_cast.py '#FPpcDojiSetsuna'

The expected values are read from the export here, not taken from the converter; only the list of
sheets and the two name aliases are shared. Every key of the export's `system` is compared or named in
NOT_CARRIED with the reason. Exit 1 on any difference.
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(HERE, 'campaign/source'))
from archivist import correct as house  # noqa: E402  (the site's house corrections; convert_cast.py)
from convert_cast import (SHEETS, GM_SHEETS, FOUNDRY, ALIAS, SCHOOL_ALIAS,  # noqa: E402
                          AS_RECORDED_FIX, OWNER_RULINGS, CORRECTIONS, MISCLASSIFIED)

# each group of sheets against its own built layer (a book of its own)
LAYERS = [(SHEETS, 'campaign/data/campaign.js')]

NOT_CARRIED = {
    'soft_locked': "Foundry's sheet lock",
    'notes': None, 'description': None,
    'techniques': "Foundry's allowed-technique-type switches; the corpus's School carries them",
    'prepared': "Foundry's prepared toggle",
    'xp_spent': 'Foundry stores 0 and computes it; Experience Spent is the sum of the items\' xp_used (checked)',
    'xp_saved': 'Foundry stores 0',
    'template': "Foundry's creation template (\"core\")",
    'twenty_questions': 'the creation answers; their results are the sheet (rings, skills, peculiarities — checked)',
    'zeni': 'in Equipment as "N zeni" (checked)',
    'money': 'in Equipment as "N koku/bu/zeni" (checked)',
    'is_afflicted_or_compromised': "Foundry's derived flag",
    'fatigue': 'value in archived versions (checked); max = Endurance',
    'strife': 'value in archived versions (checked); max = Composure',
    'void_points': 'max = Void Points (checked); value is the live tracker',
    'endurance': None, 'composure': None, 'focus': None, 'vigilance': None, 'identity': None, 'rings': None,
    'social': None, 'skills': None, 'stance': None, 'xp_total': None,
}
COMES_WITH = {'school_ability', 'mastery_ability', 'title_ability'}


def built(path):
    src = open(os.path.join(HERE, path), encoding='utf-8').read()
    return json.loads(re.search(r'var d=(\{.*\});var T=window\.L5R5E', src, re.S).group(1))['entities']


def arg(a):
    for k in ('s', 'c', 'i', 'b', 'w'):
        if k in a:
            return a[k]
    if 'l' in a:
        return [arg(x) for x in a['l']]
    return a.get('h')


def props(e):
    out = {}
    for p in e.get('props', []):
        vk = p.get('vk')
        if vk in ('scalar', 'enum'):
            out[p['name']] = p.get('value', p.get('default'))
        elif vk == 'list':
            out[p['name']] = [arg(x) for x in p.get('items', [])]
        elif vk == 'def':
            out[p['name']] = {f['name']: f.get('value') for f in p.get('fields', [])}
        elif vk == 'ref':
            out[p['name']] = (p.get('ref') or {}).get('hash')
    return out


def text_of(h):
    from html.parser import HTMLParser
    class P(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True); self.lines, self.cur = [], ''
        def handle_starttag(self, tag, a):
            if tag == 'br': self.lines.append(self.cur); self.cur = ''
        def handle_endtag(self, tag):
            if tag == 'p': self.lines.append(self.cur); self.cur = ''
        def handle_data(self, x):
            self.cur += x
    p = P(); p.feed(h or ''); p.close(); p.lines.append(p.cur)
    return '\n'.join(x.strip() for x in p.lines if x.strip())


def plain(n):
    """Foundry's item name as the corpus names it: apostrophe, alias, then a trailing (x) / [x] / ": x" off."""
    n = n.replace('’', "'").strip()
    if n in ALIAS:
        return ALIAS[n]
    if n in ('Ally [Name]', 'Shadowlands Taint (Air)', 'Stalked by [Creature]'):   # corpus entities whose names carry the brackets
        return n
    n = re.sub(r'\s*(\([^)]*\)|\[[^\]]*\])$', '', n).split(':')[0].strip()
    return ALIAS.get(n, n)


def held(items):
    """Every item the character holds, a title's own items after it: a technique bought through a
    title lives in that title's `system.items`, not at the top level (Harunobu's Righteous Example and
    Heartpiercing Strike; Morozane's six; Setsuna's Shallow Waters and three kata)."""
    for i in items:
        yield i
        if i['type'] == 'title':
            subs = (i.get('system') or {}).get('items') or []
            for j in (subs.values() if isinstance(subs, dict) else subs):
                yield j


def ruled_text(eid, field, v):
    """The text the layer must hold: the export's, with an owner ruling or a recorded correction applied."""
    for table in (OWNER_RULINGS, CORRECTIONS):
        r = table.get((eid, field))
        if not r:
            continue
        if 'replace' in r and r['replace'][0] in v:
            return v.replace(*r['replace'])
        if 'before' in r and v == r['before']:
            return r['after']
    return v


def compare(label, name, d, P, archived=None, eid=None):
    s, rows = d['system'], []
    def eq(field, old, new):
        rows.append((field, old, new, old == new))
    idn, so, items = s['identity'], s['social'], d['items']
    eq('name = the id\'s', name, P.get('Name'))
    eq('Foundry\'s name, verbatim (Foundry Name, or Name when the same)', d['name'], P.get('Foundry Name', P.get('Name')))
    eq('identity.clan', idn['clan'], P.get('Clan'))
    eq('identity.family (house spelling)', house(idn['family']), P.get('Family'))
    sch = re.sub(r' School$', '', re.sub(r' \[[^\]]+\]$', '', idn['school']))
    eq('identity.school (less " School", "[Clan]"; SCHOOL_ALIAS)', SCHOOL_ALIAS.get(sch, sch), P.get('School'))
    eq('identity.school_rank', idn['school_rank'], P.get('School Rank'))
    eq('identity.roles (an empty one is none)', [x.strip() for x in idn['roles'].split(',') if x.strip()], P.get('Roles'))
    for r in ('air', 'earth', 'fire', 'water', 'void'):
        eq('rings.' + r, s['rings'][r], (P.get('Rings') or {}).get(r.title()))
    for k in ('honor', 'glory', 'status'):
        # Where the owner has ruled a value the export does not carry yet, the ruled value is what
        # the layer must hold — the expectation is taken from the ruling, not from the converter.
        want = so[k]
        r = OWNER_RULINGS.get((eid, k.title()))
        if r and want == r['before']:
            want = r['after']
        eq('social.' + k + (' (owner ruling)' if r and want != so[k] else ''), want, P.get(k.title()))
    eq('social.ninjo', house(ruled_text(eid, 'Ninjō', so['ninjo'])), P.get('Ninjō'))
    eq('social.giri', house(ruled_text(eid, 'Giri', so['giri'])), P.get('Giri'))
    eq('social.bushido_tenets.paramount', so['bushido_tenets']['paramount'], (P.get('Bushido') or {}).get('Paramount Tenet'))
    eq('social.bushido_tenets.less_significant', so['bushido_tenets']['less_significant'], (P.get('Bushido') or {}).get('Less Significant Tenet'))
    for k in ('endurance', 'composure', 'focus', 'vigilance'):
        eq(k, s[k], P.get(k.title()))
    eq('void_points.max', s['void_points']['max'], P.get('Void Points'))
    eq('stance', s['stance'].title(), P.get('Stance'))
    eq('xp_total', s['xp_total'], P.get('Experience'))
    eq('Σ items xp_used', sum(i['system'].get('xp_used') or 0 for i in items), P.get('Experience Spent'))
    eq('ledger = items with xp_used', [(i['system']['xp_used'], i['name']) for i in items if i['system'].get('xp_used')],
       [(int(x.split(' · ')[0]), x.split(' · ')[1]) for x in P.get('Experience Ledger', [])])
    nz = sorted((k, v) for g in s['skills'].values() for k, v in g.items() if v)
    got = sorted((re.sub(r'^Martial Arts \[(\w+)\]$', lambda m: m.group(1).lower(), x.rsplit(' ', 1)[0]).lower(), int(x.rsplit(' ', 1)[1])) for x in P.get('Skills') or [])
    eq('skills (every non-zero rank)', nz, got)
    eq('techniques, a title\'s own included (less the school/title ability)',
       [plain(i['name']) for i in held(items) if i['type'] == 'technique'
        and i['system'].get('technique_type') not in COMES_WITH], P.get('Techniques'))
    # An item Foundry types wrongly, which really comes with a title, is absent from the layer like
    # any other title ability — and the title that grants it has to be on the sheet.
    for i in items:
        if i['type'] == 'signature_scroll':
            grant = MISCLASSIFIED.get(i['name'])
            eq('%s: comes with a title the sheet holds' % i['name'], True,
               bool(grant) and any(j['type'] == 'title' and j['name'] == grant for j in items))
    eq('peculiarities: distinction + passion', [plain(i['name']) for i in items if i['type'] == 'peculiarity' and i['system']['peculiarity_type'] in ('distinction', 'passion')], P.get('Advantages'))
    eq('peculiarities: adversity + anxiety', [plain(i['name']) for i in items if i['type'] == 'peculiarity' and i['system']['peculiarity_type'] in ('adversity', 'anxiety')], P.get('Disadvantages'))
    eq('titles', [plain(i['name']) for i in items if i['type'] == 'title'], P.get('Titles', []))
    # A bond is named for the person; the corpus entity is the KIND, which Foundry keeps in
    # bond_type ("Wife (Lover)"). The person's name is checked below, in As Recorded.
    def bond_kind(i):
        n = plain(i['name'])
        if n != i['name'].replace('\u2019', "'"):
            return n
        bt = i['system'].get('bond_type') or ''
        return '%s Bond' % (re.sub(r'^.*\(([^)]*)\).*$', r'\1', bt).strip() or bt)
    eq('bonds (by kind, not by the partner)', [bond_kind(i) for i in items if i['type'] == 'bond'], P.get('Bonds', []))
    money = s.get('zeni') or 0
    eq('gear names + money', [i['name'] for i in items if i['type'] in ('weapon', 'armor', 'item')] + (['%d zeni' % money] if money else []), P.get('Equipment'))
    # A bond's recorded name is always the partner, because the entity is the kind.
    recorded = [AS_RECORDED_FIX.get(i['name'], i['name']) for i in held(items)
                if i['type'] in ('technique', 'peculiarity', 'title', 'bond')
                and i['system'].get('technique_type') not in COMES_WITH
                and (i['type'] == 'bond' or plain(i['name']) != i['name'].replace('\u2019', "'"))]
    eq('as recorded: every item (and school) name the corpus spells otherwise',
       recorded + ([idn['school']] if sch in SCHOOL_ALIAS else []), P.get('As Recorded', []))
    # Older exports here carry only `zeni` and no `money` record; absent is zero either way.
    eq('money koku/bu/zeni all 0 (an empty field, or none at all, counts as 0)',
       {'koku': 0, 'bu': 0, 'zeni': 0},
       {'koku': 0, 'bu': 0, 'zeni': 0} | {k: (v or 0) for k, v in (s.get('money') or {}).items()})
    for key in ('description', 'notes'):
        # the rich text read here with the stdlib parser, not the converter's regex
        eq(key + ' (as text, a line a paragraph; house spelling)', house(text_of(s[key])), P.get(key.title(), ''))
    left = [i['type'] + ':' + i['name'] for i in items if i['type'] not in ('technique', 'peculiarity', 'title', 'bond', 'weapon', 'armor', 'item', 'advancement')]
    eq('no item of another type', [], [x for x in left if not x.startswith('signature_scroll:')])
    if archived:
        eq('strife.value', s['strife']['value'], P.get('Strife'))
        eq('fatigue.value', s['fatigue']['value'], P.get('Fatigue'))
        eq('version label', archived[0], P.get('Version Label'))
        # A version whose export carries no date in its filename (Anzu's creation snapshot is a
        # state, not a date) has no Version Date at all, rather than an empty one.
        eq('version date', archived[1] or None, P.get('Version Date'))
    extra = sorted(set(s) - set(NOT_CARRIED))
    eq('every system key accounted for', [], extra)
    bad = [r for r in rows if not r[3]]
    print('== %s: %d fields, %d differ' % (label, len(rows), len(bad)))
    for f, o, n, ok in bad:
        print('   DIFFERS  %-44s export=%r  built=%r' % (f, o, n))
    return len(rows), len(bad)


def main():
    only = sys.argv[1:]
    total = bad = sheets = 0
    for group, path in LAYERS:
        E = built(path)
        for pid, name, versions in group:
            if only and pid not in only:
                continue
            for f, label in versions:
                d = json.load(open(os.path.join(FOUNDRY, f), encoding='utf-8'))
                # the same rule convert_cast uses: a date from the filename where there is one,
                # otherwise the label squeezed to letters and digits
                md = re.search(r'(\d{4}-\d{2}-\d{2})', f)
                date = md.group(1) if md else ''
                short = label.split(' · ')[1] if (label and ' · ' in label) else label
                eid = pid if label is None else pid + (date.replace('-', '') or re.sub(r'[^A-Za-z0-9]', '', short))
                if eid not in E:
                    print('== %s: NOT IN %s' % (eid, path)); bad += 1; continue
                P = props(E[eid])
                if label is not None and P.get('Version Of') != pid:
                    print('== %s: Version Of %r, expected %s' % (eid, P.get('Version Of'), pid)); bad += 1
                n, b = compare('%s ← %s' % (eid, f), name, d, P, (label, date) if label else None, eid=pid)
                total += n; bad += b; sheets += 1
    print('check_pcs: %s — %d fields compared across %d sheets, %d differ' % ('OK' if not bad else 'FAILED', total, sheets, bad))
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
