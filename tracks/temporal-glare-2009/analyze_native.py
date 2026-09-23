#!/usr/bin/env python3
"""Measurement-only analysis of the NATIVE temporal-glare artefacts (nothing is re-simulated).

Inputs (all produced by the unmodified author code, see README):
  A  research-cache/temporal-glare-2009/trace_psf/frames.csv   per simulate() step: hippus pupil uniform
     (from `apitrace dump` of the glare_demo run; one step = 20 ms simulated time, glare.cpp sim_timer)
  B  research-cache/temporal-glare-2009/trace_psf/dumps/f*.json float RGB32F PSF framebuffer (glretrace -D)
  C  research-cache/temporal-glare-2009/native_psf|native_glare/png  8-bit X11 grabs of the demo window
  D  results/native/temporal-glare-2009/NATIVE_hippus_curves.csv       Octave run of the author's hippus.m
Outputs: results/native/temporal-glare-2009/NATIVE_*  (plots, CSV, JSON, montage, MP4 via ffmpeg)
Run: tracks/temporal-glare-2009/py.sh tracks/temporal-glare-2009/analyze_native.py
"""
import base64, csv, glob, json, os, re, subprocess, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import OpenImageIO as oiio

REPO = "/home/user/human-night-perception-experiments"
RC = f"{REPO}/research-cache/temporal-glare-2009"
OUT = f"{REPO}/results/native/temporal-glare-2009"
os.makedirs(OUT, exist_ok=True)
STEP_S = 0.020  # glare.cpp: sim_timer = 20 ms, simulate_hippus(sim_timer*1e-3) per step

# demo angular scale DERIVED from glare.cpp constants (not stated in the paper):
#   aperture image width N = 10 mm over FFT_SIZE = 512 px; lambda1 = N/d = 10/20.32*1e3 (nm) so that one FFT
#   sample at lambda1 is lambda1*d/N = 1.0 um on the retina; PSF drawn magnified by glare_scale = 1.5;
#   d = 20.32 mm pupil-retina distance -> 1 um = 1e-3/20.32 rad.
D_MM, GLARE_SCALE = 20.32, 1.5
DEG_PER_SCREEN_PX = np.degrees(1e-3 / D_MM) / GLARE_SCALE          # 1 um / d, divided by 1.5
PX_PER_DEG_NATIVE = 1.0 / DEG_PER_SCREEN_PX


def load_pfm_from_dump(path):
    d = json.loads(open(path, errors="replace").read(), strict=False)
    fb = d["framebuffer"]
    if "GL_COLOR_ATTACHMENT0" not in fb:
        return None
    raw = base64.b64decode(fb["GL_COLOR_ATTACHMENT0"]["__data__"])
    parts = raw.split(b"\n", 3)
    w, h = map(int, parts[1].split())
    a = np.frombuffer(parts[3], dtype="<f4").reshape(h, w, -1)[..., :3].astype(np.float64)
    return a[::-1]  # PFM rows are bottom-up


def radial_profile(img, cx, cy, rmax=256):
    y, x = np.indices(img.shape[:2])
    r = np.hypot(x - cx, y - cy).astype(int)
    out = []
    for c in range(img.shape[2]):
        s = np.bincount(r.ravel(), img[..., c].ravel(), minlength=rmax + 1)[: rmax + 1]
        n = np.bincount(r.ravel(), minlength=rmax + 1)[: rmax + 1]
        out.append(s / np.maximum(n, 1))
    return np.array(out).T  # (r, c)


def spectrum(x, dt):
    x = np.asarray(x, float) - np.mean(x)
    w = np.hanning(len(x))
    f = np.fft.rfftfreq(len(x), dt)
    p = np.abs(np.fft.rfft(x * w)) ** 2
    return f, p


def autocorr(x):
    x = np.asarray(x, float) - np.mean(x)
    c = np.correlate(x, x, "full")[len(x) - 1:]
    return c / c[0]


