#!/usr/bin/env python3
"""D1-AX, exactly as d1/a_extract/PREREG.md (committed before this code).
Axis-A luminance read from pcond's own chain *before* matscan's clipgamut: L_eff (post-scotscan, from the XYZE file
pcond reads) -> F (pcond -x map, cumf reconstructed at the bin edges) -> M (compxyz2rgbWBmat, Radiance verbatim).
  nix develop -c d1/a_extract/build_mat.sh; nix develop -c d1/a_extract/run_ax.sh
  tracks/temporal-glare-2009/py.sh d1/a_extract/extract.py   -> results.json, .cache/<scene>/Y_new.npy, sheet_F1.png"""
import json, os, subprocess, sys
import numpy as np, OpenImageIO as oiio
from scipy.ndimage import label, binary_dilation, binary_erosion, distance_transform_edt
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")); os.chdir(REPO); sys.path.insert(0, "d0")
exec(open("d1/chroma_b4/run.py").read().split("res = {")[0])          # frozen B: filament(), stage(), uv(), M709, WU
AXD = "d1/a_extract"; AXC = f"{AXD}/.cache"                         # after the exec (it defines its own D, C)
MAT = np.loadtxt(f"{AXD}/matscan_mat.txt")                                # pcond matscan matrix (XYZ_E -> Rec.709, von Kries)
LMIN, BOT, TOP, SWNORM, LDMAX, LDMIN, HIST, WHTEFF = 1e-7, 5.62e-3, 5.62, 2.26, 100.0, 1.0, 100, 179.0
t = lambda L: L / (L + 0.108)


def tone_map(path):
    """pcond's F from -x: returns (fn L -> Y_map, info). mapscan branch: exact cumf reconstruction at bin edges."""
    m = np.loadtxt(path); w, d = m[:, 0], m[:, 1]; ratio = d / w
    if np.ptp(ratio[(d > LDMIN * 1.0001) & (d < LDMAX * 0.9999)]) / np.median(ratio) < 1e-4:      # DO_LINEAR
        k = np.median(ratio[(d > LDMIN * 1.0001) & (d < LDMAX * 0.9999)])
        return (lambda L: np.where(L > 0, k * L / WHTEFF, 0.0)), {"mode": "linear", "slope_cdm2_per_cdm2": float(k)}   # v2 (PREREG_v2.md)
    b = np.log(w); s = np.mean(np.diff(b)); bwmin = b[0] - 0.5 * s; bwmax = bwmin + HIST * s
    c = (np.log(d) - np.log(LDMIN)) / (np.log(LDMAX) - np.log(LDMIN)); cum = np.zeros(HIST + 1)
    for i in range(HIST): cum[i + 1] = 2 * c[i] - cum[i]
    edges = bwmin + s * np.arange(HIST + 1); Bmin, Bmax = np.log(LDMIN), np.log(LDMAX)
    def F(L):
        L = np.asarray(L, float); bb = np.log(np.maximum(L, 1e-300)); cf = np.interp(bb, edges, cum)
        Bd = np.where((L <= LMIN) | (bb <= bwmin + 1e-6), Bmin, np.where(bb >= bwmax - 1e-6, Bmax, Bmin + cf * (Bmax - Bmin)))
        return np.where(L < LMIN, 0.0, (np.exp(Bd) - LDMIN) / (LDMAX - LDMIN))                # mapscan: Lw < LMIN -> black
    info = {"mode": "mapped", "bwmin": float(bwmin), "bwmax": float(bwmax), "cumf_last": float(cum[-1]),
            "cumf_min_step": float(np.diff(cum).min()), "C1": bool(np.diff(cum).min() >= -1e-5 and abs(cum[-1] - 1) <= 1e-3)}
    return F, info


