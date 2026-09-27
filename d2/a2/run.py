#!/usr/bin/env python3
"""D2-A2 stage 1, exactly as d2/a2/PREREG.md (committed before this code): native pcond -w as the axis-A exposure
selection on RoadLine-A2 canonical. Frozen D1 display/B/extraction code is exec'd unchanged; only the A caches differ
(built by d2/a2/axis_a_w.sh and axis_a_x_w.sh, whose diff vs the frozen scripts is exactly the -w flag).
  nix develop -c d2/a2/axis_a_w.sh   n1/roadline/work/A6/canonical_cdm2.exr 60 d1/pipeline/.cache/A/A2w_RLA2_canonical.exr
  nix develop -c d2/a2/axis_a_x_w.sh n1/roadline/work/A6/canonical_cdm2.exr 60 d1/a_extract/.cache/A2w_RLA2_canonical
  tracks/temporal-glare-2009/py.sh d2/a2/run.py   -> d2/a2/results.json, d2/a2/renders/roadline_w{,_raw}.png, d2/a2/map_*.txt"""
import json, math, os, re, shutil, subprocess, sys
import numpy as np, OpenImageIO as oiio
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")); os.chdir(REPO); sys.path.insert(0, f"{REPO}/n1")
from cam import project_view
ORACLE_S = 0.2641; YW = np.array([0.2126, 0.7152, 0.0722]); os.makedirs("d2/a2/renders", exist_ok=True)
res = {"prereg": "d2/a2/PREREG.md", "verify_manifest_before": subprocess.run(["d1/verify_manifest.sh"], capture_output=True, text=True).stdout}
for fz, cp in (("d1/pipeline/axis_a.sh", "d2/a2/axis_a_w.sh"), ("d1/a_extract/axis_a_x.sh", "d2/a2/axis_a_x_w.sh")):   # the one change
    a, b = open(fz).read(), open(cp).read(); assert a.replace("pcond -s -c -p", "pcond -s -w -c -p").replace("pcond -s -p", "pcond -s -w -p") == b, cp
src = open("d1/display_r/run.py").read().split("\nres = {\"prereg\"")[0]; a = 'return g, dict(H=H, W=W,'; assert a in src
src = src.replace(a, 'return g, dict(RAX=r_ax, YA=Ya, PHYS=phys, H=H, W=W,')
__file__ = f"{REPO}/d1/display_r/run.py"; exec(src)


def expo(hdr):
    return float(re.search(r"EXPOSURE=([0-9.eE+-]+)", open(hdr).read()).group(1))


def disp(png):
    cv = oiio.ImageBuf(png).get_pixels(oiio.UINT16)[..., :3].astype(float); v = cv / 65535
    lin = np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4); return cv, 0.1 + 99.9 * (lin @ YW)


# scale report: pcond mode/EXPOSURE, frozen vs -w
for tag, d in (("frozen", "d1/a_extract/.cache/RLA2_canonical"), ("w", "d1/a_extract/.cache/A2w_RLA2_canonical")):
    shutil.copy(f"{d}/map.txt", f"d2/a2/map_RLA2_canonical_{tag}.txt")
    res[f"pcond_{tag}"] = {"EXPOSURE": expo(f"{d}/out.header"), "tone_map": tone_map(f"{d}/map.txt")[1]}
fz, w = res["pcond_frozen"], res["pcond_w"]
res["scale"] = {"log2_EXPOSURE_w_over_frozen": math.log2(w["EXPOSURE"] / fz["EXPOSURE"]), "log2_oracle_over_frozen": math.log2(ORACLE_S)}
if fz["tone_map"]["mode"] == w["tone_map"]["mode"] == "linear":
    res["scale"]["log2_slope_w_over_frozen"] = math.log2(w["tone_map"]["slope_cdm2_per_cdm2"] / fz["tone_map"]["slope_cdm2_per_cdm2"])

