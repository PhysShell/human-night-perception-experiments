#!/usr/bin/env python3
"""D1-A3-K0, exactly as d1/axis_a3_pcond/PREREG.md: Y_display from pcond (-s | -s -c, path A), chromaticity from
frozen B; the A1 gates + A2 artefact gates + B-preservation + clipping. -> results.json, sheet_S1.png
  nix develop -c d1/axis_a3_pcond/run_pcond.sh; tracks/temporal-glare-2009/py.sh d1/axis_a3_pcond/recombine.py"""
import json, os, sys
import numpy as np, OpenImageIO as oiio
from scipy.ndimage import label, binary_dilation, binary_erosion, distance_transform_edt
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")); os.chdir(REPO); sys.path.insert(0, "d0")
exec(open("d1/chroma_b4/run.py").read().split("res = {")[0])          # B: filament(), stage(), uv(), M709
from display_model import decode
img = oiio.ImageBuf("d0/work/inputs/S1.exr").get_pixels(oiio.FLOAT)[..., :3].astype(np.float64); H, W = img.shape[:2]
phys = img.reshape(-1, 3); Y = (phys @ M709[1]).reshape(H, W)
t = lambda L: L / (L + 0.108)
b = stage(filament(phys), Y.ravel(), t(Y.ravel()), "uv"); Yb = b @ M709[1]
m0 = dict(np.load("d0/work/inputs/masks/S1.npz")); sky = m0["sky"]; L_sky = np.median(Y[sky]); lamp = m0["lamp"]
hor = int(np.flatnonzero(m0["ground"].any(1)).min()); above = np.zeros_like(sky); above[:hor - 12, :] = True
lab, n = label((Y < 0.5 * L_sky) & above); sz = np.bincount(lab.ravel()); sz[0] = 0; trees = np.isin(lab, np.argsort(sz)[::-1][:2])
dist = distance_transform_edt(~trees); ring = (dist >= 5) & (dist <= 20) & above & ~trees; far = (dist > 60) & sky
inner = trees & ~binary_erosion(trees, iterations=2); outer = binary_dilation(trees, iterations=2) & ~trees & above
_, (iy, ix) = distance_transform_edt(~inner, return_indices=True); oy, ox = np.nonzero(outer); py, px = iy[oy, ox], ix[oy, ox]
srcpol = Y[oy, ox] > Y[py, px]
V0 = 0.3165039339023349
res = {"prereg": "d1/axis_a3_pcond/PREREG.md", "variants": {}}; codes = {}
for var in ("s", "sc"):
    rel = oiio.ImageBuf(f"d1/axis_a3_pcond/.cache/{var}.exr").get_pixels(oiio.FLOAT)[..., :3].astype(np.float64)
    Yrel = rel @ M709[1]; Yd = 0.1 + 99.9 * Yrel
    x = b * (Yd.ravel() / np.where(Yb > 0, Yb, 1))[:, None]
    v = np.clip((x - 0.1) / 99.9, 0, 1); code = np.where(v <= 0.0031308, 12.92 * v, 1.055 * v ** (1 / 2.4) - 0.055).reshape(H, W, 3)
    XYZ, _ = decode(code, "SDR100", "DARK"); Ye = XYZ[..., 1]; E = XYZ.reshape(-1, 3)
    hi, lo = (x > 100).any(1), (x < 0.1).any(1); ok = ~hi & ~lo; s_ = E[:, 0] + 15 * E[:, 1] + 3 * E[:, 2]
    duv = np.hypot(4 * E[:, 0] / s_ - uv(b)[:, 0], 9 * E[:, 1] / s_ - uv(b)[:, 1])
    skyd = float(np.median(Ye[sky])); treed = float(np.median(Ye[trees])); rev = (Ye[oy, ox] <= Ye[py, px]) & srcpol
    r = {"Yrel_max": float(Yrel.max()), "sky_median": skyd, "lamp_median": float(np.median(Ye[lamp])), "poplar_median": treed,
         "silhouette_weber": 1 - treed / skyd, "silhouette_weber_D0_tree_mask": float(1 - np.median(Ye[m0["tree"]]) / skyd),
         "ring_median": float(np.median(Ye[ring])), "far_sky_median": float(np.median(Ye[far])), "edge_reversal_frac": float(rev.sum() / max(srcpol.sum(), 1)),
         "duv_max_unclipped": float(duv[ok].max()), "frac_channel_above_peak": float(hi.mean()), "frac_channel_below_black": float(lo.mean()),
         "sky_Yd_pre_encoding": float(np.median(Yd[sky]))}
    r["consistency_vs_V0_sky"] = r["sky_Yd_pre_encoding"] / V0
    r["gates"] = {"G1 sky<=2": skyd <= 2, "G1 lamp/sky>=10": r["lamp_median"] / skyd >= 10, "G1 silhouette>=0.1": r["silhouette_weber"] >= 0.1,
                  "G2 poplar<ring": treed < r["ring_median"], "G2 reversals<=5%": r["edge_reversal_frac"] <= 0.05,
                  "G2 halo within 1.5x": 1 / 1.5 <= r["ring_median"] / r["far_sky_median"] <= 1.5,
                  "G3 B preserved": r["duv_max_unclipped"] <= 1e-6, "G4 above-peak <=1%": r["frac_channel_above_peak"] <= 0.01}
    r["gates"] = {k: bool(v) for k, v in r["gates"].items()}; r["pass"] = all(r["gates"].values())
    res["variants"][var] = r; codes[var] = code
res["consistency_ok"] = abs(res["variants"]["sc"]["consistency_vs_V0_sky"] - 1) <= 0.05
json.dump(res, open("d1/axis_a3_pcond/results.json", "w"), indent=1)
for var, code in codes.items():
    o = oiio.ImageBuf(oiio.ImageSpec(W, H, 3, oiio.UINT16)); o.set_pixels(oiio.ROI(0, W, 0, H, 0, 1, 0, 3), np.ascontiguousarray(code, np.float32)); o.write(f"d1/axis_a3_pcond/.cache/S1_A3_{var}__PHONE_SDR100_DARK.png")
fig, axs = plt.subplots(2, 2, figsize=(14, 6.5))
for j, var in enumerate(("s", "sc")):
    c = codes[var]; r = res["variants"][var]
    axs[0, j].imshow(c[::2, ::2]); axs[0, j].set_title(f"A3 pcond -{var} (Y only) + frozen B chromaticity: SDR100 codes as delivered\nsky {r['sky_median']:.3g} cd/m^2, poplar Weber {r['silhouette_weber']:.3f}, lamps {r['lamp_median']:.3g}, PASS={r['pass']}", fontsize=7, loc="left")
    axs[1, j].imshow(np.clip(c[120:430, 40:260] * 4, 0, 1)); axs[1, j].set_title(f"-{var}: poplar crop, codes x4 (DIAGNOSTIC stretch)", fontsize=7, loc="left")
for a in axs.ravel(): a.axis("off")
plt.tight_layout(); plt.savefig("d1/axis_a3_pcond/sheet_S1.png", dpi=90)
print("consistency (-s -c sky vs V0 0.3165):", round(res["variants"]["sc"]["consistency_vs_V0_sky"], 4), "ok" if res["consistency_ok"] else "FAIL")
for var, r in res["variants"].items(): print(var, json.dumps(r)[:1100])
for p in ("d1/chroma_b4/.cache/i.f32", "d1/chroma_b4/.cache/o.f32"):
    if os.path.exists(p): os.remove(p)
