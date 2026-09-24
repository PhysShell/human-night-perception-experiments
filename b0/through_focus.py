#!/usr/bin/env python3
"""B0 v3 BEST_FOCUS_550 sensitivity: ISET 'wvf human' (Thibos mean virtual eye, 6 mm, on-axis,
monochromatic 550 nm) with every Zernike term kept as published except defocus c4 (OSA j=4), swept
-0.20 .. +0.60 um in 0.05 um steps, refined to 0.01 um over 0 .. +0.10 um (b0/iset_kernel.m B0_C4;
kernels in b0/out/focus). Reported as a GRID optimum plus near-optimal intervals (criterion within 1 % and
5 % of its maximum), so that the grid step is not read as physiological precision.
Criterion declared before the sweep was looked at:
  primary   = encircled energy within 1' radius (compactness of the core that pcond will clip);
  secondary = PSF peak on the 4x grid (a Strehl proxy).
With spherical aberration present the two need not pick the same focus; both are reported, and the
PSF metrics of the three named eyes: THIBOS_NATIVE (c4 +0.335), ZERO_DEFOCUS_550 (c4 0), BEST_FOCUS_550.
Dioptres: D = 4 sqrt(3) c4 / r^2 (r = 3 mm pupil radius, c4 in um).
  python3 b0/through_focus.py   -> b0/results/through_focus.json
"""
import glob, json, re
import numpy as np


def metrics(p):
    with open(p, "rb") as f:
        h, w, c, _ = np.fromfile(f, "<i4", 4); E = np.fromfile(f, "<f4").reshape(h, w, c)[..., 0].astype(float)
    ppd = 73 * json.load(open(p.replace(".raw", ".json")))["supersample"]
    E = np.maximum(E - np.median(E[:5, :5]), 0); E /= E.sum()
    cy, cx = np.unravel_index(E.argmax(), E.shape)
    r = np.hypot(*np.mgrid[-cy:h - cy, -cx:w - cx]) / ppd * 60
    o = np.argsort(r.ravel()); ee = np.cumsum(E.ravel()[o]); rs = r.ravel()[o]
    return {"EE_within_1arcmin": float(ee[np.searchsorted(rs, 1.0)]), "peak": float(E.max()),
            "EE_radius_arcmin": {q: float(rs[np.searchsorted(ee, q / 100)]) for q in (50, 80, 95)}}


rows = []
for p in glob.glob("b0/out/focus/iset_kernel_c4_*.raw"):
    c4 = float(re.search(r"c4_(-?[0-9.]+)\.raw", p).group(1))
    rows.append({"c4_um": c4, "defocus_D": 4 * np.sqrt(3) * c4 / 9, **metrics(p)})
rows.sort(key=lambda r: r["c4_um"])
bp = max(rows, key=lambda r: r["EE_within_1arcmin"]); bs = max(rows, key=lambda r: r["peak"])


def interval(key, frac):
    m = max(r[key] for r in rows); ok = [r["c4_um"] for r in rows if r[key] >= (1 - frac) * m]
    return [min(ok), max(ok)]
nat = min(rows, key=lambda r: abs(r["c4_um"] - 0.335))
res = {"what": __doc__.split("\n")[0], "step_um": 0.05, "rows": rows,
       "BEST_FOCUS_550_primary_EE1": {"grid_optimum_c4_um": bp["c4_um"], "defocus_D": bp["defocus_D"],
                                      "near_optimal_c4_um_within_1pct": interval("EE_within_1arcmin", 0.01),
                                      "near_optimal_c4_um_within_5pct": interval("EE_within_1arcmin", 0.05)},
       "BEST_FOCUS_550_secondary_peak": {"grid_optimum_c4_um": bs["c4_um"], "defocus_D": bs["defocus_D"],
                                         "near_optimal_c4_um_within_5pct": interval("peak", 0.05),
                                         "note": "peak on a 0.2' grid is noisy; secondary only"},
       "named_eyes": {"THIBOS_NATIVE (nearest step to +0.335)": nat,
                      "ZERO_DEFOCUS_550": next(r for r in rows if abs(r["c4_um"]) < 1e-9),
                      "BEST_FOCUS_550 (primary)": bp}}
json.dump(res, open("b0/results/through_focus.json", "w"), indent=1, default=float)
for r in rows:
    print(f"c4 {r['c4_um']:+.2f} um ({r['defocus_D']:+.3f} D)  EE(1') {r['EE_within_1arcmin']:.3f}  peak {r['peak']:.4f}  "
          f"EE50/80/95 {r['EE_radius_arcmin'][50]:.2f} {r['EE_radius_arcmin'][80]:.2f} {r['EE_radius_arcmin'][95]:.2f}'")
print(json.dumps({k: res[k] for k in ("BEST_FOCUS_550_primary_EE1", "BEST_FOCUS_550_secondary_peak")}, indent=1, default=float))
