#!/usr/bin/env python3
"""N1.6 RoadLine-A2 (n1/roadline/PREREG_A2.md), written and committed before any A2 D1 run.
  per input NAME in (in_s0, in_s1, canonical):
    nix develop -c d1/a_extract/axis_a_x.sh n1/roadline/work/A6/NAME_cdm2.exr 60 d1/a_extract/.cache/RLA2_NAME
    nix develop -c d1/pipeline/axis_a.sh   n1/roadline/work/A6/NAME_cdm2.exr 60 d1/pipeline/.cache/A/RLA2_NAME.exr
    tracks/temporal-glare-2009/py.sh n1/roadline/a2_eval.py d1 NAME     (canonical also writes the linear anchor 'raw')
  tracks/temporal-glare-2009/py.sh n1/roadline/a2_eval.py gate          -> G-A2, R3, R4, R5 in n1/roadline/a2_A.json
Estimator (addendum 6): aperture r_ap = projected emitter radius (px) + 1.5 px; background = median of the annulus
r_ap+1 < r <= r_ap+3.5 px excluding pixels within r_ap of any other emitter centre. Display domain: 16-bit code ->
sRGB decode -> Y_disp = 0.1 + 99.9 * Y (cd/m^2). Presence: max-channel code in the aperture >= annulus median + 1."""
import json, math, os, sys
import numpy as np, OpenImageIO as oiio
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")); os.chdir(REPO); sys.path.insert(0, f"{REPO}/n1")
from cam import project_view
STEP = sys.argv[1]; W = "n1/roadline/work/A6"; RES_F = "n1/roadline/a2_A.json"; YW = np.array([0.2126, 0.7152, 0.0722])
F = 960 / math.tan(math.radians(30)); RADIUS = 0.105; EYE = (0.5, 0.0, 1.7)
lamps = [l for l in json.load(open("n1/roadline/work/A/lamps.json"))["lamps"] if l["in_frame"]]
diam = {l["d"]: 2 * RADIUS / l["r_m"] * F for l in lamps}
res = json.load(open(RES_F)) if os.path.exists(RES_F) else {"prereg": "n1/roadline/PREREG_A2.md"}


def est(img, l):
    cx, cy = l["px"]; r_ap = diam[l["d"]] / 2 + 1.5; R = int(np.ceil(r_ap + 4.5))
    x0, y0 = int(cx) - R, int(cy) - R; sub = img[y0:y0 + 2 * R + 1, x0:x0 + 2 * R + 1]
    ys, xs = np.mgrid[y0:y0 + sub.shape[0], x0:x0 + sub.shape[1]]; r = np.hypot(xs + 0.5 - cx, ys + 0.5 - cy)
    excl = np.zeros_like(r, bool)
    for o in lamps:
        if o is not l: excl |= np.hypot(xs + 0.5 - o["px"][0], ys + 0.5 - o["px"][1]) <= diam[o["d"]] / 2 + 1.5
    bg = float(np.median(sub[(r > r_ap + 1) & (r <= r_ap + 3.5) & ~excl])); ap = r <= r_ap
    om = (F / np.sqrt(F ** 2 + (xs + 0.5 - 960) ** 2 + (ys + 0.5 - 410) ** 2)) ** 3 / F ** 2
    return float(((sub - bg) * om)[ap].sum()), bg, sub[ap]


def display_rows(png):
    cv = oiio.ImageBuf(png).get_pixels(oiio.UINT16)[..., :3].astype(np.int64)
    v = cv / 65535.0; lin = np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4); Yd = 0.1 + 99.9 * (lin @ YW)
    mx = cv.max(-1).astype(float); rows = {}
    for l in lamps:
        s = est(Yd, l)[0]; _, bgc, apc = est(mx, l)
        rows[str(l["d"])] = {"display_signal": s, "present": bool(apc.max() >= bgc + 1), "max_code_above_bg": float(apc.max() - bgc)}
    return rows


