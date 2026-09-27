#!/usr/bin/env python3
"""D2-A1 / A1a probe, exactly as d2/a1/PREREG.md (committed before this code). Frozen D1 code is exec'd with ONE change:
Yreq = 0.1 + 99.9 * S * Y_A (S = 0.2641). No frozen file is edited or overwritten.
  tracks/temporal-glare-2009/py.sh d2/a1/run.py roadline   -> d2/a1/results.json [roadline], d2/a1/renders/roadline_a1a.png
  tracks/temporal-glare-2009/py.sh d2/a1/run.py corpus     -> d2/a1/results.json [corpus] (P-1..P-6, P-8; P-7 not run)"""
import json, math, os, subprocess, sys
import numpy as np, OpenImageIO as oiio
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")); os.chdir(REPO); sys.path.insert(0, f"{REPO}/n1")
from cam import project_view
S_A1A = 0.2641; STEP = sys.argv[1]; RES_F = "d2/a1/results.json"; os.makedirs("d2/a1/renders", exist_ok=True); os.makedirs("d2/a1/work", exist_ok=True)
res = json.load(open(RES_F)) if os.path.exists(RES_F) else {"prereg": "d2/a1/PREREG.md", "S": S_A1A}
res.setdefault("verify_manifest", {})[f"before_{STEP}"] = subprocess.run(["d1/verify_manifest.sh"], capture_output=True, text=True).stdout
YW = np.array([0.2126, 0.7152, 0.0722]); SCALE_LINE = "Yreq = LO + (HI - LO) * Ya"


def frozen_display_src():
    src = open("d1/display_r/run.py").read().split("\nres = {\"prereg\"")[0]
    assert src.count(SCALE_LINE) == 1
    return src.replace(SCALE_LINE, "Yreq = LO + (HI - LO) * S_A1A * Ya")                   # the one A1a change


def ceil_floor(png):
    a = oiio.ImageBuf(png).get_pixels(oiio.UINT16)[..., :3]; return a.max(-1) == 65535, a.max(-1) == 0


if STEP == "roadline":
    src = frozen_display_src(); a = 'return g, dict(H=H, W=W,'; assert a in src
    src = src.replace(a, 'return g, dict(RAX=r_ax, YA=Ya, PHYS=phys, H=H, W=W,')
    __file__ = f"{REPO}/d1/display_r/run.py"; exec(src)
    W6 = "n1/roadline/work/A6"; out = "d2/a1/renders/roadline_a1a.png"
    g, v = run_image(f"{W6}/canonical_cdm2.exr", "RLA2_canonical", "yprio", out)
    H_, W2 = v["H"], v["W"]; phys, Ya = v["PHYS"], v["YA"]; Y = phys @ M709[1]
    EYE = (0.5, 0.0, 1.7); ax, ay = project_view((-10, 40, 0), EYE, 0.0, 0.0); win = (slice(int(ay) - 3, int(ay) + 4), slice(int(ax) - 3, int(ax) + 4))
    k = float(np.median(Ya.reshape(H_, W2)[win]) / np.median(Y.reshape(H_, W2)[win])); Yreq_k = LO + (HI - LO) * S_A1A * k * Y     # linear anchor, same s
    x, c = realise(phys * (Yreq_k / np.where(Y > 0, Y, 1))[:, None], Yreq_k, "yprio"); emit(x, "d2/a1/renders/roadline_a1a_raw.png", H_, W2)
    # geometric road / field masks (as used to derive S in the PREREG)
    F = 960 / math.tan(math.radians(30)); ys, xs = np.mgrid[0:H_, 0:W2]; dy = ys + 0.5 - 410; below = dy > 0.5
    t = np.where(below, EYE[2] / np.maximum(dy / F, 1e-9), np.nan); gx = EYE[0] + t * (xs + 0.5 - 960) / F
    road = below & (gx >= 0) & (gx <= 7) & (t >= 3) & (t <= 1700); field = below & ((gx < 0) | (gx > 7)) & (t >= 3) & (t <= 1700)
    ce, fl = ceil_floor(out)
    H1 = float(ce.mean()); H2 = float(ce[road].mean()); H3f, H3g = float(fl.mean()), float(fl[field].mean())
    # R4 / R5 with the addendum-6 estimator (n1/roadline/a2_eval.py functions, loaded without running it)
    a2 = open("n1/roadline/a2_eval.py").read(); ns = {"__name__": "a2", "__file__": f"{REPO}/n1/roadline/a2_eval.py"}
    code = a2.split("\nif STEP == \"d1\":")[0].replace("STEP = sys.argv[1]; ", "STEP = 'none'; ")
    exec(compile(code, "a2_eval_defs", "exec"), ns)
    fin, raw = ns["display_rows"](out), ns["display_rows"]("d2/a1/renders/roadline_a1a_raw.png"); inv = ns["order"](fin)
    rl = {"R3_display_gates": {kk: g[kk] for kk in ("finite", "ch_min", "ch_max", "G1", "G2", "G3", "S-1", "S-2", "S-3")},
          "R3_extraction_C0": v["RAX"]["C0_bit_identical"],
          "H1_ceiling_frac": H1, "H1_PASS": H1 <= 0.0435, "H2_road_ceiling_frac": H2, "H2_PASS": H2 <= 0.001,
          "H3_floor_frac": H3f, "H3_field_floor_frac": H3g, "H3_PASS": H3f <= 0.0062 and H3g <= 0.0062,
          "R4_inversions": inv, "R4_PASS": not inv, "R5_present_final": {d: fin[d]["present"] for d in fin}, "R5_present_raw": {d: raw[d]["present"] for d in raw},
          "lamp_max_code_above_bg": {d: fin[d]["max_code_above_bg"] for d in fin}, "lamp_display_signal": {d: fin[d]["display_signal"] for d in fin}}
    rl["R5_PASS"] = rl["R5_present_final"] == rl["R5_present_raw"]
    rl["automatic_PASS"] = all(rl[kk] for kk in ("H1_PASS", "H2_PASS", "H3_PASS", "R4_PASS", "R5_PASS"))
    res["roadline"] = rl; print(json.dumps(rl, indent=1, default=float))
