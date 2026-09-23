#!/usr/bin/env bash
# M1.1 colorimetry gate driver. Inputs: m0 synthetic + Fairchild McKeesPub (cd/m^2), M1 scene (K=179).
set -euo pipefail
D=m1/out/colorimetry; mkdir -p "$D"
run() { # name exr hfov scale
  local n=$1 f=$2 h=$3 s=$4
  oiiotool "$f" --ch R,G,B --clamp:min=0 -o "$D/${n}_in.exr"
  for m in A B AB; do
    m1/pcond_colorimetric.sh "$f" "$h" $m "$D/${n}_$m.hdr" "$s"
    oiiotool "$D/${n}_$m.hdr" -o "$D/${n}_$m.exr"
    oiiotool "$D/${n}_$m.pcond.hdr" -o "$D/${n}_$m.pcond.exr"
  done
  # old M1 route: same data, no PRIMARIES header (mislabelled as Radiance-standard RGB)
  read -r W H < <(oiiotool --info "$f" | sed -E 's/.* : +([0-9]+) x +([0-9]+),.*/\1 \2/')
  local v; v=$(awk -v h="$h" -v W="$W" -v H="$H" 'BEGIN{pi=atan2(0,-1); print 2*atan2(sin(h*pi/360)/cos(h*pi/360)*H/W,1)*180/pi}')
  oiiotool "$f" --ch R,G,B --clamp:min=0 --mulc "$s" -o "$D/${n}_old_raw.hdr"
  getinfo -a "VIEW= -vtv -vh $h -vv $v" < "$D/${n}_old_raw.hdr" > "$D/${n}_old_in.hdr"
  KEEP_CAPPED="$D/${n}_old.hdr" m1/pcond_keep_hue.sh "$D/${n}_old_in.hdr" "$D/${n}_old_cg.hdr"
  oiiotool "$D/${n}_old.hdr" -o "$D/${n}_old.exr"
}
run synthetic m0/data/synthetic_night.exr 60 0.00558659
run mckeespub m0/data/fairchild_McKeesPub_cdm2.exr 60 0.00558659
run scene m1/out/scene.exr 60 1
python3 m1/check_colorimetry.py "$D"