def main():
    res = {"label": "NATIVE", "px_per_deg_native_derived": PX_PER_DEG_NATIVE,
           "px_per_deg_note": "derived from glare.cpp constants (N=10 mm/512 px, d=20.32 mm, lambda1=N/d, glare_scale=1.5); the paper states no PSF angular scale"}

    # ---------------- A: hippus pupil series from the traced run ----------------
    rows = list(csv.DictReader(open(f"{RC}/trace_psf/frames.csv")))
    D = np.array([float(r["pupil_diameter_mm"]) for r in rows])
    t = np.arange(len(D)) * STEP_S
    f, p = spectrum(D, STEP_S)
    ac = autocorr(D)
    lag_1e = t[np.argmax(ac < 1 / np.e)] if np.any(ac < 1 / np.e) else None
    half = len(D) // 2
    fpk = f[1:][np.argmax(p[1:])]
    cum = np.cumsum(p[1:]) / np.sum(p[1:])
    f50 = f[1:][np.searchsorted(cum, 0.5)]
    f90 = f[1:][np.searchsorted(cum, 0.9)]
    res["hippus_trace"] = {
        "n_steps": len(D), "sim_duration_s": float(t[-1]),
        "initial_mean_pupil_mm_eq2": float(D[0]),
        "mean_mm": float(D.mean()), "std_mm": float(D.std()), "min_mm": float(D.min()), "max_mm": float(D.max()),
        "halves_mean_mm": [float(D[:half].mean()), float(D[half:].mean())],
        "halves_std_mm": [float(D[:half].std()), float(D[half:].std())],
        "autocorr_1_over_e_lag_s": None if lag_1e is None else float(lag_1e),
        "spectrum_peak_hz": float(fpk), "spectrum_median_hz": float(f50), "spectrum_90pct_hz": float(f90),
        "relative_pupil_area_pp": float((D.max() ** 2 - D.min() ** 2) / D.mean() ** 2),
    }
    fig, ax = plt.subplots(1, 3, figsize=(13, 3.4))
    ax[0].plot(t, D); ax[0].set_xlabel("simulated time [s]"); ax[0].set_ylabel("pupil diameter [mm]")
    ax[0].set_title("glare_demo hippus (traced)")
    ax[1].semilogy(f[1:], p[1:]); ax[1].set_xlim(0, 5); ax[1].set_xlabel("Hz"); ax[1].set_title("power spectrum")
    ax[2].plot(t[: len(t) // 2], ac[: len(t) // 2]); ax[2].axhline(1 / np.e, ls=":", c="k"); ax[2].set_xlabel("lag [s]")
    ax[2].set_title("autocorrelation")
    fig.tight_layout(); fig.savefig(f"{OUT}/NATIVE_hippus_trace_timeseries.png", dpi=90); plt.close(fig)

    # ---------------- D: author's Matlab hippus.m under Octave ----------------
    hc = f"{OUT}/NATIVE_hippus_curves.csv"
    if os.path.exists(hc):
        cur = {}
        for r in csv.DictReader(open(hc)):
            cur.setdefault(int(r["curve"]), []).append((float(r["t_s"]), float(r["pupil_mm"])))
        hm = []
        for k, v in sorted(cur.items()):
            tt, yy = np.array(v).T
            ff, pp = spectrum(yy, tt[1] - tt[0])
            c2 = np.cumsum(pp[1:]) / pp[1:].sum()
            hm.append({"curve": k, "mean_mm": float(yy.mean()), "std_mm": float(yy.std()),
                       "peak_to_peak_mm": float(yy.max() - yy.min()),
                       "spectrum_median_hz": float(ff[1:][np.searchsorted(c2, 0.5)])})
        res["hippus_matlab_octave"] = hm

    # ---------------- B: float PSF frames ----------------
    dumps = sorted(glob.glob(f"{RC}/trace_psf/dumps/f*.json"))
    psf_rows, frames = [], []
    for fn in dumps:
        k = int(re.findall(r"f(\d+)\.json", fn)[0])
        a = load_pfm_from_dump(fn)
        if a is None:
            continue  # glare-mode frames before the 'c' key: dump call is inside the convolution
        frames.append((k, a))
    res["psf_frames_used"] = [k for k, _ in frames]
    prof_all = []
    for k, a in frames:
        Y = a.sum(axis=2)  # demo RGB (Stockman-Sharpe based spectrum2rgb.h), channel sum as 'energy'
        yy, xx = np.indices(Y.shape)
        E = Y.sum()
        cx, cy = (xx * Y).sum() / E, (yy * Y).sum() / E
        pk = np.unravel_index(np.argmax(Y), Y.shape)
        prof = radial_profile(a, 256, 256)
        Yp = prof.sum(axis=1)
        r = np.arange(len(Yp))
        # lenticular-halo bump: largest local prominence Yp[r] / min(Yp[r-30:r]) for r in 100..240 px (~11-27 arcmin)
        prom = np.array([Yp[q] / Yp[q - 30:q].min() for q in range(100, 241)])
        ring_r = int(100 + np.argmax(prom))
        ring_prom = float(prom.max())
        core_hwhm = int(np.argmax(Yp < Yp[0] / 2))
        rr = np.hypot(xx - 256, yy - 256)
        ee = [float(Y[rr <= R].sum() / E) for R in (2, 5, 10, 50, 100, 200)]
        rb = prof[:, 0] / np.maximum(prof[:, 2], 1e-30)
        psf_rows.append({"frame": k, "t_s": k * STEP_S, "pupil_mm": float(D[k]),
                         "energy_sum": float(E), "energy_R": float(a[..., 0].sum()), "energy_G": float(a[..., 1].sum()),
                         "energy_B": float(a[..., 2].sum()), "peak": float(Y.max()), "peak_xy": [int(pk[1]), int(pk[0])],
                         "centroid_xy": [float(cx), float(cy)], "core_hwhm_px": core_hwhm, "ring_radius_px": ring_r,
                         "ring_radius_deg": ring_r / PX_PER_DEG_NATIVE,
                         "ring_to_core_ratio": float(Yp[ring_r] / Yp[0]), "ring_prominence": ring_prom,
                         "EE_r2_r5_r10_r50_r100_r200": ee,
                         "R_over_B_at_r0_r10_ring_r200": [float(rb[0]), float(rb[10]), float(rb[ring_r]), float(rb[200])]})
        prof_all.append(Yp)
    if psf_rows:
        Es = np.array([r["energy_sum"] for r in psf_rows]); Ds = np.array([r["pupil_mm"] for r in psf_rows])
        pks = np.array([r["peak"] for r in psf_rows])
        res["psf_summary"] = {
            "n_frames": len(psf_rows),
            "energy_rel_std": float(Es.std() / Es.mean()),
            "energy_rel_peak_to_peak": float((Es.max() - Es.min()) / Es.mean()),
            "corr_energy_vs_pupil_area": float(np.corrcoef(Es, Ds ** 2)[0, 1]),
            "fit_log_energy_vs_log_D_slope": float(np.polyfit(np.log(Ds), np.log(Es), 1)[0]),
            "peak_rel_peak_to_peak": float((pks.max() - pks.min()) / pks.mean()),
            "fit_log_peak_vs_log_D_slope": float(np.polyfit(np.log(Ds), np.log(pks), 1)[0]),
            "centroid_motion_px_max": float(np.max(np.hypot(*(np.array([r["centroid_xy"] for r in psf_rows]) - 256).T))),
            "ring_radius_px_range": [int(min(r["ring_radius_px"] for r in psf_rows)), int(max(r["ring_radius_px"] for r in psf_rows))],
            "ring_prominence_range": [float(min(r["ring_prominence"] for r in psf_rows)), float(max(r["ring_prominence"] for r in psf_rows))],
            "corr_ring_prominence_vs_pupil": float(np.corrcoef([r["ring_prominence"] for r in psf_rows], Ds)[0, 1]),
            "core_hwhm_px_range": [int(min(r["core_hwhm_px"] for r in psf_rows)), int(max(r["core_hwhm_px"] for r in psf_rows))],
            "note": "energy = sum of the demo's RGB PSF before its tone pass (fbo 1, RGB32F). In PSF view the demo divides by max_intensity=1; in glare view it additionally divides by pupil area (glare.cpp display()). The demo's PSF is the Fourier AMPLITUDE |F| (FFT.cpp display1_frag: gl_FragColor.r = length(ffts.rg)), not |F|^2 as in paper Eq. 3."}
        with open(f"{OUT}/NATIVE_psf_float_metrics.csv", "w") as fo:
            fo.write("frame,t_s,pupil_mm,energy_sum,energy_R,energy_G,energy_B,peak,centroid_x,centroid_y,core_hwhm_px,ring_radius_px,ring_to_core,EE_r10,EE_r50,EE_r100\n")
            for r in psf_rows:
                fo.write("%d,%.3f,%.5f,%.6g,%.6g,%.6g,%.6g,%.6g,%.3f,%.3f,%d,%d,%.4g,%.5f,%.5f,%.5f\n" % (
                    r["frame"], r["t_s"], r["pupil_mm"], r["energy_sum"], r["energy_R"], r["energy_G"], r["energy_B"],
                    r["peak"], r["centroid_xy"][0], r["centroid_xy"][1], r["core_hwhm_px"], r["ring_radius_px"],
                    r["ring_to_core_ratio"], r["EE_r2_r5_r10_r50_r100_r200"][2], r["EE_r2_r5_r10_r50_r100_r200"][3],
                    r["EE_r2_r5_r10_r50_r100_r200"][4]))
        # plots: energy/peak vs time & pupil; radial profiles
        tt = np.array([r["t_s"] for r in psf_rows])
        fig, ax = plt.subplots(1, 3, figsize=(13, 3.4))
        ax[0].plot(tt, Es / Es.mean(), "o-", label="PSF energy / mean")
        ax[0].plot(tt, pks / pks.mean(), "s-", label="PSF peak / mean")
        ax[0].plot(tt, Ds ** 2 / np.mean(Ds ** 2), "k:", label="pupil area / mean")
        ax[0].set_xlabel("simulated time [s]"); ax[0].legend(fontsize=7); ax[0].set_title("float PSF (NATIVE)")
        ax[1].loglog(Ds, Es, "o", label="energy"); ax[1].loglog(Ds, pks, "s", label="peak")
        ax[1].set_xlabel("pupil D [mm]"); ax[1].legend(fontsize=7); ax[1].set_title("vs pupil diameter")
        rdeg = np.arange(len(prof_all[0])) / PX_PER_DEG_NATIVE
        for Yp, r in zip(prof_all[:: max(1, len(prof_all) // 6)], psf_rows[:: max(1, len(prof_all) // 6)]):
            ax[2].semilogy(rdeg * 60, Yp, lw=0.8, label="D=%.2f" % r["pupil_mm"])
        ax[2].set_xlabel("radius [arcmin] (derived scale)"); ax[2].legend(fontsize=6); ax[2].set_title("radial profile (R+G+B)")
        fig.tight_layout(); fig.savefig(f"{OUT}/NATIVE_psf_float_energy_profile.png", dpi=90); plt.close(fig)
        # montage of float PSFs (log display, common scale)
        sel = frames[:: max(1, len(frames) // 8)][:8]
        vmax = max(a.max() for _, a in sel)
        tiles = []
        for k, a in sel:
            lg = np.clip((np.log10(np.maximum(a, 1e-12)) - np.log10(vmax) + 6) / 6, 0, 1)
            tiles.append((lg[::2, ::2] * 255).astype(np.uint8))
        m = np.concatenate([np.concatenate(tiles[:4], 1), np.concatenate(tiles[4:8], 1)], 0) if len(tiles) == 8 else np.concatenate(tiles, 1)
        buf = oiio.ImageBuf(oiio.ImageSpec(m.shape[1], m.shape[0], 3, oiio.UINT8)); buf.set_pixels(oiio.ROI(), m)
        buf.write(f"{OUT}/NATIVE_psf_float_montage_log6decades.png")
        np.save(f"{RC}/psf_float_stack.npy", np.stack([a for _, a in frames]).astype(np.float32))
        np.save(f"{RC}/psf_float_frames.npy", np.array([k for k, _ in frames]))

    # ---------------- C: 8-bit display grabs ----------------
    for mode in ("psf", "glare"):
        pngs = sorted(glob.glob(f"{RC}/native_{mode}/png/*.png"))
        if not pngs:
            continue
        ts = np.array([float(l.split()[1]) for l in open(f"{RC}/native_{mode}/timestamps.txt")])[: len(pngs)]
        fps = [float(l.split()[1]) for l in open(f"{RC}/native_{mode}/glare_demo_stdout.txt") if l.startswith("fps:")]
        stats, prev, nuniq = [], None, 0
        for i, fn in enumerate(pngs):
            b = oiio.ImageBuf(fn)
            a = b.get_pixels(oiio.UINT8)[:512, :512, :3].astype(np.float64)
            if prev is None or np.any(a != prev):
                nuniq += 1
            prev = a
            lin = (a / 255.0) ** (1 / 0.4545)  # the demo's own display encoding: pow(x, 0.4545)
            Y = lin @ np.array([0.2126, 0.7152, 0.0722])
            yy, xx = np.indices(Y.shape)
            E = Y.sum()
            stats.append((ts[i] - ts[0], E, (xx * Y).sum() / E, (yy * Y).sum() / E, float((a >= 255).any(axis=2).mean()),
                          float(Y[:64, :64].mean()), float(Y[240:272, 240:272].mean())))
        s = np.array(stats)
        spec = oiio.ImageBuf(pngs[0]).spec()
        res[f"capture_{mode}"] = {"n_grabs": len(pngs), "n_distinct_consecutive": nuniq, "resolution": [spec.width, spec.height],
                                  "format": str(spec.format), "wall_duration_s": float(s[-1, 0]),
                                  "demo_fps_median": float(np.median(fps)) if fps else None,
                                  "sim_time_estimate_s": float(np.sum(fps) * STEP_S) if fps else None,
                                  "display_energy_rel_std": float(s[:, 1].std() / s[:, 1].mean()),
                                  "display_energy_rel_p2p": float((s[:, 1].max() - s[:, 1].min()) / s[:, 1].mean()),
                                  "centroid_motion_px_std": [float(s[:, 2].std()), float(s[:, 3].std())],
                                  "clipped_pixel_fraction_mean": float(s[:, 4].mean()),
                                  "corner_veil_rel_std": float(s[:, 5].std() / max(s[:, 5].mean(), 1e-12)),
                                  "centre_rel_std": float(s[:, 6].std() / max(s[:, 6].mean(), 1e-12))}
        fig, ax = plt.subplots(figsize=(7, 3))
        ax.plot(s[:, 0], s[:, 1] / s[:, 1].mean(), lw=0.7, label="display energy (linearised)")
        ax.plot(s[:, 0], s[:, 5] / s[:, 5].mean(), lw=0.7, label="corner 64x64 (veil)")
        ax.set_xlabel("wall time [s] (llvmpipe; ~%.1f demo fps, 20 ms sim per frame)" % (np.median(fps) if fps else 0))
        ax.legend(fontsize=7); ax.set_title(f"NATIVE 8-bit capture, {mode} view")
        fig.tight_layout(); fig.savefig(f"{OUT}/NATIVE_capture_{mode}_timeseries.png", dpi=90); plt.close(fig)
        # short MP4 (first 300 grabs), each grab shown for 1/10 s
        subprocess.run(["bash", "-c", f"export PATH=/nix/var/nix/profiles/default/bin:$PATH; cd {REPO}; nix shell --inputs-from . nixpkgs#ffmpeg-headless -c ffmpeg -loglevel error -y -framerate 10 -start_number 0 -i {RC}/native_{mode}/png/%05d.png -frames:v 300 -vf scale=384:384 -c:v libx264 -pix_fmt yuv420p -crf 26 {OUT}/NATIVE_capture_{mode}.mp4"], check=False)

    json.dump(res, open(f"{OUT}/NATIVE_metrics.json", "w"), indent=1)
    print(json.dumps(res, indent=1)[:6000])


if __name__ == "__main__":
    main()
