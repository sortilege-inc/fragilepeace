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
           linked.
  numbers  digits and the spelled numerals one..twelve, plus ordinals. Concrete
           scale is load-bearing in this voice and is the easiest thing to
           smooth away.
  quotes   *italicised speech* — what somebody actually said, reduced to a
           content-word fingerprint so rewrapping and re-punctuating are free
           but rewording is not.

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

import os, re, io, sys, subprocess, unicodedata, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Tokens accepted everywhere, for a reason that is the same in every file. Use
# this only when the loss is one editorial decision applied across a whole
# surface; anything file-specific belongs in ACCEPT below, where it can be read
# against the file it applies to.
ACCEPT_ALL = {
    "archivist": "2026-08-13: every sources/entities page ended with some form "
                 "of 'Not in the Archivist export.' — the site announcing its "
                 "own machinery inside gazetteer prose, 36 times over. The "
                 "provenance is real and worth keeping, so it moved out of the "
                 "entries and into one meta line the builder renders for any "
                 "page flagged Page.local. No information lost; one voice "
                 "violation removed.",
}

# Losses that were looked at and accepted, keyed by file basename. Each entry is
# (token, reason). Nothing goes in here without a reason a reader can check.
ACCEPT = {
    # The owner's 2026-08-13 call on the ## Setsuna register: keep every
    # conclusion, drop the imperatives. Each of these is the capitalised opening
    # verb of an instruction to the reader, and each lost its capital rather
    # than its content — "Ask before the delegations sit down" became "the
    # asking should happen before the delegations sit down", and so on.
    "s02-loyalty-castle.md": [
        ("assume", "opened 'Assume from here that she is not on any list…'"),
    ],
    "s08-whispers-of-the-ancestors.md": [
        ("note", "opened 'Note the technique.'"),
        ("whether", "opened 'Whether it also told Kitsu Takeko where the "
                    "pressure goes is a question worth holding.'"),
    ],
    "s13-winters-wrath.md": [
        ("hold", "opened 'Hold that against Shoshuro Amane at the parley.'"),
    ],
    "s19-negotiations-and-hidden-truths.md": [
        ("watch", "opened 'Watch for them trying to hold the offer without "
                  "paying for it.'"),
    ],
    "s25-court-of-competing-claims.md": [
        ("read", "opened 'Read it either way and it is worth knowing which'"),
    ],
    "s43-the-midnight-treaty.md": [
        ("deploy", "opened 'Deploy it last, when it will land, not first.'"),
    ],
    "s48-the-stone-in-the-shoe.md": [
        ("ask", "opened 'Ask before the delegations sit down, not after.'"),
    ],
    # Owner 2026-08-13: Kaeru Haia and Kaeru Haya are one woman, merged onto
    # Haya. Both spellings had a bullet in s32, and the ledger keys by session,
    # so one was silently overwriting the other on her page. Folded into one.
    "s32-spirits-and-shadows.md": [
        ("kaeru haia", "merged into Kaeru Haya on the owner's call; her s32 "
                       "bullet is now the second half of Haya's."),
        ("haia", "same merge."),
    ],
    # The same defect, found by the scan the merge prompted and older than it:
    # s26 carried two Shosuro Aishi bullets, one for the living advocate and one
    # for the ancestor she is named for. The ancestor's was being dropped.
    "s26-court-of-ancestral-shadows.md": [
        ("note", "opened 'Note that this is the second time this week…'"),
        ("shoshuro aishi", "the duplicate ledger key. Its content — that the "
                           "ancestor manifested in the courtroom alongside "
                           "Ikoma Akuyaku — is folded into the surviving "
                           "Shosuro Aishi bullet, which previously overwrote it."),
        ("manifested", "still present, in lower case, inside that folded "
                       "sentence. The capitalised form now reads as a sentence "
                       "opener and is discounted."),
    ],
    "s51-matters-of-fact.md": [
        ("west", "was the bold section label '**West.**'. The scene keeps its "
                 "place and its opening now reads 'Far to the west, …', so the "
                 "word survives in lower case."),
    ],
    "s04-the-duel.md": [
        ("empire", "Only occurrence was the narrator's aside on Monban's trade of "
                   "honour for contempt — 'which is the sort of trade the Empire "
                   "makes constantly'. An opinion about the setting, not a fact "
                   "about the session."),
    ],
}

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


def f_names(t):
    t = strip_markup(t)
    # The source is hard-wrapped mid-sentence, so a line break is not a sentence
    # break. Join wrapped lines before splitting, or a name that happens to land
    # at the start of a line gets discounted as a sentence opener and reads as a
    # loss. Blank lines stay: those are real paragraph breaks.
    t = re.sub(r"(?<!\n)\n(?!\s*\n)", " ", t)
    # Ordinary words that this text also uses in lower case. A capital at the
    # start of a sentence is only evidence of a name if the word is never seen
    # uncapitalised — otherwise it is just a sentence beginning.
    lower = {w for w in re.findall(r"\b[a-zà-ɏ'’-]+\b", t)}

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
    for m in ITAL_RE.findall(strip_markup(t)):
        words = [w for w in norm(m).split() if w not in STOP and len(w) > 2]
        if len(words) >= 2:
            got[" ".join(sorted(set(words)))[:120]] += 1
    return got


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
    for chan, fn in CHANNELS:
        o, n = fn(old), fn(new)
        for tok, cnt in sorted(o.items()):
            if tok in accepted:
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
        targets = sorted(
            os.path.join("sources", d, f)
            for d in ("chronicle", "entities")
            for f in os.listdir(os.path.join(ROOT, "sources", d))
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
