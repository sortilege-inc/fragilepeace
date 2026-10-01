#!/usr/bin/env python3
"""M5, once: the old site's hand-written pages into campaign/docs/ (campaign/PLAN.md F4, M5).

build_site.py writes the generated pages as documents itself. These were never generated — the home
page, the five character dossiers, the player notes and the map — so they move once, through the same
to_docs.document, and from then on campaign/docs/<path> is where they are edited. check_docs.py proves
every one against the old page.

    python3 campaign/source/migrate_docs.py          # refuses once the old page is gone
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from to_docs import document, write_manifest  # noqa: E402

HAND = ['index.html', 'character/index.html', 'character/setsuna.html', 'character/harunobu.html',
        'character/jujiro.html', 'character/anzu.html', 'notes/index.html', 'map/index.html']


def main():
    docs = os.path.join(SITE, 'docs')
    for page in HAND:
        src = os.path.join(SITE, page)
        if not os.path.exists(src):
            sys.exit('%s is gone: the move has been made (campaign/docs/%s is the page now)' % (page, page))
        out = os.path.join(docs, page)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(src, encoding='utf-8') as f, open(out, 'w', encoding='utf-8') as g:
            g.write(document(page, f.read()))
    print('moved %d hand-written pages; manifest: %d documents' % (len(HAND), write_manifest(docs)))


if __name__ == '__main__':
    main()