elif STEP == "corpus":
    fsrc = open("d1/final/run.py").read()
    reps = [('OUTF = "d0/work/out/d1_pipeline/final"', 'OUTF = "d2/a1/work/final"'),
            ('src = open("d1/display_r/run.py").read().split("\\nres = {\\"prereg\\"")[0]',
             'src = open("d1/display_r/run.py").read().split("\\nres = {\\"prereg\\"")[0].replace("' + SCALE_LINE + '", "Yreq = LO + (HI - LO) * S_A1A * Ya")'),
            ("Yexp = np.clip(LO + (HI - LO) * YA, LO, HI)", "Yexp = np.clip(LO + (HI - LO) * S_A1A * YA, LO, HI)"),
            ('f"{OUTF}/S2__PHONE_SDR100_DARK/{n}.png"', "None"),
            ('open("d1/final/acceptance.json", "w")', 'open("d2/a1/work/acceptance_a1a.json", "w")')]
    for a_, b_ in reps:
        assert fsrc.count(a_) == 1, a_
        fsrc = fsrc.replace(a_, b_)
    g_ = {"__name__": "__main__", "__file__": f"{REPO}/d1/final/run.py", "S_A1A": S_A1A}
    exec(compile(fsrc, "d1/final/run.py[A1a]", "exec"), g_)
    acc = json.load(open("d2/a1/work/acceptance_a1a.json")); cor = {"note": "P-7 not run (ratio gate; S2 frames not written)"}
    for s, r in acc["stills"].items():
        ce, fl = ceil_floor(f"d2/a1/work/final/{s}__PHONE_SDR100_DARK.png")
        cor[s] = {k_: r[k_] for k_ in r if k_.startswith("P-") or k_ in ("S1", "S3_bar_weber")}; cor[s]["ceiling_frac"] = float(ce.mean()); cor[s]["floor_frac"] = float(fl.mean())
    ce, fl = ceil_floor("d2/a1/work/final/F1__PHONE_SDR100_DARK.png")
    cor["F1"] = {k_: acc["F1"][k_] for k_ in acc["F1"] if k_.startswith("P-")}; cor["F1"]["ceiling_frac"] = float(ce.mean())
    cor["S2_frames"] = acc["S2_frames"]; res["corpus"] = cor; print(json.dumps(cor, indent=1, default=float))
res["verify_manifest"][f"after_{STEP}"] = subprocess.run(["d1/verify_manifest.sh"], capture_output=True, text=True).stdout
json.dump(res, open(RES_F, "w"), indent=1, default=lambda o: bool(o) if isinstance(o, np.bool_) else float(o))
