#!/usr/bin/env python3
"""N1.6A1 evaluation, as n1/roadline/PREREG.md (+ addenda 1-3). Written and committed before the A1 render.
  step gate : tracks/temporal-glare-2009/py.sh n1/roadline/a1_eval.py STIM gate   (R1 on the noisy pass, R2 OIDN bias)
              -> n1/roadline/work/STIM/rl_cdm2.exr (denoised x 179), rl_rgb.exr (Cycles units, for the comparator)
  (then)      nix develop -c d1/a_extract/axis_a_x.sh n1/roadline/work/STIM/rl_cdm2.exr 60 d1/a_extract/.cache/RL_STIM
              nix develop -c d1/pipeline/axis_a.sh   n1/roadline/work/STIM/rl_cdm2.exr 60 d1/pipeline/.cache/A/RL_STIM.exr
  step d1   : ... a1_eval.py STIM d1   (D1 final + the linear anchor 'raw'; R3, R4, R5) -> n1/roadline/renders/STIM_*.png
Lamp windows: half-size h = clip(floor(0.5 * distance to the nearest other lamp in pixels), 2, 16); background = median
of the ring h+1..h+3 px. Pixel solid angle cos^3(theta)/f^2 (pinhole)."""
import json, math, os, sys
import numpy as np, OpenImageIO as oiio
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")); os.chdir(REPO); sys.path.insert(0, f"{REPO}/n1")
from cam import project_view
ST, STEP = sys.argv[1], sys.argv[2]; W_ = f"n1/roadline/work/{ST}"; RES_F = f"n1/roadline/a1_{ST}.json"
K, YW = 179.0, np.array([0.2126, 0.7152, 0.0722]); EYE = (0.5, 0.0, 1.7); F = 960 / math.tan(math.radians(30))
CROPS = {"near_road": (3, 12, 0.003), "far_road": (3, 150, 0.003), "field": (-10, 40, 0), "sky": (0, 3000, 400)}
meta = json.load(open(f"{W_}/lamps.json")); lamps = [l for l in meta["lamps"] if l["in_frame"]]
res = json.load(open(RES_F)) if os.path.exists(RES_F) else {"stim": ST, "out_of_frame": [l["d"] for l in meta["lamps"] if not l["in_frame"]]}


def windows():
    P = np.array([l["px"] for l in lamps]); out = []
    for i, l in enumerate(lamps):
        dmin = min(np.hypot(*(P[j] - P[i])) for j in range(len(P)) if j != i); h = int(np.clip(np.floor(0.5 * dmin), 2, 16))
        out.append((l, h))
    return out


def window_signal(img, px, h, omega=True):
    """Integrated (img - ring median) over the window; x omega (sr) if omega, else plain sum. Returns (signal, bg, window)."""
    cx, cy = int(round(px[0] - 0.5)), int(round(px[1] - 0.5)); H_, W2 = img.shape[:2]
    y0, y1, x0, x1 = max(cy - h, 0), min(cy + h + 1, H_), max(cx - h, 0), min(cx + h + 1, W2)
    R = img[max(cy - h - 3, 0):cy + h + 4, max(cx - h - 3, 0):cx + h + 4]; ry, rx = np.mgrid[0:R.shape[0], 0:R.shape[1]]
    ring = (np.maximum(abs(ry - (cy - max(cy - h - 3, 0))), abs(rx - (cx - max(cx - h - 3, 0)))) > h)
    bg = float(np.median(R[ring])); win = img[y0:y1, x0:x1]
    if not omega: return float((win - bg).sum()), bg, win
    ys, xs = np.mgrid[y0:y1, x0:x1]; dx, dy = xs + 0.5 - 960, ys + 0.5 - 410
    om = (F / np.sqrt(F ** 2 + dx ** 2 + dy ** 2)) ** 3 / F ** 2
    return float(((win - bg) * om).sum()), bg, win


def ap_signal(img, px, others):
    """Addendum-5 estimator: r = 2.5 px aperture, background = median of the 3.5 < r <= 6.0 px annulus excluding other
    emitters' apertures; signal in (value x sr)."""
    cx, cy = px; x0, x1, y0, y1 = int(cx) - 8, int(cx) + 9, int(cy) - 8, int(cy) + 9
    ys, xs = np.mgrid[y0:y1, x0:x1]; r = np.hypot(xs + 0.5 - cx, ys + 0.5 - cy); sub = img[y0:y1, x0:x1]
    excl = np.zeros_like(r, bool)
    for o in others: excl |= np.hypot(xs + 0.5 - o[0], ys + 0.5 - o[1]) <= 2.5
    ann = (r > 3.5) & (r <= 6.0) & ~excl; ap = r <= 2.5; bg = float(np.median(sub[ann]))
    om = (F / np.sqrt(F ** 2 + (xs + 0.5 - 960) ** 2 + (ys + 0.5 - 410) ** 2)) ** 3 / F ** 2
    return float(((sub - bg) * om)[ap].sum()), bg, sub[ap]


def ap_all(img):
    out = {}
    for l in lamps:
        others = [m["px"] for m in lamps if m is not l]; out[l["d"]] = ap_signal(img, l["px"], others)
    return out


