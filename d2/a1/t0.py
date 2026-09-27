#!/usr/bin/env python3
"""T0 distance-transport audit, exactly as d2/a1/PREREG_T0.md (committed before this code). No render, no image shown.
  tracks/temporal-glare-2009/py.sh d2/a1/t0.py build V    -> d2/a1/work/T0/V_cdm2.exr + stats   (V in atm, glare25, glare70)
  nix develop -c d1/pipeline/axis_a.sh   d2/a1/work/T0/V_cdm2.exr 60 d1/pipeline/.cache/A/T0_V.exr
  nix develop -c d1/a_extract/axis_a_x.sh d2/a1/work/T0/V_cdm2.exr 60 d1/a_extract/.cache/T0_V
  tracks/temporal-glare-2009/py.sh d2/a1/t0.py eval V     -> C1/C2/presence into d2/a1/results_T0.json; caches deleted
  (d2/a1/t0.sh runs all three variants)"""
import json, math, os, re, shutil, subprocess, sys
import numpy as np, OpenImageIO as oiio
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")); os.chdir(REPO)
STEP, V = sys.argv[1], sys.argv[2]; WK = "d2/a1/work/T0"; os.makedirs(WK, exist_ok=True); RES_F = "d2/a1/results_T0.json"
res = json.load(open(RES_F)) if os.path.exists(RES_F) else {"prereg": "d2/a1/PREREG_T0.md"}
YW = np.array([0.2126, 0.7152, 0.0722]); VIS = 25_000.0; P_PIG = 0.5; LUM_POLE_X = 7.5; EYE = (0.5, 0.0, 1.7)
T = lambda d: np.exp(-3.912 * d / VIS)
H_, W_ = 820, 1920; F = 960 / math.tan(math.radians(30)); ys, xs = np.mgrid[0:H_, 0:W_]; dx, dy = xs + 0.5 - 960, ys + 0.5 - 410
below = dy > 0.5; t_ = np.where(below, EYE[2] / np.maximum(dy / F, 1e-9), np.nan); gx = EYE[0] + t_ * dx / F
road = below & (gx >= 0) & (gx <= 7) & (t_ >= 3) & (t_ <= 1700); field = below & ((gx < 0) | (gx > 7)) & (t_ >= 3) & (t_ <= 1700)
lamps = json.load(open("n1/roadline/work/A/lamps.json"))["lamps"]


def rays(px, py):
    v = np.stack([(px + 0.5 - 960) / F, np.ones_like(px, float), (410 - (py + 0.5)) / F], -1); return v / np.linalg.norm(v, axis=-1, keepdims=True)


def cie146(th, A):
    th = np.maximum(th, 0.1); return 10 / th ** 3 + (5 / th ** 2 + 0.1 * P_PIG / th) * (1 + (A / 62.5) ** 4) + 0.0025 * P_PIG


if STEP == "build":
    rgb = oiio.ImageBuf("n1/roadline/work/A6/canonical_cdm2.exr").get_pixels(oiio.FLOAT)[..., :3].astype(np.float64); L = rgb @ YW
    sky_med = float(np.median(L[~below])); obj = ~below & (L > 2 * sky_med); sky = ~below & ~obj
    d = np.full((H_, W_), np.inf); d[below] = (t_ * np.sqrt(F ** 2 + dx ** 2 + dy ** 2) / F)[below]
    cols = np.array([[l["px"][0], 960 + F * (LUM_POLE_X - EYE[0]) / l["r_m"]] for l in lamps]); rm = np.array([l["r_m"] for l in lamps])
    near = np.abs(xs[obj][:, None, None] - cols[None]).min(-1).argmin(-1); d[obj] = rm[near]
    Lh = float(np.median(L[(ys >= 390) & (ys < 410)]))
    st = {"sky_median": sky_med, "L_h": Lh, "frac_ground": float(below.mean()), "frac_object_above_horizon": float(obj.mean()), "frac_sky": float(sky.mean()),
          "T_at": {str(dd): float(T(dd)) for dd in (25, 50, 100, 200, 400, 800, 1600)}}
    Tm = np.where(np.isfinite(d), T(np.where(np.isfinite(d), d, 0)), 1.0)
    if V == "atm":
        fac = np.where(below, Tm ** 2, Tm); add = np.where(np.isfinite(d), Lh * (1 - Tm), 0.0)
    else:
        fac = Tm; add = np.where(np.isfinite(d), Lh * (1 - Tm), 0.0); A = {"glare25": 25, "glare70": 70}[V]
        pix = rays(xs.astype(float), ys.astype(float)); veil = np.zeros((H_, W_)); per = {}
        for l in lamps:
            u = rays(np.array(l["px"][0] - 0.5), np.array(l["px"][1] - 0.5)); c = np.clip(pix @ u, -1, 1); th = np.degrees(np.arccos(c))
            E = float(T(l["r_m"])) * l["I_table_cd"] / l["r_m"] ** 2; vl = E * np.maximum(c, 0) * cie146(th, A); veil += vl
            per[str(l["d"])] = {"E_gl_lx_axis": E, "veil_at_centre": float(vl[410, 960])}
        add = add + veil
        st["veil"] = {"A": A, "per_lamp": per, "centre": float(veil[410, 960]),
                      "median_ratio_veil_over_scene": {k: float(np.median((veil / np.maximum(L, 1e-12))[m])) for k, m in (("road", road), ("field", field), ("sky", sky))},
                      "frac_frame_veil_gt_scene": float((veil > L).mean())}
    out = rgb * fac[..., None] + add[..., None]; Lo = out @ YW
    q = lambda a, m: {str(p): float(np.percentile(a[m], p)) for p in (50, 90, 99, 99.9)}
    st.update({"road_Q_before": q(L, road), "road_Q_after": q(Lo, road),
               "frame_logmean_before": float(np.exp(np.log(np.maximum(L, 1e-7)).mean())), "frame_logmean_after": float(np.exp(np.log(np.maximum(Lo, 1e-7)).mean()))})
    o = oiio.ImageBuf(oiio.ImageSpec(W_, H_, 3, oiio.FLOAT)); o.set_pixels(oiio.ROI(0, W_, 0, H_, 0, 1, 0, 3), np.ascontiguousarray(out, np.float32)); o.write(f"{WK}/{V}_cdm2.exr")
    res.setdefault(V, {})["build"] = st; print(json.dumps(st, indent=1))
