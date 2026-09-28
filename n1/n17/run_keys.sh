#!/usr/bin/env bash
# N1.7 driver (n1/n17/PREREG_N17.md + amendment 1): per keyframe, one at a time (disk): render at the accepted B/C
# settings -> OIDN gate (image windows; raw EXR deleted) -> frozen A + extraction -> frozen D1 (n1/view_eval.py d1).
set -euo pipefail
export PATH=/root/.nix-profile/bin:$PATH
BL=/nix/store/pvqaxj50f35qs19slx54zwalhkcwxh4c-blender-5.2.2/bin/blender
d1/verify_manifest.sh
for V in ${@:-K070 K080 K0875}; do
  W=n1/work/view_$V; mkdir -p $W
  date -u +"%FT%TZ render $V start"
  $BL -b --factory-startup --python n1/view_render.py -- $V $W > $W/render.log 2>&1
  date -u +"%FT%TZ render $V done"
  tracks/temporal-glare-2009/py.sh n1/n17/gate.py $V
  nix develop -c d1/a_extract/axis_a_x.sh $W/view_cdm2.exr 60 d1/a_extract/.cache/N1_$V
  nix develop -c d1/pipeline/axis_a.sh $W/view_cdm2.exr 60 d1/pipeline/.cache/A/N1_$V.exr
  tracks/temporal-glare-2009/py.sh n1/view_eval.py $V d1
done
d1/verify_manifest.sh
