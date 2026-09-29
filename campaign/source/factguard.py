#!/usr/bin/env python3
"""
factguard.py — prove a voice rewrite did not lose facts.

    python3 scripts/factguard.py [ref] [path ...]

Compares each source file against its committed version (default ref: HEAD) and
reports every *fact token* that the old text carried and the new one does not.
The rewrite is allowed to change every sentence; it is not allowed to drop a
name, a number, a rank, or a piece of quoted speech.

Six extractors. The first four fail on a token that vanishes outright:

  links    [[wikilink]] targets, normalised. A dropped link is a dropped person,
           place or thing — and it also silently changes what the ledger builds,
           since Dramatis Personae pages are assembled from these.
  names    capitalised words and multi-word runs that are not sentence-initial
           and not ordinary English. Catches a person named in prose but never
           linked. "Ordinary English" is judged against the union of BOTH
           texts' lower-case vocabularies — deriving it per text made the
           comparison asymmetric and reported words that were sitting in both.
  numbers  digits and the spelled numerals one..twelve, plus ordinals. Concrete
           scale is load-bearing in this voice and is the easiest thing to
           smooth away.
  quotes   *italicised speech* — what somebody actually said, reduced to a
           content-word fingerprint so rewrapping and re-punctuating are free
           but rewording is not. Merging two adjacent runs into one is free
           too: a fingerprint whose words all survive inside a longer run of
           the new text is absorbed, not lost. Splitting one run into two
           still reports, because that can put half a line in another mouth.

  bullets  the ## Learned list, which is the ledger every Dramatis Personae and
           Gazetteer page is assembled from. Its subject keys — the text before
           the first colon — must survive one for one. Losing one silently
           empties a panel on another page.

The sixth is advisory and prints without failing:

  thin     a name or link whose count merely *drops*. Tightening prose removes
           repetition legitimately, so this cannot be a gate; but a clause that
           carried a fact about somebody mentioned four other times disappears
           exactly here, and nowhere else. Read the list.

Exit codes: 0 clean, 1 losses found, 2 bad invocation.

Losses are not automatically wrong. A name can legitimately vanish because the
old text used it twice in one sentence, or because two sentences merged. The
gate's job is to make every one of them a decision that was looked at, rather
than an accident. Record accepted ones in ACCEPT below with a reason.
"""

import os, sys, re, io, sys, subprocess, unicodedata, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import cfg

SUP  = cfg.BASE          # …/fragile-peace-support
ROOT = cfg.ROOT          # sibling site repo

# The accept table lives in the SITE REPO, not here: fragile-peace/sources/
# factguard-accept.json. Every entry records a token a rewrite deliberately
# dropped and the reason it was allowed to go, and those reasons need git
# history for the same reason sources/ does — see the _repo_inputs note in
# site.config.json. This folder is not a repo, so keeping them here meant 197
# recorded decisions with no history and no backup.
#
#   "all"       token -> reason, applied to every file. Use only when the loss
#               is one editorial decision across a whole surface.
#   "per_file"  basename -> [[token, reason], ...] for anything file-specific,
#               where it can be read against the file it applies to.
#
# scripts/acceptcheck.py gates the file for duplicate keys and duplicate tokens.
ACCEPT_PATH = cfg.ACCEPT


def _load_accepts(path=ACCEPT_PATH):
    import json
    try:
        with io.open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except IOError:
        sys.stderr.write("factguard: cannot read the accept table at %s\n" % path)
        raise SystemExit(2)
    return (dict(data["all"]),
            {f: [tuple(pair) for pair in v] for f, v in data["per_file"].items()})


ACCEPT_ALL, ACCEPT = _load_accepts()

# Losses that were looked at and accepted, keyed by file basename. Each entry is
# (token, reason). Nothing goes in here without a reason a reader can check.
# Owner's ruling 2026-09-13: the Scorpion family is spelled SHOSURO. The sources
# had been writing "Shoshuro" in ten files; archivist.CORRECTIONS was already
# normalising it at read time, so no rendered page ever said anything else, and
# this sweep is the sources catching up. Every one of these is the same rename
# and nothing else moved — the links, bullets and names channels all report the
# corrected spelling arriving as the old one leaves.
for _t in ("shoshuro", "shoshuro s", "shoshuro aishi", "shoshuro amane",
           "daimyo shoshuro"):
    ACCEPT_ALL[_t] = ("owner's spelling ruling 2026-09-13: Shoshuro -> Shosuro, "
                      "swept across the sources. CORRECTIONS already rendered it "
                      "this way; the files now match.")