def extract(sc):
    d = f"{AXC}/{sc}"; W, H = map(int, open(f"{d}/size").read().split())
    XYZ = np.fromfile(f"{d}/inX.f32", np.float32).reshape(-1, 3).astype(np.float64)          # file values / exposure
    col = open(f"{d}/colour_active").read().strip() == "1"
    Lp = XYZ[:, 1]
    if col:
        w = np.clip((Lp - BOT) / (TOP - BOT), 0, 1)
        with np.errstate(divide="ignore", invalid="ignore"):
            Ys = XYZ[:, 1] * (1.33 * (1 + (XYZ[:, 1] + XYZ[:, 2]) / XYZ[:, 0]) - 1.68)
        Ys = np.where(XYZ[:, 0] > 0, Ys, 0.0)                                                 # X = 0: reported below
        XYZp = np.where((w < 1 - 1e-6)[:, None], w[:, None] * XYZ + ((1 - w) * Ys / SWNORM)[:, None], XYZ)
    else:
        XYZp = XYZ
    Leff = XYZp[:, 1]; F, info = tone_map(f"{d}/map.txt"); Ymap = F(Leff)
    with np.errstate(divide="ignore", invalid="ignore"):
        pre = np.where((Leff > 0)[:, None], (Ymap / Leff)[:, None] * (XYZp @ MAT.T), 0.0)
    Ynew = pre @ M709[1]
    # C3: verbatim clipgamut(greypoint) on pre -> compare with pcond's actual output
    pre.astype(np.float32).tofile(f"{d}/pre.f32")
    subprocess.run([f"{AXC}/clipgamut", f"{d}/pre.f32", f"{d}/clip.f32", str(len(pre))], check=True)
    clip = np.fromfile(f"{d}/clip.f32", np.float32).reshape(-1, 3).astype(np.float64)
    out = oiio.ImageBuf(f"{d}/out.exr").get_pixels(oiio.FLOAT)[..., :3].astype(np.float64).reshape(-1, 3)
    froz = oiio.ImageBuf(f"d1/pipeline/.cache/A/{sc}.exr").get_pixels(oiio.FLOAT)[..., :3].astype(np.float64).reshape(-1, 3)
    Yold = out @ M709[1]; mx = out.max(1)
    c3ok = (np.abs(clip - out) <= (mx / 128 + 1e-3 * mx)[:, None] + 1e-12).all(1)
    inact = ((pre >= 0) & (pre <= 1)).all(1)
    c2ok = np.abs(Ynew - Yold) <= mx / 128 + 1e-3 * np.abs(Ynew) + 1e-12
    r = {"colour_active": col, "tone_map": info, "X_le_0_px": int((XYZ[:, 0] <= 0).sum()),
         "C0_bit_identical": bool(np.array_equal(out, froz)),
         "C2_frac_ok": float(c2ok[inact].mean()) if inact.any() else 1.0, "C2_n": int(inact.sum()),
         "C3_frac_ok": float(c3ok.mean()), "C3_fail_px": int((~c3ok).sum()),
         "vonKries_lum_factor_p1_p50_p99": np.percentile((Ynew / np.where(Ymap > 0, Ymap, np.nan))[Ymap > 1e-9], [1, 50, 99]).tolist(),
         "frac_Ynew_gt_1": float((Ynew > 1).mean())}
    return r, dict(W=W, H=H, XYZ=XYZ, Leff=Leff, Ymap=Ymap, Ynew=Ynew, Yold=Yold, mx=mx, c2ok=c2ok, c3ok=c3ok, inact=inact, out=out, clip=clip)


res = {"prereg": "d1/a_extract/PREREG.md", "scenes": {}}
# F1
r, v = extract("F1"); lay = json.load(open("d1/pipeline/.cache/F1_layout.json")); per = {}
I = lambda a: a.reshape(v["H"], v["W"], *a.shape[1:])
for p in lay:
    sl = (slice(p["y0"] + 4, p["y0"] + p["size"] - 4), slice(p["x0"] + 4, p["x0"] + p["size"] - 4))
    med = lambda a: float(np.median(I(a)[sl]))
    per.setdefault(p["colour"], []).append({"L": p["L"], "Y_new": med(v["Ynew"]), "Y_old": med(v["Yold"]), "Y_sens_Fonly": med(v["Ymap"]),
        "L_eff": med(v["Leff"]), "clipgamut_inactive": bool(I(v["inact"])[sl].all()), "C2_ok": bool(I(v["c2ok"])[sl].all()),
        "C3_ok_patch_median": bool(np.all(np.abs(np.median(I(v["clip"])[sl].reshape(-1, 3), 0) - np.median(I(v["out"])[sl].reshape(-1, 3), 0))
                                          <= np.median(I(v["mx"])[sl]) * (1 / 128 + 1e-3) + 1e-12))})
