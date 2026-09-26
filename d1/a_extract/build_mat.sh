#!/usr/bin/env bash
# Builds and runs matscan_mat.c against the pinned Radiance source (same store path as the pcond binary) -> matscan_mat.txt
set -euo pipefail; cd "$(dirname "$0")"
SRC=/nix/store/rp1xsl3blq9wnnlm8hlscryarhk2jbka-source/src   # = source of the pcond binary in nix develop (radiance-6.0-unstable-2026-08-19, verified via its .drv)
mkdir -p .cache; cc -O0 -I"$SRC/common" matscan_mat.c "$SRC/common/spec_rgb.c" "$SRC/common/color.c" -lm -o .cache/matscan_mat 2>&1 | tail -5
.cache/matscan_mat | tee matscan_mat.txt; echo "radiance source: $SRC" > matscan_mat.src
cc -O0 -I"$SRC/common" clipgamut.c "$SRC/common/spec_rgb.c" "$SRC/common/color.c" -lm -o .cache/clipgamut 2>&1 | grep -i error || true
