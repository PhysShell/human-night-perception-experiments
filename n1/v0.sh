#!/usr/bin/env bash
# The frozen V0 display path for one image: the body of one() in d0/donors/pcond/run.sh, NATIVE_DEFAULT/SDR100,
# copied verbatim (that script only runs the D0 corpus). usage (inside nix develop): n1/v0.sh IN_cdm2.exr HFOV OUT.png
set -euo pipefail
in=$1 hfov=$2 out=$3
CFG=$(ls "$(dirname "$(readlink -f "$(command -v blender)")")"/../share/blender/*/datafiles/colormanagement/config.ocio)
t=$(mktemp -d -p n1/work)
m1/pcond_colorimetric.sh "$in" "$hfov" LC "$t/lc.hdr" 0.00558659 2>/dev/null
oiiotool "$t/lc.hdr" -o "$t/lc.exr"
oiiotool "$t/lc.exr" --maxchan --subc 1 --mulc 1e9 --clamp:min=0:max=1 --ch 0,0,0 -o "$t/oog.exr"
oiiotool --colorconfig "$CFG" "$t/lc.exr" --iscolorspace "Linear Rec.709" --ociodisplay sRGB Standard -d uint16 -o "$t/std.png"
oiiotool --colorconfig "$CFG" "$t/lc.exr" --iscolorspace "Linear Rec.709" --ociodisplay sRGB "Khronos PBR Neutral" -d uint16 -o "$t/pbr.png"
oiiotool "$t/pbr.png" "$t/std.png" --sub "$t/oog.exr" --mul "$t/std.png" --add -d uint16 -o "$t/srgb.png"
cp "$t/srgb.png" "$out"; rm -rf "$t"