def order(rows):
    ds = sorted(int(d) for d in rows); inv = []
    for a, b in zip(ds, ds[1:]):                                        # the table intensity at the eye decreases with d here
        fa, fb = rows[str(a)], rows[str(b)]
        if (fa["present"] or fb["present"]) and fb["display_signal"] > fa["display_signal"] * (1 + 1e-6): inv.append([a, b])
    return inv


if STEP == "d1":
    NAME = sys.argv[2]
    src = open("d1/display_r/run.py").read().split("\nres = {\"prereg\"")[0]
    a = 'return g, dict(H=H, W=W,'; assert a in src
    src = src.replace(a, 'return g, dict(RAX=r_ax, YA=Ya, PHYS=phys, H=H, W=W,')
    __file__ = f"{REPO}/d1/display_r/run.py"; exec(src)
    os.makedirs("n1/roadline/renders", exist_ok=True); out = f"n1/roadline/renders/A2_{NAME}_final.png"
    g, v = run_image(f"{W}/{NAME}_cdm2.exr", f"RLA2_{NAME}", "yprio", out)
    ent = {"R3": {"extraction_selfcheck": {k: v["RAX"][k] for k in ("colour_active", "C0_bit_identical", "C2_frac_ok", "C3_frac_ok")},
                  "tone_map_mode": v["RAX"]["tone_map"]["mode"], "display_gates": {k: g[k] for k in ("finite", "ch_min", "ch_max", "G1", "G2", "G3", "S-1", "S-2", "S-3")}},
           "final": display_rows(out)}
    if NAME == "canonical":
        H_, W2 = v["H"], v["W"]; phys, Ya = v["PHYS"], v["YA"]; Y = phys @ M709[1]
        ax, ay = project_view((-10, 40, 0), EYE, 0.0, 0.0); win = (slice(int(ay) - 3, int(ay) + 4), slice(int(ax) - 3, int(ax) + 4))
        k = float(np.median(Ya.reshape(H_, W2)[win]) / np.median(Y.reshape(H_, W2)[win])); Yreq_k = LO + (HI - LO) * k * Y
        x, c = realise(phys * (Yreq_k / np.where(Y > 0, Y, 1))[:, None], Yreq_k, "yprio"); emit(x, "n1/roadline/renders/A2_canonical_raw.png", H_, W2)
        ent["raw"] = display_rows("n1/roadline/renders/A2_canonical_raw.png"); ent["anchor_k_per_cdm2"] = k
    res[NAME] = ent; print(json.dumps(ent, indent=1, default=float))
elif STEP == "gate":
    s0, s1, cn = res["in_s0"]["final"], res["in_s1"]["final"], res["canonical"]
    far = {d: s0[d]["display_signal"] / s1[d]["display_signal"] - 1 for d in ("800", "1600")}
    GA2 = {"far_display_signal_dev": far, "R4_inversions_s0": order(s0), "R4_inversions_s1": order(s1),
           "R5_present_s0": {d: s0[d]["present"] for d in s0}, "R5_present_s1": {d: s1[d]["present"] for d in s1}}
    GA2["PASS"] = all(abs(v) <= 0.02 for v in far.values()) and GA2["R4_inversions_s0"] == GA2["R4_inversions_s1"] and GA2["R5_present_s0"] == GA2["R5_present_s1"]
    res["G-A2"] = GA2
    res["R3"] = cn["R3"]
    inv = order(cn["final"]); res["R4"] = {"inversions": inv, "display_signal": {d: cn["final"][d]["display_signal"] for d in cn["final"]}, "PASS": not inv}
    pf = {d: cn["final"][d]["present"] for d in cn["final"]}; pr = {d: cn["raw"][d]["present"] for d in cn["raw"]}
    res["R5"] = {"present_final": pf, "present_raw": pr, "max_code_above_bg_final": {d: cn["final"][d]["max_code_above_bg"] for d in cn["final"]},
                 "max_code_above_bg_raw": {d: cn["raw"][d]["max_code_above_bg"] for d in cn["raw"]}, "PASS": pf == pr}
    print(json.dumps({k: res[k] for k in ("G-A2", "R3", "R4", "R5")}, indent=1, default=float))
json.dump(res, open(RES_F, "w"), indent=1, default=float)
