#!/usr/bin/env bash
# B0 step 2: the same frozen display step for every retinal image, for Ldmax 50 / 100 / 200 (phone
# peak x0.5 / x1 / x2); the temporal-glare sequence (k=1, 6 s at 24 fps); measurements;
# dark-bar visibility with HDR-VDP-3 (displayed bar vs no bar, PHONE, 73 px/deg, display none =
# the images are already display luminance) and the real-world reference (physical stimuli,
# 'cie' eye optics).   nix develop -c b0/run_display.sh
set -euo pipefail
O=b0/out; mkdir -p $O/display $O/vis $O/seq
jobs=()
for v in V0_none V1_iset V2_hdrvdpmtf V3_cie99 V4_spencer V5_temporal; do for k in 1 10 100; do for b in bar nobar; do for ld in 50 100 200; do
  jobs+=("$O/optics/${v}_k${k}_${b}.exr $O/display/${v}_k${k}_${b}_LD${ld} $ld")
done; done; done; done
printf '%s\n' "${jobs[@]}" | xargs -P 4 -L 1 b0/display.sh
# temporal sequence (k=1, no bar): 144 frames = 6 s of demo time
if [ ! -f $O/seq/done ]; then
  tracks/temporal-glare-2009/py.sh b0/apply_kernels.py temporal $O/stim/B0_k1_nobar.exr $O/seq/V5_k1 144 > /dev/null
  ls $O/seq/V5_k1_0*.exr | sed -E 's/\.exr$//' | xargs -P 4 -I{} b0/display.sh {}.exr {}_LD100 100
  touch $O/seq/done
fi
tracks/temporal-glare-2009/py.sh b0/measure.py
# visibility of the dark bar
vis() { tracks/hdrvdp3/run_hdrvdp.sh "$1" "$2" PHONE "$3" --display none --mtf "$4" --tasks side-by-side > /dev/null 2>&1 || true; }
for k in 1 10 100; do
  vis $O/stim/B0_k${k}_bar.exr $O/stim/B0_k${k}_nobar.exr $O/vis/WORLD_k$k cie
  for v in V0_none V1_iset V2_hdrvdpmtf V3_cie99 V4_spencer V5_temporal; do for ld in 50 100 200; do
    vis $O/display/${v}_k${k}_bar_LD${ld}_displayed_cdm2.exr $O/display/${v}_k${k}_nobar_LD${ld}_displayed_cdm2.exr $O/vis/${v}_k${k}_LD$ld hdrvdp
  done; done
done
python3 - <<'PY'
import glob, json, re
rows = []
for f in sorted(glob.glob("b0/out/vis/*/run.json")):
    t = open(f).read()
    m = re.search(r'"side-by-side":\{"P_det":([-0-9.e]+)', t)
    rows.append({"case": f.split("/")[-2], "P_det_bar": float(m.group(1)) if m else None})
json.dump(rows, open("b0/results/bar_visibility.json", "w"), indent=1)
print("\n".join(f"{r['case']:28s} {r['P_det_bar']}" for r in rows))
PY
