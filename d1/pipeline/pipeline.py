#!/usr/bin/env python3
"""D1 frozen A+B pipeline + acceptance gates P-1..P-6, P-8 (d1/pipeline/PREREG.md). Axis A from .cache/A (axis_a.sh).
Outputs: d0/work/out/d1_pipeline/frozen/<scene>__PHONE_SDR100_DARK.png (+ S2 dir) for d0/metrics.py; acceptance.json
  nix develop -c d1/pipeline/run_axis_a.sh; tracks/temporal-glare-2009/py.sh d1/pipeline/pipeline.py [frozen|r1_gamut]
Variant r1_gamut (PREREG_R1_gamut.md): minimum chroma projection towards Y_A*white into [0.1, 100]^3; P-2 -> P-2a/P-2b."""
import json, os, sys, glob
import numpy as np, OpenImageIO as oiio
from scipy.stats import spearmanr
from scipy.ndimage import label, binary_dilation, binary_erosion, distance_transform_edt
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")); os.chdir(REPO); sys.path.insert(0, "d0")
exec(open("d1/chroma_b4/run.py").read().split("res = {")[0])          # frozen B: filament(), stage(), uv(), M709
from display_model import decode
VAR = sys.argv[1] if len(sys.argv) > 1 else "frozen"; assert VAR in ("frozen", "r1_gamut")
ACC = "d1/pipeline/acceptance.json" if VAR == "frozen" else f"d1/pipeline/acceptance_{VAR[:2]}.json"
OUT = f"d0/work/out/d1_pipeline/{VAR}"; A = "d1/pipeline/.cache/A"; os.makedirs(f"{OUT}/S2__PHONE_SDR100_DARK", exist_ok=True)
t = lambda L: L / (L + 0.108)
def ld(p): return oiio.ImageBuf(p).get_pixels(oiio.FLOAT)[..., :3].astype(np.float64)

