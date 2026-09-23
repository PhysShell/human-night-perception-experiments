#!/usr/bin/env bash
# COMMON run of VSS: the frozen baseline's LDR display image of S7 (results/baseline/S7/S7_BASELINE.png,
# pcond LC -> sRGB 8-bit, 1920x820 at 32 px/deg) through the NEUTRAL/normal VSS configuration
# (no config = all simulation nodes at defaults = no impairment). VSS decodes inputs with image::to_rgba8()
# (vss/src/node/rgb_buffer/upload.rs l.133-141), i.e. it only accepts display-referred 8-bit input, so the
# LDR baseline is the compatible form of S7. No disease parameter is touched.
# VSS has no viewing-geometry input on the normal-eye path (lens node inactive, retina map identity), so
# display_targets.json values cannot be passed; recorded as not applicable.
set -euo pipefail
. "$(dirname "$0")/env.sh"
R=/home/user/human-night-perception-experiments; O=$R/results/common/vss; mkdir -p "$O"
T=$(mktemp -d); cp "$R/results/baseline/S7/S7_BASELINE.png" "$T/S7_BASELINE.png"
nice -n 10 "$VSS_BIN" render --force --verbose --output "$O/COMMON_{stem}.{config}.{extension}" "$T/S7_BASELINE.png" 2>&1 | tee "$O/common_run.log"
rm -rf "$T"
cd $R && nix develop -c oiiotool --diff results/baseline/S7/S7_BASELINE.png "$O/COMMON_S7_BASELINE.vss.png" 2>&1 | tee -a "$O/common_run.log" || true
