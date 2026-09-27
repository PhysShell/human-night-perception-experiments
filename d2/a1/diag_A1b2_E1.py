#!/usr/bin/env python3
"""Post-hoc diagnostic (after results_A1b2.json; changes no result): classify the A1b stage-2 literal FAILs (hero G3;
S2 P-2b) against d1/ERRATA.md E1 (sRGB knee round-trip). Re-runs the identical shoulder path without writing images and
reports, per failing image, the offending pixels and their linear display channel values vs the knee 0.04045/12.92.
  tracks/temporal-glare-2009/py.sh d2/a1/diag_A1b2_E1.py   -> d2/a1/diag_A1b2_E1.json"""
import json, os
import numpy as np
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")); os.chdir(REPO)
SCALE_LINE = "Yreq = LO + (HI - LO) * Ya"; SHOULDER_LINE = "Yreq = LO + (HI - LO) * (np.maximum(Ya, 0) / (1 + np.maximum(Ya, 0)))"
assert f'SHOULDER_LINE = "{SHOULDER_LINE}"' in open("d2/a1/run_A1b.py").read()
src = open("d1/display_r/run.py").read().split("\nres = {\"prereg\"")[0]; src = src.replace(SCALE_LINE, SHOULDER_LINE)
a = 'return g, dict(H=H, W=W,'; src = src.replace(a, 'return g, dict(DH=dh, HM=hm, CO=co, CB=cb, X=x, ING=c["ing"], H=H, W=W,')
gv = {"__name__": "diag", "__file__": f"{REPO}/d1/display_r/run.py"}; exec(compile(src, "d1/display_r/run.py[diag]", "exec"), gv)
KNEE = 0.04045 / 12.92; out = {}


def diag(inp, ax):
    g, v = gv["run_image"](inp, ax, "yprio", None); keys = ("G3", "S-1", "S-2", "S-3", "G3_hue_max_rad", "S2_chroma_increase_max")
    r = {k: g[k] for k in keys}
    if not (g["G3"] and g["S-2"] and g["S-1"] and g["S-3"]):
        bad = (v["HM"] & (v["DH"] > 1e-6)) | ((v["CO"] - v["CB"]) > 1e-12); idx = np.flatnonzero(bad)
        lin = (v["X"][idx] - 0.1) / 99.9
        r["bad_px"] = int(len(idx)); r["bad_in_gamut"] = int(v["ING"][idx].sum())
        r["bad_detail"] = [{"px": int(i), "lin_rgb": [float(t) for t in l], "min_abs_dist_to_knee": float(np.abs(l - KNEE).min()),
                            "hue_rad": float(v["DH"][i]), "chroma_inc": float(v["CO"][i] - v["CB"][i]), "chroma_out": float(v["CO"][i])} for i, l in zip(idx[:10], lin[:10])]
    return r


out["hero"] = diag("n1/work/hero_cdm2.exr", "N1_hero")
out["S2"] = {}
for f in range(1, 49):
    n = f"frame_{f:04d}"; r = diag(f"d0/work/inputs/S2/{n}.exr", f"S2/{n}")
    if "bad_px" in r: out["S2"][n] = r
out["S2_failing_frames"] = sorted(out["S2"]); json.dump(out, open("d2/a1/diag_A1b2_E1.json", "w"), indent=1, default=float)
print(json.dumps(out, indent=1, default=float)[:6000])
