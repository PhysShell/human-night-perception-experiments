#!/usr/bin/env python3
"""N1.6A0 evaluation (n1/roadline/PREREG.md addendum 1). tracks/temporal-glare-2009/py.sh n1/roadline/a0_eval.py A"""
import json, math, os, sys
import numpy as np, OpenImageIO as oiio
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
ST = sys.argv[1]; W = "n1/roadline/work/a0"; K, YW, TOL = 179.0, np.array([0.2126, 0.7152, 0.0722]), 0.10
Y = lambda p: K * (oiio.ImageBuf(p).get_pixels(oiio.FLOAT)[..., :3] @ YW)
meta = json.load(open(f"{W}/a0_dirs.json")); res = {"stim": ST, "probes": {}, "emit": {}}
for name, p in meta["probes"].items():
    L = float(np.median(Y(f"{W}/a0_{name}.exr"))); I = math.pi * L * p["r_m"] ** 2; It = p["I_table_cd"]
    ok = abs(I / It - 1) <= TOL if It >= 10 else I < 10
    res["probes"][name] = {"I_measured": I, "I_table": It, "ratio": I / It if It > 0 else None, "PASS": ok}
f = (1920 / 2) / math.tan(math.radians(30))
for D in (50, 100, 400):                                       # addendum 3: 25 m is out of frame
    m = json.load(open(f"{W}/a0emit_{D}.json")); img = Y(f"{W}/a0emit_{D}.exr"); h, w = img.shape
    bgv = np.median(np.concatenate([img[:4].ravel(), img[-4:].ravel(), img[:, :4].ravel(), img[:, -4:].ravel()]))
    x0, y0 = m["px"][0] - 32, m["px"][1] - 32
    ys, xs = np.mgrid[0:h, 0:w]; dx = xs + 0.5 + x0 - 960; dy = ys + 0.5 + y0 - 410
    cos3 = (f / np.sqrt(f ** 2 + dx ** 2 + dy ** 2)) ** 3; omega = cos3 / f ** 2
    E = float(((img - bgv) * omega).sum()); I = E * m["r_m"] ** 2
    res["emit"][D] = {"I_measured": I, "I_table": m["I_table_cd"], "ratio": I / m["I_table_cd"], "V": m["V"], "H": m["H"],
                      "peak_px_cdm2": float(img.max()), "bg_cdm2": float(bgv), "PASS": abs(I / m["I_table_cd"] - 1) <= TOL}
res["A0_PASS"] = all(v["PASS"] for v in res["probes"].values()) and all(v["PASS"] for v in res["emit"].values())
json.dump(res, open(f"n1/roadline/a0_{ST}.json", "w"), indent=1)
for k, v in res["probes"].items(): print(f"probe {k:12s} meas {v['I_measured']:8.1f}  table {v['I_table']:8.1f}  ratio {v['ratio'] if v['ratio'] is None else round(v['ratio'], 3)}  {'PASS' if v['PASS'] else 'FAIL'}")
for k, v in res["emit"].items(): print(f"emit {k:5d} m meas {v['I_measured']:8.1f}  table {v['I_table']:8.1f}  ratio {v['ratio']:.3f}  peak {v['peak_px_cdm2']:.3g} cd/m2  {'PASS' if v['PASS'] else 'FAIL'}")
print("A0", "PASS" if res["A0_PASS"] else "FAIL")
