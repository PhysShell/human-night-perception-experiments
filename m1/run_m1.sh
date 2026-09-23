#!/usr/bin/env bash
# M1: the SAME Cycles render through existing tools only.
# Usage (inside `nix develop`):  m1/run_m1.sh [scene.exr] [hfov_deg] [outdir]
# Input contract: Cycles EXR in Blender's scene-linear Rec.709, lights authored with Radiance's
# 179 lm/W equal-energy-white convention (m1/scene.py): cd/m^2 = 179 * (0.2126 R + 0.7152 G
# + 0.0722 B). Conversion to Radiance's own RGB/XYZ is done by ra_xyze, never by relabelling.
set -euo pipefail
IN=${1:-m1/out/scene.exr}
HFOV=${2:-60}
OUT=${3:-m1/out/results}
T=$OUT/tmp
mkdir -p "$T"

CFG=$(ls "$(dirname "$(readlink -f "$(command -v blender)")")"/../share/blender/*/datafiles/colormanagement/config.ocio)
read -r W H < <(oiiotool --info "$IN" | sed -E 's/.* : +([0-9]+) x +([0-9]+),.*/\1 \2/')
VFOV=$(awk -v h="$HFOV" -v W="$W" -v H="$H" 'BEGIN{pi=atan2(0,-1); print 2*atan2(sin(h*pi/360)/cos(h*pi/360)*H/W,1)*180/pi}')
echo "input $IN ${W}x${H} hfov=$HFOV vfov=$VFOV"

# Display encodings, all from Blender's own OCIO config (display "sRGB").
view() { # in.exr view out.png
  oiiotool --colorconfig "$CFG" "$1" --iscolorspace "Linear Rec.709" --ociodisplay sRGB "$2" -d uint8 -o "$3"; }
hdr2exr() { oiiotool "$1" -o "$2"; }   # stored pcond values are display-linear (1 = Ldmax)

REC709="0.640 0.330 0.300 0.600 0.150 0.060 0.3127 0.3290"

# Honest colorimetry (M1.1, m1/pcond_colorimetric.sh AB): Rec.709 -> XYZE via ra_xyze -> pcond
# for every pixel pcond does not clip; clipped (lamp) pixels come from pcond's own unclipped
# run on Radiance-standard RGB, scaled to display max, so lamps keep their chromaticity.
# Gamut: only pixels outside the display cube go through Khronos PBR Neutral (highlight
# compression, hue-preserving); every displayable pixel is pcond's output unchanged.
honest() { # in.exr mode out_prefix
  local st=$T/$(basename "$3")
  m1/pcond_colorimetric.sh "$1" "$HFOV" "$2" "$st.hdr" 1 2>/dev/null
  hdr2exr "$st.hdr" "$st.exr"
  oiiotool "$st.exr" --maxchan --subc 1 --mulc 1e9 --clamp:min=0:max=1 --ch 0,0,0 -o "${st}_oog.exr"
  view "$st.exr" Standard "${st}_std.png"
  view "$st.exr" "Khronos PBR Neutral" "${st}_pbr.png"
  oiiotool "${st}_pbr.png" "${st}_std.png" --sub "${st}_oog.exr" --mul "${st}_std.png" --add \
    -d uint8 -o "$OUT/$3_pbrneutral_oog.png"; }

# 1. raw linear render, photometric: 1 cd/m^2 in the scene = 1 cd/m^2 on a 100-nit display
oiiotool "$IN" --ch R,G,B --mulc 1.79 -o "$T/photometric.exr"
view "$T/photometric.exr" Standard "$OUT/1_raw_photometric_100nit.png"

# 2. normal display transform: auto-exposure (log-mean -> 0.18) + Blender's default AgX view
K=$(python3 -c "import sys,numpy as np,OpenImageIO as o; a=o.ImageBuf(sys.argv[1]).get_pixels(o.FLOAT)[...,:3]; \
  Y=a@[0.2126,0.7152,0.0722]; print(0.18/np.exp(np.log(Y.clip(0)+1e-12).mean()))" "$IN")
oiiotool "$IN" --ch R,G,B --mulc "$K" -o "$T/autoexp.exr"
view "$T/autoexp.exr" AgX "$OUT/2_camera_autoexposure_agx.png"

# 3 + 4. pcond -s -c as shipped (honest XYZE input, lamps clipped to white) and with lamp colour
honest "$IN" AB 4_pcond_sc_AB
hdr2exr "$T/4_pcond_sc_AB.pcond.hdr" "$T/pcond_sc.exr"
view "$T/pcond_sc.exr" Standard "$OUT/3_pcond_sc.png"

# 5. eye glare first (Blender Fog Glow = Spencer'95 PSF, FOV-calibrated), then as 4
blender -b --factory-startup --python m1/fog_glow.py -- "$IN" "$T/glare.exr" "$HFOV" 2>&1 | grep "fog glow"
honest "$T/glare.exr" AB 5_fogglow_pcond_sc_AB

# contact sheets: full frames + 4x crop of the lamp ribbon
cd "$OUT"
magick montage -label '%t' -font DejaVu-Sans -pointsize 18 -tile 1x -geometry +4+4 -background '#222' -fill '#ddd' \
  [1-5]_*.png sheet_full.png
CROP=${CROP:-640x90+1000+340}
for f in [1-5]_*.png; do magick "$f" -crop "$CROP" +repage -filter point -resize 300% "tmp/crop_$f"; done
magick montage -label '%t' -font DejaVu-Sans -pointsize 18 -tile 1x -geometry +4+4 -background '#222' -fill '#ddd' \
  tmp/crop_*.png sheet_crop_ribbon.png
echo done; ls "$PWD"
