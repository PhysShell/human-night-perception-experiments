#!/usr/bin/env python3
"""N1.7 addendum 3, per stage-2 frame (after the D1 step): CF, SRC, R3 (+ E1 diagnostic), EXPOSURE, frame-mean and median
Y_disp, trace agreement -> appends to n1/n17/stage2.jsonl.   tracks/temporal-glare-2009/py.sh n1/n17/frame_eval.py VIEW"""
import json, math, os, re, sys
import numpy as np, OpenImageIO as oiio
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")); os.chdir(REPO); sys.path.insert(0, f"{REPO}/n1")
from cam import project_view
K = sys.argv[1]; V = json.load(open("n1/views.json"))[K]; YW = np.array([0.2126, 0.7152, 0.0722]); KNEE = 0.04045 / 12.92
png = f"n1/renders/final/cam_{K}.png"; cv = oiio.ImageBuf(png).get_pixels(oiio.UINT16)[..., :3].astype(float); vv = cv / 65535
Yd = 0.1 + 99.9 * (np.where(vv <= 0.04045, vv / 12.92, ((vv + 0.055) / 1.055) ** 2.4) @ YW); mx = cv.max(-1)
hdr = open(f"d1/a_extract/.cache/N1_{K}/out.header").read(); m = re.search(r"EXPOSURE=([0-9.eE+-]+)", hdr); vj = json.load(open(f"n1/view_{K}.json"))
tr = {json.loads(l)["t"]: json.loads(l)["EXPOSURE"] for l in open("n1/n17/trace.jsonl")}
r = {"key": K, "t": V["t"], "EXPOSURE": float(m.group(1)) if m else None, "tone_map_mode": vj["d1"]["tone_map_mode"], "mean_Y_disp": float(Yd.mean()),
     "median_Y_disp": float(np.median(Yd)), "lum_ceiling": float((Yd >= 99.9).mean()), "any_ch_ceiling": float((mx == 65535).mean()), "floor": float((mx == 0).mean()),
     "OIDN": vj["oidn_gate"]["PASS"], "OIDN_max_abs": max(abs(w["rel_dev"]) for w in vj["oidn_gate"]["windows"].values()),
     "R3_extraction": vj["d1"]["extraction_selfcheck"], "R3_display": vj["d1"]["display_gates"]}
r["TRACE_rel"] = r["EXPOSURE"] / tr[round(V["t"], 3)] - 1; r["TRACE_PASS"] = abs(r["TRACE_rel"]) <= 0.05
r["CF_PASS"] = r["floor"] <= 0.006250 and r["any_ch_ceiling"] <= 0.043545
lx, ly = project_view((4.5, 45.0, 5.92), V["loc"], V["yaw_deg"], V["pitch_deg"]); sy, cy = math.sin(math.radians(V["yaw_deg"])), math.cos(math.radians(V["yaw_deg"]))
if (4.5 - V["loc"][0]) * (-sy) + (45.0 - V["loc"][1]) * cy > 0 and 7 <= lx <= 1913 and 7 <= ly <= 813:
    ys, xs = np.mgrid[0:820, 0:1920]; rr = np.hypot(xs + 0.5 - lx, ys + 0.5 - ly)
    r["SRC_code_above_annulus"] = float(mx[rr <= 3].max() - np.median(mx[(rr > 4.5) & (rr <= 7)])); r["SRC_PASS"] = r["SRC_code_above_annulus"] >= 1
g = r["R3_display"]
if not (g["G3"] and g["S-2"]):
    src = open("d1/display_r/run.py").read().split("\nres = {\"prereg\"")[0]
    src = src.replace('return g, dict(H=H, W=W,', 'return g, dict(DH=dh, HM=hm, CO=co, CB=cb, X=x, ING=c["ing"], H=H, W=W,')
    gv = {"__name__": "fe", "__file__": f"{REPO}/d1/display_r/run.py"}; exec(compile(src, "d1/display_r/run.py[frame_eval diag]", "exec"), gv)
    gg, v = gv["run_image"](f"n1/work/view_{K}/view_cdm2.exr", f"N1_{K}", "yprio", None)
    bad = np.flatnonzero((v["HM"] & (v["DH"] > 1e-6)) | ((v["CO"] - v["CB"]) > 1e-12)); lin = (v["X"][bad] - 0.1) / 99.9
    d = [float(np.abs(l - KNEE).min()) for l in lin]; r["E1_diag"] = {"bad_px": int(len(bad)), "in_gamut": int(v["ING"][bad].sum()), "min_abs_dist_to_knee": d[:10]}
    r["E1_class"] = bool(0 < len(bad) <= 3 and v["ING"][bad].all() and all(x < 1e-8 for x in d))
e = r["R3_extraction"]; r["R3_PASS"] = bool(e["C0_bit_identical"] and min(e["C2_frac_ok"], e["C3_frac_ok"]) >= 0.999 and all(g[x] for x in ("finite", "G1", "G2", "S-1", "S-3"))
                                          and ((g["G3"] and g["S-2"]) or r.get("E1_class", False)))
open("n1/n17/stage2.jsonl", "a").write(json.dumps(r, default=float) + "\n"); print({k: r[k] for k in ("key", "EXPOSURE", "TRACE_rel", "OIDN", "R3_PASS", "CF_PASS")}, r.get("SRC_PASS"), r.get("E1_class"))