def load_passes(src):
    P = {}
    for si in range(oiio.ImageBuf(src).nsubimages):
        b = oiio.ImageBuf(src, si, 0); a = b.get_pixels(oiio.FLOAT)
        for i, c in enumerate(b.spec().channelnames):
            parts = c.split("."); P.setdefault(parts[-2], {})[parts[-1]] = a[..., i]
    return P


if STEP == "conv":                                                  # addendum 5: raw 2048 vs raw 4096
    Y = {n: K * (np.stack([load_passes(p)["Noisy Image"][c] for c in "RGB"], -1) @ YW) for n, p in ((2048, "n1/roadline/work/A2048/roadline.exr"), (4096, f"{W_}/roadline.exr"))}
    cr = {}
    for k_, p in CROPS.items():
        cx, cy = project_view(p, EYE, 0.0, 0.0); x0, y0 = int(round(cx)) - 24, int(round(cy)) - 24
        A_ = Y[4096][y0:y0 + 48, x0:x0 + 48].reshape(6, 8, 6, 8).transpose(0, 2, 1, 3).reshape(36, 64)
        B_ = Y[2048][y0:y0 + 48, x0:x0 + 48].reshape(6, 8, 6, 8).transpose(0, 2, 1, 3).reshape(36, 64)
        ma, mb = np.median(A_, 1), np.median(B_, 1); cr[k_] = float(np.median(np.abs(ma / mb - 1)))
    s4, s2 = ap_all(Y[4096]), ap_all(Y[2048]); em = {d: s4[d][0] / s2[d][0] - 1 for d in s4}
    res["convergence"] = {"crops_block_median_dev": cr, "emitter_dev": em,
                          "PASS": all(abs(v) <= 0.02 for v in cr.values()) and all(abs(v) <= 0.02 for v in em.values())}
    r1 = {}
    for l in lamps:
        I = s4[l["d"]][0] * l["r_m"] ** 2; r1[l["d"]] = {"I_measured": I, "I_table": l["I_table_cd"], "ratio": I / l["I_table_cd"], "bg_cdm2": s4[l["d"]][1], "PASS": abs(I / l["I_table_cd"] - 1) <= 0.10}
    res["R1v2"] = {"lamps": r1, "PASS": all(v["PASS"] for v in r1.values())}; res["R2"] = "N/A (no denoiser used; addendum 5)"
    raw = np.stack([load_passes(f"{W_}/roadline.exr")["Noisy Image"][c] for c in "RGB"], -1); H_, W2 = raw.shape[:2]
    for name, arr in (("rl_cdm2.exr", raw * K), ("rl_rgb.exr", raw)):
        o = oiio.ImageBuf(oiio.ImageSpec(W2, H_, 3, oiio.FLOAT)); o.set_pixels(oiio.ROI(0, W2, 0, H_, 0, 1, 0, 3), np.ascontiguousarray(arr, np.float32)); o.write(f"{W_}/{name}")
    print(json.dumps({k_: res[k_] for k_ in ("convergence", "R1v2", "R2")}, indent=1, default=float))
elif STEP == "gate":
    P = {}
    src = f"{W_}/roadline.exr"
    for si in range(oiio.ImageBuf(src).nsubimages):
        b = oiio.ImageBuf(src, si, 0); a = b.get_pixels(oiio.FLOAT)
        for i, c in enumerate(b.spec().channelnames):
            parts = c.split("."); P.setdefault(parts[-2], {})[parts[-1]] = a[..., i]
    noisy = np.stack([P["Noisy Image"][c] for c in "RGB"], -1); den = np.stack([P["Combined"][c] for c in "RGB"], -1)
    Yn, Yd = K * (noisy @ YW), K * (den @ YW)
    r1, r2l = {}, {}
    for l, h in windows():
        s_n, bg, _ = window_signal(Yn, l["px"], h); s_d, _, _ = window_signal(Yd, l["px"], h); I = s_n * l["r_m"] ** 2
        r1[l["d"]] = {"h": h, "I_measured": I, "I_table": l["I_table_cd"], "ratio": I / l["I_table_cd"], "bg_cdm2": bg, "PASS": abs(I / l["I_table_cd"] - 1) <= 0.10}
        r2l[l["d"]] = {"signal_noisy": s_n, "signal_denoised": s_d, "rel_dev": s_d / s_n - 1, "PASS": abs(s_d / s_n - 1) <= 0.02}
    r2c = {}
    for k, p in CROPS.items():
        cx, cy = project_view(p, EYE, 0.0, 0.0); sl = (slice(int(round(cy)) - 24, int(round(cy)) + 24), slice(int(round(cx)) - 24, int(round(cx)) + 24))
        r2c[k] = {"mean_noisy": float(Yn[sl].mean()), "mean_denoised": float(Yd[sl].mean()), "rel_dev": float(Yd[sl].mean() / Yn[sl].mean() - 1)}
        r2c[k]["PASS"] = abs(r2c[k]["rel_dev"]) <= 0.02
    res["R1"] = {"lamps": r1, "PASS": all(v["PASS"] for v in r1.values())}
    res["R2"] = {"crops": r2c, "lamp_windows": r2l, "whole_frame_rel_dev": float(Yd.mean() / Yn.mean() - 1),
                 "PASS": all(v["PASS"] for v in r2c.values()) and all(v["PASS"] for v in r2l.values())}
    H_, W2 = den.shape[:2]
    for name, arr in (("rl_cdm2.exr", den * K), ("rl_rgb.exr", den)):
        o = oiio.ImageBuf(oiio.ImageSpec(W2, H_, 3, oiio.FLOAT)); o.set_pixels(oiio.ROI(0, W2, 0, H_, 0, 1, 0, 3), np.ascontiguousarray(arr, np.float32)); o.write(f"{W_}/{name}")
    print(json.dumps({k: res[k] for k in ("R1", "R2")}, indent=1, default=float))
