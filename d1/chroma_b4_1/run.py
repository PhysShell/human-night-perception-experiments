#!/usr/bin/env python3
"""D1-B4.1, exactly as d1/chroma_b4_1/PREREG.md: the B4 chroma stage (functions imported unchanged from
d1/chroma_b4/run.py) with t = L_drive/(L_drive + 0.108), L_drive = local | global mean | 1-degree Gaussian field.
  tracks/temporal-glare-2009/py.sh d1/chroma_b4_1/run.py -> results.json
"""
import json, os
import numpy as np, OpenImageIO as oiio
from scipy.ndimage import gaussian_filter
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")); os.chdir(REPO)
exec(open("d1/chroma_b4/run.py").read().split("res = {")[0])     # M709, exact WU, filament(), uv(), chroma(), hue(), stage()
os.makedirs("d1/chroma_b4/.cache", exist_ok=True)
MAN = json.load(open("d0/work/inputs/manifest.json"))["scenes"]
t = lambda L: L / (L + 0.108)
out = {"prereg": "d1/chroma_b4_1/PREREG.md", "scenes": {}}
for sc in ("S1", "S0", "S4"):
    img = oiio.ImageBuf(f"d0/work/inputs/{sc}.exr").get_pixels(oiio.FLOAT)[..., :3].astype(np.float64); H, W = img.shape[:2]
    m = dict(np.load(f"d0/work/inputs/masks/{sc}.npz")); flat = img.reshape(-1, 3); L = flat @ M709[1]
    sigma = MAN[sc]["scene_px_per_deg"] * 1.0
    drives = {"local": L, "global": np.full_like(L, L.mean()), "field": gaussian_filter(L.reshape(H, W), sigma, mode="nearest").ravel()}
    f = filament(flat); cf = chroma(f).reshape(H, W); r = {"L_mean": float(L.mean()), "sigma_px": sigma}
    for v, Ld in drives.items():
        o = stage(f, L, t(Ld), "uv"); co = chroma(o).reshape(H, W); ho = hue(o).reshape(H, W); e = {"t_median_lamp": None}
        for rg in ("sky", "ground", "tree", "lamp"):
            if rg in m and m[rg].any():
                e[f"{rg}_chroma_median"] = float(np.median(co[m[rg]])); e[f"{rg}_hue_median"] = float(np.median(ho[m[rg]]))
        if "lamp" in m and m["lamp"].any():
            e["lamp_chroma_ratio_median"] = float(np.median((co / np.maximum(cf, 1e-12))[m["lamp"]]))
            e["t_median_lamp"] = float(np.median(t(Ld).reshape(H, W)[m["lamp"]]))
        e["finite"] = bool(np.isfinite(o).all())
        if sc == "S1":
            e["pass_G8_thresholds"] = bool(e["lamp_chroma_ratio_median"] >= 0.9 and e["sky_chroma_median"] <= 0.01)
        r[v] = e
    out["scenes"][sc] = r
for p in ("d1/chroma_b4/.cache/i.f32", "d1/chroma_b4/.cache/o.f32"):
    if os.path.exists(p): os.remove(p)
json.dump(out, open("d1/chroma_b4_1/results.json", "w"), indent=1)
for sc, r in out["scenes"].items():
    print(f"== {sc}  mean L {r['L_mean']:.4g} cd/m^2")
    for v in ("local", "global", "field"):
        e = r[v]; print(f"  {v:6s} " + " | ".join(f"{k} {e[k]:.4g}" for k in e if isinstance(e[k], float)) + (f" | G8 {'PASS' if e.get('pass_G8_thresholds') else 'FAIL'}" if sc == "S1" else ""))
