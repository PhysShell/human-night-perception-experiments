#!/usr/bin/env bash
# M1: the SAME Cycles render through existing tools only.
# Usage (inside `nix develop`):  m1/run_m1.sh [scene.exr] [hfov_deg] [outdir]
# Input contract: Cycles EXR authored with K = 179 lm/W (m1/scene.py), i.e. already a
# Radiance picture: luminance [cd/m^2] = 179 * (0.2126 R + 0.7152 G + 0.0722 B).
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

# Radiance picture headers. VIEW is needed by pcond for the angular field.
# No PRIMARIES header: with one, pcond's matscan()/clipgamut() turns every lamp white.
prep() { # in.exr stem
  oiiotool "$1" --ch R,G,B --clamp:min=0 -o "$T/$2_raw.hdr"
  getinfo -a "VIEW= -vtv -vh $HFOV -vv $VFOV" < "$T/$2_raw.hdr" > "$T/$2.hdr"
  getinfo -a "PRIMARIES= 0.640 0.330 0.300 0.600 0.150 0.060 0.3127 0.3290" \
    < "$T/$2.hdr" > "$T/$2_prim.hdr"; }

# pcond -s -c, lamp colour kept (Radiance only), then the out-of-gamut pixels
# (and only those) rendered with Khronos PBR Neutral from Blender's OCIO config.
keephue() { # stem out_prefix
  KEEP_CAPPED="$T/$1_capped.hdr" m1/pcond_keep_hue.sh "$T/$1.hdr" "$T/$1_clipgamut.hdr"
  hdr2exr "$T/$1_clipgamut.hdr" "$T/$1_clipgamut.exr"
  view "$T/$1_clipgamut.exr" Standard "$OUT/$2_radiance_clipgamut.png"
  hdr2exr "$T/$1_capped.hdr" "$T/$1_capped.exr"
  oiiotool "$T/$1_capped.exr" --maxchan --subc 1 --mulc 1e9 --clamp:min=0:max=1 --ch 0,0,0 -o "$T/$1_oog.exr"
  view "$T/$1_capped.exr" Standard "$T/$1_std.png"
  view "$T/$1_capped.exr" "Khronos PBR Neutral" "$T/$1_pbr.png"
  oiiotool "$T/$1_pbr.png" "$T/$1_std.png" --sub "$T/$1_oog.exr" --mul "$T/$1_std.png" --add \
    -d uint8 -o "$OUT/$2_pbrneutral_oog.png"; }

prep "$IN" scene

# 1. raw linear render, photometric: 1 cd/m^2 in the scene = 1 cd/m^2 on a 100-nit display
oiiotool "$IN" --ch R,G,B --mulc 1.79 -o "$T/photometric.exr"
view "$T/photometric.exr" Standard "$OUT/1_raw_photometric_100nit.png"

# 2. normal display transform: auto-exposure (log-mean -> 0.18) + Blender's default AgX view
K=$(python3 -c "import sys,numpy as np,OpenImageIO as o; a=o.ImageBuf(sys.argv[1]).get_pixels(o.FLOAT)[...,:3]; \
  Y=a@[0.2126,0.7152,0.0722]; print(0.18/np.exp(np.log(Y.clip(0)+1e-12).mean()))" "$IN")
oiiotool "$IN" --ch R,G,B --mulc "$K" -o "$T/autoexp.exr"
view "$T/autoexp.exr" AgX "$OUT/2_camera_autoexposure_agx.png"

# 3. pcond -s -c, standard path (input declares Rec.709 primaries)
pcond -s -c "$T/scene_prim.hdr" > "$T/pcond_sc.hdr"
hdr2exr "$T/pcond_sc.hdr" "$T/pcond_sc.exr"
view "$T/pcond_sc.exr" Standard "$OUT/3_pcond_sc.png"

# 4. pcond -s -c keeping lamp colour
keephue scene 4_pcond_sc_keephue

# 5. eye glare first (Blender Fog Glow = Spencer'95 PSF, FOV-calibrated), then as 4
blender -b --factory-startup --python m1/fog_glow.py -- "$IN" "$T/glare.exr" "$HFOV" 2>&1 | grep "fog glow"
prep "$T/glare.exr" glare
keephue glare 5_fogglow_pcond_sc_keephue

# contact sheets: full frames + 4x crop of the lamp ribbon
cd "$OUT"
magick montage -label '%t' -font DejaVu-Sans -pointsize 18 -tile 1x -geometry +4+4 -background '#222' -fill '#ddd' \
  [1-5]_*.png sheet_full.png
CROP=${CROP:-640x90+1000+340}
for f in [1-5]_*.png; do magick "$f" -crop "$CROP" +repage -filter point -resize 300% "tmp/crop_$f"; done
magick montage -label '%t' -font DejaVu-Sans -pointsize 18 -tile 1x -geometry +4+4 -background '#222' -fill '#ddd' \
  tmp/crop_*.png sheet_crop_ribbon.png
echo done; ls "$PWD"
