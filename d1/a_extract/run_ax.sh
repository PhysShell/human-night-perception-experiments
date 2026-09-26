#!/usr/bin/env bash
# Runs axis_a_x.sh on F1 and every still -> d1/a_extract/.cache/<scene>/   (nix develop -c d1/a_extract/run_ax.sh)
set -euo pipefail; cd "$(dirname "$0")/../.."
hf() { python3 -c "import json;m=json.load(open('d0/work/inputs/manifest.json'))['scenes']['$1'];print(m['size'][0]/m['scene_px_per_deg'])"; }
d1/a_extract/axis_a_x.sh d1/pipeline/.cache/F1.exr 30 d1/a_extract/.cache/F1; echo AX F1
for s in S0 S1 S3_bar S3_nobar S4 S5; do d1/a_extract/axis_a_x.sh d0/work/inputs/$s.exr "$(hf ${s%%_*})" d1/a_extract/.cache/$s; echo AX $s; done
