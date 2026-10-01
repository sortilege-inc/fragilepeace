# The Fragile Peace × sortilege-vtt-l5r5e — plan and decision log

A **Legend of the Five Rings 5th Edition** campaign — Emerald Magistrates through a Lion/Unicorn
war and what is under the great willow — rebuilt as an **instance** of `sortilege-vtt-l5r5e`. The
process is `~/Sortilege/VTT/INSTANCES.md`; Portents & Fortunes is the reference instance on this
VTT and The Bushi Oni the second.

Status words: **PROPOSED** (awaiting the owner), **(owner)** decided, **landed** built and proven.

## Where things are

| What | Where |
|---|---|
| This repo | `sortilege-inc/fragilepeace`, **PUBLIC**; `~/Sortilege/Campaigns/2025 The Fragile Peace/fragile-peace`; live at `fragilepeace.sortilege.online` |
| Upstream | `sortilege-inc/sortilege-vtt-l5r5e` (private), to be added as remote `upstream` |
| Support folder | `../fragile-peace-support/` — never in the repo. `archive/{recordings,transcriptions,foundry-export,obsidian-export}`, `scripts/`, `doji-setsuna/`, `site.config.json` |
| Dev | launch `fragilepeace` (python http.server, 8734). A Worker launch is added at deploy |
| Work branch | `vtt-instance`; `main` is fast-forwarded to it at deploy |

### What the campaign already has

| Thing | Shape | Count |
|---|---|---|
| The site | **generated** by `fragile-peace-support/scripts/build_site.py` from `sources/` + the Archivist export | 509 pages |
| Chronicle | `sources/chronicle/*.md`, hand-written from the recordings, sessions 1–58 + 2 interludes | 60 files |
| Entities | `sources/entities/*.md` local + 543 export files, merged by `archivist.py` | 191 NPC, 12 PC, 142 place, 57 faction, 39 relic, 3 document |
| Playable sheets | `play/*.html` on a bespoke engine (`sheet.js`, `sheet.css`, `l5rdata.js`), built by 5 scripts + `doji-setsuna/` | 6 characters |
| Hand-authored pages | `index.html`, `character/` (5), `notes/`, `map/`, `rokugan.css` | |
| Gates | `build_site`, `acceptcheck`, `factguard`, `voicecheck`, `verify_site` — all exit 0 | 5 |
| Foundry actors | 6 `character` + 3 `npc` (Khar Baatar, Kurige, the manifest water kami); Setsuna's in `doji-setsuna/build/sources/` | 9 |

## Decisions

**F1 — Visibility: public, and the books publish with it (owner, 2026-09-29, by reference).**
The instruction was a merged site *"similar to Portents & Fortunes, or the Bushi Oni"*, and both
are PUBLIC instances of this VTT carrying its `data/` — 32 files, 12 MB of L5R5e books, verbatim.
`fragilepeace` is already PUBLIC, so the first push of the merge is the point of publication and
cannot be taken back from git history. Flagged rather than assumed: **stop here if that is not
intended.** The family default `siteBooks: false` still applies — the books' tabs stay off the
public site (PLAYBOOK §4b.4).

**F2 — The six sheets port onto the VTT sheet; `play/` retires (owner, 2026-09-29).**
Chosen over keeping the bespoke engine or running both. Each character goes onto the VTT's sheet
from `ACTOR Samurai`, every version checked field by field against the sheet it replaces, and the
five builders in `fragile-peace-support/scripts/` become one-way converters kept for provenance.
This is the largest milestone and the one with the most ways to lose a fact quietly — the field
check is the gate, not the build succeeding.

**F3 — Run: plan, fork, integrate; stop before deploy (owner, 2026-09-29).**
Work through M0–M6 to a site that runs locally. The Worker, Pages and HTTPS are a separate step
the owner confirms.

**F4 — The content moves by rebuilding it, not by scraping it. PROPOSED (M5 depends on it).**
INSTANCES.md step 5 says move the old pages rather than rewrite them, because Portents' pages were
hand-authored HTML. Fragile Peace's are **generated**: 509 pages built from 60 chronicle files and
56 local entity files by `build_site.py`. Scraping its own output back into `campaign/docs/` would
put a lossy round-trip between the source and the page for no gain.
*Proposal:* retarget `build_site.py` to emit into `campaign/docs/`, drop the nav/footer chrome the
VTT supplies, and keep `sources/` where it is so `factguard` keeps its git history. The proof is
the same one the playbook asks for — text identical to the old region, every link resolving —
run as a diff of old output against new before anything is deleted.

**F5 — `scripts/` comes into the repo. Landed 2026-09-29.**
The builders and all five gates live in the unversioned support folder, which has been a known gap
for months. An instance that cannot rebuild its own content from a clone is not finished. Moved `fragile-peace-support/scripts/` to `campaign/source/` and `site.config.json` to
`campaign/`, leaving `archive/` (raw recordings, the Archivist export, Foundry dumps) and
`doji-setsuna/` outside. The config now splits two things the fork made different: `output_repo`
is the **git** root, because `factguard` resolves old versions with `git show <ref>:<path>` and
those paths are repo-root-relative; the new `site_root` is where pages are written and crawled
beneath it. The support-folder copies were deleted afterwards so nothing can drift — all five
gates were re-run with them gone. Setsuna's generator stays in the support folder and reaches the
shared config where it now lives.

