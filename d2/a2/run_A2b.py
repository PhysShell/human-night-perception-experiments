#!/usr/bin/env python3
"""D2-A2b stage 1, exactly as d2/a2/PREREG_A2b.md (committed before this code): global Q99.9(Y_A) highlight guard
s_hist = min(1, 99.8 / (99.9 q)) on the frozen axis-A exposure, RoadLine-A2 canonical. Frozen D1 code is exec'd with
ONE change: Yreq = 0.1 + 99.9 * s_hist * Y_A. No frozen file is edited or overwritten; frozen A caches are reused.
  tracks/temporal-glare-2009/py.sh d2/a2/run_A2b.py   -> d2/a2/results_A2b.json, d2/a2/renders/roadline_A2b{,_raw}.png"""
import json, math, os, subprocess, sys
import numpy as np, OpenImageIO as oiio
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")); os.chdir(REPO); sys.path.insert(0, f"{REPO}/n1")
from cam import project_view
ORACLE_S = 0.2641; YW = np.array([0.2126, 0.7152, 0.0722]); SCALE_LINE = "Yreq = LO + (HI - LO) * Ya"; GUARD = {}
res = {"prereg": "d2/a2/PREREG_A2b.md", "verify_manifest_before": subprocess.run(["d1/verify_manifest.sh"], capture_output=True, text=True).stdout}


def s_hist(Ya, name):
    """The policy: whole frame, scalar Y_A, numpy linear percentile; s <= 1."""
    q = float(np.percentile(Ya, 99.9)); s = min(1.0, (99.9 - 0.1) / (99.9 * q)) if q > 0 else 1.0
    GUARD[name] = {"q": q, "s_hist": s, "active": s < 1.0, "Q": {str(p): float(np.percentile(Ya, p)) for p in (50, 90, 99, 99.9, 99.99)}}
    return s


src = open("d1/display_r/run.py").read().split("\nres = {\"prereg\"")[0]; assert src.count(SCALE_LINE) == 1
src = src.replace(SCALE_LINE, "S_H = s_hist(Ya, axname); Yreq = LO + (HI - LO) * S_H * Ya")                  # the one change
a = 'return g, dict(H=H, W=W,'; assert a in src; src = src.replace(a, 'return g, dict(RAX=r_ax, YA=Ya, PHYS=phys, S_H=S_H, H=H, W=W,')
__file__ = f"{REPO}/d1/display_r/run.py"; exec(src)


def disp(png):
    cv = oiio.ImageBuf(png).get_pixels(oiio.UINT16)[..., :3].astype(float); v = cv / 65535
    lin = np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4); return cv, 0.1 + 99.9 * (lin @ YW)


