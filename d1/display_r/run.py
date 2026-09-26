#!/usr/bin/env python3
"""D1-DR, exactly as d1/display_r/PREREG.md (committed before this code): C-priority vs Y-priority display realisation
of (Y_A, u'v'_B) on SDR100. Y_A = frozen pre-gamut extraction (d1/a_extract, v2); b = frozen B.
  nix develop -c d1/a_extract/run_ax.sh; nix develop -c d1/display_r/run_s2_ax.sh
  tracks/temporal-glare-2009/py.sh d1/display_r/run.py; tracks/temporal-glare-2009/py.sh d0/metrics.py d1_pipeline
  -> results.json (P-7 from d0/results/tables/metrics.jsonl), d0/work/out/d1_pipeline/dr_{cprio,yprio}/"""
import json, os, sys
import numpy as np, OpenImageIO as oiio
from scipy.stats import spearmanr
from scipy.ndimage import label, binary_dilation, binary_erosion, distance_transform_edt
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")); os.chdir(REPO)
__file__ = f"{REPO}/d1/a_extract/extract.py"
exec(open("d1/a_extract/extract.py").read().split("\nres = {\"prereg\"")[0])      # frozen extract(), frozen B (filament, stage, uv, M709, WU)
from display_model import decode
OUT = "d0/work/out/d1_pipeline"; CAND = {"cprio": "dr2_cprio", "yprio": "dr2_yprio"}; LO, HI = 0.1, 100.0   # v2 output dirs (v1 kept as dr_*)
ld = lambda p: oiio.ImageBuf(p).get_pixels(oiio.FLOAT)[..., :3].astype(np.float64)


def project(x, Yc):
    """Y-priority: towards Yc*white at fixed Y, maximal t in [0,1] (closed form). Returns x', t."""
    d = x - Yc[:, None]
    with np.errstate(divide="ignore", invalid="ignore"):
        lim = np.where(d > 0, (HI - Yc[:, None]) / d, np.where(d < 0, (LO - Yc[:, None]) / d, np.inf))
    tt = np.clip(np.minimum(1.0, lim.min(1)), 0, 1)
    return np.where((tt < 1)[:, None], Yc[:, None] + tt[:, None] * d, x), tt


def realise(x0, Yreq, cand):
    above, below = (x0 > HI).any(1), (x0 < LO).any(1); ing = ~above & ~below
    if cand == "yprio":
        x, tt = project(x0, np.clip(Yreq, LO, HI)); fb = np.zeros(len(x0), bool)
    else:
        s = np.minimum(1.0, HI / np.maximum(x0.max(1), 1e-300)); xs = x0 * s[:, None]
        fb = (xs < LO).any(1); Yc = np.clip(xs @ M709[1], LO, HI)
        xp, _ = project(xs, Yc); x = np.where(fb[:, None], xp, xs)
    x = np.where(ing[:, None], x0, x)                                               # in-gamut: exactly x0
    return x, dict(above=above, below=below, ing=ing, fb=fb)


def emit(x, dst, H, W):
    v = np.clip((x - LO) / (HI - LO), 0, 1); code = np.where(v <= 0.04045 / 12.92, 12.92 * v, 1.055 * v ** (1 / 2.4) - 0.055).reshape(H, W, 3)
    if dst:
        o = oiio.ImageBuf(oiio.ImageSpec(W, H, 3, oiio.UINT16)); o.set_pixels(oiio.ROI(0, W, 0, H, 0, 1, 0, 3), np.ascontiguousarray(code, np.float32)); o.write(dst)
    XYZ, _ = decode(code, "SDR100", "DARK"); return XYZ.reshape(-1, 3)


def uvE(E):
    s_ = E[:, 0] + 15 * E[:, 1] + 3 * E[:, 2]; return np.stack([4 * E[:, 0] / s_, 9 * E[:, 1] / s_], -1)


