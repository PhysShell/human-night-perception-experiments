#!/usr/bin/env python3
"""Check m2/calibrate_volume.py renders against Beer-Lambert."""
import math, sys
import numpy as np
import OpenImageIO as oiio

D = sys.argv[1] if len(sys.argv) > 1 else "m2/out/vcal"
load = lambda n: oiio.ImageBuf(f"{D}/{n}.exr").get_pixels(oiio.FLOAT)[..., :3]
vac = load("vacuum")
disc = vac.mean(-1) > 0.5 * vac.mean(-1).max()          # the sphere's own pixels
ring = ~disc & (vac.mean(-1) < 1e-6)
fails = []
for name, expect in (("abs_grey", [math.exp(-1)] * 3),
                     ("abs_rgb", [math.exp(-0.5), math.exp(-1), math.exp(-2)]),
                     ("sca_hg07", [math.exp(-1)] * 3)):
    a = load(name)
    t = a[disc].sum(0) / vac[disc].sum(0)
    halo = a[ring].sum(0) / vac[disc].sum(0)
    ok = np.allclose(t, expect, rtol=0.02)
    print(f"{name:9s} direct T = {np.round(t, 4)}  expected {np.round(expect, 4)}  "
          f"light around the disc / unattenuated source = {np.round(halo, 4)}  {'ok' if ok else 'FAIL'}")
    if not ok:
        fails.append(name)
sys.exit("VOLUME CALIBRATION FAILED: " + ", ".join(fails) if fails else 0)
