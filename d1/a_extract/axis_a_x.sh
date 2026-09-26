#!/usr/bin/env bash
# AX: the frozen axis A (d1/pipeline/axis_a.sh: pcond -s -c, path A), identical commands, plus
#  - keeps pcond's actual input inX.hdr and dumps it as floats (pvalue -o: file values / exposure = cd/m^2),
#  - pcond -x map.txt (pcond's own tone-mapping function, putmapping()),
#  - a control run pcond -s (no -c): colour_active = 0 if its output is bit-identical to -s -c (DO_COLOR cleared).
#   usage (inside nix develop): d1/a_extract/axis_a_x.sh IN.exr HFOV OUTDIR
set -euo pipefail
IN=$(realpath "$1") HFOV=$2 O=$(realpath -m "$3"); mkdir -p "$O"
REC709="0.640 0.330 0.300 0.600 0.150 0.060 0.3127 0.3290"
T=$(mktemp -d -p "$O"); trap 'cd /; rm -rf "$T"' EXIT; cd "$T"
read -r W H < <(oiiotool --info "$IN" | sed -E 's/.* : +([0-9]+) x +([0-9]+),.*/\1 \2/')
VFOV=$(awk -v h="$HFOV" -v W="$W" -v H="$H" 'BEGIN{pi=atan2(0,-1); print 2*atan2(sin(h*pi/360)/cos(h*pi/360)*H/W,1)*180/pi}')
oiiotool "$IN" --ch R,G,B --clamp:min=0 --mulc 0.00558659 -o raw.hdr
getinfo -a "VIEW= -vtv -vh $HFOV -vv $VFOV" "PRIMARIES= $REC709" < raw.hdr > in709.hdr
ra_xyze in709.hdr > inX.hdr
pcond -s -c -p $REC709 -x map.txt inX.hdr > out.hdr
pcond -s -p $REC709 inX.hdr > s.hdr
if cmp -s out.hdr s.hdr; then echo 0 > "$O/colour_active"; else echo 1 > "$O/colour_active"; fi
oiiotool out.hdr -o "$O/out.exr"
pvalue -o -h -H -df inX.hdr > "$O/inX.f32"; getinfo inX.hdr > "$O/inX.header"; getinfo out.hdr > "$O/out.header"
echo "$W $H" > "$O/size"; cp map.txt "$O/map.txt"