W6 = "n1/roadline/work/A6"; out = "d2/a2/renders/roadline_A2b.png"; EYE = (0.5, 0.0, 1.7); os.makedirs("d2/a2/renders", exist_ok=True)
g, v = run_image(f"{W6}/canonical_cdm2.exr", "RLA2_canonical", "yprio", out); S = v["S_H"]
H_, W2 = v["H"], v["W"]; phys, Ya = v["PHYS"], v["YA"]; Y = phys @ M709[1]
ax, ay = project_view((-10, 40, 0), EYE, 0.0, 0.0); win = (slice(int(ay) - 3, int(ay) + 4), slice(int(ax) - 3, int(ax) + 4))
k = float(np.median(Ya.reshape(H_, W2)[win]) / np.median(Y.reshape(H_, W2)[win])); Yreq_k = LO + (HI - LO) * S * k * Y   # linear anchor, same s_hist
x, c = realise(phys * (Yreq_k / np.where(Y > 0, Y, 1))[:, None], Yreq_k, "yprio"); emit(x, "d2/a2/renders/roadline_A2b_raw.png", H_, W2)
F = 960 / math.tan(math.radians(30)); ys, xs = np.mgrid[0:H_, 0:W2]; dy = ys + 0.5 - 410; below = dy > 0.5
t_ = np.where(below, EYE[2] / np.maximum(dy / F, 1e-9), np.nan); gx = EYE[0] + t_ * (xs + 0.5 - 960) / F
road = below & (gx >= 0) & (gx <= 7) & (t_ >= 3) & (t_ <= 1700); field = below & ((gx < 0) | (gx > 7)) & (t_ >= 3) & (t_ <= 1700)
cv, Yd = disp(out); mx = cv.max(-1); ce, fl = mx == 65535, mx == 0
a2 = open("n1/roadline/a2_eval.py").read(); ns = {"__name__": "a2", "__file__": f"{REPO}/n1/roadline/a2_eval.py"}
exec(compile(a2.split("\nif STEP == \"d1\":")[0].replace("STEP = sys.argv[1]; ", "STEP = 'none'; "), "a2_eval_defs", "exec"), ns)
fin, raw = ns["display_rows"](out), ns["display_rows"]("d2/a2/renders/roadline_A2b_raw.png"); inv = ns["order"](fin)
gd = GUARD["RLA2_canonical"]
rl = {"guard": gd, "stops": math.log2(S), "log2_s_over_oracle": math.log2(S / ORACLE_S),
      "H2v2_road_luminance_ceiling_frac": float((Yd[road] >= 99.9).mean()),
      "H3_floor_frac": float(fl.mean()), "H3_field_floor_frac": float(fl[field].mean()),
      "R3_extraction": {kk: v["RAX"][kk] for kk in ("colour_active", "C0_bit_identical", "C2_frac_ok", "C3_frac_ok")},
      "R3_display_gates": {kk: g[kk] for kk in ("finite", "ch_min", "ch_max", "G1", "G2", "G3", "S-1", "S-2", "S-3")},
      "R4_inversions": inv, "R5_present_final": {d: fin[d]["present"] for d in fin}, "R5_present_raw": {d: raw[d]["present"] for d in raw},
      "report_H1_any_channel_frame_ceiling": float(ce.mean()), "report_C1_road_chromatic_ceiling": float((ce & (Yd < 99.9))[road].mean()),
      "report_frame_luminance_ceiling": float((Yd >= 99.9).mean()), "report_lamp_max_code_above_bg": {d: fin[d]["max_code_above_bg"] for d in fin},
      "report_lamp_display_signal": {d: fin[d]["display_signal"] for d in fin}}
# R3: C0 bit-identical; AX-C2/C3 still bound >= 99.9 %; display gates
rl["H2v2_PASS"] = rl["H2v2_road_luminance_ceiling_frac"] <= 0.001
rl["H3_PASS"] = rl["H3_floor_frac"] <= 0.0062 and rl["H3_field_floor_frac"] <= 0.0062
rl["R3_PASS"] = rl["R3_extraction"]["C0_bit_identical"] and min(rl["R3_extraction"]["C2_frac_ok"], rl["R3_extraction"]["C3_frac_ok"]) >= 0.999 and all(bool(vv) for kk, vv in rl["R3_display_gates"].items() if kk not in ("ch_min", "ch_max"))
rl["R4_PASS"] = not inv; rl["R5_PASS"] = rl["R5_present_final"] == rl["R5_present_raw"]
rl["stage1_automatic_PASS"] = all(rl[kk] for kk in ("H2v2_PASS", "H3_PASS", "R3_PASS", "R4_PASS", "R5_PASS"))
res["stage1_roadline"] = rl
res["verify_manifest_after"] = subprocess.run(["d1/verify_manifest.sh"], capture_output=True, text=True).stdout
dflt = lambda o: bool(o) if isinstance(o, np.bool_) else float(o)
json.dump(res, open("d2/a2/results_A2b.json", "w"), indent=1, default=dflt)
print(json.dumps(rl, indent=1, default=dflt))
