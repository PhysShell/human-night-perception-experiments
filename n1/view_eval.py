#!/usr/bin/env python3
"""N1.5 per-view evaluation (n1/PREREG.md addendum 6): OIDN bias gate on the view's pre-registered crops, then the
frozen D1 (called, not edited) on the single denoised EXR.
  step 1: tracks/temporal-glare-2009/py.sh n1/view_eval.py VIEW gate      -> n1/work/view_VIEW/view_cdm2.exr
  step 2: nix develop -c d1/a_extract/axis_a_x.sh n1/work/view_VIEW/view_cdm2.exr 60 d1/a_extract/.cache/N1_VIEW
          nix develop -c d1/pipeline/axis_a.sh   n1/work/view_VIEW/view_cdm2.exr 60 d1/pipeline/.cache/A/N1_VIEW.exr
  step 3: tracks/temporal-glare-2009/py.sh n1/view_eval.py VIEW d1        -> n1/renders/final/cam_VIEW.png
  results -> n1/view_VIEW.json"""
import json, os, sys
import numpy as np, OpenImageIO as oiio
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..")); os.chdir(REPO); sys.path.insert(0, f"{REPO}/n1")
from cam import project_view
VIEW, STEP = sys.argv[1], sys.argv[2]; V = json.load(open("n1/views.json"))[VIEW]
W_ = f"n1/work/view_{VIEW}"; RES = f"n1/view_{VIEW}.json"; K, YW, TOL = 179.0, np.array([0.2126, 0.7152, 0.0722]), 0.02
res = json.load(open(RES)) if os.path.exists(RES) else {"view": VIEW, "spec": V}
if STEP == "gate":
    P = {}; src = f"{W_}/hero_b.exr"
    for si in range(oiio.ImageBuf(src).nsubimages):
        b = oiio.ImageBuf(src, si, 0); a = b.get_pixels(oiio.FLOAT)
        for i, c in enumerate(b.spec().channelnames):
            parts = c.split("."); P.setdefault(parts[-2], {})[parts[-1]] = a[..., i]
    noisy = np.stack([P["Noisy Image"][c] for c in "RGB"], -1); den = np.stack([P["Combined"][c] for c in "RGB"], -1)
    Yn, Yd = K * (noisy @ YW), K * (den @ YW); g = {}
    for k, p in V["crops"].items():
        cx, cy = project_view(p, V["loc"], V["yaw_deg"], V["pitch_deg"]); sl = (slice(int(round(cy)) - 24, int(round(cy)) + 24), slice(int(round(cx)) - 24, int(round(cx)) + 24))
        a_, b_ = Yn[sl], Yd[sl]
        g[k] = {"mean_noisy": float(a_.mean()), "mean_denoised": float(b_.mean()), "rel_dev": float(b_.mean() / a_.mean() - 1),
                "cov_noisy": float(a_.std() / a_.mean()), "cov_denoised": float(b_.std() / b_.mean())}
    res["oidn_gate"] = {"crops": g, "whole_frame_rel_dev": float(Yd.mean() / Yn.mean() - 1), "PASS": all(abs(v["rel_dev"]) <= TOL for v in g.values())}
    H, Wd = den.shape[:2]; o = oiio.ImageBuf(oiio.ImageSpec(Wd, H, 3, oiio.FLOAT))
    o.set_pixels(oiio.ROI(0, Wd, 0, H, 0, 1, 0, 3), np.ascontiguousarray(den * K, np.float32)); o.write(f"{W_}/view_cdm2.exr")
    o2 = oiio.ImageBuf(oiio.ImageSpec(Wd, H, 3, oiio.FLOAT)); o2.set_pixels(oiio.ROI(0, Wd, 0, H, 0, 1, 0, 3), np.ascontiguousarray(den, np.float32)); o2.write(f"{W_}/view_rgb.exr")
    print(json.dumps(res["oidn_gate"], indent=1))
else:
    src = open("d1/display_r/run.py").read().split("\nres = {\"prereg\"")[0]
    a = 'return g, dict(H=H, W=W,'; assert a in src
    src = src.replace(a, 'return g, dict(RAX=r_ax, H=H, W=W,')
    __file__ = f"{REPO}/d1/display_r/run.py"; exec(src)
    os.makedirs("n1/renders/final", exist_ok=True)
    g, v = run_image(f"{W_}/view_cdm2.exr", f"N1_{VIEW}", "yprio", f"n1/renders/final/cam_{VIEW}.png")
    res["d1"] = {"extraction_selfcheck": {k: v["RAX"][k] for k in ("colour_active", "C0_bit_identical", "C2_frac_ok", "C3_frac_ok", "C3_fail_px", "X_le_0_px")},
                 "tone_map_mode": v["RAX"]["tone_map"]["mode"],
                 "display_gates": {k: g[k] for k in ("finite", "ch_min", "ch_max", "G1", "G2", "G3", "S-1", "S-2", "S-3") if k in g}}
    print(json.dumps(res["d1"], indent=1, default=float))
json.dump(res, open(RES, "w"), indent=1, default=float)
