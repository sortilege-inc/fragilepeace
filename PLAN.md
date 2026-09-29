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

**F4 — The content moves by rebuilding it, not by scraping it. PROPOSED.**
INSTANCES.md step 5 says move the old pages rather than rewrite them, because Portents' pages were
hand-authored HTML. Fragile Peace's are **generated**: 509 pages built from 60 chronicle files and
56 local entity files by `build_site.py`. Scraping its own output back into `campaign/docs/` would
put a lossy round-trip between the source and the page for no gain.
*Proposal:* retarget `build_site.py` to emit into `campaign/docs/`, drop the nav/footer chrome the
VTT supplies, and keep `sources/` where it is so `factguard` keeps its git history. The proof is
the same one the playbook asks for — text identical to the old region, every link resolving —
run as a diff of old output against new before anything is deleted.

**F5 — `scripts/` comes into the repo. PROPOSED.**
The builders and all five gates live in the unversioned support folder, which has been a known gap
for months. An instance that cannot rebuild its own content from a clone is not finished. Move
`fragile-peace-support/scripts/` to `campaign/source/`, leaving `archive/` (raw recordings, the
Archivist export, Foundry dumps) and `site.config.json` outside as they are.

**F6 — The homebrew layer is the cast, and only the cast. PROPOSED.**
There are no campaign statblocks in the chronicle and no house rules on record. `campaign/dsl/`
gets the 6 PCs and the 3 companions, as instances of the system's actor; NPCs stay prose on their
entity pages until one of them needs numbers. Sheet records in `campaign/source/` byte for byte,
checked every version.

**F7 — Worker `fragile-peace`, origin `fragilepeace.sortilege.online` + the github.io behind it.**
At deploy, not before.

## Milestones

| | What | Proof |
|---|---|---|
| **M0** | This plan; owner's answers on F4–F6 | — |
| **M1** | **The fork.** Three commits on `vtt-instance`: `git mv` everything under `campaign/`; merge `upstream/main` with `--allow-unrelated-histories`; the boundary files + `.gitattributes` + the driver | Move commit is `R100` only, 0 insertions, 0 deletions. Boundary proven by making it fail first in a throwaway clone |
| **M2** | **The gates keep working** from the new paths — all five exit 0 with `sources/` under `campaign/` | Five exit codes, before any content change |
| **M3** | **The cast into `campaign/dsl/`**, piloted on one character field by field including a planted difference that must fail, then the rest | Per-character field check vs the retiring sheet; layer gated three ways by `build_layer.sh` |
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
