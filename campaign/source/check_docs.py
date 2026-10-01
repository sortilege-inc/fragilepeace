#!/usr/bin/env python3
"""M5's gate: the old site's pages as the VTT's documents (campaign/PLAN.md F4, M5).

    python3 campaign/source/check_docs.py [old-site-root]     # exit 0 = every check passes

1. Every page: the old site's (default: the pages as they stood at OLD_REF, read from git — the old site is
   deleted once this passes) against campaign/docs/<same path>: the same set of pages, and each page's text —
   its <body> less the shell's nav bar, footer and scripts — identical to its document's.
2. Every link in every document resolves. A route (#tab/…) names a document by the same rules as
   campaign/site/site.js's router (ROUTE below, kept in step with it): the longest run of the path that is a
   document, then at most one more segment, an element id in it. A campaign/… or root path is a real file.
3. Nothing in campaign/docs/ is left that the old site did not have (manifest.js excepted).
4. Every old page's styles are carried: a page that linked the site's stylesheets links only rokugan.css (and
   the map, map.css), scoped to .fp-site; a page with a <style> of its own is a dossier in OWN, and its
   campaign/source/css/dossier-<name>.css holds that block verbatim (scope_css.py scopes it to .fp-own-<name>,
   the class site.js gives that document).

Independent of to_docs.py: it reads both sides with the stdlib parser, not to_docs's regexes, and resolves
routes itself.
"""
import os
import re
import subprocess
import sys
from html.parser import HTMLParser
from urllib.parse import unquote

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)                  # campaign/
ROOT = os.path.dirname(SITE)                  # the repo, the VTT's root
DOCS = os.path.join(SITE, 'docs')
OLD_REF = '5a1f6a6'                           # the last commit with the old site whole (M4 and the Void Wound)
OLD_DIRS = ('index.html', 'character/', 'party/', 'chronicle/', 'dramatis-personae/', 'atlas/', 'lore/', 'notes/', 'map/')

# the documents whose old page had its own styles (campaign/site/site.js OWN)
OWN = {'character/setsuna.html': 'setsuna', 'character/harunobu.html': 'harunobu',
       'character/jujiro.html': 'jujiro', 'character/anzu.html': 'anzu'}
SITE_CSS = {'rokugan.css', 'map/map.css'}

# the router (campaign/site/site.js ROUTE): a tab → its section of the old site
ROUTE = {'fp': '', 'pcs': 'character', 'party': 'party', 'chronicle': 'chronicle', 'personae': 'dramatis-personae',
         'atlas': 'atlas', 'rokugan': 'lore', 'notes': 'notes'}


class Text(HTMLParser):
    """A page's visible text, less the shell (nav.topnav, footer.foot), scripts, styles and the head."""
    SKIP = {'script', 'style', 'head', 'title'}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self.depth, self.ids = [], [], set()

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get('id'):
            self.ids.add(a['id'])
        if self.depth:
            if tag == self.depth[-1][0]:
                self.depth[-1][1] += 1
            return
        if tag in self.SKIP or (tag == 'nav' and a.get('class') == 'topnav') or (tag == 'footer' and a.get('class') == 'foot'):
            self.depth.append([tag, 1])

    def handle_endtag(self, tag):
        if self.depth and tag == self.depth[-1][0]:
            self.depth[-1][1] -= 1
            if not self.depth[-1][1]:
                self.depth.pop()

    def handle_data(self, d):
        if not self.depth:
            self.out.append(d)


def text_of(h):
    p = Text()
    p.feed(h)
    return re.sub(r'\s+', ' ', ''.join(p.out)).strip(), p.ids


def old_pages(src):
    """{path: html} of the old site: from a directory, or from git at OLD_REF."""
    out = {}
    if src:
        for d, _, fs in os.walk(src):
            for f in fs:
                rel = os.path.relpath(os.path.join(d, f), src)
                if f.endswith('.html') and rel.startswith(OLD_DIRS):
                    out[rel] = open(os.path.join(d, f), encoding='utf-8').read()
        return out
    ls = subprocess.run(['git', '-C', ROOT, 'ls-tree', '-r', '--name-only', OLD_REF, 'campaign/'],
                        capture_output=True, text=True, check=True).stdout.split()
    for p in ls:
        rel = p[len('campaign/'):]
        if rel.endswith('.html') and rel.startswith(OLD_DIRS):
            out[rel] = subprocess.run(['git', '-C', ROOT, 'show', '%s:%s' % (OLD_REF, p)],
                                      capture_output=True, text=True, check=True).stdout
    return out


