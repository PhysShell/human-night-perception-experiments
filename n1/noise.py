#!/usr/bin/env python3
"""N1.2 step 1: sample-count calibration on the raw linear hero (n1/PREREG.md addendum 4). No D1 involved.
  tracks/temporal-glare-2009/py.sh n1/noise.py 512 1024 2048 [4096]   -> n1/noise.json
Metric per crop (48 x 48 px around a fixed world point): median over 8 x 8-px blocks of
|block median(N) - block median(2N)| / block median(2N). Rule: frozen spp = first N with every crop <= 2 %
(D1's frozen P-7 step tolerance)."""
import json, math, os, sys
import numpy as np
import OpenImageIO as oiio
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
K, YW, TOL = 179.0, np.array([0.2126, 0.7152, 0.0722]), 0.02
CROPS = {"barn_shadow": (3, 16, 0), "shadow_pool_boundary": (4.5, 28, 0.003), "warm_pool": (4.5, 43, 0.003),
         "puddle": (1.0, 10.1, 0.006), "moonlit_dark_field": (-6, 14, 0)}
sys.path.insert(0, "n1"); from cam import project


def Y(n):
    b = oiio.ImageBuf(f"n1/work/spp{n}/hero_b.exr", 0, 0)                 # part 0 = Combined
    return K * (b.get_pixels(oiio.FLOAT)[..., :3] @ YW)


ns = [int(a) for a in sys.argv[1:]]
ref = json.load(open(f"n1/work/spp{ns[0]}/hero_b_px.json"))
check = {k: (project(v["world"]), (v["x"], v["y"])) for k, v in ref.items() if v["in_frame"] and k in ("barn_shadow", "puddle", "field_open", "lane_under_lamp")}
maxerr = max(math.dist(a, b) for a, b in check.values())
assert maxerr < 1.0, check
out = {"projection_check_max_px": maxerr, "crops_px": {k: project(p) for k, p in CROPS.items()}, "pairs": {}}
imgs = {n: Y(n) for n in ns}
for a, b in zip(ns, ns[1:]):
    row = {}
    for k, (cx, cy) in out["crops_px"].items():
        x0, y0 = int(round(cx)) - 24, int(round(cy)) - 24
        A = imgs[a][y0:y0 + 48, x0:x0 + 48].reshape(6, 8, 6, 8).transpose(0, 2, 1, 3).reshape(36, 64)
        B = imgs[b][y0:y0 + 48, x0:x0 + 48].reshape(6, 8, 6, 8).transpose(0, 2, 1, 3).reshape(36, 64)
        ma, mb = np.median(A, 1), np.median(B, 1)
        row[k] = {"metric": float(np.median(np.abs(ma - mb) / mb)), "crop_median_cdm2": float(np.median(mb))}
    row["all_within_2pct"] = all(v["metric"] <= TOL for v in row.values())
    out["pairs"][f"{a}->{b}"] = row
frozen = next((int(p.split("->")[0]) for p, r in out["pairs"].items() if r["all_within_2pct"]), None)
out["frozen_spp"] = frozen
json.dump(out, open("n1/noise.json", "w"), indent=1)
print(json.dumps(out, indent=1))
