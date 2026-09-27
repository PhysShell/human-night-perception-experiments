#!/usr/bin/env python3
"""D2-A1b stage 1, exactly as d2/a1/PREREG_A1b.md (committed before this code): Yreq = 0.1 + 99.9 * f(max(Y_A, 0)),
f(Y) = Y / (1 + Y) (Reinhard 2002 Eq. 3), on RoadLine-A2 canonical and S1. Frozen code exec'd; B untouched; no frozen
file edited. Also builds the two frozen-vs-shoulder sheets.
  tracks/temporal-glare-2009/py.sh d2/a1/run_A1b.py   -> d2/a1/results_A1b.json, d2/a1/renders/A1b_*.png"""
import json, math, os, subprocess
import numpy as np, OpenImageIO as oiio, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")); os.chdir(REPO)
SCALE_LINE = "Yreq = LO + (HI - LO) * Ya"
SHOULDER_LINE = "Yreq = LO + (HI - LO) * (np.maximum(Ya, 0) / (1 + np.maximum(Ya, 0)))"          # the one change
YW = np.array([0.2126, 0.7152, 0.0722]); WK = "d2/a1/work/A1b"; os.makedirs(WK, exist_ok=True); os.makedirs("d2/a1/renders", exist_ok=True)
res = {"prereg": "d2/a1/PREREG_A1b.md", "operator": "f(Y)=Y/(1+Y) on max(Y_A,0)",
       "verify_manifest_before": subprocess.run(["d1/verify_manifest.sh"], capture_output=True, text=True).stdout}


def disp(png):
    cv = oiio.ImageBuf(png).get_pixels(oiio.UINT16)[..., :3].astype(float); v = cv / 65535
    lin = np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4); return cv, 0.1 + 99.9 * (lin @ YW)


def report(png, frozen, Ya):
    r = {"Y_A_Q": {str(p): float(np.percentile(Ya, p)) for p in (50, 90, 99, 99.9)}, "Y_A_negative_px": int((Ya < 0).sum())}
    for tag, p in (("frozen", frozen), ("shoulder", png)):
        cv, Yd = disp(p); mx = cv.max(-1)
        r[tag] = {"lum_ceiling": float((Yd >= 99.9).mean()), "any_ch_ceiling": float((mx == 65535).mean()), "floor": float((mx == 0).mean()), "median_Y_disp": float(np.median(Yd))}
    return r


# --- RoadLine ---
src = open("d1/display_r/run.py").read().split("\nres = {\"prereg\"")[0]; assert src.count(SCALE_LINE) == 1
src = src.replace(SCALE_LINE, SHOULDER_LINE); a = 'return g, dict(H=H, W=W,'; assert a in src; src = src.replace(a, 'return g, dict(RAX=r_ax, YA=Ya, H=H, W=W,')
gv = {"__name__": "a1b", "__file__": f"{REPO}/d1/display_r/run.py"}; exec(compile(src, "d1/display_r/run.py[A1b]", "exec"), gv)
FROZ_RL = "n1/roadline/renders/A2_canonical_final.png"; RAW_RL = "n1/roadline/renders/A2_canonical_raw.png"     # frozen output; frozen linear anchor
out = "d2/a1/renders/roadline_A1b.png"; g, v = gv["run_image"]("n1/roadline/work/A6/canonical_cdm2.exr", "RLA2_canonical", "yprio", out)
H_, W2 = v["H"], v["W"]; F = 960 / math.tan(math.radians(30)); ys, xs = np.mgrid[0:H_, 0:W2]; dy = ys + 0.5 - 410; below = dy > 0.5
t_ = np.where(below, 1.7 / np.maximum(dy / F, 1e-9), np.nan); gx = 0.5 + t_ * (xs + 0.5 - 960) / F
road = below & (gx >= 0) & (gx <= 7) & (t_ >= 3) & (t_ <= 1700); field = below & ((gx < 0) | (gx > 7)) & (t_ >= 3) & (t_ <= 1700)
cv, Yd = disp(out); fl = cv.max(-1) == 0
a2 = open("n1/roadline/a2_eval.py").read(); ns = {"__name__": "a2", "__file__": f"{REPO}/n1/roadline/a2_eval.py"}
exec(compile(a2.split("\nif STEP == \"d1\":")[0].replace("STEP = sys.argv[1]; ", "STEP = 'none'; "), "a2_eval_defs", "exec"), ns)
fin, raw = ns["display_rows"](out), ns["display_rows"](RAW_RL); inv = ns["order"](fin)
rl = {"R3_extraction": {kk: v["RAX"][kk] for kk in ("C0_bit_identical", "C2_frac_ok", "C3_frac_ok")},
      "R3_display_gates": {kk: g[kk] for kk in ("finite", "G1", "G2", "G3", "S-1", "S-2", "S-3")},
      "R4_inversions": inv, "R5_present_final": {d: fin[d]["present"] for d in fin}, "R5_present_raw": {d: raw[d]["present"] for d in raw},
      "lamp_max_code_above_bg": {d: fin[d]["max_code_above_bg"] for d in fin}, "lamp_display_signal": {d: fin[d]["display_signal"] for d in fin},
      "H3_floor_frac": float(fl.mean()), "H3_field_floor_frac": float(fl[field].mean()),
      "report_H2v2_road_luminance_ceiling": float((Yd[road] >= 99.9).mean()), "report_road_median_Y_disp": float(np.median(Yd[road])),
      "report": report(out, FROZ_RL, v["YA"])}
