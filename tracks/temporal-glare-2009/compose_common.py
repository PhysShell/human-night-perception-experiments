#!/usr/bin/env python3
"""COMMON (ADAPTED) billboard of the NATIVE glare_demo PSF sequence onto stimuli S0 / S1.

No glare model is evaluated here: the PSF frames are the author demo's own float output (extracted from the
unmodified program with apitrace, see trace_glare_demo_psf.sh / dump_psf_floats.sh). This script only
re-samples, normalises and composites them (wrapper / format conversion), then writes display-referred
previews WITHOUT pcond. Every mapping choice is ADAPTED and listed in MAPPING below and in the README.

Run: tracks/temporal-glare-2009/py.sh tracks/temporal-glare-2009/compose_common.py
"""
import csv, json, os, subprocess
import numpy as np
from scipy.signal import fftconvolve
from scipy.ndimage import zoom
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import OpenImageIO as oiio

REPO = "/home/user/human-night-perception-experiments"
RC = f"{REPO}/research-cache/temporal-glare-2009"
OUT = f"{REPO}/results/common/temporal-glare-2009"
os.makedirs(OUT, exist_ok=True)
STEP_S = 0.020
D_MM, GLARE_SCALE = 20.32, 1.5
PX_PER_DEG_PSF = 1.0 / (np.degrees(1e-3 / D_MM) / GLARE_SCALE)   # ~532 px/deg, derived from glare.cpp constants
targets = json.load(open(f"{REPO}/stimuli/display_targets.json"))
PHONE = targets["PHONE_TARGET"]
MAPPING = {
    "label": "ADAPTED",
    "psf_source": "glare_demo float PSF (fbo 1 RGB32F, before the demo's tone pass), PSF view, frames listed in psf_frames",
    "psf_angular_scale": f"{PX_PER_DEG_PSF:.1f} px/deg, DERIVED from glare.cpp constants (N=10 mm/512 px, d=20.32 mm, lambda1=N/d -> 1 um per FFT px, glare_scale 1.5); paper states none",
    "psf_centre": "(256,256) = FFT DC after the demo's size/2 shift",
    "resampling_to_stimulus": "flux-conserving area rebin from PSF px to 32 px/deg (stimulus pack)",
    "normalisation": "each PSF frame and colour channel normalised to unit sum (energy-conserving billboard; source colour preserved; the demo's own per-frame energy change is NOT applied, it is reported separately in results/native)",
    "demo_rgb": "demo RGB is Stockman-Sharpe-based spectrum2rgb.h, used only as relative per-channel spatial distribution",
    "billboard": "source-only component (stimulus minus median sky) convolved with the kernel, sky kept; equivalent to a per-light billboard for an isolated point",
    "display": f"PHONE_TARGET from stimuli/display_targets.json: {PHONE['px_per_deg_centre']} px/deg, peak {PHONE['peak_cd_m2']} cd/m^2; value = clip(Y_scene/peak,0,1) per channel (absolute, NO pcond, no tone curve, black floor ignored), sRGB OETF; 32->73 px/deg by bilinear (luminance-preserving) resampling",
    "time_base": "simulated time = demo frame index x 20 ms (glare.cpp sim_timer)",
}


def rebin_kernel(psf, s_native_per_target, half=17):
    """Area-integrate psf (H,W,3) onto a (2*half+1)^2 grid centred at (256,256)."""
    H, W, C = psf.shape
    cs = np.zeros((H + 1, W + 1, C))
    cs[1:, 1:] = psf.cumsum(0).cumsum(1)
    edges = 256.0 + (np.arange(2 * half + 2) - (half + 0.5)) * s_native_per_target  # native pixel-edge coords
    edges = np.clip(edges, 0, W)

    def I(yv, xv):  # bilinear interpolation of the integral image at fractional edge coordinates
        y0 = np.clip(np.floor(yv).astype(int), 0, H - 1); x0 = np.clip(np.floor(xv).astype(int), 0, W - 1)
        fy = (yv - y0)[:, None, None]; fx = (xv - x0)[None, :, None]
        a = cs[y0][:, x0]; b = cs[y0][:, x0 + 1]; c = cs[y0 + 1][:, x0]; d = cs[y0 + 1][:, x0 + 1]
        return a * (1 - fy) * (1 - fx) + b * (1 - fy) * fx + c * fy * (1 - fx) + d * fy * fx

    J = I(edges, edges)
    k = J[1:, 1:] - J[:-1, 1:] - J[1:, :-1] + J[:-1, :-1]
    return np.maximum(k, 0)


