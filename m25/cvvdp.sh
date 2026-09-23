#!/usr/bin/env bash
# M2.5 perceptual DIAGNOSTIC (not a gate): ColorVideoVDP between two displayed clips, in JOD
# (10 = no visible difference; 1 JOD ~ 75 % of observers would pick the reference), under the
# declared reference viewing (m25/display_models_m25.json). Run inside `nix develop .#video`.
#   m25/cvvdp.sh TEST.mp4 REF.mp4 OUTDIR
set -euo pipefail
mkdir -p "$3"
cvvdp -t "$1" -r "$2" --display "${CVVDP_DISPLAY:-m25_geometric}" -c "${CVVDP_CONFIG:-$(dirname "$0")/display_models_m25.json}" \
  --device cpu --ffmpeg-cc --heatmap threshold -o "$3" 2>&1 | grep -v "^\s*$" | tail -3