rl["R3_PASS"] = rl["R3_extraction"]["C0_bit_identical"] and min(rl["R3_extraction"]["C2_frac_ok"], rl["R3_extraction"]["C3_frac_ok"]) >= 0.999 and all(rl["R3_display_gates"].values())
rl["R4_PASS"] = not inv; rl["R5_PASS"] = rl["R5_present_final"] == rl["R5_present_raw"]
rl["H3_PASS"] = rl["H3_floor_frac"] <= 0.0062 and rl["H3_field_floor_frac"] <= 0.0062
rl["automatic_PASS"] = all(rl[k] for k in ("R3_PASS", "R4_PASS", "R5_PASS", "H3_PASS")); res["roadline"] = rl

# --- S1 through the frozen d1/final/run.py text (still loop restricted to S1; F1/S2 not run) ---
fsrc = open("d1/final/run.py").read().split('\ng, v = run_image("d1/pipeline/.cache/F1.exr"')[0]
reps = [('OUTF = "d0/work/out/d1_pipeline/final"', f'OUTF = "{WK}"'),
        ('src = open("d1/display_r/run.py").read().split("\\nres = {\\"prereg\\"")[0]',
         'src = open("d1/display_r/run.py").read().split("\\nres = {\\"prereg\\"")[0].replace("' + SCALE_LINE + '", "' + SHOULDER_LINE + '")'),
        ("Yexp = np.clip(LO + (HI - LO) * YA, LO, HI)", "Yexp = np.clip(LO + (HI - LO) * (np.maximum(YA, 0) / (1 + np.maximum(YA, 0))), LO, HI)"),
        ('for s in ("S0", "S1", "S3_bar", "S3_nobar", "S4", "S5"):', 'for s in ("S1",):')]
for a_, b_ in reps:
    assert fsrc.count(a_) == 1, a_
    fsrc = fsrc.replace(a_, b_)
gf = {"__name__": "__main__", "__file__": f"{REPO}/d1/final/run.py"}; exec(compile(fsrc, "d1/final/run.py[A1b S1]", "exec"), gf)
s1 = gf["acc"]["stills"]["S1"]; frz = json.load(open("d1/final/acceptance.json"))["stills"]["S1"]
S1png = f"{WK}/S1__PHONE_SDR100_DARK.png"; FROZ_S1 = "d0/work/out/d1_pipeline/final/S1__PHONE_SDR100_DARK.png"
r1 = {"P": {k: s1[k] for k in s1 if k.startswith("P-")}, "P5_metrics": {"shoulder": s1["S1"], "frozen": frz["S1"]}, "report": report(S1png, FROZ_S1, gf["v"]["YA"])}
r1["automatic_PASS"] = all(bool(r1["P"][k]) for k in ("P-1", "P-2a", "P-2b", "P-3", "P-5")) and str(r1["P"]["P-4"]).endswith("PASS")
res["S1"] = r1
res["stage1_automatic_PASS"] = rl["automatic_PASS"] and r1["automatic_PASS"]
res["verify_manifest_after"] = subprocess.run(["d1/verify_manifest.sh"], capture_output=True, text=True).stdout
dflt = lambda o: bool(o) if isinstance(o, np.bool_) else float(o)
json.dump(res, open("d2/a1/results_A1b.json", "w"), indent=1, default=dflt)

# --- sheets (external visual gates): frozen D1 vs shoulder ---
ld = lambda p: oiio.ImageBuf(p).get_pixels(oiio.UINT16)[..., :3].astype(float) / 65535


def stack_sheet(dst, blocks):
    lab_h = 26; H = sum(b.shape[0] + lab_h for _, b in blocks); canvas = np.zeros((H, 960, 3)); y = 0; ys_ = []
    for c, b in blocks:
        ys_.append(y); canvas[y + lab_h:y + lab_h + b.shape[0], :b.shape[1]] = b; y += lab_h + b.shape[0]
    fig = plt.figure(figsize=(9.6, H / 100), dpi=100, facecolor="black"); fig.figimage(canvas, 0, 0, origin="upper")
    for (c, _), y0 in zip(blocks, ys_): fig.text(0.01, 1 - (y0 + 18) / H, c, color="w", fontsize=10)
    fig.savefig(dst, dpi=100, facecolor="black")


gap = np.zeros((6, 960, 3)); blocks = []
for lab, p in (("frozen D1", FROZ_RL), ("shoulder f=Y/(1+Y)", out)):
    im = ld(p); crop = np.zeros((410, 960, 3)); crop[:, 80:880] = im[410:820, 560:1360]
    blocks.append((f"RoadLine: {lab}: full frame | road crop 1:1 rows 410-820 cols 560-1360", np.concatenate([im.reshape(410, 2, 960, 2, 3).mean((1, 3)), gap, crop])))
stack_sheet("d2/a1/renders/A1b_sheet_roadline.png", blocks); blocks = []
for lab, p in (("frozen D1", FROZ_S1), ("shoulder f=Y/(1+Y)", S1png)):
    im = ld(p); blocks.append((f"S1: {lab}: full frame | band rows 100-420 1:1, left half | right half",
                               np.concatenate([im.reshape(410, 2, 960, 2, 3).mean((1, 3)), gap, im[100:420, :960], gap, im[100:420, 960:]])))
stack_sheet("d2/a1/renders/A1b_sheet_S1.png", blocks)
print(json.dumps({k: res[k] for k in ("roadline", "S1", "stage1_automatic_PASS")}, indent=1, default=dflt))
