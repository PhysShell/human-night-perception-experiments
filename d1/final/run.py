#!/usr/bin/env python3
"""D1 final acceptance, exactly as d1/final/PREREG.md (committed before this run). Frozen code only:
A = d1/a_extract (v2), B = d1/chroma_b4, display = Y-priority (d1/display_r v2), P-4 = d1/p4v2.
  nix develop -c d1/a_extract/run_ax.sh; nix develop -c d1/display_r/run_s2_ax.sh
  tracks/temporal-glare-2009/py.sh d1/final/run.py; tracks/temporal-glare-2009/py.sh d0/metrics.py d1_pipeline (P-7)"""
import json, os
import numpy as np
from scipy.stats import spearmanr
from scipy.ndimage import label, binary_dilation, binary_erosion, distance_transform_edt
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")); os.chdir(REPO)
src = open("d1/display_r/run.py").read().split("\nres = {\"prereg\"")[0]
a = 'return g, dict(H=H, W=W,'; assert a in src
src = src.replace(a, 'return g, dict(LEFF=v["Leff"], YMAP=v["Ymap"], YA=Ya, DUV=duv, H=H, W=W,')
__file__ = f"{REPO}/d1/display_r/run.py"; exec(src)
OUTF = "d0/work/out/d1_pipeline/final"; os.makedirs(f"{OUTF}/S2__PHONE_SDR100_DARK", exist_ok=True); TOL = 1e-6


def p4(v):                                                   # d1/p4v2 logic, unchanged
    Yo, L, F, YA = v["Yo"], v["LEFF"], v["YMAP"], v["YA"]
    Yexp = np.clip(LO + (HI - LO) * YA, LO, HI); r = {"G1_max_rel_dev": float((np.abs(Yo - Yexp) / Yexp).max())}
    rng = np.random.default_rng(0); idx = rng.choice(len(L), min(20000, len(L)), replace=False)
    Ls, Fs, As, Os = L[idx], F[idx], YA[idx], Yo[idx]; n_res = n_inv = 0
    for s0 in range(0, len(idx), 500):
        sl = slice(s0, s0 + 500); res_ = (Fs[sl, None] < Fs[None, :]) & (As[None, :] > As[sl, None] * (1 + TOL))
        n_res += int(res_.sum()); n_inv += int((res_ & (Os[sl, None] > Os[None, :] * (1 + TOL))).sum())
    r.update({"resolvable_pairs": n_res, "inversions": n_inv})
    if n_res == 0:
        vals, cnt = np.unique(Ls, return_counts=True); m = L == vals[np.argmax(cnt)]
        r["R3_flat_rel_range"] = float(Yo[m].max() / Yo[m].min() - 1); r["P-4"] = "N/A+R3-flat " + ("PASS" if r["R3_flat_rel_range"] <= TOL and r["G1_max_rel_dev"] <= TOL else "FAIL")
    else:
        r["P-4"] = "PASS" if (r["G1_max_rel_dev"] <= TOL and n_inv == 0) else "FAIL"
    return r


def gates(g, v):
    c = v["c"]; ing = c["ing"]
    out = {"P-1": g["finite"], "P-2a_duv_max": float(v["DUV"][ing].max()) if ing.any() else 0.0}
    out["P-2a"] = bool(g["G2"] and out["P-2a_duv_max"] <= 1e-6)
    out["P-2b"] = bool(g["S-1"] and g["S-2"] and g["S-3"] and g["G3"])
    out["P-3"] = bool(g["G1"]); out["ch_min_max"] = [g["ch_min"], g["ch_max"]]; out["frac_projected"] = float((~ing).mean())
    out.update(p4(v)); return out


