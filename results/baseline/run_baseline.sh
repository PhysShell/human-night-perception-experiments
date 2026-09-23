#!/usr/bin/env bash
# BASELINE outputs of the frozen stack for the still stimuli of the common pack (label: BASELINE).
# Per stimulus: cd/m^2 EXR -> m1/pcond_colorimetric.sh LC (SCALE 1/179 = Radiance units,
# HFOV = width / 32 px/deg) -> PBR Neutral on out-of-gamut pixels (stills display) -> sRGB PNG.
# The image is formed at the stimulus's own resolution (32 px/deg; M2.6 order: display first).
#   nix develop -c results/baseline/run_baseline.sh
set -euo pipefail
CFG=$(ls "$(dirname "$(readlink -f "$(command -v blender)")")"/../share/blender/*/datafiles/colormanagement/config.ocio)
for S in S0 S1 S2 S3 S4 S5 S7; do
  d=results/baseline/$S; mkdir -p "$d"; t=$(mktemp -d)
  in=stimuli/pack/$S/$S.exr
  W=$(oiiotool --info "$in" | sed -E 's/.* : +([0-9]+) x.*/\1/'); HF=$(awk -v w=$W 'BEGIN{print w/32}')
  m1/pcond_colorimetric.sh "$in" "$HF" LC "$t/lc.hdr" 0.00558659 2>/dev/null
  getinfo < "$t/lc.pcond.hdr" | grep -E "EXPOSURE|VIEW" > "$d/pcond_header.txt" || true
  oiiotool "$t/lc.hdr" -o "$d/${S}_pcond_LC_displaylinear.exr"
  l="$d/${S}_pcond_LC_displaylinear.exr"
  oiiotool "$l" --maxchan --subc 1 --mulc 1e9 --clamp:min=0:max=1 --ch 0,0,0 -o "$t/oog.exr"
  oiiotool --colorconfig "$CFG" "$l" --iscolorspace "Linear Rec.709" --ociodisplay sRGB Standard -d uint8 -o "$t/std.png"
  oiiotool --colorconfig "$CFG" "$l" --iscolorspace "Linear Rec.709" --ociodisplay sRGB "Khronos PBR Neutral" -d uint8 -o "$t/pbr.png"
  oiiotool "$t/pbr.png" "$t/std.png" --sub "$t/oog.exr" --mul "$t/std.png" --add -d uint8 -o "$d/${S}_BASELINE.png"
  rm -rf "$t"; echo "$S: $(cat "$d/pcond_header.txt" | tr '\n' ' ')"
done
