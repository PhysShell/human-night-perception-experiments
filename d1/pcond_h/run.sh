#!/usr/bin/env bash
# D1.1: Radiance pcond's documented human-vision bundle, through the SAME frozen display path as D0 donor A
# (m1/pcond_colorimetric.sh LC -> PBR Neutral on out-of-gamut pixels -> sRGB, SDR100 default Ldmax 100, 100:1).
#   V0      : -s -c              (the frozen baseline; wrapper default)
#   acuity  : -s -c -a           (+ defocus of darker regions, "human visual acuity loss")
#   h       : -s -c -a -v  = -h  (+ veiling glare; man page: -h is the bundle of -a -v -s -c)
# Scenes S0, S1, S3_bar, S3_nobar; output contract as D0 (16-bit PNG, SDR100 sRGB).
#   nix develop -c d1/pcond_h/run.sh
set -euo pipefail
I=d0/work/inputs; O=d1/pcond_h/.cache/out; T=d1/pcond_h/.cache/tmp; mkdir -p $O $T
CFG=$(ls "$(dirname "$(readlink -f "$(command -v blender)")")"/../share/blender/*/datafiles/colormanagement/config.ocio)
hfov() { python3 -c "import json;m=json.load(open('$I/manifest.json'))['scenes']['$1'];print(m['size'][0]/m['scene_px_per_deg'])"; }
one() { # scene cfg flags...
  local s=$1 c=$2; shift 2; local t; t=$(mktemp -d -p $T); local h; h=$(hfov ${s%%_*})
  mkdir -p $O/$c
  m1/pcond_colorimetric.sh $I/$s.exr "$h" LC "$t/lc.hdr" 0.00558659 "$@" 2>/dev/null
  oiiotool "$t/lc.hdr" -o "$t/lc.exr"
  oiiotool "$t/lc.exr" --maxchan --subc 1 --mulc 1e9 --clamp:min=0:max=1 --ch 0,0,0 -o "$t/oog.exr"
  oiiotool --colorconfig "$CFG" "$t/lc.exr" --iscolorspace "Linear Rec.709" --ociodisplay sRGB Standard -d uint16 -o "$t/std.png"
  oiiotool --colorconfig "$CFG" "$t/lc.exr" --iscolorspace "Linear Rec.709" --ociodisplay sRGB "Khronos PBR Neutral" -d uint16 -o "$t/pbr.png"
  oiiotool "$t/pbr.png" "$t/std.png" --sub "$t/oog.exr" --mul "$t/std.png" --add -d uint16 -o "$O/$c/${s}__PHONE_SDR100_DARK.png"
  rm -rf "$t"; echo "$c $s"; }
for s in S0 S1 S3_bar S3_nobar; do
  one $s V0
  one $s acuity -a
  one $s h -a -v
done
rm -rf $T
