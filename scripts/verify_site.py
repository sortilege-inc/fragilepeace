#!/usr/bin/env python3
"""
verify_site.py — gate the generated site.

    python3 scripts/build_site.py && python3 scripts/verify_site.py

Exits non-zero on any failure. Five checks:

  links   every local href/src in every .html/.css/.js resolves to a real file
  masks   every mask bar is empty — there must be nothing behind a mask
  names   no superseded spelling from archivist.CORRECTIONS survives anywhere
  rewrit  every [[wikilink]] in a hand-authored session or interlude resolves
  span    session count, the first/last dates, and any gap in the numbering
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


def check_names():
    """No superseded spelling may appear anywhere in the generated site.

    A rename used to relabel only the page's own title, leaving the old spelling
    all over everyone else's prose. archivist.CORRECTIONS now rewrites the text
    at read time; this is the assertion that it worked, and the thing that fails
    the build if a corrected name ever comes back.
    """
    bad = collections.Counter()
    where = {}
    for path in walk():
        if not path.endswith(".html"):
            continue
        txt = io.open(path, encoding="utf-8", errors="replace").read()
        for rx, repl in A.CORRECTIONS:
            hits = rx.findall(txt)
            if hits:
                bad[rx.pattern] += len(hits)
                where.setdefault(rx.pattern, os.path.relpath(path, ROOT))
    return [(p, n, where[p]) for p, n in bad.most_common()]


def check_ledger():
    """No session may carry two ## Learned bullets for the same entity.

    Ledger.learned is keyed {page: {session: line}}, so a second bullet for the
    same person in the same session silently replaces the first and its content
    never reaches the page. Two ways in: an entity written under two spellings
    that CORRECTIONS later merges — Kaeru Haia and Kaeru Haya both had a bullet
    in s32 — and one written twice deliberately, as Shosuro Aishi was in s26,
    once for the living advocate and once for the ancestor she is named for.
    Both read as a normal source file and neither shows up in the built site
    except as an entry that is quietly missing.
    """
    import glob
    bad = []
    for path in sorted(glob.glob(os.path.join(ROOT, "sources", "chronicle", "*.md"))):
        txt = A.correct(io.open(path, encoding="utf-8").read())
        m = re.search(r"## Learned(.*?)(?=^## |\Z)", txt, re.S | re.M)
        if not m:
            continue
        keys = [norm(l.split(":", 1)[0])
                for l in re.findall(r"^-\s+(.+)$", m.group(1), re.M)]
        dup = sorted({k for k in keys if keys.count(k) > 1})
        if dup:
            bad.append((os.path.basename(path), dup))
    return bad


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

    bad = check_names()
    print("names      : %d superseded spelling(s) still rendered" % len(bad))
    for pat, n, f in bad[:20]:
        print("             %s  x%d  (e.g. %s)" % (pat, n, f))
    fail |= bool(bad)

    ns, n, bad = check_rewrites()
    print("rewrites   : %d entries, %d wikilinks, %d unresolved" % (ns, n, len(bad)))
    for label, name in bad[:20]:
        print("             %s -> [[%s]]" % (label, name))
    fail |= bool(bad)

    bad = check_ledger()
    print("ledger     : %d session(s) with two bullets for one entity" % len(bad))
    for f, keys in bad[:20]:
        print("             %s : %s" % (f, ", ".join(keys)))
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