# Owner's ruling 2026-09-13: the Kitsu is YUE. Sources written before that call
# are being brought over file by file as the pass reaches them;
# archivist.CORRECTIONS was already rewriting Yui -> Yue at read time, so no
# rendered page ever changed name.
for _t in ("kitsu yui", "yui", "yui s", "katsuki yui"):
    ACCEPT_ALL[_t] = ("owner's merge 2026-09-13: Kitsu Yui -> Kitsu Yue. "
                      "CORRECTIONS already rendered it this way; the sources are "
                      "catching up as the pass reaches each file.")

# 2026-09-13: the Unicorn advocate is Ide TSUBAME, not "Ide Subane" — see
# archivist.CORRECTIONS. Swept across the sources; CORRECTIONS already renders
# it, so no page changes name.
for _t in ("ide subane", "subane"):
    ACCEPT_ALL[_t] = ("2026-09-13 spelling fix: Ide Subane -> Ide Tsubame. The "
                      "transcriptions say Tsubame 8 times out of 8, including "
                      "from the player who voices her; Subane is the export's "
                      "dropped consonant, as 'Okoto' is for 'Akodo'.")

for _t in ("kitsuko", "kitsuko ayoko"):
    ACCEPT_ALL[_t] = ("2026-09-13 spelling fix: Kitsuko Ayoko -> Kitsu Ayoko. "
                      "The transcriptions say Kitsu Ayoko 27 times across 11 "
                      "recordings against a single 'Kitsuko' (2025-04-28). Kitsu "
                      "is a real Lion family and the canonical ancestor-speaking "
                      "bloodline, which is exactly her role; Kitsuko is not a "
                      "family at all. Shosuro Aishi says so on the 2025-10-06 "
                      "recording -- 'that is only the provenance of the Kitsu' -- "
                      "and the Castle of the Swift Sword is the Kitsu seat.")


# Words that start sentences, or are simply English, and would otherwise flood
# the "names" channel with noise.
STOP = set("""
a an and are as at be been but by for from had has have he her hers here him his
how i if in into is it its me my no nor not of on or our out over she so than
that the their them then there these they this those to too under until up was
we were what when where which while who whom why will with would you your
after again against all also am among any because before being below between
both did do does doing down during each few further more most no only other
same some such through very
""".split())

# Sentence-initial capitals that are still real names get caught anyway, because
# they almost always recur mid-sentence somewhere. These are the openers that do
# not, and are pure noise.
OPENERS = set("""
And But Then So That This These Those There Here It Its He She They We You I If
When Where While What Which Who Whom Why How A An The As At By For From In Into
Of On Or Out Over To Up With After Again Against All Also Am Among Any Because
Before Being Below Between Both Did Do Does Doing Down During Each Few Further
More Most Only Other Same Some Such Through Very Her His Their Our My No Not Nor
Every Neither Either Once Now Later Afterwards Nobody Nothing Everything Someone
Somebody Anyone Anything Whatever Whoever However Meanwhile Instead Still Yet
""".split())

NUMWORDS = set("""
one two three four five six seven eight nine ten eleven twelve
first second third fourth fifth sixth seventh eighth ninth tenth
once twice thrice half quarter dozen hundred thousand
""".split())

LINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]*)?\]\]")
ITAL_RE = re.compile(r"(?<!\*)\*(?!\*)([^*\n]{4,})\*(?!\*)")
BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")


def norm(s):
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", s.replace("’", "'").lower()).strip()


def strip_markup(t):
    """Prose as a reader sees it: links flattened to their display text."""
    t = re.sub(r"\[\[([^\]|]+)\|([^\]]*)\]\]", r"\2", t)
    t = re.sub(r"\[\[([^\]]+)\]\]", r"\1", t)
    t = BOLD_RE.sub(r"\1", t)
    t = re.sub(r"^\s*(!lede|!note)\s*", "", t, flags=re.M)
    return t


