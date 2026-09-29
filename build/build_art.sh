#!/usr/bin/env bash
# Regenerate assets/art/ from the owner's L5R art (the Portents & Fortunes campaign site,
# owner's call 2026-09-23: "you can use the icons, etc from … 2026 Portents & Fortunes").
# Copies, never edits: the Roll & Keep dice faces (keyed by their symbols — ring_ot is a ring
# die showing (op) (st)), the five ring glyphs, the eight clan mon, the favicon, and the map of
# Rokugan (offered to the table as a map). Regenerate, never hand-edit.
#
#   bash build/build_art.sh [<path to the art: portents-and-fortunes/campaign/assets>]
#
# Portents & Fortunes is itself an instance of this VTT now (PLAN.md, "Instances"), so its art
# lives under its campaign/ folder.
set -euo pipefail
cd "$(dirname "$0")/.."
SRC="${1:-$HOME/Sortilege/Campaigns/2026 Portents & Fortunes/portents-and-fortunes/campaign/assets}"
OUT=assets/art
rm -rf "$OUT"
mkdir -p "$OUT/dice" "$OUT/rings" "$OUT/mon"
cp "$SRC"/dice/*.svg "$OUT/dice/"
cp "$SRC"/rings/*.svg "$OUT/rings/"
cp "$SRC"/mon/*.svg "$OUT/mon/"
cp "$SRC"/favicon.svg "$OUT/favicon.svg"
cp "$SRC"/rokugan-map.webp "$OUT/rokugan-map.webp"
{
  echo "Copied by build/build_art.sh from $SRC on $(date -u +%Y-%m-%d); do not edit."
  (cd "$OUT" && find . -type f ! -name PROVENANCE.txt | sort | xargs sha256sum)
} > "$OUT/PROVENANCE.txt"
echo "build_art: $(find "$OUT" -type f ! -name PROVENANCE.txt | wc -l) files → $OUT"
