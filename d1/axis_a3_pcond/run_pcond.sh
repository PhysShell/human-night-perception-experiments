#!/usr/bin/env bash
# D1-A3-K0: pcond path A (as m1/pcond_colorimetric.sh), flags -s and -s -c, S1, HFOV 60 -> .cache/{s,sc}.exr
#   nix develop -c d1/axis_a3_pcond/run_pcond.sh
set -euo pipefail
D=$(realpath d1/axis_a3_pcond/.cache); mkdir -p "$D"; IN=$(realpath d0/work/inputs/S1.exr)
REC709="0.640 0.330 0.300 0.600 0.150 0.060 0.3127 0.3290"; HFOV=60
T=$(mktemp -d -p "$D"); cd "$T"
read -r W H < <(oiiotool --info "$IN" | sed -E 's/.* : +([0-9]+) x +([0-9]+),.*/\1 \2/')
VFOV=$(awk -v h="$HFOV" -v W="$W" -v H="$H" 'BEGIN{pi=atan2(0,-1); print 2*atan2(sin(h*pi/360)/cos(h*pi/360)*H/W,1)*180/pi}')
oiiotool "$IN" --ch R,G,B --clamp:min=0 --mulc 0.00558659 -o raw.hdr
getinfo -a "VIEW= -vtv -vh $HFOV -vv $VFOV" "PRIMARIES= $REC709" < raw.hdr > in709.hdr
ra_xyze in709.hdr > inX.hdr
pcond -s -p $REC709 inX.hdr > s.hdr
pcond -s -c -p $REC709 inX.hdr > sc.hdr
oiiotool s.hdr -o "$D/s.exr"; oiiotool sc.hdr -o "$D/sc.exr"
cd /; rm -rf "$T"; echo "pcond runs written to $D"
