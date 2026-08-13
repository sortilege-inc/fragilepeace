#!/usr/bin/env python3
"""
verify_site.py — gate the generated site.

    python3 scripts/build_site.py && python3 scripts/verify_site.py

Exits non-zero on any failure. Four checks:

  links   every local href/src in every .html/.css/.js resolves to a real file
  masks   every mask bar is empty — there must be nothing behind a mask
  rewrit  every [[wikilink]] in a hand-authored session file resolves to a page
  span    prints the session count and the first/last dates on record
"""

import os, re, io, sys, collections
from urllib.parse import unquote

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import archivist as A
from archivist import norm
import build_site as B

ROOT = A.ROOT
SKIP = (".git", "ingest", "sources", "scripts", "__pycache__")
HREF_RE = re.compile(r"""(?:href|src)\s*=\s*["']([^"']+)["']""")
CSSURL_RE = re.compile(r"""url\(\s*["']?([^"')]+)["']?\s*\)""")
MASK_RE = re.compile(r"<[^>]*class=[\"'][^\"']*mask-bar[^\"']*[\"'][^>]*>(.*?)</\w+>", re.S)


def walk():
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP and not d.startswith(".")]
        for fn in files:
            yield os.path.join(base, fn)


def check_links():
    bad, n = [], 0
    for path in walk():
        ext = os.path.splitext(path)[1].lower()
        if ext not in (".html", ".css", ".js"):
            continue
        txt = io.open(path, encoding="utf-8", errors="replace").read()
        refs = HREF_RE.findall(txt) if ext == ".html" else []
        refs += CSSURL_RE.findall(txt)
        for r in refs:
            # Unquote first: a data: URI can carry its own percent-encoded
            # url(%23n) fragment, which is not a file reference.
            r = unquote(r)
            if re.match(r"^(https?:|mailto:|data:|#|//)", r):
                continue
            n += 1
            tgt = r.split("#")[0].split("?")[0]
            if not tgt:
                continue
            full = os.path.normpath(os.path.join(os.path.dirname(path), tgt))
            if not os.path.exists(full):
                bad.append((os.path.relpath(path, ROOT), r))
    return n, bad


def check_masks():
    bad, n = [], 0
    for path in walk():
        if not path.endswith(".html"):
            continue
        txt = io.open(path, encoding="utf-8", errors="replace").read()
        for m in MASK_RE.finditer(txt):
            n += 1
            if m.group(1).strip():
                bad.append((os.path.relpath(path, ROOT), m.group(1)[:60]))
        n += txt.count('class="mask-bar"') - len(MASK_RE.findall(txt))
    return n, bad


def check_rewrites():
    """Self-closing mask bars carry no children by construction; the real risk is
    a wikilink in a hand-written session that silently renders as a dead span."""
    pages = A.discover() + A.discover_local()
    reg = A.build_registry(pages)
    sessions = A.discover_sessions()
    unres = collections.Counter()
    for s in sessions:
        for t in (s.recap, s.moments, s.timeline):
            B.link_wikilinks(t, "x.html", reg, unres)
    for p in pages:
        B.link_wikilinks(p.raw, p.url or "x.html", reg, unres)
    A.add_fuzzy_aliases(reg, set(unres.keys()))

    rewrites = B.load_rewrites()
    entries = [("session %d" % no, rewrites[no]) for no in sorted(rewrites)]
    entries += [("interlude %r" % iv.title, iv.rw) for iv in B.load_interludes()]
    bad, n = [], 0
    for label, rw in entries:
        for txt in (rw.narrative, rw.coda, rw.epigraph):
            for m in A.LINK_RE.findall(txt):
                n += 1
                if reg.get(norm(m[0].strip())) is None:
                    bad.append((label, m[0]))
    return len(entries), n, bad


def main():
    fail = 0

    n, bad = check_links()
    print("links      : %d checked, %d broken" % (n, len(bad)))
    for f, r in bad[:20]:
        print("             %s -> %s" % (f, r))
    fail |= bool(bad)

    n, bad = check_masks()
    print("masks      : %d bars, %d with content" % (n, len(bad)))
    for f, r in bad[:20]:
        print("             %s : %r" % (f, r))
    fail |= bool(bad)

    ns, n, bad = check_rewrites()
    print("rewrites   : %d entries, %d wikilinks, %d unresolved" % (ns, n, len(bad)))
    for label, name in bad[:20]:
        print("             %s -> [[%s]]" % (label, name))
    fail |= bool(bad)

    sessions = A.discover_sessions()
    rewrites = B.load_rewrites()
    have = {s.number for s in sessions}
    dates = {s.number: s.date for s in sessions}
    titles = {s.number: s.title for s in sessions}
    for no in sorted(set(rewrites) - have):
        dates[no] = rewrites[no].meta.get("date", "?")
        titles[no] = rewrites[no].meta.get("title", "?")
    order = sorted(dates)
    gaps = [no for no in range(1, order[-1] + 1) if no not in dates]
    print("span       : %d sessions, %s (s%d) .. %s (s%d)%s"
          % (len(order), dates[order[0]], order[0], dates[order[-1]], order[-1],
             "" if not gaps else ", MISSING %s" % gaps))
    print("last       : session %d, %s  %r" % (order[-1], dates[order[-1]],
                                               titles[order[-1]]))
    fail |= bool(gaps)

    print("RESULT     : %s" % ("FAIL" if fail else "PASS"))
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
