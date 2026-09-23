#!/usr/bin/env bash
# Renders the ribbon test view of the real scene for vacuum/clear/mild (128 spp, ~30 s each),
# runs the frozen pcond stage, then t2/haze_metamorphic.py.
set -euo pipefail
D=${1:-t2/out/haze}; mkdir -p "$D"
for a in vacuum clear mild; do
  T2_VIEW=ribbon blender -b --factory-startup --python m1/scene.py -- "$D/scene_$a.exr" 128 "$a" > "$D/render_$a.log" 2>&1
  m1/pcond_colorimetric.sh "$D/scene_$a.exr" 8 LC "$D/lc_$a.hdr" 1
done
python3 t2/haze_metamorphic.py "$D"
