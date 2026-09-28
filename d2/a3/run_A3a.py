#!/usr/bin/env python3
"""D2-A3a, exactly as d2/a3/PREREG_A3a.md (committed before this code): Yreq = 0.1 + 99.9 f(max(s Y_A, 0)),
f(Y) = Y/(1+Y) (A1b, unchanged), one analytic s from the Blender AgX +7 road median. RoadLine only; frozen code exec'd.
  tracks/temporal-glare-2009/py.sh d2/a3/run_A3a.py   -> d2/a3/results_A3a.json, d2/a3/renders/roadline_A3a.png"""
import json, math, os, subprocess
import numpy as np, OpenImageIO as oiio
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")); os.chdir(REPO); os.makedirs("d2/a3/renders", exist_ok=True)
SCALE_LINE = "Yreq = LO + (HI - LO) * Ya"; A1B_LINE = "Yreq = LO + (HI - LO) * (np.maximum(Ya, 0) / (1 + np.maximum(Ya, 0)))"
assert f'SHOULDER_LINE = "{A1B_LINE}"' in open("d2/a1/run_A1b.py").read()
ORACLE_LINE = "Yreq = LO + (HI - LO) * (np.maximum(S_A3A * Ya, 0) / (1 + np.maximum(S_A3A * Ya, 0)))"   # the one change vs A1b
YW = np.array([0.2126, 0.7152, 0.0722]); FROZ = "n1/roadline/renders/A2_canonical_final.png"; RAW = "n1/roadline/renders/A2_canonical_raw.png"
BLENDER = "n1/roadline/renders/A2_comparator.png"; A1B = "d2/a1/renders/roadline_A1b.png"
res = {"prereg": "d2/a3/PREREG_A3a.md", "verify_manifest_before": subprocess.run(["d1/verify_manifest.sh"], capture_output=True, text=True).stdout}
H_, W_ = 820, 1920; F = 960 / math.tan(math.radians(30)); ys, xs = np.mgrid[0:H_, 0:W_]; dy = ys + 0.5 - 410; below = dy > 0.5
t_ = np.where(below, 1.7 / np.maximum(dy / F, 1e-9), np.nan); gx = 0.5 + t_ * (xs + 0.5 - 960) / F
road = below & (gx >= 0) & (gx <= 7) & (t_ >= 3) & (t_ <= 1700); field = below & ((gx < 0) | (gx > 7)) & (t_ >= 3) & (t_ <= 1700)


def disp(png):
    a = oiio.ImageBuf(png).get_pixels(oiio.FLOAT)[..., :3].astype(float); lin = np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)
    return 0.1 + 99.9 * (lin @ YW)


def stats(png):
    Y = disp(png); p10, p90 = np.percentile(Y[road], [10, 90])
    return {"road_median": float(np.median(Y[road])), "road_p10": float(p10), "road_p90": float(p90), "road_p90_over_p10": float(p90 / p10),
            "field_median": float(np.median(Y[field])), "H2v2_road_lum_ceiling": float((Y[road] >= 99.9).mean())}


src = open("d1/display_r/run.py").read().split("\nres = {\"prereg\"")[0]; assert src.count(SCALE_LINE) == 1
src = src.replace(SCALE_LINE, ORACLE_LINE).replace('return g, dict(H=H, W=W,', 'return g, dict(RAX=r_ax, H=H, W=W,')
gv = {"__name__": "a3a", "__file__": f"{REPO}/d1/display_r/run.py", "S_A3A": None}; exec(compile(src, "d1/display_r/run.py[A3a]", "exec"), gv)
# --- the one analytic s ---
Ystar = stats(BLENDER)["road_median"]; _, v0 = gv["extract"]("RLA2_canonical")
for f_ in ("pre.f32", "clip.f32"):
    p_ = f"d1/a_extract/.cache/RLA2_canonical/{f_}"
    if os.path.exists(p_): os.remove(p_)
q = float(np.median(v0["Ynew"].reshape(H_, W_)[road])); u = (Ystar - 0.1) / 99.9; S = u / (1 - u) / q; gv["S_A3A"] = S
res["s"] = {"Y_star_blender_road_median": Ystar, "q_road_median_Y_A": q, "u": u, "s": S, "stops": math.log2(S)}; print(res["s"], flush=True)
out = "d2/a3/renders/roadline_A3a.png"; g, v = gv["run_image"]("n1/roadline/work/A6/canonical_cdm2.exr", "RLA2_canonical", "yprio", out)
cv = oiio.ImageBuf(out).get_pixels(oiio.UINT16)[..., :3]; fl = cv.max(-1) == 0
a2 = open("n1/roadline/a2_eval.py").read(); ns = {"__name__": "a2", "__file__": f"{REPO}/n1/roadline/a2_eval.py"}
exec(compile(a2.split("\nif STEP == \"d1\":")[0].replace("STEP = sys.argv[1]; ", "STEP = 'none'; "), "a2_eval_defs", "exec"), ns)
fin, raw = ns["display_rows"](out), ns["display_rows"](RAW); inv = ns["order"](fin)
r = {"R3_extraction": {k: v["RAX"][k] for k in ("C0_bit_identical", "C2_frac_ok", "C3_frac_ok")},
     "R3_display_gates": {k: g[k] for k in ("finite", "G1", "G2", "G3", "S-1", "S-2", "S-3")},
     "R4_inversions": inv, "R5_present_final": {d: fin[d]["present"] for d in fin}, "R5_present_raw": {d: raw[d]["present"] for d in raw},
     "lamp_max_code_above_bg": {d: fin[d]["max_code_above_bg"] for d in fin}, "H3_floor_frac": float(fl.mean()), "H3_field_floor_frac": float(fl[field].mean())}
r["R3_PASS"] = r["R3_extraction"]["C0_bit_identical"] and min(r["R3_extraction"]["C2_frac_ok"], r["R3_extraction"]["C3_frac_ok"]) >= 0.999 and all(r["R3_display_gates"].values())
r["R4_PASS"] = not inv; r["R5_PASS"] = r["R5_present_final"] == r["R5_present_raw"]; r["H3_PASS"] = r["H3_floor_frac"] <= 0.0062 and r["H3_field_floor_frac"] <= 0.0062
r["automatic_PASS"] = all(r[k] for k in ("R3_PASS", "R4_PASS", "R5_PASS", "H3_PASS")); res["roadline"] = r
res["report"] = {"oracle_A1b": stats(out), "A1b": stats(A1B), "Blender_AgX_+7": stats(BLENDER), "frozen_D1": stats(FROZ)}
res["verify_manifest_after"] = subprocess.run(["d1/verify_manifest.sh"], capture_output=True, text=True).stdout
json.dump(res, open("d2/a3/results_A3a.json", "w"), indent=1, default=lambda o: bool(o) if isinstance(o, np.bool_) else float(o))
print(json.dumps({k: res[k] for k in ("s", "report")} | {"automatic_PASS": r["automatic_PASS"], "R3_display": r["R3_display_gates"], "R5": r["R5_PASS"], "codes": r["lamp_max_code_above_bg"]}, indent=1, default=float))
