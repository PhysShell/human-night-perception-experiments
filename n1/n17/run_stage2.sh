#!/usr/bin/env bash
# N1.7 addendum 3 stage-2 driver, one frame at a time (disk); resumable (skips keys already in stage2.jsonl).
set -euo pipefail
export PATH=/root/.nix-profile/bin:$PATH
BL=/nix/store/pvqaxj50f35qs19slx54zwalhkcwxh4c-blender-5.2.2/bin/blender
d1/verify_manifest.sh
for V in ${@:-K0125 K0175 K0225 K0350 K0400 K0450 K0475 K0525 K0825 K0850 K0925 K0975}; do
  if [ -f n1/n17/stage2.jsonl ] && grep -q "\"key\": \"$V\"" n1/n17/stage2.jsonl; then continue; fi
  W=n1/work/view_$V; mkdir -p $W
  date -u +"%FT%TZ render $V start"
  $BL -b --factory-startup --python n1/view_render.py -- $V $W > $W/render.log 2>&1
  date -u +"%FT%TZ render $V done"
  tracks/temporal-glare-2009/py.sh n1/n17/gate.py $V 2>&1 | grep -v -i warn | tail -3
  rm -f $W/view_rgb.exr
  nix develop -c d1/a_extract/axis_a_x.sh $W/view_cdm2.exr 60 d1/a_extract/.cache/N1_$V > /dev/null
  nix develop -c d1/pipeline/axis_a.sh $W/view_cdm2.exr 60 d1/pipeline/.cache/A/N1_$V.exr > /dev/null
  tracks/temporal-glare-2009/py.sh n1/view_eval.py $V d1 > /dev/null 2>&1
  tracks/temporal-glare-2009/py.sh n1/n17/frame_eval.py $V 2>&1 | grep -v -i warn
  rm -rf d1/a_extract/.cache/N1_$V d1/pipeline/.cache/A/N1_$V.exr $W/view_cdm2.exr
  df -h / | tail -1
done
d1/verify_manifest.sh
