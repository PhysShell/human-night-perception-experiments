#!/usr/bin/env bash
# M2 renders: the M1 scene (same camera, lamps, trees) without a medium and through three
# boundary-layer atmospheres. Half resolution (same 60 deg FOV), 1024 samples, CPU.
set -euo pipefail
SPP=${SPP:-1024}
mkdir -p m2/out
for a in none clear mild moderate; do
  SECONDS=0
  M2_HALF_RES=1 blender -b --factory-startup --python m1/scene.py -- "m2/out/scene_$a.exr" "$SPP" "$a" > "m2/out/render_$a.log" 2>&1
  echo "$a: ${SECONDS}s"
done
