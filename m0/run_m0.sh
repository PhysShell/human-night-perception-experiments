#!/usr/bin/env bash
# M0: run the SAME calibrated HDR through existing operators, unmodified.
# Glue only: format conversion (oiiotool), header metadata (getinfo), montage.
# Usage (inside `nix develop`):  m0/run_m0.sh [input.exr] [hfov_deg] [outdir]
# Input: linear Rec.709 EXR whose Y channel is luminance in cd/m^2.
set -euo pipefail

set -- "${1:-m0/data/synthetic_night.exr}" "${2:-60}" "${3:-m0/out}"
IN=$1
HFOV=$2
OUT=$3
mkdir -p "$OUT/tmp"
T=$OUT/tmp
# Real HDR merges contain small negative values; every operator gets the same clamped input.
oiiotool "$1" --ch R,G,B --clamp:min=0 -o "$T/in_clamped.exr"
IN=$T/in_clamped.exr

read -r W H < <(oiiotool --info "$IN" | sed -E 's/.* : +([0-9]+) x +([0-9]+),.*/\1 \2/')
VFOV=$(awk -v h="$HFOV" -v W="$W" -v H="$H" 'BEGIN{pi=atan2(0,-1); print 2*atan2(sin(h*pi/360)/cos(h*pi/360)*H/W,1)*180/pi}')
echo "input $IN  ${W}x${H}  hfov=$HFOV vfov=$VFOV"


# ---------- baselines (no vision model) ----------
# (a) "camera": global auto-exposure, log-mean -> 0.18, 2.2 gamma, clip.
LOGMEAN=$(python3 -c "import sys,numpy as np,OpenImageIO as o; a=o.ImageBuf(sys.argv[1]).get_pixels(o.FLOAT); \
  Y=a[...,:3]@[0.2126,0.7152,0.0722]; print(np.log(Y.clip(0)+1e-9).mean())" "$IN")
K=$(awk -v m="$LOGMEAN" 'BEGIN{print 0.18/exp(m)}')
oiiotool "$IN" --mulc "$K" --clamp:min=0:max=1 --powc 0.4545 -d uint8 -o "$OUT/a_camera_autoexposure.png"
# (b) "photometric": display luminance == scene luminance on a 100 cd/m^2 display.
oiiotool "$IN" --mulc 0.01 --clamp:min=0:max=1 --powc 0.4545 -d uint8 -o "$OUT/b_photometric_100nit.png"

# ---------- Radiance pcond (Ward Larson, Rushmeier, Piatko 1997) ----------
# Radiance pictures store radiance (W/sr/m^2); luminance = 179 lm/W * Y.
# VIEW tells pcond the angular size (acuity + veil need it);
# PRIMARIES tells it the input is Rec.709/D65 rather than Radiance's default.
oiiotool "$IN" --mulc 0.00558659 -o "$T/in_raw.hdr"
getinfo -a "VIEW= -vtv -vh $HFOV -vv $VFOV" \
           "PRIMARIES= 0.640 0.330 0.300 0.600 0.150 0.060 0.3127 0.3290" \
           < "$T/in_raw.hdr" > "$T/in.hdr"
rad() { # name, pcond flags...
  local n=$1; shift
  pcond "$@" -x "$T/$n.map" "$T/in.hdr" > "$T/$n.hdr"
  ra_ppm -g 2.2 "$T/$n.hdr" "$T/$n.ppm" && oiiotool "$T/$n.ppm" -o "$OUT/$n.png"; }
rad c_pcond_histogram             # histogram adjustment only (no human flags)
rad d_pcond_s_c        -s -c      # + contrast sensitivity + mesopic/scotopic colour
rad e_pcond_human      -h         # -h = -a -v -s -c (acuity, veil, CSF, colour)
rad f_pcond_human_dim  -h -u 30   # same, for a 30 cd/m^2 (dimmed) display
rad k_pcond_veil_only  -v         # isolate: veiling glare
rad l_pcond_acuity_only -a        # isolate: acuity loss

# ---------- pfstools / pfstmo ----------
oiiotool "$IN" -o "$T/in.pfm"
pfs() { # name, needs_gamma(0/1), cmd...
  local n=$1 g=$2; shift 2
  pfsin "$T/in.pfm" | pfstag --set "LUMINANCE=ABSOLUTE" | "$@" \
    | { if [ "$g" = 1 ]; then pfsgamma -g 2.2; else cat; fi; } \
    | pfsoutpfm "$T/$n.pfm"
  oiiotool "$T/$n.pfm" -d uint8 -o "$OUT/$n.png"; }
pfs g_pattanaik00_global  1 pfstmo_pattanaik00
pfs h_pattanaik00_local   1 pfstmo_pattanaik00 --local
pfs i_mantiuk08_display   0 pfstmo_mantiuk08 -d pd=lcd_office
pfs j_reinhard05          1 pfstmo_reinhard05

# ---------- contact sheet (+ crops for the synthetic image only) of the light ribbon / Purkinje probe ----------
cd "$OUT"
CROP=480x205+1100+300   # ribbon + village near x=0.7W
magick montage -label '%t' -font DejaVu-Sans -pointsize 18 -tile 2x -geometry +4+4 -background '#222' -fill '#ddd' \
  [a-l]_*.png sheet_full.png 2>/dev/null || magick montage -tile 2x -geometry +4+4 [a-l]_*.png sheet_full.png
[ "${CROPS:-1}" = 1 ] || { echo done; exit 0; }
for f in [a-l]_*.png; do magick "$f" -crop $CROP +repage -filter point -resize 400% "tmp/crop_$f"; done
magick montage -label '%t' -tile 2x -geometry +4+4 -background '#222' tmp/crop_*.png sheet_crop_lights.png 2>/dev/null \
  || magick montage -tile 2x -geometry +4+4 tmp/crop_*.png sheet_crop_lights.png
for f in [a-l]_*.png; do magick "$f" -crop 220x80+540+690 +repage -filter point -resize 300% "tmp/probe_$f"; done
magick montage -label '%t' -tile 2x -geometry +4+4 -background '#222' tmp/probe_*.png sheet_purkinje_probe.png 2>/dev/null \
  || magick montage -tile 2x -geometry +4+4 tmp/probe_*.png sheet_purkinje_probe.png
echo done; ls
