#!/usr/bin/env python3
"""
voicecheck.py — find the house style's known failure modes in the chronicle.

    python3 scripts/voicecheck.py [path ...]

`.claude/skills/rokugan-voice/SKILL.md` names the anti-patterns this project
actually produces. Most of them are not mechanically detectable — whether an
image is earned is a judgement. These five are, or are close enough that a
short list of candidates beats reading 76,000 words looking for them.

  2nd-person   you / your / we / our outside quoted speech. World-facing prose
               does not know the reader exists. A hard error.
  bold-narr    ** ** inside ## Narrative. Owner's call, 2026-08-13: emphasis is
               carried by sentence structure there. A hard error.
  wink         a trailing "which is/was …" clause of the kind the skill tells us
               to strip — the narrator nudging the reader after the fact has
               already landed. Advisory: some are genuine consequence clauses,
               which the voice wants. Read them.
  theme        the narrator announcing significance — "everything worth knowing",
               "the thing to keep", "note that", "worth noting". Advisory.
  hedge        perhaps / maybe / somewhat / rather a lot, used to sound careful.
               The skill allows hedging only by attributing a claim. Advisory.

Exit codes: 0 no hard errors, 1 hard errors found.
"""

import os, re, io, sys, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECOND = re.compile(r"\b(you|your|yours|yourself|we|we're|our|ours|us)\b", re.I)
BOLD = re.compile(r"\*\*[^*]+\*\*")
ITAL = re.compile(r"(?<!\*)\*(?!\*)[^*\n]+\*(?!\*)")

WINK = re.compile(
    r",\s*(?:and\s+)?which\s+(?:is|was|are|were)\b[^.]*\.", re.I)
THEME = re.compile(
    r"\b(everything worth knowing|the thing to keep|worth noting|note the\b|"
    r"note that\b|is the thing to|the whole of the (?:point|evidence)|"
    r"which is the point|that is the (?:single )?most important)\b", re.I)
HEDGE = re.compile(r"\b(perhaps|maybe|somewhat|arguably|it seems|some might)\b", re.I)

HARD = ("2nd-person", "bold-narr")


def sections(t):
    out, cur, buf = {}, "front", []
    _, _, rest = t.partition("\n---\n")
    for line in rest.splitlines():
        h = re.match(r"^## (.+)$", line)
        if h:
            out[cur] = "\n".join(buf)
            cur, buf = h.group(1).strip(), []
        else:
            buf.append(line)
    out[cur] = "\n".join(buf)
    return out


def outside_quotes(text):
    """The text with *italicised runs* blanked, so dialogue is exempt."""
    return ITAL.sub(lambda m: " " * len(m.group(0)), text)


def scan(path):
    t = io.open(path, encoding="utf-8").read()
    secs = sections(t)
    hits = []
    narr = secs.get("Narrative", "")

    for m in SECOND.finditer(outside_quotes(narr + "\n" + secs.get("Setsuna", ""))):
        hits.append(("2nd-person", m.group(0), context(narr, m)))
    for m in BOLD.finditer(narr):
        hits.append(("bold-narr", m.group(0)[:50], ""))
    for name, rx in (("wink", WINK), ("theme", THEME), ("hedge", HEDGE)):
        for m in rx.finditer(outside_quotes(narr + "\n" + secs.get("Setsuna", ""))):
            hits.append((name, m.group(0)[:90].replace("\n", " "), ""))
    return hits


def context(text, m):
    s = max(0, m.start() - 45)
    return text[s:m.end() + 30].replace("\n", " ").strip()[:90]


def main(argv):
    targets = argv[1:] or sorted(
        glob.glob(os.path.join(ROOT, "sources", "chronicle", "*.md")))
    nhard = ntot = 0
    for path in targets:
        hits = scan(path)
        if not hits:
            continue
        print("\n%s" % os.path.relpath(path, ROOT))
        for kind, txt, ctx in hits:
            mark = "!!" if kind in HARD else "  "
            print("  %s %-11s %s%s" % (mark, kind, txt, (" | " + ctx) if ctx else ""))
            nhard += kind in HARD
            ntot += 1
    print("\nvoicecheck: %d flag(s), %d hard" % (ntot, nhard))
    print("RESULT    : %s" % ("PASS" if nhard == 0 else "FAIL"))
    return 0 if nhard == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
