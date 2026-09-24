#!/usr/bin/env python3
"""D0 descriptive measurements, identical for every donor (no score, no ranking).
Every output PNG (code values, d0 output contract) is decoded by d0/display_model.py with its scenario, so all
numbers are the light the (parametric) display emits, cd/m^2. Masks: d0/work/inputs/masks/<scene>.npz.

A NIGHT      sky_median, dark_median (non-source pixels), dark_log_range (log10 p99/p1 of non-source pixels),
             near_black_pct (Y <= 1.05 x black), silhouette_weber = (sky - tree)/sky (S0/S1/S2)
B SOURCES    peak, clipped_pct (any channel code >= 0.999, SDR; Y >= 0.99 peak, HDR), plateau blobs (Y >= 0.99 x peak,
             equivalent-area diameter in arcmin at the display's px/deg: count, median, max), source_bg_contrast
             (p99.9 in the source mask / sky median), halo_ratio (mean Y 2-10 px outside sources / sky median),
             lamp u'v' vs the scene's lamp u'v' (d_uv, saturation retention = |uv - white| out / in)
C VISIBILITY S3 pair only: HDR-VDP-3 side-by-side P_det of the bar (EVAL_VIEWER: the viewer's eye at the phone, HDR-VDP
             MTF; EVAL_OFF: optics off), a DIAGNOSTIC under HDR-VDP's observer model, never a human truth; and the
             displayed Weber contrast of the bar against the sky beside it
D TEMPORAL   S2: per-frame sky median, mean, energy in the source region; global flicker (max frame-to-frame change of the
             mean and sky median), source-region modulation (max-min)/mean, isolated flashes (5x5 windows around sources
             deviating > 20 % from BOTH neighbours in the same direction), empirical tone-curve movement (per frame, the
             displayed Y over pixels whose input Y is within +-3 % of fixed scene levels = frame-1 percentiles 10/50/90/99)
E DISPLAY    Y p0.1 / p99.9, used_log_range, headroom = peak / p99.9
  nix develop -c python3 d0/metrics.py [donor ...]  -> d0/results/tables/metrics.jsonl (+ scene reference rows)
"""
import glob, json, math, os, re, subprocess, sys
import numpy as np
import OpenImageIO as oiio
from scipy.ndimage import binary_dilation, label, uniform_filter
sys.path.insert(0, "d0")
from display_model import SCEN, decode, read_code, save_exr

I = "d0/work/inputs"; OUT = "d0/work/out"; TAB = "d0/results/tables"; os.makedirs(TAB, exist_ok=True)
Yw = np.array([0.2126, 0.7152, 0.0722]); M709 = np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750], [0.0193339, 0.1191920, 0.9503041]])
WHITE_UV = (0.1978, 0.4683)
MAN = json.load(open(f"{I}/manifest.json"))
PAT = re.compile(r"(?P<scene>S\d(?:_bar|_nobar)?)__(?P<geom>[A-Z]+)_(?P<lum>[A-Z0-9]+(?:_PQ)?)_(?P<amb>[A-Z]+)")


def uv(XYZ):
    X, Y, Z = XYZ[..., 0], XYZ[..., 1], XYZ[..., 2]; s = X + 15 * Y + 3 * Z + 1e-30
    return np.stack([4 * X / s, 9 * Y / s], -1)


def masks(scene):
    m = dict(np.load(f"{I}/masks/{scene.split('_')[0]}.npz"))
    if "lamp_any" in m:
        m["lamp"] = m["lamp_any"]
    return m


def scene_ref(scene):
    f = f"{I}/{scene}.exr"
    return oiio.ImageBuf(f).get_pixels(oiio.FLOAT)[..., :3].astype(np.float64)