def render(src, apath, dst):
    img = ld(src); H, W = img.shape[:2]; phys = img.reshape(-1, 3); Y = phys @ M709[1]
    b = stage(filament(phys), Y, t(Y), "uv"); Yb = b @ M709[1]
    Yd = 0.1 + 99.9 * (ld(apath).reshape(-1, 3) @ M709[1])
    x = b * (Yd / np.where(Yb > 0, Yb, 1))[:, None]; r1 = {}
    if VAR == "r1_gamut":
        x0 = x; bad = (Yd < 0.1) | (Yd > 100); Ya = np.clip(Yd, 0.1, 100); d = x0 - Ya[:, None]
        with np.errstate(divide="ignore", invalid="ignore"):
            lim = np.where(d > 0, (100 - Ya[:, None]) / d, np.where(d < 0, (0.1 - Ya[:, None]) / d, np.inf))
        tt = np.clip(np.minimum(1.0, lim.min(1)), 0, 1); proj = tt < 1
        x = np.where(proj[:, None], Ya[:, None] + tt[:, None] * d, x0)
        r1 = {"x0": x0, "t": tt, "proj": proj, "Ya": Ya, "Yd_outside_range": int(bad.sum())}
    v = np.clip((x - 0.1) / 99.9, 0, 1); code = np.where(v <= 0.0031308, 12.92 * v, 1.055 * v ** (1 / 2.4) - 0.055).reshape(H, W, 3)
    o = oiio.ImageBuf(oiio.ImageSpec(W, H, 3, oiio.UINT16)); o.set_pixels(oiio.ROI(0, W, 0, H, 0, 1, 0, 3), np.ascontiguousarray(code, np.float32)); o.write(dst)
    XYZ, _ = decode(code, "SDR100", "DARK"); E = XYZ.reshape(-1, 3); s_ = E[:, 0] + 15 * E[:, 1] + 3 * E[:, 2]
    tol = 1e-9 if VAR == "r1_gamut" else 0.0
    hi, lo = (x > 100 * (1 + tol)).any(1), (x < 0.1 * (1 - tol)).any(1); ok = ~hi & ~lo
    duv = np.hypot(4 * E[:, 0] / s_ - uv(b)[:, 0], 9 * E[:, 1] / s_ - uv(b)[:, 1])
    rng = np.random.default_rng(0); idx = rng.choice(len(Y), min(20000, len(Y)), replace=False)
    g = {"finite": bool(np.isfinite(x).all() and np.isfinite(code).all()), "duv_max_unclipped": float(duv[ok].max()) if ok.any() else 0.0,
         "frac_above_peak": float(hi.mean()), "frac_below_black": float(lo.mean()), "spearman": float(spearmanr(Y[idx], E[idx, 1]).statistic)}
    if r1:
        pj, ub = r1["proj"], uv(b); uo = np.stack([4 * E[:, 0] / s_, 9 * E[:, 1] / s_], -1); cb, co = ub - WU, uo - WU
        rb, ro = np.hypot(*cb.T), np.hypot(*co.T); hm = pj & (rb > 1e-6)
        dh = np.abs(np.angle(np.exp(1j * (np.arctan2(co[:, 1], co[:, 0]) - np.arctan2(cb[:, 1], cb[:, 0])))))
        xp = x[pj]; tight = np.minimum(np.abs(xp - 100) / 100, np.abs(xp - 0.1) / 0.1).min(1) if pj.any() else np.zeros(0)
        g["P-2a_duv_max"] = float(duv[~pj].max()) if (~pj).any() else 0.0
        g["R1"] = {"frac_projected": float(pj.mean()), "t_median_projected": float(np.median(r1["t"][pj])) if pj.any() else 1.0,
                   "t_p5_projected": float(np.percentile(r1["t"][pj], 5)) if pj.any() else 1.0, "Yd_outside_range": r1["Yd_outside_range"],
                   "G1_identity_maxabs": float(np.abs(x[~pj] - r1["x0"][~pj]).max()) if (~pj).any() else 0.0,
                   "P2b_dY_rel_max": float((np.abs(E[pj, 1] - r1["Ya"][pj]) / r1["Ya"][pj]).max()) if pj.any() else 0.0,
                   "P2b_dhue_max_rad": float(dh[hm].max()) if hm.any() else 0.0,
                   "P2b_chroma_increase_max": float((ro[pj] - rb[pj]).max()) if pj.any() else 0.0,
                   "P2b_tightness_max": float(tight.max()) if pj.any() else 0.0,
                   "channel_min": float(x.min()), "channel_max": float(x.max())}
        R = g["R1"]
        g["P-2a"] = g["P-2a_duv_max"] <= 1e-6
        g["P-2b"] = R["P2b_dY_rel_max"] <= 1e-6 and R["P2b_dhue_max_rad"] <= 1e-6 and R["P2b_chroma_increase_max"] <= 1e-12 and R["P2b_tightness_max"] <= 1e-9
        g["R1-G1"] = R["G1_identity_maxabs"] == 0.0
        g["R1-G4"] = R["channel_min"] >= 0.1 * (1 - 1e-9) and R["channel_max"] <= 100 * (1 + 1e-9) and g["frac_above_peak"] == 0.0
    return g, Y.reshape(H, W), XYZ[..., 1], hi.reshape(H, W)

acc = {"prereg": "d1/pipeline/PREREG.md", "stills": {}}
for s in ("S0", "S1", "S3_bar", "S3_nobar", "S4", "S5"):
    g, Y, Ye, hi = render(f"d0/work/inputs/{s}.exr", f"{A}/{s}.exr", f"{OUT}/{s}__PHONE_SDR100_DARK.png")
    g["P-1"] = g["finite"]; g["P-2"] = g["duv_max_unclipped"] <= 1e-6 if VAR == "frozen" else (g["P-2a"] and g["P-2b"]); g["P-3"] = g["frac_above_peak"] <= 0.01; g["P-4"] = g["spearman"] >= 0.98
    if s == "S1":
        m0 = dict(np.load("d0/work/inputs/masks/S1.npz")); sky = m0["sky"]; L_sky = np.median(Y[sky])
        hor = int(np.flatnonzero(m0["ground"].any(1)).min()); above = np.zeros_like(sky); above[:hor - 12, :] = True
        lab, n = label((Y < 0.5 * L_sky) & above); sz = np.bincount(lab.ravel()); sz[0] = 0; tr = np.isin(lab, np.argsort(sz)[::-1][:2])
        dist = distance_transform_edt(~tr); ring = (dist >= 5) & (dist <= 20) & above & ~tr; far = (dist > 60) & sky
        inner = tr & ~binary_erosion(tr, iterations=2); outer = binary_dilation(tr, iterations=2) & ~tr & above
        _, (iy, ix) = distance_transform_edt(~inner, return_indices=True); oy, ox = np.nonzero(outer); py, px = iy[oy, ox], ix[oy, ox]; sp = Y[oy, ox] > Y[py, px]
        skyd, trd = np.median(Ye[sky]), np.median(Ye[tr]); rev = ((Ye[oy, ox] <= Ye[py, px]) & sp).sum() / max(sp.sum(), 1)
        g["S1"] = {"sky": float(skyd), "lamp_over_sky": float(np.median(Ye[m0["lamp"]]) / skyd), "poplar_weber": float(1 - trd / skyd), "reversals": float(rev),
                   "halo": float(np.median(Ye[ring]) / np.median(Ye[far]))}
        g["P-5"] = skyd <= 2 and g["S1"]["lamp_over_sky"] >= 10 and g["S1"]["poplar_weber"] >= 0.1 and rev <= 0.05 and 1 / 1.5 <= g["S1"]["halo"] <= 1.5
    if s == "S3_bar":
        m3 = dict(np.load("d0/work/inputs/masks/S3.npz")); bw = 1 - Ye[m3["bar"]].mean() / Ye[m3["beside_bar"]].mean()
        g["S3_bar_weber_displayed"] = float(bw); g["P-6"] = bw > 0
    acc["stills"][s] = {k: (bool(v) if isinstance(v, (bool, np.bool_)) else v) for k, v in g.items()}; print(s, acc["stills"][s], flush=True)