def resolve(route, docs):
    """#tab/a/b/c → (document path, anchor or None), or None. The router's rules, mirrored."""
    parts = [unquote(x) for x in route.lstrip('#').split('/') if x]
    if not parts or parts[0] not in ROUTE:
        return None
    tab, parts = parts[0], parts[1:]
    if tab == 'atlas' and not parts:
        return 'map/index.html', None
    if tab == 'atlas' and parts[0] == 'gazetteer':
        return ('atlas/index.html', parts[1] if len(parts) > 1 else None) if len(parts) <= 2 else None
    base = ROUTE[tab]
    for k in range(len(parts), -1, -1):
        for cand in ([os.path.join(base, *parts[:k]) + '.html'] if k else []) + [os.path.join(base, *parts[:k], 'index.html')]:
            if cand in docs:
                rest = parts[k:]
                return (cand, rest[0] if rest else None) if len(rest) <= 1 else None
    return None


def main():
    old = old_pages(sys.argv[1] if len(sys.argv) > 1 else None)
    docs = {}
    for d, _, fs in os.walk(DOCS):
        for f in fs:
            if f.endswith('.html'):
                rel = os.path.relpath(os.path.join(d, f), DOCS)
                docs[rel] = open(os.path.join(d, f), encoding='utf-8').read()
    bad = []
    missing, extra = sorted(set(old) - set(docs)), sorted(set(docs) - set(old))
    bad += ['no document for %s' % p for p in missing] + ['a document the old site did not have: %s' % p for p in extra]
    ids = {}
    for p in sorted(set(old) & set(docs)):
        a, _ = text_of(old[p])
        b, ids[p] = text_of(docs[p])
        if a != b:
            i = next((i for i in range(min(len(a), len(b))) if a[i] != b[i]), min(len(a), len(b)))
            bad.append('%s: text differs at %d — old %r · new %r' % (p, i, a[max(0, i - 30):i + 40], b[max(0, i - 30):i + 40]))
    links = 0
    for p, h in sorted(docs.items()):
        for ref in re.findall(r'''(?:href|src)\s*=\s*["']([^"']*)["']''', h):
            if re.match(r'^(https?:|mailto:|data:|//)', ref):
                continue
            links += 1
            if ref.startswith('#'):
                r = resolve(ref, docs)
                if not r:
                    bad.append('%s: route %s names no document' % (p, ref))
                elif r[1] and r[1] not in ids.get(r[0], set()):
                    bad.append('%s: route %s — no id %r in %s' % (p, ref, r[1], r[0]))
            elif not os.path.exists(os.path.join(ROOT, unquote(ref.split('#')[0].split('?')[0]))):
                bad.append('%s: %s is not a file' % (p, ref))
    for p, h in sorted(old.items()):
        styles = re.findall(r'<style[^>]*>(.*?)</style>', h, re.S)
        sheets = {os.path.normpath(os.path.join(os.path.dirname(p), x)) for x in
                  re.findall(r'<link[^>]*rel="stylesheet"[^>]*href="([^"]+)"', h) if not x.startswith('http')}
        if p in OWN:
            css = os.path.join(HERE, 'css', 'dossier-%s.css' % OWN[p])
            kept = open(css, encoding='utf-8').read() if os.path.exists(css) else ''
            if len(styles) != 1 or styles[0].strip('\n') not in kept or sheets:
                bad.append('%s: its own <style> is not carried verbatim in %s' % (p, os.path.relpath(css, ROOT)))
        elif styles or not sheets or not sheets <= SITE_CSS:
            bad.append('%s: styles not accounted for (%d <style>, links %s)' % (p, len(styles), sorted(sheets)))
    for b in bad[:40]:
        print('FAIL ' + b)
    print('%s: %d pages, %d documents, text identical in %d; %d links, every one resolving%s' % (
        'PASS' if not bad else 'FAIL', len(old), len(docs), len(set(old) & set(docs)) - sum(1 for b in bad if 'text differs' in b),
        links, '' if not bad else ' — %d failures' % len(bad)))
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
