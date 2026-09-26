#!/usr/bin/env bash
# Frozen axis A: pcond -s -c, path A of m1/pcond_colorimetric.sh (ra_xyze -> pcond on XYZE, Rec.709 output),
# input in cd/m^2 (x 1/179). Writes pcond's display-relative Rec.709 output (1 = Ldmax) as EXR; the pipeline keeps
# only its luminance.   usage (inside nix develop): d1/pipeline/axis_a.sh IN.exr HFOV OUT.exr
set -euo pipefail
IN=$(realpath "$1") HFOV=$2 OUT=$(realpath -m "$3")
REC709="0.640 0.330 0.300 0.600 0.150 0.060 0.3127 0.3290"
T=$(mktemp -d -p "$(dirname "$OUT")"); trap 'cd /; rm -rf "$T"' EXIT; cd "$T"
read -r W H < <(oiiotool --info "$IN" | sed -E 's/.* : +([0-9]+) x +([0-9]+),.*/\1 \2/')
VFOV=$(awk -v h="$HFOV" -v W="$W" -v H="$H" 'BEGIN{pi=atan2(0,-1); print 2*atan2(sin(h*pi/360)/cos(h*pi/360)*H/W,1)*180/pi}')
oiiotool "$IN" --ch R,G,B --clamp:min=0 --mulc 0.00558659 -o raw.hdr
getinfo -a "VIEW= -vtv -vh $HFOV -vv $VFOV" "PRIMARIES= $REC709" < raw.hdr > in709.hdr
ra_xyze in709.hdr > inX.hdr
pcond -s -c -p $REC709 inX.hdr > out.hdr
oiiotool out.hdr -o "$OUT"