def sections(t):
    """{heading: body}, plus 'epigraph' and 'front' pulled from the header."""
    out = {}
    head, _, rest = t.partition("\n---\n")
    m = re.search(r"^epigraph:\s*(.+?)(?=\n\w+:|\Z)", head, re.S | re.M)
    out["epigraph"] = m.group(1).strip() if m else ""
    cur, buf = "front", []
    for line in rest.splitlines():
        h = re.match(r"^## (.+)$", line)
        if h:
            out[cur] = "\n".join(buf)
            cur, buf = h.group(1).strip(), []
        else:
            buf.append(line)
    out[cur] = "\n".join(buf)
    return out


def f_links(t):
    return collections.Counter(norm(m) for m in LINK_RE.findall(t) if norm(m))


def lower_vocab(t):
    """Words this text uses in lower case. See f_names."""
    return {w for w in re.findall(r"\b[a-zà-ɏ'’-]+\b", strip_markup(t))}


def f_names(t, lower=None):
    t = strip_markup(t)
    # The source is hard-wrapped mid-sentence, so a line break is not a sentence
    # break. Join wrapped lines before splitting, or a name that happens to land
    # at the start of a line gets discounted as a sentence opener and reads as a
    # loss. Blank lines stay: those are real paragraph breaks.
    t = re.sub(r"(?<!\n)\n(?!\s*\n)", " ", t)
    # Ordinary words that the text also uses in lower case. A capital at the
    # start of a sentence is only evidence of a name if the word is never seen
    # uncapitalised — otherwise it is just a sentence beginning.
    #
    # This vocabulary MUST be the same on both sides of a comparison. Deriving
    # it from each text separately made the test asymmetric: a rewrite that
    # happened to use the word in lower case somewhere had its sentence-initial
    # capital discounted while the original's was counted, and the token was
    # reported as a loss while sitting in both texts. That fired four times in
    # the 2026-09 pass (s08 "two", s09 "elsewhere", s10 "pushing") before it was
    # diagnosed. compare() passes the union of both texts' vocabularies.
    if lower is None:
        lower = lower_vocab(t)

    got = collections.Counter()
    for sent in re.split(r"(?<=[.!?;:])\s+|\n+", t):
        toks = re.findall(r"[A-Z][A-Za-zÀ-ɏ'’-]+", sent)
        if not toks:
            continue
        first = re.match(r"\s*[\"'“‘*]*([A-Z][A-Za-z'’-]+)", sent)
        for i, w in enumerate(toks):
            if w in OPENERS:
                continue
            if (i == 0 and first and first.group(1) == w
                    and w.lower() in lower):
                # Sentence-initial, and the same word appears in lower case
                # elsewhere, so the capital is punctuation rather than a name.
                continue
            if norm(w) in STOP:
                continue
            got[norm(w)] += 1
    return got


def f_numbers(t):
    t = strip_markup(t).lower()
    got = collections.Counter()
    for m in re.findall(r"\b\d[\d,]*(?:st|nd|rd|th)?\b", t):
        got[m.replace(",", "")] += 1
    for w in re.findall(r"[a-z]+", t):
        if w in NUMWORDS:
            got[w] += 1
    return got


def f_quotes(t):
    """Fingerprint each italic run by its content words, order-independent."""
    got = collections.Counter()
    for words in quote_word_sets(t):
        got[" ".join(sorted(words))[:120]] += 1
    return got


def quote_word_sets(t):
    """The content words of each italic run, untruncated.

    f_quotes caps its key at 120 characters so the report stays readable, which
    means a long run's fingerprint is missing whatever sorted last. The
    absorption check in compare() must not use those clipped keys — it asks
    whether an old run's words all survive inside a new one, and a clipped key
    answers "no" for the very case absorption exists to allow: a short quote
    expanded into a longer one.
    """
    out = []
    for m in ITAL_RE.findall(strip_markup(t)):
        words = {w for w in norm(m).split() if w not in STOP and len(w) > 2}
        if len(words) >= 2:
            out.append(words)
    return out


def f_bullets(t):
    """Subject keys of the ## Learned list — the text before the first colon."""
    body = sections(t).get("Learned", "")
    got = collections.Counter()
    for line in re.findall(r"^-\s+(.+)$", body, re.M):
        key = strip_markup(line).split(":", 1)[0]
        got[norm(key)[:60] or norm(strip_markup(line))[:60]] += 1
    return got


