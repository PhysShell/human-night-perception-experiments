#!/usr/bin/env bash
# Regression test for the Blender Fog Glow adapter (m1/fog_glow.py): single-pixel source,
# 1920x820, HFOV 60 deg -> profile must follow Spencer'95 Eq. 5, energy must be conserved.
set -euo pipefail
T=${1:-$(mktemp -d)}
mkdir -p "$T"
python3 -c "
import numpy as np, OpenImageIO as o, sys
a=np.zeros((820,1920,3),np.float32); a[410,960]=1e4
o.ImageBuf(a).write(sys.argv[1])" "$T/point.exr"
blender -b --factory-startup --python "$(dirname "$0")/fog_glow.py" -- "$T/point.exr" "$T/point_glare.exr" 60 \
  2>&1 | grep -E "fog glow|adapter verified" || true
python3 "$(dirname "$0")/check_fog_glow.py" "$T/point.exr" "$T/point_glare.exr" 60
