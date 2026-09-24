#!/usr/bin/env python3
"""B0 v3: CIE99 OTF sampling spot check, production 4x vs 8x (b0/hdrvdp_optics.m B0_SS).
A full 12 x 6 deg field at 8x is a 7008 x 3504 grid (FFT at twice that), so the check runs on a
3 x 3 deg crop centred on the source of the achromatic stimulus (k = 1 and k = 100, no bar). Both
grids see the same crop, so this tests sampling only, not the far glare tail cut by the crop.
Reported on the luminance of the retinal image (73 px/deg after binning): energy-weighted and peak
relative difference, the largest local difference where L > 1 % of the peak, and the retinal
luminance at 5', 15', 30' from the source.
  nix develop -c python3 b0/cie_ss_check.py   -> b0/results/cie_ss_check.json
"""
import json, subprocess
import numpy as np
import OpenImageIO as oiio

O = "b0/out/conv"; subprocess.run(f"mkdir -p {O}", shell=True, check=True)
meta = json.load(open("b0/out/stim_ach/meta.json"))
x, y = (int(v) for v in meta["source_px"]); h = 110                      # 220 px = 3.0 deg at 73 px/deg
Yw = np.array([0.2126, 0.7152, 0.0722])
res = {"crop_deg": 2 * h / 73, "grid": "73 px/deg output; OTF evaluated at 4x / 8x and area-binned"}
for k in (1, 100):
    L = {}
    for ss in (4, 8):
        p = f"{O}/cie_k{k}_ss{ss}"
        subprocess.run(f"oiiotool b0/out/stim_ach/B0_k{k}_nobar.exr --cut {2*h}x{2*h}+{x-h}+{y-h} -o {p}_in.exr && "
                       f"python3 tracks/hdrvdp3/img2raw.py {p}_in.exr {p}_in.raw && "
                       f"REPO=$PWD B0_IN={p}_in.raw B0_OUT_PREFIX={p} B0_MTF=cie B0_PPD=73 B0_SS={ss} "
                       f"tracks/hdrvdp3/octave.sh b0/hdrvdp_optics.m >/dev/null && "
                       f"python3 b0/raw2exr.py {p}_retinal.raw {p}.exr", shell=True, check=True)
        L[ss] = oiio.ImageBuf(f"{p}.exr").get_pixels(oiio.FLOAT)[..., :3].astype(float) @ Yw
    a, b = L[4], L[8]; d = np.abs(a - b); m = b > 0.01 * b.max()
    cy, cx = np.unravel_index(b.argmax(), b.shape)
    at = lambda im, am: float(im[cy, cx + int(round(am / 60 * 73))])
    res[f"k{k}"] = {"energy_weighted_rel_diff": float(d.sum() / b.sum()),
                    "peak_rel_diff": float(abs(a.max() - b.max()) / b.max()),
                    "max_local_rel_diff_where_L>1%peak": float((d[m] / b[m]).max()),
                    "L_at_arcmin_4x": {am: at(a, am) for am in (5, 15, 30)},
                    "L_at_arcmin_8x": {am: at(b, am) for am in (5, 15, 30)}}
json.dump(res, open("b0/results/cie_ss_check.json", "w"), indent=1)
print(json.dumps(res, indent=1))
