#!/usr/bin/env bash
# N1.7 addendum 2 stage-1 driver: 41 frames t = 0..1 step 0.025, one at a time (disk). Resumable: skips t already in trace.jsonl.
set -euo pipefail
export PATH=/root/.nix-profile/bin:$PATH
BL=/nix/store/pvqaxj50f35qs19slx54zwalhkcwxh4c-blender-5.2.2/bin/blender; W=n1/work/trace; mkdir -p $W
d1/verify_manifest.sh
for i in $(seq 0 40); do
  read -r T X Y Z YAW PITCH < <(python3 -c "t=$i*0.025; print(f'{t:.3f}', 3*(1-t)+0.5*t, 47*(1-t)+18*t, 1.7, 180+171.6*t, -3*(1-t))")
  if [ -f n1/n17/trace.jsonl ] && grep -q "\"t\": $T," n1/n17/trace.jsonl; then continue; fi
  AX=N17T_$i
  $BL -b --factory-startup --python n1/n17/trace_render.py -- $X $Y $Z $YAW $PITCH $W > $W/render.log 2>&1
  tracks/temporal-glare-2009/py.sh n1/n17/trace_frame.py convert $W
  nix develop -c d1/pipeline/axis_a.sh $W/cdm2.exr 60 d1/pipeline/.cache/A/$AX.exr > /dev/null
  nix develop -c d1/a_extract/axis_a_x.sh $W/cdm2.exr 60 d1/a_extract/.cache/$AX > /dev/null
  tracks/temporal-glare-2009/py.sh n1/n17/trace_frame.py stats $W $AX $T $X $Y $Z $YAW $PITCH 2>&1 | grep -v -i warn
  rm -rf d1/a_extract/.cache/$AX d1/pipeline/.cache/A/$AX.exr $W/cdm2.exr
done
d1/verify_manifest.sh
