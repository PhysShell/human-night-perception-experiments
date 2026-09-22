#!/usr/bin/env bash
# pcond -s -c with warm light colour kept -- Radiance tools only, no new formula.
#
# Why this exists (verified in pcond source, Radiance master bcffc2b):
#  * sub-pixel lamps lie above the top of pcond's 1-degree foveal histogram, so
#    mapscan() maps them 1e3..1e4 x above display max while keeping RGB ratios;
#  * the colour dies only in matscan() -> clipgamut(), whose "brightness > max"
#    branch returns pure white. matscan() runs whenever the input has a
#    PRIMARIES= header (inprims != outprims is a pointer comparison).
# Route:
#  1. pcond -s -c on an input WITHOUT PRIMARIES -> no matscan, colour survives,
#     luminance of lamps overshoots; -x writes pcond's own world->display curve.
#  2. pcomb: where pcond overshot display max (Yp>1), rescale that pixel to the
#     display luminance pcond's curve assigns to its world luminance (tabfunc of
#     the -x table). Every other pixel is pcond's output, untouched.
#  3. pcond -l -e 1 with PRIMARIES = Radiance standard primaries: identity colour
#     matrix, but matscan() now runs clipgamut() in its in-range branch, which
#     desaturates toward equal-brightness grey (Radiance's own hue-preserving clip).
#
# usage: pcond_keep_hue.sh in_world.hdr(no PRIMARIES, has VIEW) out.hdr [extra pcond flags]
set -euo pipefail
IN=$1 OUT=$2; shift 2
T=$(mktemp -d); trap 'rm -rf "$T"' EXIT

pcond -s -c "$@" -x "$T/map.dat" "$IN" > "$T/mapped.hdr"

# display luminance range used by pcond (defaults -u 100 -d 100 unless overridden)
LDMAX=100 LDDYN=100
while [ $# -gt 0 ]; do case $1 in -u) LDMAX=$2; shift;; -d) LDDYN=$2; shift;; esac; shift; done

pcomb -e "$(tabfunc -i Ld < "$T/map.dat")" \
      -e "ldmax=$LDMAX; ldmin=ldmax/$LDDYN; Lw=179*li(1); Yp=li(2);" \
      -e "Yd=(Ld(Lw)-ldmin)/(ldmax-ldmin); s=if(Yp-1, Yd/Yp, 1);" \
      -e "ro=s*ri(2); go=s*gi(2); bo=s*bi(2)" \
      "$IN" "$T/mapped.hdr" > "$T/capped_raw.hdr"

getinfo -a "PRIMARIES= 0.640 0.330 0.290 0.600 0.150 0.060 0.3333 0.3333" \
  < "$T/capped_raw.hdr" > "$T/capped.hdr"
[ -n "${KEEP_CAPPED:-}" ] && cp "$T/capped_raw.hdr" "$KEEP_CAPPED"   # for comparing other gamut mappers
pcond -l -e 1 "$T/capped.hdr" > "$OUT"
