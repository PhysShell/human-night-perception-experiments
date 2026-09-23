#!/usr/bin/env bash
# pcond -s -c with honest colorimetry and warm lamps kept (M1.1; replaces pcond_keep_hue.sh).
#
#   pcond_colorimetric.sh in_rec709.exr HFOV A|B|AB out.hdr [SCALE] [extra pcond flags]
#
# Input: linear Rec.709/D65 EXR (Blender's scene-linear space). SCALE converts pixel values
# to Radiance radiometric units: 1 for Cycles renders authored with Radiance's 179 lm/W
# equal-energy-white convention, 1/179 = 0.00558659 for images whose Y is already cd/m^2.
# Output: display-linear Rec.709/D65 (1 = Ldmax), luminance <= 1. In B/AB, over-bright lamp
# pixels keep their chromaticity and may have a channel > 1 (gamut handling is downstream).
#
# All colour conversion is Radiance's own (ra_xyze, von Kries to Radiance's white), starting
# from a truthful PRIMARIES= Rec.709/D65 header. No pcond formula is re-implemented:
#   A : ra_xyze -> XYZE -> pcond. pcond's scotopic estimate for XYZ (cielum) falls inside the
#       range of spectral recoveries (m1/scotopic_oracle.py), but XYZE input always goes
#       through matscan()/clipgamut(), so over-bright pixels come out white.
#   B : ra_xyze -r -> Radiance-standard RGB, i.e. pcond's default space. The (redundant,
#       verified) PRIMARIES line is moved out of the active header with a pcomb pass-through,
#       pcond then skips matscan() and returns its own UNCLIPPED result; over-bright pixels
#       are scaled to luminance 1 (pcond's clip point) keeping chromaticity. Its RGB scotopic
#       weights (rgblum) overestimate reds/oranges vs. the spectral range.
#   AB (default): A wherever pcond did not clip, B on the pixels it clipped.
set -euo pipefail
IN=$(realpath "$1") HFOV=$2 MODE=$3 OUT=$(realpath -m "$4") SCALE=${5:-1}
shift 4; [ $# -gt 0 ] && shift
TMP=$(mktemp -d); trap 'cd /; rm -rf "$TMP"' EXIT
# Radiance tools record their command lines in the picture header; OpenImageIO's RGBE reader
# fails on long header lines (seen with Nix sandbox paths), so work with short relative names.
cd "$TMP"; T=.
REC709="0.640 0.330 0.300 0.600 0.150 0.060 0.3127 0.3290"
STD="0.6400 0.3300 0.2900 0.6000 0.1500 0.0600 0.3333 0.3333"

read -r W H < <(oiiotool --info "$IN" | sed -E 's/.* : +([0-9]+) x +([0-9]+),.*/\1 \2/')
VFOV=$(awk -v h="$HFOV" -v W="$W" -v H="$H" 'BEGIN{pi=atan2(0,-1); print 2*atan2(sin(h*pi/360)/cos(h*pi/360)*H/W,1)*180/pi}')

oiiotool "$IN" --ch R,G,B --clamp:min=0 --mulc "$SCALE" -o "$T/raw.hdr"
getinfo -a "VIEW= -vtv -vh $HFOV -vv $VFOV" "PRIMARIES= $REC709" < "$T/raw.hdr" > "$T/in709.hdr"

path_A() { # -> $T/A.hdr, Rec.709 display values, clipped by pcond
  ra_xyze "$T/in709.hdr" > "$T/inX.hdr"
  pcond -s -c -p $REC709 "$@" "$T/inX.hdr" > "$T/A.hdr"; }

path_B() { # -> $T/B.hdr, Rec.709 display values, unclipped chroma, luminance <= 1
  ra_xyze -r "$T/in709.hdr" > "$T/instd.hdr"
  getinfo < "$T/instd.hdr" | grep -q "^PRIMARIES= $STD\$" \
    || { echo "ra_xyze did not produce Radiance-standard primaries" >&2; exit 1; }
  pcomb -e "ro=ri(1);go=gi(1);bo=bi(1)" "$T/instd.hdr" > "$T/instd_default.hdr"
  pcond -s -c "$@" "$T/instd_default.hdr" > "$T/Bstd.hdr"
  pcomb -e "Y=li(1); s=if(Y-1,1/Y,1); ro=s*ri(1); go=s*gi(1); bo=s*bi(1)" "$T/Bstd.hdr" > "$T/Bcap.hdr"
  ra_xyze -r -u -p $REC709 "$T/Bcap.hdr" > "$T/B.hdr"; }

case $MODE in
  A)  path_A "$@"; cp "$T/A.hdr" "$OUT" ;;
  B)  path_B "$@"; cp "$T/B.hdr" "$OUT" ;;
  AB) path_A "$@"; path_B "$@"
      # clipgamut() puts every pixel it touches on the display cube (max channel = 1):
      # over-bright ones become (1,1,1), in-range ones with a channel > 1 are desaturated
      pcomb -h -e "M(a,b)=if(a-b,a,b); c=M(M(ri(1),gi(1)),bi(1)); clipped=if(c-.999,1,0);" \
            -e "ro=if(clipped-.5,ri(2),ri(1)); go=if(clipped-.5,gi(2),gi(1)); bo=if(clipped-.5,bi(2),bi(1))" \
            "$T/A.hdr" "$T/B.hdr" > "$OUT" ;;
  *)  echo "mode must be A, B or AB" >&2; exit 2 ;;
esac
# pcond as shipped (honest XYZE input, clipped) next to the result, for comparison and tests
[ -f "$T/A.hdr" ] || path_A "$@"
cp "$T/A.hdr" "${OUT%.hdr}.pcond.hdr"
