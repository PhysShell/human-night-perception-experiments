#!/usr/bin/env bash
# NATIVE runs of VSS (wgpu branch, commit 22055373) with BUNDLED presets on BUNDLED assets, headless via
# `vss-desktop render` on Mesa lavapipe. Outputs -> results/native/vss/NATIVE_<asset>.<preset>.png
set -euo pipefail
. "$(dirname "$0")/env.sh"
O=/home/user/human-night-perception-experiments/results/native/vss; mkdir -p "$O"
A=$VSS_SRC/assets; P=$VSS_SRC/vss-catalog/presets
run() { # $1 input, $2.. configs (may be empty => defaults = normal eye)
  local in=$1; shift
  local cargs=(); for c in "$@"; do cargs+=(--config "$c"); done
  nice -n 10 "$VSS_BIN" render --force --verbose "${cargs[@]}" \
     --output "$O/NATIVE_{stem}.{config}.{extension}" "$in" 2>&1 | tee -a "$O/native_run.log"
}
: > "$O/native_run.log"
run "$A/marketplace.png"                                   # default settings = normal eye (config name 'vss')
run "$A/shanghai-night.png"                                # normal eye
run "$A/shanghai-night.png" "$P/dysadaptation/dysadaptation-nyctalopia-severe.json"   # cf. doc/teaser-nyctalopia.jpg
run "$A/marketplace.png"    "$P/cataract/cataract-mild.json"
run "$A/marketplace.png"    "$P/cataract/cataract-severe.json"
run "$A/marketplace.rgbd.png" "$P/ametropia/ametropia-myopia-severe.json"
run "$A/marketplace.rgbd.png"                              # normal eye with depth
# identity check of the normal-eye path (input vs output)
cd /home/user/human-night-perception-experiments
for s in marketplace shanghai-night; do
  nix develop -c oiiotool --diff "$A/$s.png" "$O/NATIVE_$s.vss.png" 2>&1 | tee -a "$O/native_run.log" || true
done
# README teaser counterpart (doc/teaser-nyctalopia.jpg shows marketplace): bundled nyctalopia presets on marketplace
run "$A/marketplace.png" "$P/dysadaptation/dysadaptation-nyctalopia-severe.json"
run "$A/marketplace.png" "$P/dysadaptation/dysadaptation-nyctalopia-severe-from-map.json"