def still_metrics(XYZ, code, scene, lum, ref_rgb):
    s = SCEN["luminance"][lum]
    pk, bk = s["peak_cd_m2"], s["black_cd_m2"]; ppd = SCEN["geometry"]["PHONE"]["px_per_deg"]
    Y = XYZ[..., 1]; m = masks(scene); lamp = m.get("lamp", np.zeros(Y.shape, bool))
    src = lamp if lamp.any() else np.zeros(Y.shape, bool)
    nonsrc = ~binary_dilation(src, iterations=3) if src.any() else np.ones(Y.shape, bool)
    r = {}
    sky = m.get("sky")
    r["sky_median"] = float(np.median(Y[sky])) if sky is not None and sky.any() else None
    r["dark_median"] = float(np.median(Y[nonsrc]))
    p1, p99 = np.percentile(Y[nonsrc], [1, 99]); r["dark_log_range"] = float(math.log10(max(p99, 1e-12) / max(p1, 1e-12)))
    r["near_black_pct"] = float(100 * np.mean(Y <= 1.05 * bk + 1e-12))
    if "tree" in m and m["tree"].any() and sky is not None:
        t = np.median(Y[m["tree"]]); r["silhouette_weber"] = float((r["sky_median"] - t) / max(r["sky_median"], 1e-12))
    r["peak"] = float(Y.max())
    r["clipped_pct"] = float(100 * np.mean((code >= 0.999).any(-1))) if s["transfer"] != "pq" else float(100 * np.mean(Y >= 0.99 * pk))
    plat = Y >= 0.99 * (pk if s["transfer"] != "pq" else pk)
    lab, n = label(plat)
    if n:
        areas = np.bincount(lab.ravel())[1:]; d = 2 * np.sqrt(areas / np.pi) / ppd * 60
        r["plateau_n"] = int(n); r["plateau_diam_median_arcmin"] = float(np.median(d)); r["plateau_diam_max_arcmin"] = float(d.max())
    else:
        r["plateau_n"] = 0
    if src.any():
        bg = r["sky_median"] if r["sky_median"] else r["dark_median"]
        r["source_bg_contrast"] = float(np.percentile(Y[src], 99.9) / max(bg, 1e-12))
        ring = binary_dilation(src, iterations=10) & ~binary_dilation(src, iterations=2)
        r["halo_ratio"] = float(Y[ring].mean() / max(bg, 1e-12))
        sel = src & (Y > 0)
        if sel.sum() > 3:
            u_out = uv(XYZ[sel]).mean(0)
            refXYZ = ref_rgb @ M709.T; u_in = uv(refXYZ[sel]).mean(0)
            r["lamp_uv_out"] = u_out.tolist(); r["lamp_uv_scene"] = u_in.tolist()
            r["lamp_d_uv"] = float(np.linalg.norm(u_out - u_in))
            r["lamp_saturation_retention"] = float(np.linalg.norm(u_out - WHITE_UV) / max(np.linalg.norm(u_in - WHITE_UV), 1e-9))
    q = np.percentile(Y, [0.1, 99.9]); r["Y_p0.1"], r["Y_p99.9"] = float(q[0]), float(q[1])
    r["used_log_range"] = float(math.log10(max(q[1], 1e-12) / max(q[0], 1e-12))); r["headroom"] = float(pk / max(q[1], 1e-12))
    return r