elif STEP == "eval":
    SCALE_LINE = "Yreq = LO + (HI - LO) * Ya"
    src = open("d1/display_r/run.py").read().split("\nres = {\"prereg\"")[0]; assert src.count(SCALE_LINE) == 1
    a1b = open("d2/a1/run_A1b.py").read(); assert 'SHOULDER_LINE = "Yreq = LO + (HI - LO) * (np.maximum(Ya, 0) / (1 + np.maximum(Ya, 0)))"' in a1b
    src = src.replace(SCALE_LINE, "Yreq = LO + (HI - LO) * (Ya if MODE == 'frozen' else np.maximum(Ya, 0) / (1 + np.maximum(Ya, 0)))")
    a = 'return g, dict(H=H, W=W,'; assert a in src; src = src.replace(a, 'return g, dict(RAX=r_ax, H=H, W=W,')
    gv = {"__name__": "t0", "__file__": f"{REPO}/d1/display_r/run.py", "MODE": "frozen"}; exec(compile(src, "d1/display_r/run.py[T0]", "exec"), gv)
    a2 = open("n1/roadline/a2_eval.py").read(); ns = {"__name__": "a2", "__file__": f"{REPO}/n1/roadline/a2_eval.py"}
    exec(compile(a2.split("\nif STEP == \"d1\":")[0].replace("STEP = sys.argv[1]; ", "STEP = 'none'; "), "a2_eval_defs", "exec"), ns)
    ax = f"T0_{V}"; ev = {"frozen_EXPOSURE": float(re.search(r"EXPOSURE=([0-9.eE+-]+)", open(f"d1/a_extract/.cache/{ax}/out.header").read()).group(1))
                          if re.search("EXPOSURE=", open(f"d1/a_extract/.cache/{ax}/out.header").read()) else None}
    for mode in ("frozen", "shoulder"):
        gv["MODE"] = mode; png = f"{WK}/{V}_{mode}.png"; g, v = gv["run_image"](f"{WK}/{V}_cdm2.exr", ax, "yprio", png)
        cv = oiio.ImageBuf(png).get_pixels(oiio.UINT16)[..., :3].astype(float); vv = cv / 65535
        Yd = 0.1 + 99.9 * (np.where(vv <= 0.04045, vv / 12.92, ((vv + 0.055) / 1.055) ** 2.4) @ YW); rows = ns["display_rows"](png)
        ev[mode] = {"road_lum_ceiling": float((Yd[road] >= 99.9).mean()), "frame_lum_ceiling": float((Yd >= 99.9).mean()), "road_median_Y_disp": float(np.median(Yd[road])),
                    "C0": v["RAX"]["C0_bit_identical"], "tone_map": v["RAX"]["tone_map"],
                    "present": {d_: rows[d_]["present"] for d_ in rows}, "max_code_above_bg": {d_: rows[d_]["max_code_above_bg"] for d_ in rows}}
        os.remove(png)
    ev["C1_PASS"] = ev["frozen"]["road_lum_ceiling"] >= 0.5; ev["C2_PASS"] = ev["shoulder"]["road_lum_ceiling"] <= 0.001
    ev["presence_PASS"] = all(ev["frozen"]["present"].values()) and all(ev["shoulder"]["present"].values())   # all six present in vacuum under both
    res.setdefault(V, {})["eval"] = ev; print(json.dumps({k: ev[k] for k in ev if k not in ("frozen", "shoulder")} | {m: {k: ev[m][k] for k in ("road_lum_ceiling", "frame_lum_ceiling", "road_median_Y_disp", "C0")} for m in ("frozen", "shoulder")}, indent=1, default=float))
    shutil.rmtree(f"d1/a_extract/.cache/{ax}"); os.remove(f"d1/pipeline/.cache/A/{ax}.exr"); os.remove(f"{WK}/{V}_cdm2.exr")
res.setdefault("verify_manifest", {})[f"{STEP}_{V}"] = subprocess.run(["d1/verify_manifest.sh"], capture_output=True, text=True).stdout
json.dump(res, open(RES_F, "w"), indent=1, default=float)