elif STEP == "d1":
    src = open("d1/display_r/run.py").read().split("\nres = {\"prereg\"")[0]
    a = 'return g, dict(H=H, W=W,'; assert a in src
    src = src.replace(a, 'return g, dict(RAX=r_ax, YA=Ya, PHYS=phys, YREQ=Yreq, H=H, W=W,')
    __file__ = f"{REPO}/d1/display_r/run.py"; exec(src)
    os.makedirs("n1/roadline/renders", exist_ok=True)
    g, v = run_image(f"{W_}/rl_cdm2.exr", f"RL_{ST}", "yprio", f"n1/roadline/renders/{ST}_final.png")
    H_, W2 = v["H"], v["W"]; phys, Ya = v["PHYS"], v["YA"]; Y = phys @ M709[1]
    ax, ay = project_view(CROPS["field"], EYE, 0.0, 0.0); win = (slice(int(ay) - 3, int(ay) + 4), slice(int(ax) - 3, int(ax) + 4))
    k = float(np.median(Ya.reshape(H_, W2)[win]) / np.median(Y.reshape(H_, W2)[win])); Yreq_k = LO + (HI - LO) * k * Y
    x, c = realise(phys * (Yreq_k / np.where(Y > 0, Y, 1))[:, None], Yreq_k, "yprio"); emit(x, f"n1/roadline/renders/{ST}_raw.png", H_, W2)
    res["R3"] = {"extraction_selfcheck": {kk: v["RAX"][kk] for kk in ("colour_active", "C0_bit_identical", "C2_frac_ok", "C3_frac_ok")},
                 "tone_map_mode": v["RAX"]["tone_map"]["mode"], "display_gates": {kk: g[kk] for kk in ("finite", "ch_min", "ch_max", "G1", "G2", "G3", "S-1", "S-2", "S-3")},
                 "anchor_k_per_cdm2": k}

    def codes(p):
        return oiio.ImageBuf(p).get_pixels(oiio.UINT16)[..., :3].astype(np.int64)

    def disp_Y(cv):
        vv = cv / 65535.0; lin = np.where(vv <= 0.04045, vv / 12.92, ((vv + 0.055) / 1.055) ** 2.4); return LO + (HI - LO) * (lin @ YW)
    out = {}
    for tag in ("final", "raw"):
        cv = codes(f"n1/roadline/renders/{ST}_{tag}.png"); mx = cv.max(-1).astype(float); Yd = disp_Y(cv); rows = {}
        sY, sM = ap_all(Yd), ap_all(mx)                                # addendum-5 estimator
        for l in lamps:
            s = sY[l["d"]][0]; bgc, apc = sM[l["d"]][1], sM[l["d"]][2]
            rows[l["d"]] = {"display_signal": s, "present": bool(apc.max() >= bgc + 1), "max_code_above_bg": float(apc.max() - bgc)}
        out[tag] = rows
    ds = [l["d"] for l in lamps]; R1s = res["R1v2"]["lamps"]
    scene_sig = {d: R1s[str(d) if str(d) in R1s else d]["I_measured"] / (next(l for l in lamps if l["d"] == d)["r_m"] ** 2) for d in ds}
    inv = []
    for a_, b_ in zip(ds, ds[1:]):                                     # b_ farther than a_
        if scene_sig[b_] < scene_sig[a_]:
            fa, fb = out["final"][a_], out["final"][b_]
            if not (not fa["present"] and not fb["present"]) and fb["display_signal"] > fa["display_signal"] * (1 + 1e-6): inv.append([a_, b_])
    res["R4"] = {"final_display_signal": {d: out["final"][d]["display_signal"] for d in ds}, "inversions": inv, "PASS": not inv}
    pres_f = {d: out["final"][d]["present"] for d in ds}; pres_r = {d: out["raw"][d]["present"] for d in ds}
    res["R5"] = {"present_final": pres_f, "present_raw": pres_r, "max_code_above_bg_final": {d: out["final"][d]["max_code_above_bg"] for d in ds},
                 "max_code_above_bg_raw": {d: out["raw"][d]["max_code_above_bg"] for d in ds}, "PASS": pres_f == pres_r}
    print(json.dumps({k_: res[k_] for k_ in ("R3", "R4", "R5")}, indent=1, default=float))
json.dump(res, open(RES_F, "w"), indent=1, default=float)
