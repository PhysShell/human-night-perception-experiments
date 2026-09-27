#!/usr/bin/env python3
"""D2-A1a2, exactly as d2/a1/PREREG_A1a2.md (committed before this code). Frozen D1 code exec'd with the single A1a
change Yreq = 0.1 + 99.9 * s * Y_A, s = 0.2641. No frozen file is edited or overwritten.
  tracks/temporal-glare-2009/py.sh d2/a1/run_a1a2.py   -> d2/a1/results_a1a2.json, d2/a1/renders/holdout_C_a1a2.png"""
import json, math, os, subprocess
import numpy as np, OpenImageIO as oiio
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")); os.chdir(REPO)
S_A1A = 0.2641; YW = np.array([0.2126, 0.7152, 0.0722]); SCALE_LINE = "Yreq = LO + (HI - LO) * Ya"
res = {"prereg": "d2/a1/PREREG_A1a2.md", "S": S_A1A, "verify_manifest_before": subprocess.run(["d1/verify_manifest.sh"], capture_output=True, text=True).stdout}


def disp(png):
    cv = oiio.ImageBuf(png).get_pixels(oiio.UINT16)[..., :3].astype(float); v = cv / 65535
    lin = np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4); return cv, 0.1 + 99.9 * (lin @ YW)


# --- RoadLine (confirmatory only): H2v2, C1, H1 report ---
cv, Yd = disp("d2/a1/renders/roadline_a1a.png"); H_, W2 = Yd.shape; F = 960 / math.tan(math.radians(30))
ys, xs = np.mgrid[0:H_, 0:W2]; dy = ys + 0.5 - 410; below = dy > 0.5
t = np.where(below, 1.7 / np.maximum(dy / F, 1e-9), np.nan); gx = 0.5 + t * (xs + 0.5 - 960) / F
road = below & (gx >= 0) & (gx <= 7) & (t >= 3) & (t <= 1700); ce = cv.max(-1) == 65535
res["roadline"] = {"H2v2_road_luminance_ceiling_frac": float((Yd[road] >= 99.9).mean()), "C1_road_chromatic_ceiling_frac_report": float((ce & (Yd < 99.9))[road].mean()),
                   "H1_frame_any_channel_ceiling_report": float(ce.mean()), "note": "not prospective (A1a output); confirms the metric fix only"}
res["roadline"]["H2v2_PASS"] = res["roadline"]["H2v2_road_luminance_ceiling_frac"] <= 0.001
# --- hold-out: N1 Camera C with the same s ---
src = open("d1/display_r/run.py").read().split("\nres = {\"prereg\"")[0]; assert src.count(SCALE_LINE) == 1
src = src.replace(SCALE_LINE, "Yreq = LO + (HI - LO) * S_A1A * Ya")
__file__ = f"{REPO}/d1/display_r/run.py"; exec(src)
out = "d2/a1/renders/holdout_C_a1a2.png"; g, v = run_image("n1/work/view_C/view_cdm2.exr", "N1_C", "yprio", out)
cv, Yd = disp(out); mx = cv.max(-1)
cx, cy = 961.0, 153.0; ys, xs = np.mgrid[0:mx.shape[0], 0:mx.shape[1]]; r = np.hypot(xs + 0.5 - cx, ys + 0.5 - cy)
ap, ann = r <= 3.0, (r > 4.5) & (r <= 7.0); head_above = float(mx[ap].max() - np.median(mx[ann]))
ho = {"HO1_luminance_ceiling_frac": float((Yd >= 99.9).mean()), "HO1_limit": 0.004442,
      "HO2_floor_frac": float((mx == 0).mean()), "HO2_limit": 0.0062, "HO3_lamp_head_code_above_annulus": head_above,
      "any_channel_ceiling_report": float((mx == 65535).mean()),
      "R3_display_gates": {k: g[k] for k in ("finite", "ch_min", "ch_max", "G1", "G2", "G3", "S-1", "S-2", "S-3")}}
ho["HO1_PASS"] = ho["HO1_luminance_ceiling_frac"] <= ho["HO1_limit"]; ho["HO2_PASS"] = ho["HO2_floor_frac"] <= ho["HO2_limit"]; ho["HO3_PASS"] = head_above >= 1
res["holdout_C"] = ho
res["automatic_PASS"] = res["roadline"]["H2v2_PASS"] and ho["HO1_PASS"] and ho["HO2_PASS"] and ho["HO3_PASS"]
res["verify_manifest_after"] = subprocess.run(["d1/verify_manifest.sh"], capture_output=True, text=True).stdout
json.dump(res, open("d2/a1/results_a1a2.json", "w"), indent=1, default=lambda o: bool(o) if isinstance(o, np.bool_) else float(o))
print(json.dumps({k: res[k] for k in ("roadline", "holdout_C", "automatic_PASS")}, indent=1, default=lambda o: bool(o) if isinstance(o, np.bool_) else float(o)))