# D1 on the -w A
W6 = "n1/roadline/work/A6"; out = "d2/a2/renders/roadline_w.png"; EYE = (0.5, 0.0, 1.7)
g, v = run_image(f"{W6}/canonical_cdm2.exr", "A2w_RLA2_canonical", "yprio", out)
H_, W2 = v["H"], v["W"]; phys, Ya = v["PHYS"], v["YA"]; Y = phys @ M709[1]
ax, ay = project_view((-10, 40, 0), EYE, 0.0, 0.0); win = (slice(int(ay) - 3, int(ay) + 4), slice(int(ax) - 3, int(ax) + 4))
k = float(np.median(Ya.reshape(H_, W2)[win]) / np.median(Y.reshape(H_, W2)[win])); Yreq_k = LO + (HI - LO) * k * Y      # linear anchor, -w scale
x, c = realise(phys * (Yreq_k / np.where(Y > 0, Y, 1))[:, None], Yreq_k, "yprio"); emit(x, "d2/a2/renders/roadline_w_raw.png", H_, W2)
F = 960 / math.tan(math.radians(30)); ys, xs = np.mgrid[0:H_, 0:W2]; dy = ys + 0.5 - 410; below = dy > 0.5
t_ = np.where(below, EYE[2] / np.maximum(dy / F, 1e-9), np.nan); gx = EYE[0] + t_ * (xs + 0.5 - 960) / F
road = below & (gx >= 0) & (gx <= 7) & (t_ >= 3) & (t_ <= 1700); field = below & ((gx < 0) | (gx > 7)) & (t_ >= 3) & (t_ <= 1700)
cv, Yd = disp(out); mx = cv.max(-1); ce, fl = mx == 65535, mx == 0
a2 = open("n1/roadline/a2_eval.py").read(); ns = {"__name__": "a2", "__file__": f"{REPO}/n1/roadline/a2_eval.py"}
exec(compile(a2.split("\nif STEP == \"d1\":")[0].replace("STEP = sys.argv[1]; ", "STEP = 'none'; "), "a2_eval_defs", "exec"), ns)
fin, raw = ns["display_rows"](out), ns["display_rows"]("d2/a2/renders/roadline_w_raw.png"); inv = ns["order"](fin)
rl = {"H2v2_road_luminance_ceiling_frac": float((Yd[road] >= 99.9).mean()),
      "H3_floor_frac": float(fl.mean()), "H3_field_floor_frac": float(fl[field].mean()),
      "R3_extraction": {kk: v["RAX"][kk] for kk in ("colour_active", "C0_bit_identical", "C2_frac_ok", "C3_frac_ok")},
      "R3_display_gates": {kk: g[kk] for kk in ("finite", "ch_min", "ch_max", "G1", "G2", "G3", "S-1", "S-2", "S-3")},
      "R4_inversions": inv, "R5_present_final": {d: fin[d]["present"] for d in fin}, "R5_present_raw": {d: raw[d]["present"] for d in raw},
      "report_H1_any_channel_frame_ceiling": float(ce.mean()), "report_C1_road_chromatic_ceiling": float((ce & (Yd < 99.9))[road].mean()),
      "report_frame_luminance_ceiling": float((Yd >= 99.9).mean()), "report_lamp_max_code_above_bg": {d: fin[d]["max_code_above_bg"] for d in fin},
      "anchor_k_per_cdm2": k}
# R3: C0 bit-identical vs the -w A output; AX-C2/C3 still bound >= 99.9 %; display gates
rl["H2v2_PASS"] = rl["H2v2_road_luminance_ceiling_frac"] <= 0.001
rl["H3_PASS"] = rl["H3_floor_frac"] <= 0.0062 and rl["H3_field_floor_frac"] <= 0.0062
rl["R3_PASS"] = rl["R3_extraction"]["C0_bit_identical"] and min(rl["R3_extraction"]["C2_frac_ok"], rl["R3_extraction"]["C3_frac_ok"]) >= 0.999 and all(bool(vv) for kk, vv in rl["R3_display_gates"].items() if kk not in ("ch_min", "ch_max"))
rl["R4_PASS"] = not inv; rl["R5_PASS"] = rl["R5_present_final"] == rl["R5_present_raw"]
rl["stage1_automatic_PASS"] = all(rl[kk] for kk in ("H2v2_PASS", "H3_PASS", "R3_PASS", "R4_PASS", "R5_PASS"))
res["stage1_roadline"] = rl
res["verify_manifest_after"] = subprocess.run(["d1/verify_manifest.sh"], capture_output=True, text=True).stdout
dflt = lambda o: bool(o) if isinstance(o, np.bool_) else float(o)
json.dump(res, open("d2/a2/results.json", "w"), indent=1, default=dflt)
print(json.dumps({kk: res[kk] for kk in ("pcond_frozen", "pcond_w", "scale", "stage1_roadline")}, indent=1, default=dflt))
