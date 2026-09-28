#!/usr/bin/env bash
# D2-G1 G0.2: adaptation histogram for pcond -I. Same cd/m^2 -> Radiance conversion as the frozen axis A
# (d1/pipeline/axis_a.sh), then Radiance's own phisto.   usage (inside nix develop): d2/g1/hist.sh ADAPT.exr HFOV OUT.hist
set -euo pipefail
IN=$(realpath "$1") HFOV=$2 OUT=$(realpath -m "$3")
REC709="0.640 0.330 0.300 0.600 0.150 0.060 0.3127 0.3290"
T=$(mktemp -d -p "$(dirname "$OUT")"); trap 'cd /; rm -rf "$T"' EXIT; cd "$T"
read -r W H < <(oiiotool --info "$IN" | sed -E 's/.* : +([0-9]+) x +([0-9]+),.*/\1 \2/')
VFOV=$(awk -v h="$HFOV" -v W="$W" -v H="$H" 'BEGIN{pi=atan2(0,-1); print 2*atan2(sin(h*pi/360)/cos(h*pi/360)*H/W,1)*180/pi}')
oiiotool "$IN" --ch R,G,B --clamp:min=0 --mulc 0.00558659 -o raw.hdr
getinfo -a "VIEW= -vtv -vh $HFOV -vv $VFOV" "PRIMARIES= $REC709" < raw.hdr > in709.hdr
phisto in709.hdr > "$OUT"
