# The Fragile Peace

A Legend of the Five Rings 5th Edition campaign — Emerald Magistrates sent to hold a ceasefire
between the Lion and the Unicorn, and what they found under the great willow at the City of the
Rich Frog.

The site is an **instance** of [`sortilege-vtt-l5r5e`](https://github.com/sortilege-inc/sortilege-vtt-l5r5e):
the VTT owns the root — the site, the GM's table, the player's page, the engine and the generated
books — and the campaign owns `campaign/`. The boundary, and how to pull upstream, are in
`~/Sortilege/VTT/INSTANCES.md`; this campaign's plan and decision log are in `campaign/PLAN.md`.

Live at **fragilepeace.sortilege.online**.

## The campaign

| | |
|---|---|
| `campaign/sources/chronicle/` | The session record, written from the recordings. Sessions 1–58. |
| `campaign/sources/entities/` | Entity pages the Archivist export never had. |
| `campaign/CORRECTION-PASS.md` | The audit log: every correction made against a recording, with its proof. |
| `campaign/REWRITE.md` | How the chronicle's voice is written. |

The five gates — `build_site`, `acceptcheck`, `factguard`, `voicecheck`, `verify_site` — must all
exit 0. `factguard` proves a rewrite lost no facts by diffing each source file against its
committed version, which is why `campaign/sources/` is versioned here rather than kept in the
support folder beside it.

## Running it

```bash
git config merge.ours.driver true   # once per clone; see .gitattributes
```

Launch `fragilepeace` (the site, port 8734) and `fragilepeace-worker` (`wrangler dev`, 8800).