# F1
g, Y, Ye, hi = render("d1/pipeline/.cache/F1.exr", f"{A}/F1.exr", f"{OUT}/F1__PHONE_SDR100_DARK.png")
lay = json.load(open("d1/pipeline/.cache/F1_layout.json")); per = {}
for p in lay:
    sl = (slice(p["y0"] + 4, p["y0"] + p["size"] - 4), slice(p["x0"] + 4, p["x0"] + p["size"] - 4))
    per.setdefault(p["colour"], []).append({"L": p["L"], "Yd": float(np.median(Ye[sl])), "above_peak": bool(hi[sl].any())})
mono = {c: bool(all(b_["Yd"] >= a_["Yd"] - 1e-9 for a_, b_ in zip(v, v[1:]))) for c, v in per.items()}
clip_low = {c: [r["L"] for r in v if r["above_peak"] and r["L"] < 10] for c, v in per.items()}
acc["F1"] = {"global": g, "monotone": mono, "above_peak_below_10cdm2": clip_low, "patches": per,
             "P-8": bool(all(mono.values()) and not any(clip_low.values()) and (g["duv_max_unclipped"] <= 1e-6 if VAR == "frozen" else g["P-2a"] and g["P-2b"]))}
if VAR == "r1_gamut":
    acc["F1"]["R1-G5"] = bool(all(mono.values()) and not any(r["above_peak"] for v in per.values() for r in v))
print("F1", {k: acc["F1"][k] for k in ("monotone", "above_peak_below_10cdm2", "P-8")}, g, flush=True)
# S2
s2 = []
for f in sorted(glob.glob("d0/work/inputs/S2/frame_*.exr")):
    n = os.path.basename(f).replace(".exr", ""); g, *_ = render(f, f"{A}/S2/{n}.exr", f"{OUT}/S2__PHONE_SDR100_DARK/{n}.png")
    s2.append(g)
acc["S2_frames"] = {"all_finite": all(x["finite"] for x in s2), "max_duv_unclipped": max(x["duv_max_unclipped"] for x in s2),
                    "max_frac_above_peak": max(x["frac_above_peak"] for x in s2), "min_spearman": min(x["spearman"] for x in s2)}
if VAR == "r1_gamut":
    acc["S2_frames"].update({k: all(x[k] for x in s2) for k in ("P-2a", "P-2b", "R1-G1", "R1-G4")})
    acc["S2_frames"]["max_frac_projected"] = max(x["R1"]["frac_projected"] for x in s2)
def js(o):
    if isinstance(o, dict): return {k: js(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)): return [js(v) for v in o]
    return bool(o) if isinstance(o, np.bool_) else o
acc = js(acc)
json.dump(acc, open(ACC, "w"), indent=1); print("S2", acc["S2_frames"])
for p in ("d1/chroma_b4/.cache/i.f32", "d1/chroma_b4/.cache/o.f32"):
    if os.path.exists(p): os.remove(p)