def run_image(src, axname, cand, dst):
    r_ax, v = extract(axname); H, W = v["H"], v["W"]; Ya = v["Ynew"]
    for f_ in ("pre.f32", "clip.f32"):                                              # disk hygiene: extract() dumps
        if os.path.exists(f"{AXC}/{axname}/{f_}"): os.remove(f"{AXC}/{axname}/{f_}")
    phys = ld(src).reshape(-1, 3); Y = phys @ M709[1]
    b = stage(filament(phys), Y, t(Y), "uv"); Yb = b @ M709[1]; Yreq = LO + (HI - LO) * Ya
    x0 = b * (Yreq / np.where(Yb > 0, Yb, 1))[:, None]
    x, c = realise(x0, Yreq, cand); E = emit(x, dst, H, W); Yo = E[:, 1]
    ub, uo = uv(b), uvE(E); cb, co = np.hypot(*(ub - WU).T), np.hypot(*(uo - WU).T)
    dh = np.abs(np.angle(np.exp(1j * (np.arctan2(*(uo - WU).T[::-1]) - np.arctan2(*(ub - WU).T[::-1])))))
    hm = (co > 1e-6) & (cb > 1e-6); duv = np.hypot(*(uo - ub).T)
    g = {"finite": bool(np.isfinite(x).all() and np.isfinite(E).all()), "ch_min": float(x.min()), "ch_max": float(x.max()),
         "frac_in_gamut": float(c["ing"].mean()), "frac_above_peak_class": float(c["above"].mean()), "frac_below_black_class": float(c["below"].mean()),
         "frac_fallback": float(c["fb"].mean()), "G2_identity_maxabs": float(np.abs(x[c["ing"]] - x0[c["ing"]]).max()) if c["ing"].any() else 0.0,
         "G3_hue_max_rad": float(dh[hm].max()) if hm.any() else 0.0, "AX_C0": r_ax["C0_bit_identical"], "AX_C3": r_ax["C3_frac_ok"]}
    g["G1"] = g["finite"] and g["ch_min"] >= LO * (1 - 1e-9) and g["ch_max"] <= HI * (1 + 1e-9); g["G2"] = g["G2_identity_maxabs"] == 0.0; g["G3"] = g["G3_hue_max_rad"] <= 1e-6
    if cand == "cprio":
        nf = ~c["fb"]; red = Yo < Yreq * (1 - 1e-9)
        g["S1_duv_max"] = float(duv[nf].max()) if nf.any() else 0.0
        Yrc = np.clip(Yreq, LO, HI); red = Yo < Yrc * (1 - 1e-9)                                  # v2: clamped reference
        g["S2_Y_over_req_max"] = float((Yo / Yrc).max()); g["S2_Y_reduced_outside_above"] = int((red & ~c["above"]).sum())
        g["S3_reduced_not_in_above"] = int((red & ~c["above"]).sum())
        g["S3_reduced_max_ch_dev"] = float(np.abs(x[red].max(1) - HI).max() / HI) if red.any() else 0.0
        g["S-1"] = g["S1_duv_max"] <= 1e-6; g["S-2"] = g["S2_Y_over_req_max"] <= 1 + 1e-9 and g["S2_Y_reduced_outside_above"] == 0
        g["S-3"] = g["S3_reduced_not_in_above"] == 0 and g["S3_reduced_max_ch_dev"] <= 1e-9
    else:
        Yc = np.clip(Yreq, LO, HI); pj = ~c["ing"]
        tight = np.minimum(np.abs(x[pj] - HI) / HI, np.abs(x[pj] - LO) / LO).min(1) if pj.any() else np.zeros(1)
        g["S1_dY_rel_max"] = float((np.abs(Yo - Yc) / Yc).max()); g["S2_chroma_increase_max"] = float((co - cb).max())
        g["S3_tightness_max"] = float(tight.max())
        g["S-1"] = g["S1_dY_rel_max"] <= 1e-6; g["S-2"] = g["S2_chroma_increase_max"] <= 1e-12; g["S-3"] = g["S3_tightness_max"] <= 1e-9
    rng = np.random.default_rng(0); idx = rng.choice(len(Y), min(20000, len(Y)), replace=False)
    g["oldP4_spearman_info"] = float(spearmanr(Y[idx], Yo[idx]).statistic)
    return g, dict(H=H, W=W, Y=Y, Yo=Yo, Yreq=Yreq, cb=cb, co=co, dh=dh, hm=hm, c=c)