CHANNELS = [("links", f_links), ("names", f_names),
            ("numbers", f_numbers), ("quotes", f_quotes),
            ("bullets", f_bullets)]


def old_text(ref, relpath):
    try:
        return subprocess.check_output(
            ["git", "show", "%s:%s" % (ref, relpath)],
            cwd=ROOT, stderr=subprocess.DEVNULL).decode("utf-8")
    except subprocess.CalledProcessError:
        return None


def compare(ref, relpath):
    old = old_text(ref, relpath)
    if old is None:
        return None, [], []
    new = io.open(os.path.join(ROOT, relpath), encoding="utf-8").read()
    if old == new:
        return "unchanged", [], []
    losses, thin = [], []
    accepted = {a for a, _ in ACCEPT.get(os.path.basename(relpath), [])}
    accepted |= set(ACCEPT_ALL)
    # One vocabulary for both sides, so the sentence-opener heuristic cannot
    # discount a word in one text and not the other.
    shared_lower = lower_vocab(old) | lower_vocab(new)
    for chan, fn in CHANNELS:
        if chan == "names":
            o, n = fn(old, shared_lower), fn(new, shared_lower)
        else:
            o, n = fn(old), fn(new)
        # A quote fingerprint is the content words of one italicised run, so
        # merging two adjacent runs into one changes the fingerprints without
        # losing a word. Before calling such a token lost, check whether its
        # words survive inside some run of the new text. A reworded or deleted
        # quote is not a subset of anything and still fails. Splitting one run
        # into two is NOT absorbed and still reports, which is wanted: that can
        # put half a line in someone else's mouth.
        absorbed = set()
        if chan == "quotes":
            new_sets = quote_word_sets(new)
            for tok in o:
                if tok in n:
                    continue
                words = set(tok.split())
                if any(words <= s for s in new_sets):
                    absorbed.add(tok)

        for tok, cnt in sorted(o.items()):
            if tok in accepted or tok in absorbed:
                continue
            have = n.get(tok, 0)
            # Repetition is fair game to trim; disappearing entirely is not.
            if have == 0:
                losses.append((chan, tok, cnt, 0))
            elif have < cnt and chan in ("links", "names"):
                thin.append((chan, tok, cnt, have))
    return "changed", losses, thin


def main(argv):
    ref = argv[1] if len(argv) > 1 else "HEAD"
    if ref.startswith("-"):
        sys.stderr.write(__doc__)
        return 2
    targets = argv[2:]
    if not targets:
        # repo-relative, because these are resolved with `git show <ref>:<path>`
        targets = sorted(
            os.path.join(rel, f)
            for rel, absdir in ((cfg.CHRONICLE_REL, cfg.CHRONICLE),
                                (cfg.ENTITIES_REL, cfg.ENTITIES))
            for f in os.listdir(absdir)
            if f.endswith(".md"))
    else:
        targets = [os.path.relpath(os.path.abspath(t), ROOT) for t in targets]

    quiet = "--quiet" in argv
    targets = [t for t in targets if not t.startswith("-")]

    nchanged = nclean = 0
    total = nthin = 0
    for rel in targets:
        state, losses, thin = compare(ref, rel)
        if state is None:
            print("  ?? %s (not in %s — new file, nothing to compare)" % (rel, ref))
            continue
        if state == "unchanged":
            continue
        nchanged += 1
        nthin += len(thin)
        if not losses and (quiet or not thin):
            nclean += not losses
            continue
        print("\n%s" % rel)
        by = collections.defaultdict(list)
        for chan, tok, o, n in losses:
            by[chan].append((tok, o, n))
        for chan, _ in CHANNELS:
            if by[chan]:
                print("  %-8s %s" % (chan, ", ".join(
                    "%s(%d→%d)" % (t, o, n) for t, o, n in by[chan])))
        if thin and not quiet:
            print("  thin     %s" % ", ".join(
                "%s(%d→%d)" % (t, o, n) for _, t, o, n in thin))
        total += len(losses)
        nclean += not losses

    print("\nfactguard : %d file(s) changed vs %s, %d clean, %d loss(es), "
          "%d thinned" % (nchanged, ref, nclean, total, nthin))
    print("RESULT    : %s" % ("PASS" if total == 0 else "REVIEW"))
    return 0 if total == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
