#!/usr/bin/env python3
"""N1.7 automatic gates + sequence sheet, as n1/n17/PREREG_N17.md (+ amendment 1). Frozen D1 outputs only.
CF (floor <= 0.6250 %, any-channel ceiling <= 4.3545 %), SRC (lamp head >= 1 code where >= 7 px inside), R3 from the
view JSONs, report (pcond EXPOSURE, median Y_disp, luminance ceiling, log2 EXPOSURE steps), and an E1-class diagnostic
for any literal G3/S-2 FAIL (re-runs the frozen display path without writing images).
  tracks/temporal-glare-2009/py.sh n1/n17/eval.py   -> n1/n17/results_N17.json, n1/n17/N17_sequence_sheet.png"""
import json, math, os, re, subprocess, sys
import numpy as np, OpenImageIO as oiio, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")); os.chdir(REPO); sys.path.insert(0, f"{REPO}/n1")
from cam import project_view
V = json.load(open("n1/views.json")); YW = np.array([0.2126, 0.7152, 0.0722]); LAMP = (4.5, 45.0, 5.92)
SEQ = [("B", 0.0), ("K070", 0.70), ("K080", 0.80), ("K0875", 0.875), ("C", 1.0)]
res = {"prereg": "n1/n17/PREREG_N17.md", "verify_manifest": subprocess.run(["d1/verify_manifest.sh"], capture_output=True, text=True).stdout, "frames": {}}
src = open("d1/display_r/run.py").read().split("\nres = {\"prereg\"")[0]
src = src.replace('return g, dict(H=H, W=W,', 'return g, dict(RAX=r_ax, DH=dh, HM=hm, CO=co, CB=cb, X=x, ING=c["ing"], H=H, W=W,')
gv = {"__name__": "n17", "__file__": f"{REPO}/d1/display_r/run.py"}; exec(compile(src, "d1/display_r/run.py[n17 diag]", "exec"), gv)
KNEE = 0.04045 / 12.92
for k, t in SEQ:
    png = f"n1/renders/final/cam_{k}.png"; cv = oiio.ImageBuf(png).get_pixels(oiio.UINT16)[..., :3].astype(float); vv = cv / 65535
    Yd = 0.1 + 99.9 * (np.where(vv <= 0.04045, vv / 12.92, ((vv + 0.055) / 1.055) ** 2.4) @ YW); mx = cv.max(-1)
    hdr = open(f"d1/a_extract/.cache/N1_{k}/out.header").read(); m = re.search(r"EXPOSURE=([0-9.eE+-]+)", hdr)
    vj = json.load(open(f"n1/view_{k}.json")); r = {"t": t, "EXPOSURE": float(m.group(1)) if m else None, "tone_map_mode": vj["d1"]["tone_map_mode"],
         "median_Y_disp": float(np.median(Yd)), "lum_ceiling": float((Yd >= 99.9).mean()), "any_ch_ceiling": float((mx == 65535).mean()), "floor": float((mx == 0).mean()),
         "R3_extraction": vj["d1"]["extraction_selfcheck"], "R3_display": vj["d1"]["display_gates"], "OIDN": vj.get("oidn_gate", {}).get("PASS")}
    r["CF_PASS"] = r["floor"] <= 0.006250 and r["any_ch_ceiling"] <= 0.043545
    lx, ly = project_view(LAMP, V[k]["loc"], V[k]["yaw_deg"], V[k]["pitch_deg"]); sy, cy = math.sin(math.radians(V[k]["yaw_deg"])), math.cos(math.radians(V[k]["yaw_deg"]))
    front = (LAMP[0] - V[k]["loc"][0]) * (-sy) + (LAMP[1] - V[k]["loc"][1]) * cy > 0; r["lamp_px"] = [lx, ly] if front else "behind"
    if front and 7 <= lx <= 1913 and 7 <= ly <= 813:
        ys, xs = np.mgrid[0:820, 0:1920]; rr = np.hypot(xs + 0.5 - lx, ys + 0.5 - ly)
        r["SRC_code_above_annulus"] = float(mx[rr <= 3].max() - np.median(mx[(rr > 4.5) & (rr <= 7)])); r["SRC_PASS"] = r["SRC_code_above_annulus"] >= 1
    g = r["R3_display"]
    if not (g["G3"] and g["S-2"]):                                               # E1-class diagnostic
        gg, v = gv["run_image"](f"n1/work/view_{k}/view_cdm2.exr", f"N1_{k}", "yprio", None)
        bad = np.flatnonzero((v["HM"] & (v["DH"] > 1e-6)) | ((v["CO"] - v["CB"]) > 1e-12)); lin = (v["X"][bad] - 0.1) / 99.9
        r["E1_diag"] = {"bad_px": int(len(bad)), "bad_in_gamut": int(v["ING"][bad].sum()), "min_abs_dist_to_knee": [float(np.abs(l - KNEE).min()) for l in lin[:10]],
                        "hue_rad": [float(v["DH"][i]) for i in bad[:10]], "chroma_inc": [float(v["CO"][i] - v["CB"][i]) for i in bad[:10]]}
        r["E1_class"] = bool(len(bad) <= 3 and v["ING"][bad].all() and all(d < 1e-8 for d in r["E1_diag"]["min_abs_dist_to_knee"]))
    res["frames"][k] = r; print(k, {x: r[x] for x in ("EXPOSURE", "median_Y_disp", "lum_ceiling", "floor", "CF_PASS")}, r.get("SRC_PASS"), r.get("E1_class"), flush=True)
ex = [res["frames"][k]["EXPOSURE"] for k, _ in SEQ]; res["log2_EXPOSURE_steps"] = {f"{SEQ[i][0]}->{SEQ[i+1][0]}": math.log2(ex[i + 1] / ex[i]) for i in range(len(SEQ) - 1)}
res["automatic_PASS"] = all(f["OIDN"] is not False and f["R3_extraction"]["C0_bit_identical"] and min(f["R3_extraction"]["C2_frac_ok"], f["R3_extraction"]["C3_frac_ok"]) >= 0.999
                            and all(f["R3_display"][x] for x in ("finite", "G1", "G2", "S-1", "S-3")) and ((f["R3_display"]["G3"] and f["R3_display"]["S-2"]) or f.get("E1_class", False))
                            and f["CF_PASS"] and f.get("SRC_PASS", True) for f in res["frames"].values())
json.dump(res, open("n1/n17/results_N17.json", "w"), indent=1, default=lambda o: bool(o) if isinstance(o, np.bool_) else float(o))
print(json.dumps(res["log2_EXPOSURE_steps"], indent=1), "automatic_PASS", res["automatic_PASS"])
# sequence sheet (path order, not blind)
fig = plt.figure(figsize=(9.6, 5 * 4.45 + 0.2), dpi=100, facecolor="black"); H = fig.get_figheight() * 100
for i, (k, t) in enumerate(SEQ):
    im = oiio.ImageBuf(f"n1/renders/final/cam_{k}.png").get_pixels(oiio.FLOAT)[..., :3]
    ax = fig.add_axes([0, 1 - (i * 445 + 435) / H, 1, 410 / H]); ax.imshow(np.clip(im, 0, 1), interpolation="lanczos"); ax.axis("off")
    ax.set_title(f"{k}  t = {t}  (yaw {V[k]['yaw_deg']:.1f})", color="w", fontsize=10)
fig.savefig("n1/n17/N17_sequence_sheet.png", facecolor="black")