res = {"prereg": "d1/display_r/PREREG.md", "cand": {}}
for cand, cfg in CAND.items():
    os.makedirs(f"{OUT}/{cfg}/S2__PHONE_SDR100_DARK", exist_ok=True); R = {"stills": {}}
    for s in ("S0", "S1", "S3_bar", "S3_nobar", "S4", "S5"):
        g, v = run_image(f"d0/work/inputs/{s}.exr", s, cand, f"{OUT}/{cfg}/{s}__PHONE_SDR100_DARK.png"); H, W = v["H"], v["W"]
        I = lambda a: a.reshape(H, W); Ye, Yp = I(v["Yo"]), I(v["Y"])
        if s == "S1":
            m0 = dict(np.load("d0/work/inputs/masks/S1.npz")); sky = m0["sky"]; L_sky = np.median(Yp[sky])
            hor = int(np.flatnonzero(m0["ground"].any(1)).min()); above = np.zeros_like(sky); above[:hor - 12, :] = True
            lab, n = label((Yp < 0.5 * L_sky) & above); sz = np.bincount(lab.ravel()); sz[0] = 0; tr = np.isin(lab, np.argsort(sz)[::-1][:2])
            dist = distance_transform_edt(~tr); ring = (dist >= 5) & (dist <= 20) & above & ~tr; far = (dist > 60) & sky
            inner = tr & ~binary_erosion(tr, iterations=2); outer = binary_dilation(tr, iterations=2) & ~tr & above
            _, (iy, ix) = distance_transform_edt(~inner, return_indices=True); oy, ox = np.nonzero(outer); py, px = iy[oy, ox], ix[oy, ox]; sp = Yp[oy, ox] > Yp[py, px]
            skyd, trd = np.median(Ye[sky]), np.median(Ye[tr]); rev = ((Ye[oy, ox] <= Ye[py, px]) & sp).sum() / max(sp.sum(), 1)
            g["S1"] = {"sky": float(skyd), "lamp_over_sky": float(np.median(Ye[m0["lamp"]]) / skyd), "poplar_weber": float(1 - trd / skyd),
                       "reversals": float(rev), "halo": float(np.median(Ye[ring]) / np.median(Ye[far]))}
            g["G5"] = bool(skyd <= 2 and g["S1"]["lamp_over_sky"] >= 10 and g["S1"]["poplar_weber"] >= 0.1 and rev <= 0.05 and 1 / 1.5 <= g["S1"]["halo"] <= 1.5)
            lampd = binary_dilation(m0["lamp"], iterations=3); Yr = I(v["Yreq"]); lamps = {}
            for part, m in (("core", lampd & (Yr >= 90)), ("shoulder", lampd & (Yr >= 50) & (Yr < 90))):
                mm = m.ravel(); ok = mm & (v["cb"] > 1e-6)
                hd = np.angle(np.exp(1j * v["dh"][mm & v["hm"]])) if (mm & v["hm"]).any() else np.zeros(1)
                lamps[part] = {"n_px": int(mm.sum()), "Y_out_over_req_median": float(np.median((v["Yo"] / v["Yreq"])[mm])) if mm.any() else None,
                               "chroma_retention_median": float(np.median((v["co"] / v["cb"])[ok])) if ok.any() else None,
                               "hue_dev_mean_rad_where_defined": float(np.mean(hd))}
            g["lamps_core_shoulder"] = lamps
        if s == "S3_bar":
            m3 = dict(np.load("d0/work/inputs/masks/S3.npz")); bw = 1 - Ye[m3["bar"]].mean() / Ye[m3["beside_bar"]].mean()
            g["S3_bar_weber"] = float(bw); g["G6"] = bool(bw > 0)
        if s == "S5":
            skyp = np.zeros((H, W), bool); skyp[: int(0.08 * H), :] = True; sp_ = skyp.ravel()      # sky proxy, fixed in code before running
            g["S5_sky_proxy"] = {"B_chroma_median": float(np.median(v["cb"][sp_])), "out_chroma_median": float(np.median(v["co"][sp_])),
                                 "frac_out_of_gamut": float((~v["c"]["ing"][sp_]).mean())}
        R["stills"][s] = g; print(cand, s, {k: g[k] for k in g if k in ("G1", "G2", "G3", "G5", "G6", "S-1", "S-2", "S-3", "frac_in_gamut", "frac_fallback")}, flush=True)
    # F1
    g, v = run_image("d1/pipeline/.cache/F1.exr", "F1", cand, f"{OUT}/{cfg}/F1__PHONE_SDR100_DARK.png"); H, W = v["H"], v["W"]
    lay = json.load(open("d1/pipeline/.cache/F1_layout.json")); per = {}
    for p in lay:
        sl = (slice(p["y0"] + 4, p["y0"] + p["size"] - 4), slice(p["x0"] + 4, p["x0"] + p["size"] - 4)); I = lambda a: a.reshape(H, W)[sl]
        per.setdefault(p["colour"], []).append({"L": p["L"], "Y_out": float(np.median(I(v["Yo"]))), "Y_req": float(np.median(I(v["Yreq"]))),
                                                "chroma_retention": float(np.median(I(v["co"]) / np.maximum(I(v["cb"]), 1e-12)))})
    g["patches"] = per; g["monotone"] = {c_: bool(all(b_["Y_out"] >= a_["Y_out"] * (1 - 1e-6) for a_, b_ in zip(q, q[1:]))) for c_, q in per.items()}
    g["G4"] = all(g["monotone"].values()); R["F1"] = g
    print(cand, "F1", g["monotone"], {k: g[k] for k in ("G1", "G2", "G3", "S-1", "S-2", "S-3")}, flush=True)
    # S2
    s2 = []
    for f in range(1, 49):
        n = f"frame_{f:04d}"; gg, _ = run_image(f"d0/work/inputs/S2/{n}.exr", f"S2/{n}", cand, f"{OUT}/{cfg}/S2__PHONE_SDR100_DARK/{n}.png"); s2.append(gg)
    R["S2_frames"] = {k: all(x[k] for x in s2) for k in ("G1", "G2", "G3", "S-1", "S-2", "S-3")}
    R["S2_frames"].update({"AX_C0_all": all(x["AX_C0"] for x in s2), "AX_C3_min": min(x["AX_C3"] for x in s2), "max_frac_fallback": max(x["frac_fallback"] for x in s2)})
    print(cand, "S2", R["S2_frames"], flush=True); res["cand"][cand] = R
json.dump(res, open("d1/display_r/results.json", "w"), indent=1, default=lambda o: bool(o) if isinstance(o, np.bool_) else float(o))
for p in ("d1/chroma_b4/.cache/i.f32", "d1/chroma_b4/.cache/o.f32"):
    if os.path.exists(p): os.remove(p)
