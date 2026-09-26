#!/usr/bin/env python3
"""D1-A1 scene tests on S1, exactly as d1/axis_a/PREREG.md: frozen B chromaticity at exactly Y_display from the
Wanat 2014 global tone curve (SDR100 DARK: dmin 0.1, dmax 100). Emitted light via d0/display_model.py after
encoding to the SDR100 code values (D0 output contract).
  tracks/temporal-glare-2009/py.sh d1/axis_a/run_scene.py -> scene.json, S1_A1__PHONE_SDR100_DARK.png, sheet_S1.png"""
import json, os, sys
import numpy as np, OpenImageIO as oiio
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")); os.chdir(REPO); sys.path.insert(0, "d1/axis_a"); sys.path.insert(0, "d0")
from wanat_global import tone_curve, apply
exec(open("d1/chroma_b4/run.py").read().split("res = {")[0])
from display_model import decode
img = oiio.ImageBuf("d0/work/inputs/S1.exr").get_pixels(oiio.FLOAT)[..., :3].astype(np.float64); H, W = img.shape[:2]
m = dict(np.load("d0/work/inputs/masks/S1.npz")); phys = img.reshape(-1, 3); Lp = phys @ M709[1]
t = lambda L: L / (L + 0.108)
b = stage(filament(phys), Lp, t(Lp), "uv"); Yb = b @ M709[1]
lmin, lmax = np.log10(max(np.percentile(Lp, 0.1), 1e-5)), np.log10(Lp.max())
Tl, Tv, r = tone_curve(lmin, lmax, np.log10(0.1), np.log10(100.0))
Yd = apply(Tl, Tv, np.clip(Lp, 10 ** lmin, 10 ** lmax))
x = b * (Yd / np.where(Yb > 0, Yb, 1))[:, None]
code = np.where((v := np.clip((x - 0.1) / (100 - 0.1), 0, 1)) <= 0.0031308, 12.92 * v, 1.055 * v ** (1 / 2.4) - 0.055)
clip_hi, clip_lo = (x > 100).any(1), (x < 0.1).any(1)
XYZ, _ = decode(code.reshape(H, W, 3), "SDR100", "DARK"); E = XYZ.reshape(-1, 3); Ye = E[:, 1]
ok = ~clip_hi & ~clip_lo
s = E[:, 0] + 15 * Ye + 3 * E[:, 2]; uv_e = np.stack([4 * E[:, 0] / s, 9 * Ye / s], -1); duv = np.hypot(*(uv_e - uv(b)).T)
sky, lamp, tree = m["sky"].ravel(), m["lamp"].ravel(), m["tree"].ravel()
res = {"curve": {"lmin": float(lmin), "lmax": float(lmax), "l": Tl.tolist(), "T": Tv.tolist(), "solver": r.message},
       "sky_median_display": float(np.median(Ye[sky])), "lamp_median_display": float(np.median(Ye[lamp])),
       "lamp_over_sky": float(np.median(Ye[lamp]) / np.median(Ye[sky])), "tree_median_display": float(np.median(Ye[tree])),
       "silhouette_weber": float(1 - np.median(Ye[tree]) / np.median(Ye[sky])), "monotone": bool(np.all(np.diff(Tv) >= -1e-9)),
       "duv_max_unclipped": float(duv[ok].max()), "duv_p99_unclipped": float(np.percentile(duv[ok], 99)),
       "frac_clipped_high": float(clip_hi.mean()), "frac_below_black_channel": float(clip_lo.mean()),
       "ground_median_display": float(np.median(Ye[m["ground"].ravel()]))}
res["gates"] = {"A1-S1 sky <= 2": res["sky_median_display"] <= 2, "A1-S2 lamp/sky >= 10 and monotone": res["lamp_over_sky"] >= 10 and res["monotone"],
                "A1-S3 silhouette >= 0.1": res["silhouette_weber"] >= 0.1, "A1-S4 B untouched (duv <= 1e-6 unclipped)": res["duv_max_unclipped"] <= 1e-6}
res["gates"] = {k: bool(v) for k, v in res["gates"].items()}
M = [json.loads(l) for l in open("d0/results/tables/metrics.jsonl")]
res["controls_no_gate"] = {f"{r['donor']}/{r['config']}": {k: r.get(k) for k in ("sky_median", "silhouette_weber", "peak")} for r in M
                           if r["scene"] == "S1" and r["lum"] == "SDR100" and (r["donor"], r["config"]) in (("pcond", "native_default"), ("mantiuk08", "target_whiteauto"))}
json.dump(res, open("d1/axis_a/scene.json", "w"), indent=1)
o = oiio.ImageBuf(oiio.ImageSpec(W, H, 3, oiio.UINT16)); o.set_pixels(oiio.ROI(0, W, 0, H, 0, 1, 0, 3), np.ascontiguousarray(code.reshape(H, W, 3), np.float32))
os.makedirs("d1/axis_a/.cache", exist_ok=True); o.write("d1/axis_a/.cache/S1_A1__PHONE_SDR100_DARK.png")
print(json.dumps({k: v for k, v in res.items() if k not in ("curve",)}, indent=1))
for p in ("d1/chroma_b4/.cache/i.f32", "d1/chroma_b4/.cache/o.f32"):
    if os.path.exists(p): os.remove(p)
