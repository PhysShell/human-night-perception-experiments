#!/usr/bin/env bash
# B0: the SAME frozen display step for every optics variant (only the optics differ):
# retinal cd/m^2 EXR (73 px/deg, 12 deg wide) -> m1/pcond_colorimetric.sh LC (SCALE 1/179,
# HFOV 12, pcond -u LDMAX, default 100:1 range) -> PBR Neutral on out-of-gamut pixels -> sRGB PNG.
# Also writes the displayed luminance in cd/m^2 = display-linear x LDMAX + LDMAX/100 (black).
#   b0/display.sh IN.exr OUTPREFIX LDMAX
set -euo pipefail
IN=$1 O=$2 LD=$3
CFG=$(ls "$(dirname "$(readlink -f "$(command -v blender)")")"/../share/blender/*/datafiles/colormanagement/config.ocio)
t=$(mktemp -d)
m1/pcond_colorimetric.sh "$IN" 12 LC "$t/lc.hdr" 0.00558659 -u "$LD" 2>/dev/null
oiiotool "$t/lc.hdr" -o "$t/lc.exr"
oiiotool "$t/lc.exr" --mulc "$LD" --addc "$(awk -v l=$LD 'BEGIN{print l/100}')" -o "${O}_displayed_cdm2.exr"
oiiotool "$t/lc.exr" --maxchan --subc 1 --mulc 1e9 --clamp:min=0:max=1 --ch 0,0,0 -o "$t/oog.exr"
oiiotool --colorconfig "$CFG" "$t/lc.exr" --iscolorspace "Linear Rec.709" --ociodisplay sRGB Standard -d uint8 -o "$t/std.png"
oiiotool --colorconfig "$CFG" "$t/lc.exr" --iscolorspace "Linear Rec.709" --ociodisplay sRGB "Khronos PBR Neutral" -d uint8 -o "$t/pbr.png"
oiiotool "$t/pbr.png" "$t/std.png" --sub "$t/oog.exr" --mul "$t/std.png" --add -d uint8 -o "${O}.png"
rm -rf "$t"
