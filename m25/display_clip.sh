#!/usr/bin/env bash
# M2.5: every frame through the FROZEN perceptual stack, motion variant (m1/README.md sec. 6):
#   haze + lamps -> m1/pcond_colorimetric.sh LC -> Radiance clipgamut (pcond -l -e 1 with a
#   Rec.709 PRIMARIES header) -> sRGB PNG (Blender's OCIO "Standard" view) -> lossless video.
# pcond adapts per frame (its linear-mode exposure comes from the frame's own histogram);
# the EXPOSURE it chose is logged per frame for the invariants (m25/check_clip.py).
# DISPLAY=pbr_oog selects the frozen STILLS display instead (Khronos PBR Neutral on the pixels
# outside the display cube only; warmer lamps, but a 12-16 % luminance drop at gamut exit in
# the synthetic sweep), written to png_pbr/ and clip_pbr.mp4, so the clip invariants can say
# whether that drop shows in this clip.
#   [DISPLAY=clipgamut|pbr_oog] m25/display_clip.sh CLIPDIR [NREPEAT=240 for a static clip]
set -euo pipefail
D=$(realpath "$1") NREP=${2:-240} DISPLAY=${DISPLAY:-clipgamut}
P=png; [ "$DISPLAY" = pbr_oog ] && P=png_pbr
FPS=$(sed -E 's/.*fps=([0-9]+).*/\1/' "$D/clip.txt")
CFG=$(ls "$(dirname "$(readlink -f "$(command -v blender)")")"/../share/blender/*/datafiles/colormanagement/config.ocio)
export D CFG DISPLAY P
mkdir -p "$D/$P" "$D/lc"
frame() {
  local f=$1 t; t=$(mktemp -d)
  REC709="0.640 0.330 0.300 0.600 0.150 0.060 0.3127 0.3290"
  oiiotool "$D/haze_$f.exr" "$D/lamps_$f.exr" --add --ch R,G,B -o "$t/sum.exr"
  m1/pcond_colorimetric.sh "$t/sum.exr" 60 LC "$t/lc.hdr" 1 2>/dev/null
  echo "$f $(getinfo < "$t/lc.pcond.hdr" | sed -nE 's/.*EXPOSURE= *([0-9.eE+-]+).*/\1/p' | head -1)" > "$D/lc/$f.expo"
  (cd "$t" && getinfo -a "PRIMARIES= $REC709" < lc.hdr > lcp.hdr && pcond -l -e 1 -p $REC709 lcp.hdr > cg.hdr)
  oiiotool "$t/lc.hdr" -o "$D/lc/$f.exr"                       # pcond stage (display-linear)
  if [ "$DISPLAY" = pbr_oog ]; then                       # as m1/run_m1.sh honest()
    oiiotool "$t/lc.hdr" -o "$t/lc.exr"
    oiiotool "$t/lc.exr" --maxchan --subc 1 --mulc 1e9 --clamp:min=0:max=1 --ch 0,0,0 -o "$t/oog.exr"
    oiiotool --colorconfig "$CFG" "$t/lc.exr" --iscolorspace "Linear Rec.709" --ociodisplay sRGB Standard -d uint8 -o "$t/std.png"
    oiiotool --colorconfig "$CFG" "$t/lc.exr" --iscolorspace "Linear Rec.709" --ociodisplay sRGB "Khronos PBR Neutral" -d uint8 -o "$t/pbr.png"
    oiiotool "$t/pbr.png" "$t/std.png" --sub "$t/oog.exr" --mul "$t/std.png" --add -d uint8 -o "$D/$P/$f.png"
  else
    oiiotool --colorconfig "$CFG" "$t/cg.hdr" --iscolorspace "Linear Rec.709" --ociodisplay sRGB Standard \
      -d uint8 -o "$D/$P/$f.png"
  fi
  rm -rf "$t"; }
export -f frame
ls "$D"/haze_*.exr | sed -E 's/.*haze_([0-9]+)\.exr/\1/' | xargs -P "$(nproc)" -I{} bash -c 'frame {}'
cat "$D"/lc/*.expo > "$D/exposure.txt"
V=clip.mp4; [ "$DISPLAY" = pbr_oog ] && V=clip_pbr.mp4
n=$(ls "$D/$P"/*.png | wc -l)
if [ "$n" = 1 ]; then                           # static clip: the same frame, NREP times
  ffmpeg -loglevel error -y -loop 1 -framerate "$FPS" -i "$D/$P/0001.png" -frames:v "$NREP" \
    -c:v libx264rgb -crf 0 -preset veryslow "$D/$V"
else
  ffmpeg -loglevel error -y -framerate "$FPS" -i "$D/$P/%04d.png" -c:v libx264rgb -crf 0 -preset veryslow "$D/$V"
fi
echo "$D/$V: $n rendered frames at $FPS fps ($DISPLAY)"
