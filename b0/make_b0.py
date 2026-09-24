#!/usr/bin/env python3
"""B0 bright-point bake-off: the physical stimulus, made directly at the PHONE target density
(73 px/deg; M2.6: form the image at the display resolution), field 12 x 6 deg (876 x 438 px).

  * night sky 4e-4 cd/m^2 (the scene's sky, slightly blue as in the pack)
  * one warm (sodium-like, Rec.709 1:0.45:0.08) unresolved source at the field centre: the scene's
    road luminaire, 800 cd at 3 km -> E = 8.89e-5 lx at the eye; x10 and x100 variants
  * optional dark silhouette: a black (0 cd/m^2) bar 0.15 x 3 deg whose near edge is 0.3 deg to the
    right of the source (a poplar trunk next to a lamp): the local dark-target visibility probe
Point footprint: Cycles' Blackman-Harris 3-px window, unit energy (same convention as
stimuli/make_stimuli.py, duplicated here only for the 73 px/deg grid). Units: Y = cd/m^2.
  python3 b0/make_b0.py [outdir=b0/out/stim]
"""
import json, math, os, sys
import numpy as np
import OpenImageIO as oiio

OUT = sys.argv[1] if len(sys.argv) > 1 else "b0/out/stim"
PPD, W, H = 73.0, 876, 438
OMEGA = math.radians(1 / PPD) ** 2
E1 = 800.0 / 3000.0 ** 2
Yw = np.array([0.2126, 0.7152, 0.0722])
unit = lambda c: np.asarray(c, float) / (np.asarray(c, float) @ Yw)
SRC = (438.0, 219.0)                       # pixel corner = phase 0.5 (same as the pack)
BAR = (int(SRC[0] + 0.3 * PPD), int(SRC[0] + 0.3 * PPD) + int(round(0.15 * PPD)),
       int(SRC[1] - 1.5 * PPD), int(SRC[1] + 1.5 * PPD))


def bh(t):
    v = 2 * np.pi * (t + 0.5)
    return np.where(np.abs(t) <= 0.5, 0.35875 - 0.48829 * np.cos(v) + 0.14128 * np.cos(2 * v) - 0.01168 * np.cos(3 * v), 0)


def stim(k, bar):
    img = np.full((H, W, 3), 4e-4, np.float32) * unit([0.85, 0.9, 1.0])
    if bar:
        img[BAR[2]:BAR[3], BAR[0]:BAR[1]] = 0
    x, y = SRC
    xs, ys = np.arange(int(x) - 3, int(x) + 4), np.arange(int(y) - 3, int(y) + 4)
    w = np.outer(bh((ys + 0.5 - y) / 3), bh((xs + 0.5 - x) / 3)); w /= w.sum()
    img[ys[0]:ys[-1] + 1, xs[0]:xs[-1] + 1] += (w * k * E1 / OMEGA)[..., None] * unit([1, 0.45, 0.08])
    return img


os.makedirs(OUT, exist_ok=True)
for k in (1, 10, 100):
    for bar in (0, 1):
        img = stim(k, bar)
        b = oiio.ImageBuf(oiio.ImageSpec(W, H, 3, oiio.FLOAT))
        b.set_pixels(oiio.ROI(0, W, 0, H, 0, 1, 0, 3), img)
        b.write(f"{OUT}/B0_k{k}_{'bar' if bar else 'nobar'}.exr")
json.dump({"px_per_deg": PPD, "size_px": [W, H], "fov_deg": [W / PPD, H / PPD], "source_px": SRC,
           "E_eye_lx_k1": E1, "bar_px_x0x1y0y1": BAR, "sky_cd_m2": 4e-4, "units": "Y cd/m^2, linear Rec.709"},
          open(f"{OUT}/meta.json", "w"), indent=1)
print("B0 stimuli:", sorted(os.listdir(OUT)))
