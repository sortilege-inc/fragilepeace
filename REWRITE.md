# Voice rewrite — state of play

Started 2026-08-13. Every word of authored prose on this site is being rewritten against
`.claude/skills/rokugan-voice/SKILL.md`. The skill existed before the chronicle was written and
was not used; the prose drifted into a wry, aphoristic register that the skill names as its
principal anti-patterns. **Facts do not change. Only the voice does.**

Pre-rewrite commit: **8133e1f**. That is the reference every fact check runs against.

## The gate

    python3 scripts/factguard.py 8133e1f            # every source file
    python3 scripts/factguard.py 8133e1f sources/chronicle/s07-*.md

`factguard.py` compares each source file to its committed version and fails on any *fact token*
that the old text carried and the new one does not: `[[wikilinks]]`, capitalised names, numbers,
italicised speech, and the subject keys of the `## Learned` list. It also prints a non-failing
`thin` line for names whose count merely drops, because a clause carrying a fact about somebody
mentioned five other times disappears exactly there and nowhere else.

A loss is not automatically wrong — merged sentences legitimately shed a repeat. The gate's job is
to make each one a decision somebody looked at. Accepted losses go in `ACCEPT` with a reason.

Full gate before commit:

    python3 scripts/factguard.py 8133e1f && python3 scripts/build_site.py && python3 scripts/verify_site.py

## What is in scope

Measured against the site's own enumerable sets, not against what gets built.

| Surface | Units | Words | State |
|---|---|---|---|
| `sources/chronicle/*.md` | 54 files (52 sessions + 2 interludes) | 76,065 | 1 done |
| `sources/entities/*.md` | 36 files | 1,708 | |
| `notes/index.html` | 1 file, own register | 6,238 | |
| `index.html` | 1 file | 345 | |
| `scripts/build_site.py` blurbs | ~10 literals + panel explainers | ~400 | |

Each chronicle file carries an `epigraph`, a `!lede`, `## Narrative`, `## Learned` (374 bullets
across the corpus), and `## Setsuna`.

**Out of scope, by the skill's own register map:** `character/setsuna.html` (the dossier, carried
over unedited — "do not rewrite its prose"), `play/` and `map/` (mechanical and furniture), and all
rules text anywhere, which is verbatim from the L5R5e corpus.

## The diagnosis

Five habits, all of them named in the skill's anti-patterns.

1. **Explaining the theme.** *Everything worth knowing about the ambush on the Emperor's Road is in
   that sentence.* The prose tells the reader what a scene means instead of letting the scene mean it.
2. **The wink.** *…which by then was not news* · *…which was the more effective of the two arguments*
   · *…which is the correct use of a pony whose rider has already been taken.* The skill's rule: if a
   line would work with a wink, remove the wink.
3. **Bold as underline.** 445 bold spans across 54 files, marking what the reader is to find
   important. Same instinct as (1), in typography.
4. **`## Setsuna` drifting into advice.** *So when she wakes she should put it to both commanders…*
   That is the Player Notes register wearing chronicle clothes. The chronicle may render her
   reasoning; it should not instruct her.
5. **Epigraphs that state a moral** rather than record an observation.

## Decisions taken

Recorded as they are made, per the working agreement.

- **2026-08-13 — the gate.** Built `factguard.py` rather than trusting a read-through. Proven on a
  planted three-way loss (dropped clause, softened number, deleted ledger bullet): caught all three.
- **2026-08-13 — rewrite in place, not from transcripts.** The facts are already settled in
  `sources/`; re-deriving them from transcripts would re-open decided questions and risk drift.
- **2026-08-13 (owner) — `## Setsuna` renders her reasoning, not instruction.** Every conclusion
  is kept; the imperatives go. What she worked out, not what she ought to do. Directive framing
  already has a home in Player Notes, which is its proper register.
- **2026-08-13 (owner) — no bold in `## Narrative`.** Emphasis is carried by sentence structure.
  Bold stays rationed in `## Setsuna` for genuine turning points, and untouched in Player Notes,
  where scanning is the point.
- **2026-08-13 (owner) — s07 "twice her business" was "twice her size."** Restored as a physical
  mismatch; the phrase is no longer an open question.

## Order of work

1. ~~factguard + s07 pilot~~ — done, awaiting voice sign-off
2. Sessions 1–17 — the road east and the Snow Plain flashback
3. Sessions 18–39 — the courts
4. Sessions 40–52 and the two interludes — the peace
5. The 36 entity files
6. `index.html` and the `build_site.py` blurbs
7. `notes/index.html` audit
8. Full gate, commit, push

## Open questions for the owner

None outstanding. Anything the rewrite cannot resolve from the existing record is raised here
rather than guessed at.
