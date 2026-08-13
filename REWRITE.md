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
- **2026-08-13 — provenance moved out of the entity prose.** Every `sources/entities` page ended
  with some form of "Not in the Archivist export." — the site announcing its own machinery inside
  gazetteer prose, 36 times. `Page.local` is now set by `discover_local`, and the builder renders
  one meta line for any page carrying it. Recorded in `factguard.ACCEPT_ALL`.

## Bugs found while running the gates

Four, each of which was either hiding signal or already wrong on the live site.

- **`factguard` discounted sentence-initial names.** The opener heuristic assumed a name recurs
  mid-sentence somewhere; names appearing exactly once, at a sentence start, read as losses. It now
  discounts a sentence-initial capital only when the same word also appears in lower case in that
  file. The tighter rule surfaced 10 previously-masked losses — all of them the imperatives removed
  under the owner's `## Setsuna` call, each recorded in `ACCEPT` with the sentence it opened.
- **`factguard` split sentences on newlines.** The source is hard-wrapped mid-sentence, so any name
  landing at the start of a wrapped line was discounted. It flagged a false `Scorpion` loss in i47
  and would equally have masked a true one.
- **`voicecheck`'s italic pattern stopped at newlines,** so multi-line quoted speech read as
  unquoted and every *you* inside it flagged as address.
- **The chronicle index printed a broken date** — `"52 sessions, 2025-03 2025 to 2026-08 2026"`,
  a literal year appended to an already-formatted `YYYY-MM`. Fixed with `month_year()`. The same
  line promised a machine summary for "the rest" when the rest is zero; that clause is now
  conditional.

## Stale facts corrected on the home page

Overtaken by play, not by voice.

| Was | Now |
|---|---|
| "39 sessions, March 2025 to February 2026" | 52 and two interludes, to August 2026 |
| "Monban, Midori and Kazumi … and the six who walked part of it" | Tadayoshi is at the table; two off stage, three carried by memory |
| "Miya Misato **is** charged with brokering a peace" | she died of her wounds in s47; Setsuna carries it |
| "for her husband's freedom" | Harunobu was released in s48 |

## Order of work — complete

1. ~~factguard + s07 pilot~~ — `6494663`
2. ~~Sessions 1–17~~ — the road east and the Snow Plain flashback, `6494663`
3. ~~Sessions 18–39~~ — the courts, `25fae71`
4. ~~Sessions 40–52 and the two interludes~~ — the peace, `3a5b557`
5. ~~The 36 entity files~~ — `a61132c`
6. ~~`index.html` and the `build_site.py` blurbs~~ — `bab5382`
7. ~~`notes/index.html` audit~~
8. ~~Full gate~~

Final state: **91 files, 953 insertions, 951 deletions.** Bold went from 445 spans
to 50 — 190 of them were in `## Narrative`, and the six that remain are all `!note`
warning labels.

    factguard  : 89 changed vs 8133e1f, 89 clean, 0 losses, 0 thinned
    voicecheck : 85 flags, 0 hard
    verify     : links 23977/0 broken, masks 791/0, names 0,
                 rewrites 54/0 unresolved, span 52 sessions — PASS
    leak       : no table vocabulary in any rendered narrative

## Corrections made on the evidence of the record itself

Pronoun and name slips where the corpus contradicts itself and the weight of evidence settles it.
Anything the record does *not* settle goes to the open questions below instead.

- **Akodo Toronoko is "she."** Ikoma Akuyaku's wife, "she"/"her" in ten places across s13–s17.
  s11 had "a thin elite centre under his own hand". Corrected to hers.
- **Iuchi Minoru is "he."** The s28 body and its Learned entry are "he"/"his" throughout — *as a
  child he broke his grandmother's jade tea cup*. Only the epigraph read "she". Corrected.

## Resolved: Kaeru Haia → Kaeru Haya

**Owner's call, 2026-08-13: she is Kaeru Haya.** One line in `archivist.CORRECTIONS` does the whole
merge — `correct()` is applied to titles as well as prose, and `discover()` already collapses two
files that land on one title, so the export's `Kaeru Haia.md` and `Kaeru Haya.md` became a single
page carrying s30, s31 and s32.

Two things surfaced in the doing of it.

- **The merge was dropping a line.** `Ledger.learned` is keyed `{page: {session: line}}`, and s32
  carried a bullet under *each* spelling. Once both corrected to Haya, the second silently replaced
  the first and her "told the magistrates exactly what she thought of people who leave a spirit
  speaker alone at night" never reached the page. Folded into one bullet.
- **The same defect was already live, and older.** A scan for duplicate ledger keys found s26
  carrying two `Shosuro Aishi` bullets — one for the living advocate, one for the ancestor she is
  named for. The ancestor's was being dropped. Folded in as well.

`verify_site.py` grew a **`ledger`** check for it, proven on a planted duplicate. Nothing about
either case is visible in the built site except as an entry that is quietly missing, which is why
it went unnoticed.