**F6 — The homebrew layer is the cast, and only the cast. Characters landed 2026-09-29.**
There are no campaign statblocks in the chronicle and no house rules on record. `campaign/dsl/`
gets the characters and the 3 companions, as instances of the system's actor; NPCs stay prose on
their entity pages until one of them needs numbers. Sheet records in `campaign/source/` byte for
byte, checked every version.

Landed for the characters: 6 sheets and 2 archived versions. Two things the conversion turned up
that were not in the plan —

- **One homebrew item.** *Voice of Authority*, a signature scroll on Setsuna's sheet with no source
  book, so the corpus cannot be asked for it. Carried as its own entity in the layer, rules text
  read out of the export rather than retyped.
- **An owner ruling that existed only in code.** Harunobu's +6 glory award lived in the retiring
  sheet builder and nowhere else; the export still reads 49. Converting without noticing would have
  published 49 and lost it. `OWNER_RULINGS` now carries it as the arithmetic, self-retiring.

Landed for the companions too: Khar Baatar, Kurige and the manifest water kami, as instances of
the corpus's `^"NPC"` in exactly the property set its own 149 statblocks use, with a
`^"Companion Of"` reference to the character each belongs to — the one thing the retiring sheets
showed that the corpus's shape has nowhere to put. **69 fields compared, 0 differ**, three planted
differences each caught. The check found a real loss on the way: Khar Baatar's Foundry `notes` say
*Moto Charger.* — his breed, and not a Rokugani pony — which the first draft dropped. It now leads
his description.

**Corrected 2026-09-29 (owner):** *Voice of Authority* is not homebrew and not a signature scroll.
It is the `TITLE_ABILITY` of the corpus's Emerald Magistrate, word for word, and Foundry types the
item wrongly. It is skipped as a title ability like any other — but only once the sheet is shown to
hold the title that grants it, proven by removing that title and watching the conversion refuse.
The invented entity the first pass created is gone.

**Not in the layer at all:** Shiba Midori and Bayushi Monban. They are other players' characters and
no export of either is in this campaign's archive; `convert_cast.MISSING` names them so the absence
is stated rather than noticed later.

**F7 — Worker `fragile-peace`, origin `fragilepeace.sortilege.online` + the github.io behind it.**
At deploy, not before.

**F8 — Upstream I20 merged (owner, 2026-10-01: "merge the fix into the Bushi Oni instance too and fragile peace").**
The GM Inspector's party sheet without its duplicated blocks (`f39afa9`, from Portents' decision 80): the
live sheet's own blocks, then only the skills, advantages, the rest of the gear and the biography folded;
one GM-notes heading; versions oldest first. Client files only, so no Worker redeploy. Proven headless
through the real controls on this repo. Setsuna can't be the test character, because the campaign layer
isn't wired into `instance.stages` yet (M5). The core pregen Ide Yuina stood in. The pre-merge tree
(`51b5df9`) failed 5 checks: a second ring row; a second header, type line, stats and technique list; no
fold; versions newest first; and her advantages, which she has none of. The merged tree passed 13 of 13,
with 0 console errors.

## Milestones

| | What | Proof |
|---|---|---|
| **M0 landed** | This plan; owner's answers on F1–F3 | — |
| **M1 landed** | **The fork.** Three commits on `vtt-instance`: `git mv` everything under `campaign/`; merge `upstream/main` with `--allow-unrelated-histories`; the boundary files + `.gitattributes` + the driver | 697 files `R100`, 0 insertions, 0 deletions. Merge: no collisions. Boundary proven by making it fail first — without the driver, `CONFLICT … engine/config.js`, exit 1; with it, exit 0, config keeps *The Fragile Peace* and the upstream-owned file takes its change |
| **M2 landed** | **The gates keep working** from the new paths — all five exit 0 with `sources/` under `campaign/` All five exit 0 from `campaign/source/`, and `build_site` rewrote the 509 pages **byte-identically** after the move — zero changed files. `factguard` proven still to read git at the new path by planting a cut and watching its counts drop |
| **M3 landed** | **The cast into `campaign/dsl/`** | 8 sheets, **336 fields compared, 0 differ** (`check_cast.py`, reading the BUILT layer back against the exports). Three planted differences each caught, exit 1. Layer gated three ways by `build_layer.sh`: 401 strings 0 uncovered, 9 ids none the corpus's, every reference resolving |
| **M4** | **The characters onto the VTT sheet**; `play/` deleted | Every version of every character checked against its old sheet |
| **M5** | **The content into tabs** — `build_site.py` retargeted, stylesheet scoped to its element, tabs pushed at the `site` stage, the cast page rebuilt on the DSL layer keeping its storage keys | Old output vs new, text-identical; every link resolves; no `:root`/`body` rule escaping into the VTT |
| **M6** | **The GM's material** into `campaign/pack/seed.json`; `/gm/` gate, `ownAdventure`, `hidePanes`, robots | The family standards checked in the browser on :8734 |
| **M7** | **Deploy** — owner's step, not taken here | — |

## Open questions for the owner

1. **F4, F5, F6** above — each is a PROPOSED with a recommendation.
2. **What is the arc?** `ownAdventure.title` names the campaign's own adventure. *The Fragile Peace*
   unless there is a better name for the current arc.
3. **The `/gm/` gate wording.** Portents and Bushi Oni each have their own veil text.
4. **Is there GM-only material?** The Bushi Oni built its GM pack outside the public repo because
   players could read the solution off GitHub. Nothing in this campaign's `sources/` is secret —
   the chronicle is written for the table — but `notes/` and the support folder have not been
   audited for it.
