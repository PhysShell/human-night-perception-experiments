#!/usr/bin/env bash
# Frozen axis-A extraction commands (d1/a_extract/axis_a_x.sh) on the 48 S2 frames -> d1/a_extract/.cache/S2/frame_NNNN/
#   nix develop -c d1/display_r/run_s2_ax.sh
set -euo pipefail; cd "$(dirname "$0")/../.."
h=$(python3 -c "import json;m=json.load(open('d0/work/inputs/manifest.json'))['scenes']['S2'];print(m['size'][0]/m['scene_px_per_deg'])")
for f in $(seq -f %04g 1 48); do d1/a_extract/axis_a_x.sh d0/work/inputs/S2/frame_$f.exr "$h" d1/a_extract/.cache/S2/frame_$f; done; echo AX S2 done
