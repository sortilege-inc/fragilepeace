"""Check factguard's accept table for duplicate keys and duplicate tokens.

The table is fragile-peace/sources/factguard-accept.json, in the site repo so
its reasons have git history.

The check must see the RAW pairs, not the parsed object. Both of the obvious
ways to hold this data drop duplicates silently before anything can look at
them — a repeated literal key in a Python dict keeps only the last value, and
json.load does exactly the same — so `len(table) == len(set(table))` is always
true and proves nothing. json.JSONDecoder's object_pairs_hook is handed every
pair as it is read, which is the only place a duplicate is still visible.

A duplicate key is not cosmetic: the block that loses is a decision somebody
recorded a reason for, and it stops applying without any error.

Exit codes: 0 clean, 1 duplicates found, 2 bad invocation.
"""

import collections, io, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import cfg

PATH = cfg.ACCEPT


def _pairs(pairs):
    """object_pairs_hook: keep the raw pair list alongside the parsed dict."""
    d = dict(pairs)
    d["__pairs__"] = pairs
    return d


def main():
    if not os.path.exists(PATH):
        sys.stderr.write("acceptcheck: no accept table at %s\n" % PATH)
        return 2
    with io.open(PATH, encoding="utf-8") as fh:
        data = json.load(fh, object_pairs_hook=_pairs)

    bad, shadowed = [], []

    def dupe_keys(label, node):
        keys = [k for k, _ in node["__pairs__"] if k != "__pairs__"]
        for k, n in collections.Counter(keys).items():
            if n > 1:
                bad.append("%s: duplicate key %r appears %d times" % (label, k, n))
        return keys

    all_keys = dupe_keys("all", data["all"])
    file_keys = dupe_keys("per_file", data["per_file"])

    # A token accepted for one file and again for every file is the same
    # silent-shadowing problem one level up.
    for f in file_keys:
        toks = [t for t, _ in data["per_file"][f] if t != "__pairs__"]
        for t, n in collections.Counter(toks).items():
            if n > 1:
                bad.append("%s: duplicate token %r appears %d times" % (f, t, n))
        for t in toks:
            if t in all_keys:
                # Not a failure: the token is still accepted, via 'all'. But the
                # per-file reason is dead text that reads as live, which is worth
                # seeing. These come from tokens promoted to 'all' by a later
                # ruling without the per-file entry being retired.
                shadowed.append("%s: %r is also in 'all'; its per-file reason "
                                "never applies" % (f, t))

    # Regression guard. On 2026-09-14 the table was moved out of factguard.py
    # into this file, and a residual `ACCEPT = {...}` literal was left behind
    # below the new loader — so factguard went on using the old literal while
    # this script checked the JSON, and the two drifted apart silently for
    # three commits. Prove they are the same table, not merely both present.
    try:
        import factguard as F
    except Exception as e:                       # pragma: no cover
        bad.append("cannot import factguard to cross-check: %s" % e)
    else:
        live_all = set(F.ACCEPT_ALL)
        if live_all != set(all_keys):
            only = live_all ^ set(all_keys)
            bad.append("factguard's global table differs from this file: %s"
                       % sorted(only)[:6])
        live = {f: sorted(t for t, _ in v) for f, v in F.ACCEPT.items()}
        mine = {f: sorted(t for t, _ in data["per_file"][f]
                          if t != "__pairs__") for f in file_keys}
        if live != mine:
            diff = sorted(set(live) ^ set(mine)) or [
                f for f in mine if live.get(f) != mine[f]]
            bad.append("factguard's per-file table differs from this file: %s"
                       % diff[:6])

    print("all      : %d token(s)" % len(all_keys))
    print("per_file : %d file(s), %d token(s)"
          % (len(file_keys),
             sum(len([t for t, _ in data["per_file"][f] if t != "__pairs__"])
                 for f in file_keys)))
    if shadowed:
        print("  -- %d per-file reason(s) shadowed by 'all' (not an error):"
              % len(shadowed))
        for s in shadowed:
            print("     " + s)
    if bad:
        for b in bad:
            print("  !! " + b)
        print("RESULT   : FAIL")
        return 1
    print("RESULT   : OK — no duplicate keys or tokens")
    return 0


if __name__ == "__main__":
    sys.exit(main())