def pdet(bar_png, nobar_png, lum, amb, tag):
    res = {}
    t = f"d0/work/metrics_tmp/{tag}"; os.makedirs(t, exist_ok=True)
    for nm, p in (("bar", bar_png), ("nobar", nobar_png)):
        save_exr(f"{t}/{nm}.exr", decode(read_code(p), lum, amb)[1])
    for ev, mtf in (("EVAL_VIEWER", "hdrvdp"), ("EVAL_OFF", "none")):
        subprocess.run(f"tracks/hdrvdp3/run_hdrvdp.sh {t}/bar.exr {t}/nobar.exr PHONE {t}/{ev} --display none --mtf {mtf} --tasks side-by-side",
                       shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            txt = open(f"{t}/{ev}/run.json").read(); res[f"P_det_bar_{ev}"] = float(txt.split('"side-by-side":{"P_det":')[1].split(",")[0])
        except Exception:
            res[f"P_det_bar_{ev}"] = None
    subprocess.run(f"rm -rf {t}", shell=True)
    return res


def clip_metrics(frames, lum, amb):
    m = masks("S2"); src = binary_dilation(m["lamp_any"], iterations=2); sky = m["sky"]
    # empirical tone curve per frame: displayed Y (median) over the pixels whose INPUT luminance lies within
    # +-3 % (in log) of fixed scene levels taken from frame 1's percentiles 10/50/90/99
    ref0 = scene_ref("S1") @ Yw; levels = np.percentile(ref0, [10, 50, 90, 99])
    mean, skym, energy, tone, Ys = [], [], [], [], []
    for f in frames:
        Y = decode(read_code(f), lum, amb)[0][..., 1]
        n = int(os.path.basename(f)[6:10]); Yin = (oiio.ImageBuf(f"{I}/S2/frame_{n:04d}.exr").get_pixels(oiio.FLOAT)[..., :3] @ Yw)
        tone.append([np.median(Y[np.abs(np.log(np.maximum(Yin, 1e-12) / L)) < 0.03]) for L in levels])
        mean.append(Y.mean()); skym.append(np.median(Y[sky])); energy.append(Y[src].sum()); Ys.append(uniform_filter(Y, 5)[src])
    mean, skym, energy, tone = map(np.array, (mean, skym, energy, tone))
    flashes = 0
    for t in range(1, len(Ys) - 1):
        a, b = Ys[t] - Ys[t - 1], Ys[t] - Ys[t + 1]
        bl = np.where(a * b > 0, np.minimum(abs(a), abs(b)), 0) / np.maximum(np.maximum(Ys[t], 0.5 * (Ys[t - 1] + Ys[t + 1])), 1e-12)
        flashes += int((bl > 0.2).any())
    rel = lambda x: float(np.max(np.abs(np.diff(x)) / np.maximum(x[:-1], 1e-12)))
    return {"frames": len(frames), "mean_max_step_rel": rel(mean), "sky_median_max_step_rel": rel(skym),
            "source_energy_modulation": float((energy.max() - energy.min()) / energy.mean()), "frames_with_isolated_flash": flashes,
            "tone_curve_max_step_rel_at_scene_levels_p10_p50_p90_p99": [rel(tone[:, i]) for i in range(4)],
            "sky_median_first_last": [float(skym[0]), float(skym[-1])]}


def main(donors):
    # incremental: a still/clip already measured (same file path) is skipped; delete the jsonl for a full recompute
    done = {json.loads(l)["file"] for l in open(f"{TAB}/metrics.jsonl")} if os.path.exists(f"{TAB}/metrics.jsonl") else set()
    out = open(f"{TAB}/metrics.jsonl", "a")
    for donor in donors:
        for cfgdir in sorted(glob.glob(f"{OUT}/{donor}/*/")):
            cfg = os.path.basename(cfgdir.rstrip("/"))
            for p in sorted(glob.glob(f"{cfgdir}*.png")):
                mm = PAT.search(os.path.basename(p))
                if not mm or p in done:
                    continue
                d = mm.groupdict(); lum = d["lum"]
                XYZ, _ = decode(read_code(p), lum, d["amb"])
                row = {"donor": donor, "config": cfg, **d, "file": p, **still_metrics(XYZ, read_code(p), d["scene"], lum, scene_ref(d["scene"]))}
                if d["scene"] == "S3_bar":
                    nb = p.replace("S3_bar__", "S3_nobar__")
                    if os.path.exists(nb):
                        row.update(pdet(p, nb, lum, d["amb"], f"{donor}_{cfg}_{d['lum']}_{d['geom']}_{d['amb']}"))
                        Y = XYZ[..., 1]; mk = masks("S3"); row["bar_weber_displayed"] = float((Y[mk["beside_bar"]].mean() - Y[mk["bar"]].mean()) / max(Y[mk["beside_bar"]].mean(), 1e-12))
                out.write(json.dumps(row) + "\n"); out.flush(); print(donor, cfg, os.path.basename(p), flush=True)
            for dd in sorted(glob.glob(f"{cfgdir}S2__*/")):
                mm = PAT.search(os.path.basename(dd.rstrip("/"))); d = mm.groupdict()
                lum = d["lum"]
                frames = sorted(glob.glob(f"{dd}frame_*.png"))
                if len(frames) < 3 or dd in done:
                    continue
                out.write(json.dumps({"donor": donor, "config": cfg, **d, "file": dd, **clip_metrics(frames, lum, d["amb"])}) + "\n"); out.flush()
                print(donor, cfg, "S2", d, flush=True)


def scene_rows():
    """reference rows: the PHYSICAL scene measured with the same masks (cd/m^2), no display"""
    rows = []
    for s in ("S0", "S1", "S3_bar", "S4", "S5"):
        L = scene_ref(s); XYZ = L @ M709.T; m = masks(s); Y = XYZ[..., 1]
        r = {"donor": "SCENE", "config": "physical", "scene": s}
        sky = m.get("sky"); r["sky_median"] = float(np.median(Y[sky])) if sky is not None and sky.any() else None
        src = m.get("lamp", np.zeros(Y.shape, bool)); nonsrc = ~binary_dilation(src, iterations=3) if src.any() else np.ones(Y.shape, bool)
        r["dark_median"] = float(np.median(Y[nonsrc])); p1, p99 = np.percentile(Y[nonsrc], [1, 99]); r["dark_log_range"] = float(math.log10(p99 / max(p1, 1e-12)))
        if "tree" in m and m["tree"].any():
            r["silhouette_weber"] = float((r["sky_median"] - np.median(Y[m["tree"]])) / r["sky_median"])
        r["peak"] = float(Y.max())
        if src.any():
            bg = r["sky_median"] or r["dark_median"]; r["source_bg_contrast"] = float(np.percentile(Y[src], 99.9) / bg)
            ring = binary_dilation(src, iterations=10) & ~binary_dilation(src, iterations=2); r["halo_ratio"] = float(Y[ring].mean() / bg)
            r["lamp_uv_scene"] = uv(XYZ[src & (Y > 0)]).mean(0).tolist()
        if s == "S3_bar":
            r["bar_weber_scene"] = float((Y[m["beside_bar"]].mean() - Y[m["bar"]].mean()) / Y[m["beside_bar"]].mean())
        rows.append(r)
    json.dump(rows, open(f"{TAB}/scene_reference.json", "w"), indent=1)


if __name__ == "__main__":
    scene_rows()
    main(sys.argv[1:] or sorted(os.path.basename(d) for d in glob.glob(f"{OUT}/*") if os.path.isdir(d)))
