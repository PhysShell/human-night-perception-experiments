#!/usr/bin/env python3
"""D1-A2, exactly as d1/axis_a2/PREREG.md: literal Wanat & Mantiuk 2014 §4.1.2 local contrast on S1 (raw m and,
as sensitivity, m clamped at 0), on top of the frozen A1 curve and frozen B chromaticity.
  tracks/temporal-glare-2009/py.sh d1/axis_a2/run.py -> results.json, sheet_S1.png"""
import json, os, sys
import numpy as np, OpenImageIO as oiio
from scipy.ndimage import gaussian_filter, label, binary_dilation, binary_erosion, distance_transform_edt
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")); os.chdir(REPO)
sys.path.insert(0, "d1/axis_a"); sys.path.insert(0, "d0")
from wanat_global import csf, S_ABS, MT_CAP, apply
exec(open("d1/chroma_b4/run.py").read().split("res = {")[0])          # B: filament(), stage(), uv(), M709, WU
from display_model import decode
RPPD, N = 73.0, 5
def Gm(M): M = np.minimum(M, MT_CAP); return 0.5 * np.log10((1 + M) / (1 - M))
def Gt_px(rho, L): return Gm(1.0 / (S_ABS * csf(rho, np.maximum(L, 1e-12))))

img = oiio.ImageBuf("d0/work/inputs/S1.exr").get_pixels(oiio.FLOAT)[..., :3].astype(np.float64); H, W = img.shape[:2]
phys = img.reshape(-1, 3); Y = (phys @ M709[1]).reshape(H, W); l = np.log10(np.maximum(Y, 1e-12))
# frozen A1 curve
sc = json.load(open("d1/axis_a/scene.json")); Tl, Tv = np.array(sc["curve"]["l"]), np.array(sc["curve"]["T"])
lA1 = np.log10(apply(Tl, Tv, np.clip(Y, 10 ** sc["curve"]["lmin"], 10 ** sc["curve"]["lmax"])))
# pyramid (declared filter), base from A1
lows = [l] + [gaussian_filter(l, 2.0 ** (k - 1)) for k in range(1, N + 1)]
P = [lows[k - 1] - lows[k] for k in range(1, N + 1)]
base = gaussian_filter(lA1, 2.0 ** (N - 1)); Ybase = 10 ** base
rhos = [2.0 ** -(k + 1) * RPPD for k in range(1, N + 1)]
CK = []; M = []; diag = []
for k in range(1, N + 1):
    s = 0.5 * RPPD / rhos[k - 1]                                             # Eq. 14 -> 2,4,8,16,32 px
    c = np.sqrt(np.maximum(gaussian_filter((l - gaussian_filter(l, s)) ** 2, s), 0))   # Eq. 13
    m = np.where(c >= 1e-9, (c - Gt_px(rhos[k - 1], Y) + Gt_px(rhos[k - 1], Ybase)) / np.where(c >= 1e-9, c, 1), 0.0)  # Eq. 17; c~0 -> band 0
    CK.append(c); M.append(m); Pk = P[k - 1]
    diag.append({"k": k, "rho_cpd": rhos[k - 1], "sigma_px": s, "frac_px_m_neg": float((m < 0).mean()),
                 "frac_abs_band_m_neg": float(np.abs(Pk)[m < 0].sum() / max(np.abs(Pk).sum(), 1e-30)),
                 "m_median": float(np.median(m)), "m_p1": float(np.percentile(m, 1)), "m_p99": float(np.percentile(m, 99))})
