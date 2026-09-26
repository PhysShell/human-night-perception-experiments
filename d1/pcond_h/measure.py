#!/usr/bin/env python3
"""D1.1 measurements for pcond V0 / acuity (-a) / h (-a -v): the D0 metrics (d0/metrics.py: still_metrics, pdet) on
the emitted light (d0/display_model.py, SDR100 DARK), plus band-pass detail energy of the displayed luminance
(log domain, DoG sigma 1 vs 4 px, and 2 vs 8 px) per region, relative to V0.
  nix develop -c python3 d1/pcond_h/measure.py -> d1/pcond_h/results.json
"""
import json, os, sys
import numpy as np
from scipy.ndimage import gaussian_filter
sys.path.insert(0, "d0")
import metrics as M
from display_model import decode, read_code
O = "d1/pcond_h/.cache/out"; res = {}


def dog(Y, a, b):
    L = np.log10(np.maximum(Y, 1e-12)); return gaussian_filter(L, a) - gaussian_filter(L, b)


for cfg in ("V0", "acuity", "h"):
    for s in ("S0", "S1", "S3_bar"):
        p = f"{O}/{cfg}/{s}__PHONE_SDR100_DARK.png"; code = read_code(p); XYZ, _ = decode(code, "SDR100", "DARK")
        r = M.still_metrics(XYZ, code, s, "SDR100", M.scene_ref(s))
        m = M.masks(s); Y = XYZ[..., 1]
        r["detail"] = {f"{rg}_{a}_{b}": float(np.var(dog(Y, a, b)[m[rg]])) for rg in ("sky", "ground", "tree") if rg in m and m[rg].any() for a, b in ((1, 4), (2, 8))}
        if s == "S3_bar":
            r.update(M.pdet(p, p.replace("S3_bar", "S3_nobar"), "SDR100", "DARK", f"d1pcond_{cfg}"))
            r["bar_weber_displayed"] = float((Y[m["beside_bar"]].mean() - Y[m["bar"]].mean()) / max(Y[m["beside_bar"]].mean(), 1e-12))
        res[f"{cfg}/{s}"] = r; print(cfg, s, flush=True)
for k, r in res.items():
    cfg, s = k.split("/"); base = res[f"V0/{s}"]["detail"]
    r["detail_rel_V0"] = {d: r["detail"][d] / max(base[d], 1e-30) for d in r["detail"]}
json.dump(res, open("d1/pcond_h/results.json", "w"), indent=1)
