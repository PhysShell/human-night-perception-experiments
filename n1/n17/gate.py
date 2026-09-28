#!/usr/bin/env python3
"""N1.7 OIDN gate (n1/n17/PREREG_N17.md amendment 1): five fixed 48x48 image-space windows, |den/noisy - 1| <= 2 % each;
whole-frame bias and (if in frame) a lamp-head window report-only. Mirrors n1/view_eval.py's gate step (same EXR parsing,
same outputs view_cdm2.exr / view_rgb.exr), then deletes the raw multilayer EXR (disk).
  tracks/temporal-glare-2009/py.sh n1/n17/gate.py VIEW   -> n1/work/view_VIEW/view_cdm2.exr, n1/view_VIEW.json"""
import json, os, sys
import numpy as np, OpenImageIO as oiio
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")); os.chdir(REPO); sys.path.insert(0, f"{REPO}/n1")
from cam import project_view
VIEW = sys.argv[1]; V = json.load(open("n1/views.json"))[VIEW]; W_ = f"n1/work/view_{VIEW}"; RES = f"n1/view_{VIEW}.json"
K, YW, TOL, HW = 179.0, np.array([0.2126, 0.7152, 0.0722]), 0.02, 24
WIN = {"centre": (960, 410), "UL": (480, 205), "UR": (1440, 205), "LL": (480, 615), "LR": (1440, 615)}
res = json.load(open(RES)) if os.path.exists(RES) else {"view": VIEW, "spec": V}
P = {}; src = f"{W_}/hero_b.exr"
for si in range(oiio.ImageBuf(src).nsubimages):
    b = oiio.ImageBuf(src, si, 0); a = b.get_pixels(oiio.FLOAT)
    for i, c in enumerate(b.spec().channelnames):
        parts = c.split("."); P.setdefault(parts[-2], {})[parts[-1]] = a[..., i]
noisy = np.stack([P["Noisy Image"][c] for c in "RGB"], -1); den = np.stack([P["Combined"][c] for c in "RGB"], -1)
Yn, Yd = K * (noisy @ YW), K * (den @ YW); H, Wd = den.shape[:2]
def win(cx, cy):
    sl = (slice(cy - HW, cy + HW), slice(cx - HW, cx + HW)); a_, b_ = Yn[sl], Yd[sl]
    return {"centre_px": [cx, cy], "mean_noisy": float(a_.mean()), "mean_denoised": float(b_.mean()), "rel_dev": float(b_.mean() / a_.mean() - 1)}
for cx, cy in WIN.values(): assert HW <= cx <= Wd - HW and HW <= cy <= H - HW, "window crosses the frame edge: design error"
g = {k: win(*c) for k, c in WIN.items()}
lx, ly = project_view((4.5, 45.0, 5.92), V["loc"], V["yaw_deg"], V["pitch_deg"]); lx, ly = int(round(lx)), int(round(ly))
rep = {"whole_frame_rel_dev": float(Yd.mean() / Yn.mean() - 1)}
if HW <= lx <= Wd - HW and HW <= ly <= H - HW: rep["lamp_head_window"] = win(lx, ly)
res["oidn_gate"] = {"windows": g, "report": rep, "PASS": all(abs(v["rel_dev"]) <= TOL for v in g.values())}
o = oiio.ImageBuf(oiio.ImageSpec(Wd, H, 3, oiio.FLOAT)); o.set_pixels(oiio.ROI(0, Wd, 0, H, 0, 1, 0, 3), np.ascontiguousarray(den * K, np.float32)); o.write(f"{W_}/view_cdm2.exr")
o2 = oiio.ImageBuf(oiio.ImageSpec(Wd, H, 3, oiio.FLOAT)); o2.set_pixels(oiio.ROI(0, Wd, 0, H, 0, 1, 0, 3), np.ascontiguousarray(den, np.float32)); o2.write(f"{W_}/view_rgb.exr")
os.remove(src); json.dump(res, open(RES, "w"), indent=1, default=float); print(json.dumps(res["oidn_gate"], indent=1))
