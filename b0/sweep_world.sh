#!/usr/bin/env bash
# REAL_SCENE_REFERENCE for the sweep (reference observer models, not ground truth): physical stimulus at
# 146 px/deg (converged), donor none, evaluator optics CIE99 or HDR-VDP MTF, every 3rd k of the sweep plus x1 and x10.
# B0_LAYER=ach: the achromatic B0-optics stimulus (b0/out/stim146_ach -> b0/out/sweep_world_ach).
set -euo pipefail
O=b0/out/sweep_world; ST=b0/out/stim146
if [ "${B0_LAYER:-}" = ach ]; then O=b0/out/sweep_world_ach; ST=b0/out/stim146_ach; fi
mkdir -p $O; export O ST
python3 - <<'PY'
import os, numpy as np, OpenImageIO as oiio
O, ST = os.environ["O"], os.environ["ST"]
KA = np.geomspace(0.1, 100, 31); IDX = sorted(set(range(0, 31, 3)) | {10, 20})   # every 3rd k + x1, x10
ld = lambda p: oiio.ImageBuf(p).get_pixels(oiio.FLOAT)[..., :3]
sb, sn, s1 = (ld(f"{ST}/{c}.exr") for c in ("C_sky_bar", "C_sky_nobar", "C_src1"))
for i in IDX:
    k = KA[i]
    for b, s in (("bar", sb), ("nobar", sn)):
        a = (s + k * s1).astype(np.float32); o = oiio.ImageBuf(oiio.ImageSpec(a.shape[1], a.shape[0], 3, oiio.FLOAT))
        o.set_pixels(oiio.ROI(0, a.shape[1], 0, a.shape[0], 0, 1, 0, 3), a); o.write(f"{O}/w{i:02d}_{b}.exr")
PY
for f in $O/w*_bar.exr; do i=$(basename $f _bar.exr); for m in cie hdrvdp; do echo "$f ${f/_bar/_nobar} $O/${i}_$m $m"; done; done | \
  xargs -P 2 -L 1 sh -c '[ -f "$2/run.json" ] || tracks/hdrvdp3/run_hdrvdp.sh "$0" "$1" PHONE "$2" --display none --mtf "$3" --ppd 146 --tasks side-by-side >/dev/null 2>&1'
echo world done
