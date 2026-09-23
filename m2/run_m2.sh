#!/usr/bin/env bash
# M2: feed every atmosphere render through the UNCHANGED, frozen M1.1 perceptual stack
# (pcond_colorimetric.sh LC -> stills display: PBR Neutral on out-of-gamut pixels only),
# then compare. Renders come from m2/render_all.sh.
set -euo pipefail
D=m2/out; R=$D/results; mkdir -p "$R"
CFG=$(ls "$(dirname "$(readlink -f "$(command -v blender)")")"/../share/blender/*/datafiles/colormanagement/config.ocio)
view() { oiiotool --colorconfig "$CFG" "$1" --iscolorspace "Linear Rec.709" --ociodisplay sRGB "$2" -d uint8 -o "$3"; }
for a in vacuum clear mild moderate; do
  m1/pcond_colorimetric.sh "$D/scene_$a.exr" 60 LC "$D/lc_$a.hdr" 1
  oiiotool "$D/lc_$a.hdr" -o "$D/lc_$a.exr"
  oiiotool "$D/lc_$a.exr" --maxchan --subc 1 --mulc 1e9 --clamp:min=0:max=1 --ch 0,0,0 -o "$D/oog_$a.exr"
  view "$D/lc_$a.exr" Standard "$D/std_$a.png"
  view "$D/lc_$a.exr" "Khronos PBR Neutral" "$D/pbr_$a.png"
  oiiotool "$D/pbr_$a.png" "$D/std_$a.png" --sub "$D/oog_$a.exr" --mul "$D/std_$a.png" --add -d uint8 -o "$R/$a.png"
done
( cd "$R"
  magick montage -label '%t' -font DejaVu-Sans -pointsize 14 -tile 1x -geometry +3+3 -background '#222' -fill '#ddd' \
    vacuum.png clear.png mild.png moderate.png sheet_full.png
  for a in vacuum clear mild moderate; do magick "$a.png" -crop 480x60+240+160 +repage -filter point -resize 300% "crop_$a.png"; done
  magick montage -label '%t' -font DejaVu-Sans -pointsize 14 -tile 1x -geometry +3+3 -background '#222' -fill '#ddd' \
    crop_vacuum.png crop_clear.png crop_mild.png crop_moderate.png sheet_crop_ribbon.png )
python3 m2/compare_atmospheres.py | tee m2/compare_result.txt