def srgb(x):
    x = np.clip(x, 0, 1)
    return np.where(x <= 0.0031308, 12.92 * x, 1.055 * x ** (1 / 2.4) - 0.055)


def write_png(path, rgb01):
    a = (srgb(rgb01) * 255 + 0.5).astype(np.uint8)
    b = oiio.ImageBuf(oiio.ImageSpec(a.shape[1], a.shape[0], 3, oiio.UINT8)); b.set_pixels(oiio.ROI(), a); b.write(path)


def main():
    stack = np.load(f"{RC}/psf_float_stack.npy").astype(np.float64)
    fr = np.load(f"{RC}/psf_float_frames.npy")
    t = fr * STEP_S
    s_nat = PX_PER_DEG_PSF / 32.0
    kernels = []
    for a in stack:
        k = rebin_kernel(a, s_nat)
        k /= k.sum(axis=(0, 1), keepdims=True)
        kernels.append(k)
    kernels = np.array(kernels)
    kc = kernels.shape[1] // 2
    summary = {"mapping": MAPPING, "psf_frames": fr.tolist(), "kernel_px_at_32ppd": kernels.shape[1],
               "kernel_energy_in_centre_px_mean": float(kernels[:, kc, kc, :].sum(-1).mean() / 3),
               "kernel_energy_in_centre_px_range": [float(kernels[:, kc, kc, :].mean(-1).min()), float(kernels[:, kc, kc, :].mean(-1).max())],
               "stimuli": {}}
    ppd_out = PHONE["px_per_deg_centre"]
    for sid in ("S0", "S1"):
        meta = json.load(open(f"{REPO}/stimuli/pack/{sid}/meta.json"))
        img = oiio.ImageBuf(f"{REPO}/stimuli/pack/{sid}/{sid}.exr").get_pixels(oiio.FLOAT).astype(np.float64)[..., :3]
        sx, sy = [int(v) for v in meta["source_px"]]
        sky = np.median(img.reshape(-1, 3), axis=0)
        src = np.zeros_like(img)
        win = (slice(sy - 4, sy + 5), slice(sx - 4, sx + 5))
        src[win] = np.maximum(img[win] - sky, 0)
        base = img - src
        wY = np.array([0.2126, 0.7152, 0.0722])
        E_src = (src @ wY).sum()
        # crop for display: 4 x 2 deg around the source at 32 px/deg, then to phone px/deg
        cw, ch = 64, 32
        crop = (slice(sy - ch, sy + ch), slice(sx - cw, sx + cw))
        rows, frames_png = [], []
        fdir = f"{RC}/common_frames_{sid}"
        os.makedirs(fdir, exist_ok=True)
        ref = zoom(img[crop], (ppd_out / 32, ppd_out / 32, 1), order=1)
        write_png(f"{OUT}/ADAPTED_{sid}_noglare_phone.png", ref / PHONE["peak_cd_m2"])
        for i, k in enumerate(kernels):
            out = base + np.stack([fftconvolve(src[..., c], k[..., c], mode="same") for c in range(3)], -1)
            Y = out @ wY
            yy, xx = np.indices(Y.shape)
            rr = np.hypot(xx - sx, yy - sy) / 32.0  # deg
            ring = (rr > 0.28) & (rr < 0.38)
            rows.append({"t_s": float(t[i]), "frame": int(fr[i]),
                         "Y_peak_cd_m2": float(Y[sy, sx]),
                         "Y_mean_r_lt_0.1deg": float(Y[rr < 0.1].mean()),
                         "Y_mean_ring_0.28_0.38deg": float(Y[ring].mean()),
                         "E_within_0.05deg_frac": float(((out - base) @ wY)[rr <= 0.05].sum() / E_src),
                         "E_total_frac": float(((out - base) @ wY).sum() / E_src),
                         "phone_clipped_px": int((out[crop] > PHONE["peak_cd_m2"]).any(-1).sum())})
            disp = zoom(out[crop], (ppd_out / 32, ppd_out / 32, 1), order=1) / PHONE["peak_cd_m2"]
            p = f"{fdir}/{i:04d}.png"; write_png(p, disp); frames_png.append(p)
        with open(f"{OUT}/ADAPTED_{sid}_luminance_over_time.csv", "w") as fo:
            w = csv.DictWriter(fo, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
        R = {k: np.array([r[k] for r in rows]) for k in rows[0]}
        Y0 = img[sy, sx] @ wY
        summary["stimuli"][sid] = {
            "source_px": [sx, sy], "sky_rgb": sky.tolist(), "Y_peak_without_glare_cd_m2": float(Y0),
            "Y_peak_with_billboard_range": [float(R["Y_peak_cd_m2"].min()), float(R["Y_peak_cd_m2"].max())],
            "Y_peak_rel_p2p": float(np.ptp(R["Y_peak_cd_m2"]) / R["Y_peak_cd_m2"].mean()),
            "ring_rel_p2p": float(np.ptp(R["Y_mean_ring_0.28_0.38deg"]) / R["Y_mean_ring_0.28_0.38deg"].mean()),
            "ring_mean_cd_m2": float(R["Y_mean_ring_0.28_0.38deg"].mean()),
            "E_total_frac_range": [float(R["E_total_frac"].min()), float(R["E_total_frac"].max())],
            "phone_clipped_px_range": [int(R["phone_clipped_px"].min()), int(R["phone_clipped_px"].max())]}
        # plot
        fig, ax = plt.subplots(1, 2, figsize=(11, 3.3))
        ax[0].plot(R["t_s"], R["Y_peak_cd_m2"], "o-", ms=3, label="source pixel")
        ax[0].axhline(Y0, c="k", ls=":", label="source pixel, no billboard")
        ax[0].axhline(PHONE["peak_cd_m2"], c="r", ls="--", label="PHONE peak")
        ax[0].set_yscale("log"); ax[0].set_xlabel("simulated time [s]"); ax[0].set_ylabel("cd/m^2"); ax[0].legend(fontsize=7)
        ax[0].set_title(f"{sid} ADAPTED billboard: peak")
        ax[1].plot(R["t_s"], R["Y_mean_ring_0.28_0.38deg"], "o-", ms=3, label="ring 0.28-0.38 deg (lenticular bump)")
        ax[1].plot(R["t_s"], R["Y_mean_r_lt_0.1deg"], "s-", ms=3, label="mean r<0.1 deg")
        ax[1].set_yscale("log"); ax[1].set_xlabel("simulated time [s]"); ax[1].legend(fontsize=7); ax[1].set_title("halo luminance")
        fig.tight_layout(); fig.savefig(f"{OUT}/ADAPTED_{sid}_luminance_over_time.png", dpi=90); plt.close(fig)
        # montage of 8 frames (+ reference), 2x upscale nearest for visibility
        sel = frames_png[:: max(1, len(frames_png) // 8)][:8]
        tiles = [oiio.ImageBuf(f"{OUT}/ADAPTED_{sid}_noglare_phone.png").get_pixels(oiio.UINT8)] + [oiio.ImageBuf(p).get_pixels(oiio.UINT8) for p in sel]
        tiles = tiles + [np.zeros_like(tiles[0])] * (9 - len(tiles))
        m = np.concatenate([np.concatenate(tiles[i * 3:(i + 1) * 3], 1) for i in range(3)], 0)
        b = oiio.ImageBuf(oiio.ImageSpec(m.shape[1], m.shape[0], 3, oiio.UINT8)); b.set_pixels(oiio.ROI(), np.ascontiguousarray(m))
        b.write(f"{OUT}/ADAPTED_{sid}_montage_phone.png")
        # MP4: each PSF frame held for its simulated duration (frames are ~0.26 s apart), 25 fps, 2x nearest upscale
        dts = np.diff(np.append(t, t[-1] + np.median(np.diff(t))))
        lst = f"{fdir}/concat.txt"
        with open(lst, "w") as fo:
            for p, d in zip(frames_png, dts):
                fo.write(f"file '{p}'\nduration {d:.3f}\n")
            fo.write(f"file '{frames_png[-1]}'\n")
        subprocess.run(["bash", "-c", f"export PATH=/nix/var/nix/profiles/default/bin:$PATH; cd {REPO}; nix shell --inputs-from . nixpkgs#ffmpeg-headless -c ffmpeg -loglevel error -y -f concat -safe 0 -i {lst} -vf 'scale=iw*2:ih*2:flags=neighbor,fps=25,pad=ceil(iw/2)*2:ceil(ih/2)*2' -c:v libx264 -pix_fmt yuv420p -crf 20 {OUT}/ADAPTED_{sid}_billboard_phone.mp4"], check=False)
    json.dump(summary, open(f"{OUT}/ADAPTED_summary.json", "w"), indent=1)
    print(json.dumps(summary, indent=1)[:4000])


if __name__ == "__main__":
    main()
