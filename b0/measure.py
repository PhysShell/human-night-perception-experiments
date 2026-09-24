#!/usr/bin/env python3
"""B0 measurements on the displayed images (cd/m^2 on the PHONE target, 73 px/deg) and on the
Vangorp adaptation maps. No perceptual claim is made here; these are the numbers behind the
blind comparison.
  python3 b0/measure.py   (reads b0/out/, writes b0/results/)
"""
import glob, json, math, os, re
import numpy as np
import OpenImageIO as oiio
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

D, R = "b0/out", "b0/results"
os.makedirs(R, exist_ok=True)
meta = json.load(open(f"{D}/stim/meta.json"))
PPD = meta["px_per_deg"]; ARC = 60 / PPD; OM = math.radians(1 / PPD) ** 2
sx, sy = meta["source_px"]; cx, cy = int(sx), int(sy)
bx0, bx1, by0, by1 = meta["bar_px_x0x1y0y1"]
Yw = np.array([0.2126, 0.7152, 0.0722])
load = lambda p: oiio.ImageBuf(p).get_pixels(oiio.FLOAT)[..., :3]
VAR = ["V0_none", "V1_iset", "V2_hdrvdpmtf", "V3_cie99", "V4_spencer", "V5_temporal"]
yy, xx = np.mgrid[0:438, 0:876]
rr = np.hypot(xx + 0.5 - sx, yy + 0.5 - sy) / PPD            # deg from the source


def radial(L, edges):
    idx = np.digitize(rr.ravel(), edges) - 1
    return np.array([L.ravel()[idx == i].mean() if (idx == i).any() else np.nan for i in range(len(edges) - 1)])


rows, prof = [], {}
edges = np.r_[0, np.geomspace(0.5 / PPD, 3.0, 40)]
for f in sorted(glob.glob(f"{D}/display/*_nobar_LD*_displayed_cdm2.exr")):
    m = re.search(r"(V\d_\w+?)_k(\d+)_nobar_LD(\d+)_displayed", f)
    v, k, ld = m.group(1), int(m.group(2)), int(m.group(3))
    img = load(f); L = img @ Yw
    black = ld / 100
    bg = np.median(L)
    dl = (img - black) / ld                                   # display-linear 0..1
    peak = L.max()
    half = (L - bg) >= 0.5 * (peak - bg)
    white = (dl >= 0.98).any(-1) & (rr < 1.0)
    p = radial(L, edges)
    halo = edges[1:][np.flatnonzero(p >= 2 * bg)[-1]] * 60 if (p >= 2 * bg).any() else 0.0
    lla = load(f"{D}/optics/{v}_k{k}_bar_Lla.exr")[..., 0] if os.path.exists(f"{D}/optics/{v}_k{k}_bar_Lla.exr") else None
    row = {"variant": v, "k": k, "Ldmax": ld, "peak_display_cdm2": float(peak), "background_cdm2": float(bg),
           "core_fwhm_equiv_diam_arcmin": float(2 * math.sqrt(half.sum() / math.pi) * ARC),
           "white_core_px": int(white.sum()), "white_core_arcmin2": float(white.sum() * ARC ** 2),
           "displayed_energy_above_bg_cdm2_sr": float(((L - bg).clip(0) * OM).sum()),
           "halo_radius_2x_bg_arcmin": float(halo)}
    if lla is not None:
        row.update({"Vangorp_Lla_at_source": float(lla[cy, cx]), "Vangorp_Lla_at_bar": float(lla[(by0 + by1) // 2, (bx0 + bx1) // 2]),
                    "Vangorp_Lla_far_sky": float(np.median(lla[:40, :40]))})
    rows.append(row)
    if ld == 100:
        prof[(v, k)] = p
json.dump(rows, open(f"{R}/metrics.json", "w"), indent=1)
with open(f"{R}/metrics.csv", "w") as fh:
    keys = list(rows[0].keys()) + [k for k in rows[-1] if k not in rows[0]]
    fh.write(",".join(keys) + "\n")
    for r in rows:
        fh.write(",".join(f"{r.get(k, '')}" for k in keys) + "\n")
for k in (1, 10, 100):
    plt.figure(figsize=(7, 4.5))
    for v in VAR:
        if (v, k) in prof:
            plt.loglog(edges[1:] * 60, prof[(v, k)], label=v)
    plt.axhline(1.0 + 4e-4, color="grey", lw=0.5)
    plt.xlabel("angle from the source [arcmin]"); plt.ylabel("displayed luminance, azimuthal mean [cd/m²]")
    plt.title(f"B0 radial profiles on PHONE (Ldmax 100), source x{k}"); plt.legend(fontsize=8); plt.grid(True, which="both", lw=0.3)
    plt.tight_layout(); plt.savefig(f"{R}/radial_profiles_k{k}.png", dpi=110); plt.close()
print(f"{len(rows)} rows -> {R}/metrics.csv")