mono = lambda k: {c: bool(all(b_[k] >= a_[k] * (1 - 1e-6) for a_, b_ in zip(q, q[1:]))) for c, q in per.items()}
r["patches"] = per; r["G1_monotone_Y_new"] = mono("Y_new"); r["sens_monotone_Fonly"] = mono("Y_sens_Fonly"); r["old_monotone"] = mono("Y_old")
r["C2_F1_neutral_all"] = all(q["C2_ok"] for q in per["neutral"] if q["clipgamut_inactive"]) and any(q["clipgamut_inactive"] for q in per["neutral"])
r["C2_F1_inactive_patches_all"] = all(q["C2_ok"] for c in per.values() for q in c if q["clipgamut_inactive"])
r["C3_F1_all_patches"] = all(q["C3_ok_patch_median"] for c in per.values() for q in c)
r["G1"] = all(r["G1_monotone_Y_new"].values()); res["scenes"]["F1"] = r; print("F1", {k: r[k] for k in r if k != "patches"}, flush=True)
np.save(f"{AXC}/F1/Y_new.npy", I(v["Ynew"]).astype(np.float32))
# stills
for sc in ("S0", "S1", "S3_bar", "S3_nobar", "S4", "S5"):
    r, v = extract(sc); np.save(f"{AXC}/{sc}/Y_new.npy", I(v["Ynew"]).astype(np.float32))
    q = v["Ynew"] / np.where(v["Yold"] > 0, v["Yold"], np.nan); qq = q[np.isfinite(q)]
    r["ratio_new_old_p1_p50_p99"] = np.percentile(qq, [1, 50, 99]).tolist(); r["frac_differ_gt_1pct"] = float((np.abs(qq - 1) > 0.01).mean())
    r["C2"] = r["C2_frac_ok"] >= 0.999; r["C3"] = r["C3_frac_ok"] >= 0.999
    if sc in ("S1", "S5"):
        img = oiio.ImageBuf(f"d0/work/inputs/{sc}.exr").get_pixels(oiio.FLOAT)[..., :3].astype(np.float64); phys = img.reshape(-1, 3); Y = phys @ M709[1]
        b = stage(filament(phys), Y, t(Y), "uv"); Yb = b @ M709[1]; Yd = 0.1 + 99.9 * v["Ynew"]
        x = b * (Yd / np.where(Yb > 0, Yb, 1))[:, None]; r["frac_requested_out_of_SDR100"] = float(((x > 100) | (x < 0.1)).any(1).mean())
        if sc == "S1":
            Ye = Yd.reshape(v["H"], v["W"]); Yp = Y.reshape(v["H"], v["W"])
            m0 = dict(np.load("d0/work/inputs/masks/S1.npz")); sky = m0["sky"]; L_sky = np.median(Yp[sky])
            hor = int(np.flatnonzero(m0["ground"].any(1)).min()); above = np.zeros_like(sky); above[:hor - 12, :] = True
            lab, n = label((Yp < 0.5 * L_sky) & above); sz = np.bincount(lab.ravel()); sz[0] = 0; tr = np.isin(lab, np.argsort(sz)[::-1][:2])
            dist = distance_transform_edt(~tr); ring = (dist >= 5) & (dist <= 20) & above & ~tr; far = (dist > 60) & sky
            inner = tr & ~binary_erosion(tr, iterations=2); outer = binary_dilation(tr, iterations=2) & ~tr & above
            _, (iy, ix) = distance_transform_edt(~inner, return_indices=True); oy, ox = np.nonzero(outer); py, px = iy[oy, ox], ix[oy, ox]; sp = Yp[oy, ox] > Yp[py, px]
            skyd, trd = np.median(Ye[sky]), np.median(Ye[tr]); rev = ((Ye[oy, ox] <= Ye[py, px]) & sp).sum() / max(sp.sum(), 1)
            g = {"sky": float(skyd), "lamp_over_sky": float(np.median(Ye[m0["lamp"]]) / skyd), "poplar_weber": float(1 - trd / skyd), "reversals": float(rev),
                 "halo": float(np.median(Ye[ring]) / np.median(Ye[far]))}
            r["G2_values_requested"] = g
            r["G2"] = bool(skyd <= 2 and g["lamp_over_sky"] >= 10 and g["poplar_weber"] >= 0.1 and rev <= 0.05 and 1 / 1.5 <= g["halo"] <= 1.5)
    res["scenes"][sc] = r; print(sc, r, flush=True)
S = res["scenes"]
res["verdict"] = {"C0": all(S[s]["C0_bit_identical"] for s in S), "C1": all(S[s]["tone_map"].get("C1", True) for s in S),
                  "C2": S["F1"]["C2_F1_neutral_all"] and S["F1"]["C2_F1_inactive_patches_all"] and all(S[s]["C2"] for s in S if s != "F1"),
                  "C3": S["F1"]["C3_F1_all_patches"] and all(S[s]["C3"] for s in S if s != "F1"), "G1": S["F1"]["G1"], "G2": S["S1"]["G2"]}
res["verdict"]["PASS"] = all(res["verdict"].values()); print(res["verdict"])
json.dump(res, open(f"{AXD}/results.json", "w"), indent=1, default=lambda o: bool(o) if isinstance(o, np.bool_) else float(o))
for p in ("d1/chroma_b4/.cache/i.f32", "d1/chroma_b4/.cache/o.f32"):
    if os.path.exists(p): os.remove(p)
