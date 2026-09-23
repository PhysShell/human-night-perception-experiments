#!/usr/bin/env bash
# T2 golden-image regression (model: Blender's own render tests, tests/python/modules/
# render_report.py: reference / new / diff, idiff-style thresholds).
#
#   t2/golden.sh check  [outdir]   render + compare against t2/golden/   (exit 1 on failure)
#   t2/golden.sh update            re-render and overwrite t2/golden/     (deliberate changes only)
#
# Canonical renders: the real scene (m1/scene.py, T2_VIEW=golden: full 60 deg view at 320x137,
# 128 spp, fixed seed) for vacuum / clear / mild, each also through the frozen M1.1 stack
# (pcond_colorimetric.sh LC + stills display: PBR Neutral on out-of-gamut pixels only).
# Two comparisons per case:
#   scene.exr (cd/m^2)  : a pixel fails if |d| > 1e-4 cd/m^2 AND |d|/ref > 5 %; <= 1 % may fail
#   display.png         : Blender's render-test defaults: --fail 0.016 --failpercent 1
# 'moderate' is not a golden case (single-scattering issue, see m2/README.md section 5).
set -euo pipefail
MODE=${1:-check}; OUT=${2:-t2/out/golden}; REF=t2/golden
mkdir -p "$OUT"
CFG=$(ls "$(dirname "$(readlink -f "$(command -v blender)")")"/../share/blender/*/datafiles/colormanagement/config.ocio)
view() { oiiotool --colorconfig "$CFG" "$1" --iscolorspace "Linear Rec.709" --ociodisplay sRGB "$2" -d uint8 -o "$3"; }
render() { # case -> $OUT/<case>_scene.exr (cd/m^2, half) and $OUT/<case>_display.png
  local a=$1
  T2_VIEW=golden blender -b --factory-startup --python m1/scene.py -- "$OUT/raw_$a.exr" 128 "$a" > "$OUT/render_$a.log" 2>&1
  oiiotool "$OUT/raw_$a.exr" --ch R,G,B --mulc 179 -d half --compression zip -o "$OUT/${a}_scene.exr"
  m1/pcond_colorimetric.sh "$OUT/raw_$a.exr" 60 LC "$OUT/lc_$a.hdr" 1
  oiiotool "$OUT/lc_$a.hdr" -o "$OUT/lc_$a.exr"
  oiiotool "$OUT/lc_$a.exr" --maxchan --subc 1 --mulc 1e9 --clamp:min=0:max=1 --ch 0,0,0 -o "$OUT/oog_$a.exr"
  view "$OUT/lc_$a.exr" Standard "$OUT/std_$a.png"
  view "$OUT/lc_$a.exr" "Khronos PBR Neutral" "$OUT/pbr_$a.png"
  oiiotool "$OUT/pbr_$a.png" "$OUT/std_$a.png" --sub "$OUT/oog_$a.exr" --mul "$OUT/std_$a.png" --add \
    -d uint8 -o "$OUT/${a}_display.png"; }
compare() { # ref new kind
  if [ "$3" = scene ]; then idiff -fail 1e-4 -failrelative 0.05 -failpercent 1 -warn 1e-4 -warnrelative 0.01 "$1" "$2"
  else idiff -fail 0.016 -failpercent 1 "$1" "$2"; fi; }

status=0
for a in vacuum clear mild; do
  render "$a"
  if [ "$MODE" = update ]; then
    mkdir -p "$REF"; cp "$OUT/${a}_scene.exr" "$OUT/${a}_display.png" "$REF/"; echo "updated $a"
    continue
  fi
  for k in scene display; do
    ext=$([ $k = scene ] && echo exr || echo png)
    if out=$(compare "$REF/${a}_$k.$ext" "$OUT/${a}_$k.$ext" $k 2>&1); then r=PASS; else r=FAIL; status=1; fi
    echo "$a $k: $r  $(echo "$out" | grep -E "Max error|pixels .* over|PASS|FAIL|WARNING" | tr '\n' ' ' | sed 's/  */ /g')"
  done
done
exit $status
