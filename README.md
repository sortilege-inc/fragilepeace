# sortilege-vtt-l5r5e

A virtual tabletop for **Legend of the Five Rings, 5th Edition**, generated from the Titterpig
corpus `titterpig-dsl-l5r5e/0.5`: the books to read, the Roll & Keep dice, character creation
by the Twenty Questions, the GM's table for the sixteen published adventures, and live sessions
for players on their own devices.

- `/` — the site: the books, schools, techniques, NPCs, pregens, adventures, the lore, the dice,
  making a character, search. Writes nothing.
- `/gm/` — the GM's table: panels over the campaign, the map table (`gm/vtt.html`), the
  player's page (`gm/play.html`).

No build step for the pages; `data/` is generated:

```bash
bash build/build.sh
```

It parses every corpus file, writes `data/`, and gates the result both ways (every string the
corpus prints reaches the data as often as it is printed, and nothing in the data is not in the
corpus). The art is copied from the owner's Portents & Fortunes site by `bash build/build_art.sh`.

A campaign can run as an **instance** of this VTT — a fork that owns a `campaign/` folder and
never edits upstream. It declares its own scripts in `engine/config.js` (loaded by
`engine/instance.js`) and builds its homebrew as one more book, gated as the books are:

```bash
bash build/build_layer.sh campaign/dsl campaign "<its title>" campaign/data
```

Local: the launch entries `vtt-l5r5e` (8740) and `vtt-l5r5e-worker` (8792). See `PLAN.md` for
the milestones, the decisions and the proof of each, and its *Instances* section for the pattern.
