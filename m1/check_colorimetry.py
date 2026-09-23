#!/usr/bin/env python3
"""M1.1 colorimetry gate: compare pcond paths on the same inputs.

old = M1 route (Rec.709 data given to pcond WITHOUT primaries, i.e. mislabelled)
A   = Rec.709 -> XYZE (ra_xyze) -> pcond -p Rec.709 (pcond as shipped, clipped)
B   = Rec.709 -> Radiance-standard RGB (ra_xyze -r) -> pcond (unclipped) -> Y cap -> Rec.709
AB  = A where pcond did not clip, B where it did (recommended)
All values are display-linear (1 = Ldmax) before any gamut handling.
"""
import colorsys, sys
import numpy as np
import OpenImageIO as oiio

D = sys.argv[1] if len(sys.argv) > 1 else "m1/out/colorimetry"
def load(p): return oiio.ImageBuf(p).get_pixels(oiio.FLOAT)[..., :3]
Yw = np.array([0.2126, 0.7152, 0.0722])

def hue_sat(rgb):
    h, s, v = colorsys.rgb_to_hsv(*(rgb / rgb.max()))
    return round(h * 360), round(s, 2)

print("== 1. AB vs pcond's own XYZE output (oracle) on pixels pcond did not clip")
for name, scale in (("mckeespub", 1 / 179), ("synthetic", 1 / 179), ("scene", 1.0)):
    inp = load(f"{D}/{name}_in.exr") * scale * 179            # cd/m^2 per channel
    Lw = inp @ Yw
    for m in ("AB",):
        rec = load(f"{D}/{name}_{m}.exr")
        pc = load(f"{D}/{name}_{m}.pcond.exr")
        sel = (pc.max(-1) < 0.98) & (pc.min(-1) > 1e-3)
        err = np.abs(rec[sel] - pc[sel]) / pc[sel]
        print(f"  {name:10s} {m}: {sel.sum():7d} px  median rel.err {np.median(err):.4f}  p99 {np.percentile(err, 99):.4f}")

print("== 2. synthetic probes (equal photopic Y = 0.03 cd/m^2) and lamp")
regions = {"red probe": (slice(705, 755), slice(565, 615)), "blue probe": (slice(705, 755), slice(645, 695)),
           "field": (slice(600, 650), slice(900, 1000)), "sky": (slice(50, 100), slice(900, 1000))}
lamp = (372, 585)   # warm LED village light, input RGB ratio (1, .72, .42)
for m in ("old", "A", "B", "AB"):
    a = load(f"{D}/synthetic_{m}.exr")
    vals = "  ".join(f"{k} {a[r].mean(axis=(0, 1)).round(4).tolist()}" for k, r in regions.items())
    print(f"  {m:3s} {vals}")
    print(f"      lamp rgb {a[lamp].round(3).tolist()} hue/sat {hue_sat(a[lamp])}   (input hue/sat {hue_sat(np.array([1, .72, .42]))})")

print("== 3. A vs B vs old: mean |difference| of display-linear values")
for name in ("synthetic", "mckeespub", "scene"):
    x = {m: load(f"{D}/{name}_{m}.exr").clip(0, 1) for m in ("old", "A", "B", "AB")}
    print(f"  {name:10s} |A-B| {np.abs(x['A'] - x['B']).mean():.5f}   |AB-old| {np.abs(x['AB'] - x['old']).mean():.5f}"
          f"   |AB-B| {np.abs(x['AB'] - x['B']).mean():.5f}")
