#!/usr/bin/env python3
"""Compare Cycles calibration renders (m1/calibrate.py) with closed-form radiometry."""
import math, sys
import numpy as np
import OpenImageIO as oiio

D = sys.argv[1] if len(sys.argv) > 1 else "m1/out/calib"


def img(name):
    return oiio.ImageBuf(f"{D}/{name}.exr").get_pixels(oiio.FLOAT)[..., :3]


def centre(a, r=8):
    h, w = a.shape[:2]
    return float(a[h // 2 - r:h // 2 + r, w // 2 - r:w // 2 + r].mean())


rows = []
def check(label, measured, expected):
    rows.append((label, measured, expected, measured / expected))

check("sun E=1 W/m2, rho=0.5 -> rho*E/pi", centre(img("c1_sun_E1_rho05")), 0.5 / math.pi)
check("point P=1000 W @10 m, rho=0.5 -> rho*P/(4pi d^2)/pi",
      centre(img("c2_point_P1000_d10_rho05")), 0.5 * 1000 / (4 * math.pi * 100) / math.pi)
check("spot 180 deg P=1000 W @10 m (as point light)",
      centre(img("c2b_spot180_P1000_d10_rho05")), 0.5 * 1000 / (4 * math.pi * 100) / math.pi)
check("world strength 1e-3 seen directly", centre(img("c3_world_B1e-3")), 1e-3)
check("world 1e-3 on rho=0.5 plane -> rho*B", centre(img("c3b_world_B1e-3_plane_rho05")), 0.5e-3)
check("emission strength 2 seen directly", centre(img("c4_emission_S2")), 2.0)

# Sub-pixel emitters: integrate radiance over pixel solid angles -> irradiance at camera.
fov = math.radians(1.0)
for tag, expected_I in (("a_pointlight", 1000 / (4 * math.pi)),
                        ("b_emissive_sphere", 100 * math.pi * 0.1 ** 2)):
    a = img("c5" + tag + "_d500")
    h, w = a.shape[:2]
    pix = 2 * math.tan(fov / 2) / w          # pixel pitch on unit image plane (small angle)
    E = float(a.mean(axis=2).sum()) * pix * pix
    check(f"sub-pixel {tag} @500 m: sum(L*Omega) vs I/d^2 (I={expected_I:.2f} W/sr)",
          E, expected_I / 500 ** 2)

w = max(len(r[0]) for r in rows)
print(f"{'case'.ljust(w)}  {'measured':>11}  {'expected':>11}  ratio")
for label, m, e, r in rows:
    print(f"{label.ljust(w)}  {m:11.4e}  {e:11.4e}  {r:6.3f}")