# regions (A2-K0 definition)
m0 = dict(np.load("d0/work/inputs/masks/S1.npz")); sky = m0["sky"]; L_sky = np.median(Y[sky])
hor = int(np.flatnonzero(m0["ground"].any(1)).min()); above = np.zeros_like(sky); above[:hor - 12, :] = True
dark = (Y < 0.5 * L_sky) & above; lab, n = label(dark); sz = np.bincount(lab.ravel()); sz[0] = 0
trees = np.isin(lab, np.argsort(sz)[::-1][:2])
dist = distance_transform_edt(~trees); ring = (dist >= 5) & (dist <= 20) & above & ~trees; far = (dist > 60) & sky
inner = trees & ~binary_erosion(trees, iterations=2); outer = binary_dilation(trees, iterations=2) & ~trees & above
_, (iy, ix) = distance_transform_edt(~inner, return_indices=True)
oy, ox = np.nonzero(outer); py, px = iy[oy, ox], ix[oy, ox]; srcpol = Y[oy, ox] > Y[py, px]
t = lambda L: L / (L + 0.108)
b = stage(filament(phys), Y.ravel(), t(Y.ravel()), "uv"); Yb = b @ M709[1]
lamp = m0["lamp"]; res = {"prereg": "d1/axis_a2/PREREG.md", "bands": diag, "variants": {}}
out_imgs = {}
for var in ("raw", "clamp0"):
    lt = base + sum(P[k] * (M[k] if var == "raw" else np.maximum(M[k], 0)) for k in range(N))
    Yt = 10 ** lt; clipped = float(((Yt < 0.1) | (Yt > 100)).mean()); Yt = np.clip(Yt, 0.1, 100)
    x = b * (Yt.ravel() / np.where(Yb > 0, Yb, 1))[:, None]
    v = np.clip((x - 0.1) / (100 - 0.1), 0, 1); code = np.where(v <= 0.0031308, 12.92 * v, 1.055 * v ** (1 / 2.4) - 0.055).reshape(H, W, 3)
    XYZ, _ = decode(code, "SDR100", "DARK"); Ye = XYZ[..., 1]; E = XYZ.reshape(-1, 3)
    ok = ~((x > 100).any(1) | (x < 0.1).any(1)); s_ = E[:, 0] + 15 * E[:, 1] + 3 * E[:, 2]
    duv = np.hypot(4 * E[:, 0] / s_ - uv(b)[:, 0], 9 * E[:, 1] / s_ - uv(b)[:, 1])
    sky_d, tree_d = np.median(Ye[sky]), np.median(Ye[trees]); rev = (Ye[oy, ox] <= Ye[py, px]) & srcpol
    r = {"clipped_to_display_range": clipped, "sky_median": float(sky_d), "lamp_median": float(np.median(Ye[lamp])),
         "poplar_median": float(tree_d), "silhouette_weber": float(1 - tree_d / sky_d),
         "silhouette_weber_D0_tree_mask": float(1 - np.median(Ye[m0["tree"]]) / sky_d),
         "ring_median": float(np.median(Ye[ring])), "far_sky_median": float(np.median(Ye[far])),
         "edge_pairs": int(srcpol.sum()), "edge_reversal_frac": float(rev.sum() / max(srcpol.sum(), 1)),
         "duv_max_unclipped": float(duv[ok].max()) if ok.any() else None, "frac_channel_below_black": float((x < 0.1).any(1).mean())}
    r["gates"] = {"A2-S1 sky<=2": r["sky_median"] <= 2, "A2-S2 lamp/sky>=10": r["lamp_median"] / r["sky_median"] >= 10,
                  "A2-S3 silhouette>=0.1": r["silhouette_weber"] >= 0.1, "A2-S4 B untouched": (r["duv_max_unclipped"] or 0) <= 1e-6,
                  "A2-AR1 poplar<ring": r["poplar_median"] < r["ring_median"], "A2-AR2 reversals<=5%": r["edge_reversal_frac"] <= 0.05,
                  "A2-AR3 halo within 1.5x": 1 / 1.5 <= r["ring_median"] / r["far_sky_median"] <= 1.5}
    r["gates"] = {k: bool(v) for k, v in r["gates"].items()}; r["pass"] = all(r["gates"].values())
    res["variants"][var] = r; out_imgs[var] = code
json.dump(res, open("d1/axis_a2/results.json", "w"), indent=1)
os.makedirs("d1/axis_a2/.cache", exist_ok=True)
for var, code in out_imgs.items():
    o = oiio.ImageBuf(oiio.ImageSpec(W, H, 3, oiio.UINT16)); o.set_pixels(oiio.ROI(0, W, 0, H, 0, 1, 0, 3), np.ascontiguousarray(code, np.float32)); o.write(f"d1/axis_a2/.cache/S1_A2_{var}__PHONE_SDR100_DARK.png")
fig, axs = plt.subplots(3, 2, figsize=(14, 9))
for j, var in enumerate(("raw", "clamp0")):
    c = out_imgs[var]; r = res["variants"][var]
    axs[0, j].imshow(c[::2, ::2]); axs[0, j].set_title(f"A2 {var}: SDR100 codes as delivered | sky {r['sky_median']:.3g}, poplar Weber {r['silhouette_weber']:.3f}, reversals {r['edge_reversal_frac']:.2f} | PASS={r['pass']}", fontsize=7, loc="left")
    axs[1, j].imshow(np.clip(c[120:430, 40:260] * 8, 0, 1)); axs[1, j].set_title(f"{var}: poplar crop, codes x8 (DIAGNOSTIC stretch, not the delivered image)", fontsize=7, loc="left")
for ax in axs[:2].ravel(): ax.axis("off")
for k, d in enumerate(diag):
    axs[2, 0].bar(k, d["frac_abs_band_m_neg"], color="C3"); axs[2, 1].bar(k, d["m_median"], color="C0")
axs[2, 0].set(title="fraction of |P_k| where m_k < 0 (raw)", xticks=range(N), xticklabels=[f"{d['rho_cpd']:.2f} cpd" for d in diag])
axs[2, 1].set(title="median m_k", xticks=range(N), xticklabels=[f"{d['rho_cpd']:.2f} cpd" for d in diag])
plt.tight_layout(); plt.savefig("d1/axis_a2/sheet_S1.png", dpi=90)
for d in diag: print("band", d)
for var, r in res["variants"].items(): print(var, json.dumps({k: v for k, v in r.items()}, indent=None)[:900])
for p in ("d1/chroma_b4/.cache/i.f32", "d1/chroma_b4/.cache/o.f32"):
    if os.path.exists(p): os.remove(p)
