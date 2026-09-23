#!/usr/bin/env bash
# M2 renders: the M1 scene (same camera, lamps, trees) in vacuum and through three
# boundary-layer atmospheres, M2 lamps (camera-visible sphere + 180 deg spot) in all four.
# Half resolution (same 60 deg FOV), 512 samples, CPU (~14 min per atmosphere on 4 cores).
set -euo pipefail
SPP=${SPP:-512}
mkdir -p m2/out
for a in vacuum clear mild moderate; do
  SECONDS=0
  M2_HALF_RES=1 blender -b --factory-startup --python m1/scene.py -- "m2/out/scene_$a.exr" "$SPP" "$a" > "m2/out/render_$a.log" 2>&1
  echo "$a: ${SECONDS}s"
done
