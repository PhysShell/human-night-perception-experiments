#!/usr/bin/env python3
"""Verify m1/fog_glow.py on a single-pixel source: energy conservation and angular profile
against Spencer et al. 1995 Eq. 5 (photopic), with theta = pixel distance * HFOV / width.
The analytic PSF below is the *test oracle* (published formula), not part of the pipeline."""
import sys
import numpy as np
import OpenImageIO as oiio

src, glare, hfov = sys.argv[1], sys.argv[2], float(sys.argv[3])
a = oiio.ImageBuf(src).get_pixels(oiio.FLOAT)[..., 0]
g = oiio.ImageBuf(glare).get_pixels(oiio.FLOAT)[..., 0]
H, W = a.shape
cy, cx = np.unravel_index(a.argmax(), a.shape)
deg_px = hfov / max(W, H)

def spencer(t):
    return (0.384 * 2.61e6 * np.exp(-(t / 0.02) ** 2)
            + 0.478 * 20.91 / (t + 0.02) ** 3 + 0.138 * 72.37 / (t + 0.02) ** 2)

energy = g.sum() / a.sum()
failures = []
if energy < 0.97:
    failures.append(f"energy out/in {energy:.4f} < 0.97")
print(f"energy out/in = {energy:.4f}   (1 - fraction scattered outside the frame)")
print(f"centre pixel keeps {g[cy, cx] / a.sum():.4f} of the source")
ref_r = 32                                      # 1 degree at 32 px/deg
ref = g[cy, cx + ref_r]
print(" theta_deg  measured/ref  spencer/ref   ratio  tolerance")
# tolerances: the kernel is exact up to a few degrees; far out, FFT padding/frame edge dominate
for r, tol in ((3, .02), (10, .02), (32, 0.0), (96, .02), (320, .05), (640, None)):
    t = r * deg_px
    m = g[cy, cx + r] / ref
    s = spencer(t) / spencer(ref_r * deg_px)
    ok = tol is None or abs(m / s - 1) <= tol + 1e-6
    if not ok:
        failures.append(f"theta {t:.3f} deg: ratio {m / s:.3f} outside +-{tol}")
    print(f"{t:10.3f}  {m:12.4e}  {s:11.4e}  {m / s:6.3f}  {'info' if tol is None else f'+-{tol:.0%}'}{'' if ok else '  FAIL'}")
if failures:
    sys.exit("FOG GLOW PSF REGRESSION FAILED: " + "; ".join(failures))
print("PASS: Fog Glow reproduces Spencer et al. 1995 Eq. 5 at the calibrated Size")
