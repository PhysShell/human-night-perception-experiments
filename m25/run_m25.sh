#!/usr/bin/env bash
# M2.5: the two clips, frozen scene (clear) and frozen stack, no scintillation.
#   A = static observer, 10 s (one frame, repeated: fixed seed, nothing moves)
#   B = observer walking sideways at 1 m/s, 10 s at 24 fps (240 frames; starts at A's frame)
# Both displays: clipgamut (frozen motion variant) and PBR Neutral on out-of-gamut pixels
# (frozen stills variant). ~3 h on 4 CPU cores. Then invariants, lamp tracks, viewing copies.
# Resume an interrupted render with HAZE_START / LAMPS_START / OCC_START (m25/render_clip.sh).
#   nix develop -c m25/run_m25.sh [outdir=m25/out]
set -euo pipefail
O=${1:-m25/out}
m25/render_clip.sh "$O/A_static" 1 0 32 0 clear 24
m25/render_clip.sh "$O/B_walk" 240 1 32 0 clear 24
for c in A_static B_walk; do
  m25/display_clip.sh "$O/$c" 240
  DISPLAY=pbr_oog m25/display_clip.sh "$O/$c" 240
  for p in png png_pbr; do echo "== $c $p"; python3 m25/check_clip.py "$O/$c" "$p" || true; done
done
M2_HALF_RES=1 M25_FRAMES=240 M25_WALK=1 M25_FPS=24 M25_TRACKS="$O/B_walk/tracks.json" \
  blender -b --factory-startup --python m1/scene.py -- /dev/null 1 clear > /dev/null 2>&1
for p in png png_pbr; do python3 m25/analyse_clip.py "$O/B_walk" "$O/B_walk/tracks.json" "$p"; done
m25/export_view.sh "$O" docs/m25-results
