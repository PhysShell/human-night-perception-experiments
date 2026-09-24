#!/usr/bin/env python3
"""B0 v3: are two retinal targets with a similar trunk P_det the same retinal image? Radial profile of the
lamp component (C_src1, achromatic layer, 73 px/deg) after each retinal model, normalised to the source's
total energy: energy within r, and luminance relative to the peak at r. ISET's kernel field is +-1.24 deg,
so its wings stop there (a donor field limit, not physics).
  python3 b0/retinal_profiles.py -> b0/results/retinal_profiles.json
"""
import json
import numpy as np
import OpenImageIO as oiio

meta = json.load(open("b0/out/stim_ach/meta.json")); sx, sy = meta["source_px"]
res = {}
for v, lab in (("V0_none", "none"), ("V1_iset", "ISET wavefront, 550 nm, ZERO_DEFOCUS"),
               ("V3_cie99", "CIE99 straylight"), ("V2_hdrvdpmtf", "HDR-VDP MTF straylight")):
    Y = oiio.ImageBuf(f"b0/out/comp_ach/{v}_C_src1.exr").get_pixels(oiio.FLOAT)[..., :3].astype(float) @ [0.2126, 0.7152, 0.0722]
    r = np.hypot(*np.mgrid[0:Y.shape[0], 0:Y.shape[1]] - np.array([sy, sx])[:, None, None]) / 73 * 60
    tot = oiio.ImageBuf(f"b0/out/stim_ach/C_src1.exr").get_pixels(oiio.FLOAT)[..., :3].astype(float).sum() / 3
    res[lab] = {"energy_within_arcmin": {a: float(Y[r <= a].sum() / tot) for a in (1, 3, 10, 18, 30, 60)},
                "L_rel_peak_at_arcmin": {a: float(Y[(r > a - 0.5) & (r < a + 0.5)].mean() / Y.max()) for a in (3, 10, 18, 30, 60)}}
json.dump(res, open("b0/results/retinal_profiles.json", "w"), indent=1)
for k, v in res.items():
    print(f"{k:40s} EE(1,3,10,18,30,60') " + " ".join(f"{x:.3f}" for x in v["energy_within_arcmin"].values()) +
          " | L/peak(3,10,18,30,60') " + " ".join(f"{x:.1e}" for x in v["L_rel_peak_at_arcmin"].values()))
