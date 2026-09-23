#!/usr/bin/env bash
# M2.5: every frame through the FROZEN perceptual stack, motion variant (m1/README.md sec. 6):
#   haze + lamps -> m1/pcond_colorimetric.sh LC -> Radiance clipgamut (pcond -l -e 1 with a
#   Rec.709 PRIMARIES header) -> sRGB PNG (Blender's OCIO "Standard" view) -> lossless video.
# pcond adapts per frame (its linear-mode exposure comes from the frame's own histogram);
# the EXPOSURE it chose is logged per frame for the invariants (m25/check_clip.py).
#   m25/display_clip.sh CLIPDIR [NREPEAT=240 for a static clip]
set -euo pipefail
D=$(realpath "$1") NREP=${2:-240}
FPS=$(sed -E 's/.*fps=([0-9]+).*/\1/' "$D/clip.txt")
CFG=$(ls "$(dirname "$(readlink -f "$(command -v blender)")")"/../share/blender/*/datafiles/colormanagement/config.ocio)
export D CFG
mkdir -p "$D/png" "$D/lc"
frame() {
  local f=$1 t; t=$(mktemp -d)
  REC709="0.640 0.330 0.300 0.600 0.150 0.060 0.3127 0.3290"
  oiiotool "$D/haze_$f.exr" "$D/lamps_$f.exr" --add --ch R,G,B -o "$t/sum.exr"
  m1/pcond_colorimetric.sh "$t/sum.exr" 60 LC "$t/lc.hdr" 1 2>/dev/null
  echo "$f $(getinfo < "$t/lc.pcond.hdr" | sed -nE 's/.*EXPOSURE= *([0-9.eE+-]+).*/\1/p' | head -1)" > "$D/lc/$f.expo"
  (cd "$t" && getinfo -a "PRIMARIES= $REC709" < lc.hdr > lcp.hdr && pcond -l -e 1 -p $REC709 lcp.hdr > cg.hdr)
  oiiotool "$t/lc.hdr" -o "$D/lc/$f.exr"                       # pcond stage (display-linear)
  oiiotool --colorconfig "$CFG" "$t/cg.hdr" --iscolorspace "Linear Rec.709" --ociodisplay sRGB Standard \
    -d uint8 -o "$D/png/$f.png"
  rm -rf "$t"; }
export -f frame
ls "$D"/haze_*.exr | sed -E 's/.*haze_([0-9]+)\.exr/\1/' | xargs -P "$(nproc)" -I{} bash -c 'frame {}'
cat "$D"/lc/*.expo > "$D/exposure.txt"
n=$(ls "$D"/png/*.png | wc -l)
if [ "$n" = 1 ]; then                           # static clip: the same frame, NREP times
  ffmpeg -loglevel error -y -loop 1 -framerate "$FPS" -i "$D/png/0001.png" -frames:v "$NREP" \
    -c:v libx264rgb -crf 0 -preset veryslow "$D/clip.mp4"
else
  ffmpeg -loglevel error -y -framerate "$FPS" -i "$D/png/%04d.png" -c:v libx264rgb -crf 0 -preset veryslow "$D/clip.mp4"
fi
echo "$D/clip.mp4: $n rendered frames at $FPS fps"
