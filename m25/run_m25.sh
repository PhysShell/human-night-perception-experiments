#!/usr/bin/env bash
# M2.5: the two clips, frozen scene (clear) and frozen stack (motion display), no scintillation.
#   A = static observer, 10 s (one frame, repeated: fixed seed, nothing moves)
#   B = observer walking sideways at 1 m/s, 10 s at 24 fps (240 frames; starts at A's frame)
# ~4 h on 4 CPU cores. Then the hard invariants for both.
#   nix develop -c m25/run_m25.sh [outdir=m25/out]
set -euo pipefail
O=${1:-m25/out}
m25/render_clip.sh "$O/A_static" 1 0 32 0 clear 24
m25/display_clip.sh "$O/A_static" 240
m25/render_clip.sh "$O/B_walk" 240 1 32 0 clear 24
m25/display_clip.sh "$O/B_walk"
for c in A_static B_walk; do echo "== $c"; python3 m25/check_clip.py "$O/$c" || true; done
