#!/usr/bin/env python3
"""N1.2 step 4: four diagnostic versions of the hero from ONE EXR through the frozen D1 code (called, never edited).
  nix develop -c d1/a_extract/axis_a_x.sh n1/work/hero_cdm2.exr 60 d1/a_extract/.cache/N1_hero
  tracks/temporal-glare-2009/py.sh n1/variants.py   -> n1/renders/{raw,axis_a,axis_b,final}/hero.png, n1/variants.json
raw    : scene Y x k,  scene u'v'  | A-only: Y_A, scene u'v' | B-only: scene Y x k, B | final: Y_A, B (= D1).
k maps the open-field median to the same display luminance as in final (a diagnostic anchor, not a tone map).
All four through the same Y-priority display realisation and SDR100 encoding."""
import json, os, sys
import numpy as np
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..")); os.chdir(REPO)
src = open("d1/display_r/run.py").read().split("\nres = {\"prereg\"")[0]
a = 'return g, dict(H=H, W=W,'; assert a in src
src = src.replace(a, 'return g, dict(YA=Ya, PHYS=phys, B=b, YREQ=Yreq, H=H, W=W,')
__file__ = f"{REPO}/d1/display_r/run.py"; exec(src)
sys.path.insert(0, f"{REPO}/n1"); from cam import project
SRC, AX = "n1/work/hero_cdm2.exr", "N1_hero"
for d in ("raw", "axis_a", "axis_b", "final"): os.makedirs(f"n1/renders/{d}", exist_ok=True)
g, v = run_image(SRC, AX, "yprio", "n1/renders/final/hero.png")
H, W = v["H"], v["W"]; phys, b, Ya, Yreq = v["PHYS"], v["B"], v["YA"], v["YREQ"]
Y = phys @ M709[1]; Yb = b @ M709[1]
cx, cy = project((-4, 25, 0)); win = (slice(int(cy) - 3, int(cy) + 4), slice(int(cx) - 3, int(cx) + 4))
k = float(np.median(Ya.reshape(H, W)[win]) / np.median(Y.reshape(H, W)[win]))
Yreq_k = LO + (HI - LO) * k * Y
safe = lambda a_: np.where(a_ > 0, a_, 1)
out = {"final_D1_gates": {kk: g[kk] for kk in ("finite", "ch_min", "ch_max", "G1", "G2", "G3", "S-1", "S-2", "S-3") if kk in g},
       "anchor_k_per_cdm2": k, "anchor_point": [-4, 25, 0]}
for name, chrom, yr, ych in (("raw", phys, Yreq_k, Y), ("axis_a", phys, Yreq, Y), ("axis_b", b, Yreq_k, Yb)):
    x0 = chrom * (yr / safe(ych))[:, None]
    x, c = realise(x0, yr, "yprio"); E = emit(x, f"n1/renders/{name}/hero.png", H, W)
    out[name] = {"finite": bool(np.isfinite(x).all()), "frac_projected": float((~c["ing"]).mean()), "ch_min": float(x.min()), "ch_max": float(x.max())}
json.dump(out, open("n1/variants.json", "w"), indent=1, default=float)
print(json.dumps(out, indent=1, default=float))
