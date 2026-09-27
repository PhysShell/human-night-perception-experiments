#!/usr/bin/env python3
"""N1.2 addendum 5: precondition (Noisy Image bit-identical to the earlier 4096 Combined) and the OIDN bias gate
(crop means, <= 2 %). tracks/temporal-glare-2009/py.sh n1/oidn_gate.py -> n1/oidn_gate.json"""
import json, os, sys
import numpy as np, OpenImageIO as oiio
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")); sys.path.insert(0, "n1")
from cam import project
import ast; _src = open("n1/noise.py").read(); _i = _src.index("CROPS = ")                 # the frozen addendum-4 crops,
CROPS = ast.literal_eval(_src[_i + 8:_src.index("\n", _src.index("}", _i)) ].strip())    # read from n1/noise.py (not re-typed)
K, YW, TOL = 179.0, np.array([0.2126, 0.7152, 0.0722]), 0.02


def passes(p):
    out = {}
    for si in range(oiio.ImageBuf(p).nsubimages):
        b = oiio.ImageBuf(p, si, 0); a = b.get_pixels(oiio.FLOAT)
        for i, c in enumerate(b.spec().channelnames):
            parts = c.split("."); out.setdefault(parts[-2], {})[parts[-1]] = a[..., i]
    return {k: np.stack([v[c] for c in "RGB"], -1) for k, v in out.items() if all(c in v for c in "RGB")}


P = passes("n1/work/oidn4096/hero_b.exr")
ref = oiio.ImageBuf("n1/work/spp4096/hero_b.exr", 0, 0).get_pixels(oiio.FLOAT)[..., :3]
noisy, den = P["Noisy Image"], P["Combined"]
r = {"passes": sorted(P), "precondition_noisy_bit_identical": bool(np.array_equal(noisy, ref)),
     "noisy_vs_ref_max_abs": float(np.abs(noisy - ref).max()), "crops": {}}
Yn, Yd = K * (noisy @ YW), K * (den @ YW)
for k, p in CROPS.items():
    cx, cy = project(p); sl = (slice(int(round(cy)) - 24, int(round(cy)) + 24), slice(int(round(cx)) - 24, int(round(cx)) + 24))
    a, b = Yn[sl], Yd[sl]
    r["crops"][k] = {"mean_noisy": float(a.mean()), "mean_denoised": float(b.mean()), "rel_dev": float(b.mean() / a.mean() - 1),
                     "median_noisy": float(np.median(a)), "median_denoised": float(np.median(b)),
                     "cov_noisy": float(a.std() / a.mean()), "cov_denoised": float(b.std() / b.mean())}
r["whole_frame_rel_dev"] = float(Yd.mean() / Yn.mean() - 1)
r["gate_PASS"] = bool(r["precondition_noisy_bit_identical"] and all(abs(v["rel_dev"]) <= TOL for v in r["crops"].values()))
json.dump(r, open("n1/oidn_gate.json", "w"), indent=1)
print(json.dumps(r, indent=1))
