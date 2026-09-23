#!/usr/bin/env bash
# M2.5 regression: a canonical 4-frame walking clip renders and displays consistently.
#   m25/golden_clip.sh check  [outdir]   render + compare against m25/golden/  (exit 1 on failure)
#   m25/golden_clip.sh update            re-render and overwrite m25/golden/    (deliberate only)
# Same scene and passes as the real clips (m25/render_clip.sh) at the T2 golden view (320x137,
# 60 deg), clear, walking 3 m/s (fast, so that 4 frames differ), haze 16 spp, fixed seed;
# through the motion stack (m25/display_clip.sh: LC + clipgamut). Per frame, thresholds as in
# t2/golden.sh: scene (haze + lamps, cd/m^2) |d| > 1e-4 AND > 5 % on <= 1 % of pixels; the
# displayed PNG --fail 0.016 --failpercent 1. The hard invariants (m25/check_clip.py) must hold.
set -euo pipefail
MODE=${1:-check}; OUT=${2:-m25/out/golden_clip}; REF=m25/golden
rm -rf "$OUT"; mkdir -p "$OUT"
T2_VIEW=golden m25/render_clip.sh "$OUT" 4 3 16 0 clear
m25/display_clip.sh "$OUT" > /dev/null
python3 m25/check_clip.py "$OUT"
status=0
for f in 0001 0002 0003 0004; do
  oiiotool "$OUT/haze_$f.exr" "$OUT/lamps_$f.exr" --add --ch R,G,B --mulc 179 -d half --compression zip \
    -o "$OUT/scene_$f.exr"
  if [ "$MODE" = update ]; then
    mkdir -p "$REF"; cp "$OUT/scene_$f.exr" "$REF/scene_$f.exr"; cp "$OUT/png/$f.png" "$REF/display_$f.png"
    continue
  fi
  idiff -fail 1e-4 -failrelative 0.05 -failpercent 1 -warn 1e-4 -warnrelative 0.01 \
    "$REF/scene_$f.exr" "$OUT/scene_$f.exr" > "$OUT/idiff_scene_$f.txt" 2>&1 || status=1
  idiff -fail 0.016 -failpercent 1 "$REF/display_$f.png" "$OUT/png/$f.png" > "$OUT/idiff_display_$f.txt" 2>&1 || status=1
  echo "frame $f: scene $(tail -1 "$OUT/idiff_scene_$f.txt")  display $(tail -1 "$OUT/idiff_display_$f.txt")"
done
[ "$MODE" = update ] && echo "updated $REF" && exit 0
[ $status = 0 ] && echo "PASS" || echo "FAIL"
exit $status
