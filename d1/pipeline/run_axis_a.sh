#!/usr/bin/env bash
# Batch driver for the frozen axis A (axis_a.sh) over the acceptance corpus -> d1/pipeline/.cache/A.
# HFOV = image width / scene px/deg from d0/work/inputs/manifest.json; F1 at 30 deg (PREREG).
#   tracks/temporal-glare-2009/py.sh d1/pipeline/make_f1.py && nix develop -c d1/pipeline/run_axis_a.sh
set -euo pipefail
cd "$(dirname "$0")/../.."; A=d1/pipeline/.cache/A; mkdir -p $A/S2
hf() { python3 -c "import json;m=json.load(open('d0/work/inputs/manifest.json'))['scenes']['$1'];print(m['size'][0]/m['scene_px_per_deg'])"; }
for s in S0 S1 S3_bar S3_nobar S4 S5; do d1/pipeline/axis_a.sh d0/work/inputs/$s.exr "$(hf ${s%%_*})" $A/$s.exr; echo A $s; done
d1/pipeline/axis_a.sh d1/pipeline/.cache/F1.exr 30 $A/F1.exr; echo A F1
h=$(hf S2); for f in $(seq -f %04g 1 48); do d1/pipeline/axis_a.sh d0/work/inputs/S2/frame_$f.exr "$h" $A/S2/frame_$f.exr; done; echo A S2