- **And her pronouns disagreed across the two spellings.** s30 has "her people", s32 had "what he
  thought". The export settles it: its `Kaeru Haia.md` runs 12 *her* / 9 *she* against one *his*,
  and `Kaeru Haya.md` 9 *her* / 9 *she* against one *him*. She is a woman; s32's *he* was a slip
  and is corrected.

## Open questions for the owner

None outstanding.

## Split entity pages — all merged, 2026-08-13

**457 entity pages → 436.** Twenty-one collapsed. The scan is clean: no two pages now share a
normalised name, and nothing sits above 0.87 similarity that is not genuinely two things.

Three mechanisms, because the splits were three different faults.

- **`CORRECTIONS`** for misspellings, since `correct()` is applied to titles as well as prose and
  `discover()` merges what lands on one title: `Ikoma Aku Yaku`, `Slow Tide Harbor`,
  `Dran Merchant River`, `Asawa Family`, and the whole Shinjo Kamo cluster.
- **`RENAMES`** for pages that were correctly spelled but differently named — the export's literal
  `The Emperor (2).md` and `Asahina Nao (2).md`, the governor's residence under five names, the
  War College under short and full form, and the Diamond Mines under two.
- **`RECAT`**, new, for the cross-category pairs. `discover()` merges by `(cat, title)`, so a thing
  filed as both a person and a relic builds two pages no matter how the titles are corrected. The
  Ifrit was a person in `Characters` and a relic in `Items`; Shinjo Kamo was a person and a faction
  at once.

**Shinjo Kamo was the worst of them.** The Unicorn general at the Snow Plain, filed five ways —
twice as a person, once as a faction, and in the titles of his letters and his camp. The
`Characters` entry describes the commander unseated from his horse with his banner on the saddle,
which is what Morozane did to him in s17; the other describes the hand and the chop on the disputed
treaty. His page now carries s12, s16, s17 and s23 instead of one line each on four pages.

**`SUPERSEDED_BY_LOCAL`**, also new. Correcting `Asawa Family` to `Isawa Family` made the export's
machine prose collide with the hand-authored page, and the builder's rule is that the export wins.
That rule is right for an accidental collision and wrong when the export entry is a misspelling of a
real family and the local page is the corrected one in the house voice. The one substantive fact
from the export entry — the Isawa as the Phoenix shugenja family, their work the balance of the five
and the tending of the kami — is folded into the local page, and the export file is suppressed.

Also untracked `scripts/__pycache__`, which was committed and kept colliding on checkout.

## Superseded — the original survey

Not part of the voice rewrite and not touched by it. A sweep for near-identical page titles across
the 457 generated entity pages turned up one entity built as two pages, each holding half its
record. Each needs a `CORRECTIONS` entry and a `RENAMES` merge; several need the owner to say which
spelling is right.

| Built as | And as | Note |
|---|---|---|
| `dramatis-personae/kaeru-haia` | `kaeru-haya` | Same rōnin watch commander. Spelling unsettled — see above. |
| `dramatis-personae/ikoma-aku-yaku` | `ikoma-akuyaku` | Spacing only. |
| `dramatis-personae/asahina-nao` | `asahina-nao-2` | The `-2` is the builder disambiguating a title collision. |
| `dramatis-personae/the-emperor` | `the-emperor-2` | Same. |
| `atlas/slow-tide-harbor` | `slowtide-harbor` | Spacing only. |
| `lore/relics/shinjo-kamu-letters` | `shinjukamu-letters` | Spacing only. |
| `atlas/dran-merchant-river` | `drowned-merchant-river` | "Dran" is a truncation. |
| `atlas/governors-manor` | `governors-mansion` | |
| `lore/factions/asawa-family` | `isawa-family` | "Asawa" is not a family. |
| `atlas/war-college` | `atlas/akodo-war-college` | Short form and full, plus a third copy under `lore/factions`. |
| `atlas/akodo-war-college` | `lore/factions/akodo-war-college` | Same institution filed as both place and faction. |
| `atlas/diamond-mines` | `lore/relics/diamond-mines` | Same. |
| `dramatis-personae/ifrit` | `lore/relics/the-ifrit` | The spirit and its vessel, or one thing filed twice. |
| `dramatis-personae/shinjuku-kamu` | `lore/factions/shinjuku-kamu` | And "Shinjuku Kamu" is itself a garbling of **Shinjo Kamo** — the Unicorn general at the Snow Plain. The Shinjukamu Letters are his. |

Deliberately excluded as genuinely distinct: Phoenix Clan/Phoenix Lands, Scorpion Clan/Scorpion
Lands, Unicorn Clan/Unicorn Lands, Centipede Clan/Centipede Lands, Daidoji Family/Doji Family,
Dragon Clan/Dragonfly Clan, Akodo Osakuan/Akodo Sakura, Matsu Tsuki/Matsu Tsuko, Shosuro
Akio/Shosuro Imako, Koji/Kojin.
