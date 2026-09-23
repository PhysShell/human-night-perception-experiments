#!/usr/bin/env python3
"""T2 metamorphic test: vacuum -> clear -> mild on the real scene (m1/scene.py, T2_VIEW=ribbon:
an 8 x 2 deg window on the lamp ribbon around 4 km), through the frozen M1.1 pcond stage.

Denser medium must give, with no oracle needed for the exact values:
  * less direct lamp energy (background-subtracted window sum)          strictly decreasing
  * no higher lamp contrast (peak / background), scene and display     non-increasing
  * no narrower ribbon (RMS angular width of the background-subtracted
    vertical profile, scene luminance)                                  non-decreasing
  * finite values everywhere (no NaN/Inf), scene and display
'moderate' is deliberately not a gate: single scattering is known to misrepresent it (M2).
usage: haze_metamorphic.py DIR   (DIR/scene_<case>.exr and DIR/lc_<case>.hdr from the runner)
"""
import sys
import numpy as np
import OpenImageIO as oiio

D = sys.argv[1]
CASES = ["vacuum", "clear", "mild"]
Yw = np.array([0.2126, 0.7152, 0.0722])
load = lambda p: oiio.ImageBuf(p).get_pixels(oiio.FLOAT)[..., :3]
S = {c: load(f"{D}/scene_{c}.exr") * 179 for c in CASES}
L = {c: load(f"{D}/lc_{c}.hdr") for c in CASES}
H, W = S["vacuum"].shape[:2]
arcmin = 8.0 * 60 / W
r0 = int(np.argmax((S["vacuum"] @ Yw).sum(1)))                  # ribbon row (vacuum)
win, bg = slice(r0 - 3, r0 + 4), np.r_[r0 - 14:r0 - 9, r0 + 10:r0 + 15]
fails = []
m = {}
for c in CASES:
    Ys, Yd = S[c] @ Yw, L[c] @ Yw
    finite = np.isfinite(S[c]).all() and np.isfinite(L[c]).all()
    b = np.median(Ys[bg])
    energy = (Ys[win] - b).sum()
    contrast_s = np.percentile(Ys[win], 99.5) / max(b, 1e-12)
    contrast_d = np.percentile(Yd[win], 99.5) / max(np.median(Yd[bg]), 1e-6)
    prof = np.clip(Ys.mean(1) - b, 0, None)
    rows = np.arange(H)
    width = 2 * np.sqrt((prof * (rows - r0) ** 2).sum() / prof.sum()) * arcmin
    m[c] = dict(finite=finite, energy=energy, cs=contrast_s, cd=contrast_d, width=width)
    print(f"{c:7s} finite {finite}  direct energy {energy:9.2f}  contrast scene {contrast_s:9.1f}  "
          f"display {contrast_d:7.1f}  ribbon RMS width {width:5.2f} arcmin")
    if not finite:
        fails.append(f"{c}: NaN/Inf")
for a, b in zip(CASES, CASES[1:]):
    checks = [("direct energy decreases", m[b]["energy"] < m[a]["energy"]),
              ("scene contrast does not increase", m[b]["cs"] <= m[a]["cs"] * 1.02),
              ("display contrast does not increase", m[b]["cd"] <= m[a]["cd"] * 1.02),
              ("ribbon does not get narrower", m[b]["width"] >= m[a]["width"] * 0.98)]
    for name, ok in checks:
        print(f"  {a} -> {b}: {name:36s} {'ok' if ok else 'FAIL'}")
        if not ok:
            fails.append(f"{a}->{b}: {name}")
if fails:
    sys.exit("HAZE METAMORPHIC TEST FAILED: " + "; ".join(fails))
print("PASS")