acc = {"prereg": "d1/final/PREREG.md", "stills": {}}
for s in ("S0", "S1", "S3_bar", "S3_nobar", "S4", "S5"):
    g, v = run_image(f"d0/work/inputs/{s}.exr", s, "yprio", f"{OUTF}/{s}__PHONE_SDR100_DARK.png"); r = gates(g, v)
    H, W = v["H"], v["W"]; I = lambda a: a.reshape(H, W); Ye, Yp = I(v["Yo"]), I(v["Y"])
    if s == "S1":
        m0 = dict(np.load("d0/work/inputs/masks/S1.npz")); sky = m0["sky"]; L_sky = np.median(Yp[sky])
        hor = int(np.flatnonzero(m0["ground"].any(1)).min()); above = np.zeros_like(sky); above[:hor - 12, :] = True
        lab, n = label((Yp < 0.5 * L_sky) & above); sz = np.bincount(lab.ravel()); sz[0] = 0; tr = np.isin(lab, np.argsort(sz)[::-1][:2])
        dist = distance_transform_edt(~tr); ring = (dist >= 5) & (dist <= 20) & above & ~tr; far = (dist > 60) & sky
        inner = tr & ~binary_erosion(tr, iterations=2); outer = binary_dilation(tr, iterations=2) & ~tr & above
        _, (iy, ix) = distance_transform_edt(~inner, return_indices=True); oy, ox = np.nonzero(outer); py, px = iy[oy, ox], ix[oy, ox]; sp = Yp[oy, ox] > Yp[py, px]
        skyd, trd = np.median(Ye[sky]), np.median(Ye[tr]); rev = ((Ye[oy, ox] <= Ye[py, px]) & sp).sum() / max(sp.sum(), 1)
        r["S1"] = {"sky": float(skyd), "lamp_over_sky": float(np.median(Ye[m0["lamp"]]) / skyd), "poplar_weber": float(1 - trd / skyd),
                   "reversals": float(rev), "halo": float(np.median(Ye[ring]) / np.median(Ye[far]))}
        r["P-5"] = bool(skyd <= 2 and r["S1"]["lamp_over_sky"] >= 10 and r["S1"]["poplar_weber"] >= 0.1 and rev <= 0.05 and 1 / 1.5 <= r["S1"]["halo"] <= 1.5)
    if s == "S3_bar":
        m3 = dict(np.load("d0/work/inputs/masks/S3.npz")); r["S3_bar_weber"] = float(1 - Ye[m3["bar"]].mean() / Ye[m3["beside_bar"]].mean()); r["P-6"] = r["S3_bar_weber"] > 0
    acc["stills"][s] = r; print(s, r, flush=True)
g, v = run_image("d1/pipeline/.cache/F1.exr", "F1", "yprio", f"{OUTF}/F1__PHONE_SDR100_DARK.png"); r = gates(g, v); H, W = v["H"], v["W"]
lay = json.load(open("d1/pipeline/.cache/F1_layout.json")); per = {}
for p in lay:
    sl = (slice(p["y0"] + 4, p["y0"] + p["size"] - 4), slice(p["x0"] + 4, p["x0"] + p["size"] - 4))
    per.setdefault(p["colour"], []).append({"L": p["L"], "Y_out": float(np.median(v["Yo"].reshape(H, W)[sl]))})
r["monotone"] = {c_: bool(all(b_["Y_out"] >= a_["Y_out"] * (1 - 1e-6) for a_, b_ in zip(q, q[1:]))) for c_, q in per.items()}
r["patches"] = per; r["P-8"] = bool(all(r["monotone"].values()) and r["P-3"] and r["P-2a"] and r["P-2b"]); acc["F1"] = r
print("F1", {k: r[k] for k in r if k != "patches"}, flush=True)
s2 = []
for f in range(1, 49):
    n = f"frame_{f:04d}"; g, v = run_image(f"d0/work/inputs/S2/{n}.exr", f"S2/{n}", "yprio", f"{OUTF}/S2__PHONE_SDR100_DARK/{n}.png"); s2.append(gates(g, v))
acc["S2_frames"] = {k: all(x[k] for x in s2) for k in ("P-1", "P-2a", "P-2b", "P-3")}
acc["S2_frames"]["P-4"] = sorted(set(x["P-4"] for x in s2)); acc["S2_frames"]["inversions"] = sum(x["inversions"] for x in s2)
print("S2", acc["S2_frames"], flush=True)
json.dump(acc, open("d1/final/acceptance.json", "w"), indent=1, default=lambda o: bool(o) if isinstance(o, np.bool_) else float(o))
for p in ("d1/chroma_b4/.cache/i.f32", "d1/chroma_b4/.cache/o.f32"):
    if os.path.exists(p): os.remove(p)
