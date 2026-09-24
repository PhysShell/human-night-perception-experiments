#!/usr/bin/env python3
"""B0: apply an existing donor PSF (no PSF model is computed here) to a B0 stimulus by FFT
convolution of each channel (edge-replicated padding), energy-preserving (kernels normalised to
unit sum, per channel for the temporal-glare frames).

  iset     : the ISETBio 'wvf human' point image from b0/iset_kernel.m (73 px/deg, same grid)
  temporal : (TAPER=1: circular cosine taper of the kernel over 0.4-0.5 deg, energy renormalised;
             ADAPTED, used for the blind set so the demo's square FFT window cannot identify it)
             the Temporal Glare co-author demo's float PSF frames (research-cache, 33 frames at
             demo times 0.8-9.6 s, ~532 px/deg), area-rebinned to 73 px/deg with the track's own
             rebin_kernel (+-0.5 deg window = the demo's PSF window), then LINEARLY INTERPOLATED in
             time to 24 fps (ADAPTED: the dump is ~3.7 frames/s; hippus is < 0.6 Hz)
  python3 b0/apply_kernels.py iset IN.exr OUT.exr
  python3 b0/apply_kernels.py temporal IN.exr OUTPREFIX NFRAMES
"""
import importlib.util, json, sys
import numpy as np
import OpenImageIO as oiio

REPO = "/home/user/human-night-perception-experiments"
load = lambda p: oiio.ImageBuf(p).get_pixels(oiio.FLOAT)[..., :3].astype(np.float64)


def save(p, a):
    b = oiio.ImageBuf(oiio.ImageSpec(a.shape[1], a.shape[0], 3, oiio.FLOAT))
    b.set_pixels(oiio.ROI(0, a.shape[1], 0, a.shape[0], 0, 1, 0, 3), np.ascontiguousarray(a, np.float32)); b.write(p)


def conv(img, k):
    """img (H,W,3) * k (h,w,3 or h,w), same grid, kernel centre at its middle pixel."""
    H, W, _ = img.shape
    h, w = k.shape[:2]
    py, px = h // 2 + 1, w // 2 + 1
    pad = np.pad(img, ((py, py), (px, px), (0, 0)), mode="edge")
    Hp, Wp = pad.shape[:2]
    out = np.empty_like(img)
    for c in range(3):
        kc = k[..., c] if k.ndim == 3 else k
        K = np.zeros((Hp, Wp)); K[:h, :w] = kc
        K = np.roll(K, (-(h // 2), -(w // 2)), (0, 1))
        out[..., c] = np.real(np.fft.ifft2(np.fft.fft2(pad[..., c]) * np.fft.fft2(K)))[py:py + H, px:px + W]
    return out


mode = sys.argv[1]
img = load(sys.argv[2])
if mode == "iset":
    with open(f"{REPO}/b0/out/optics/iset_kernel.raw", "rb") as f:
        h, w, c, t = np.fromfile(f, "<i4", 4)
        E = np.fromfile(f, "<f4").reshape(h, w, c)[..., 0].astype(np.float64)
    ss = json.load(open(f"{REPO}/b0/out/optics/iset_kernel.json")).get("supersample", 1)
    E = E - np.median(E[:5, :5]); E = np.maximum(E, 0)          # the scene's 1e-9 floor
    cy, cx = np.unravel_index(E.argmax(), E.shape)
    # area-bin ss x ss around the peak onto the 73 px/deg grid (the point sits at a fine-pixel centre)
    r = (min(cy, cx, h - 1 - cy, w - 1 - cx) - ss // 2) // ss
    y0, x0 = cy - ss // 2 - r * ss, cx - ss // 2 - r * ss
    k = E[y0:y0 + (2 * r + 1) * ss, x0:x0 + (2 * r + 1) * ss].reshape(2 * r + 1, ss, 2 * r + 1, ss).sum((1, 3))
    k /= k.sum()
    out = conv(img, k)
    save(sys.argv[3], out)
    print(json.dumps({"iset_kernel_px": k.shape, "centre_px_share": float(k[r, r]), "3x3_share": float(k[r - 1:r + 2, r - 1:r + 2].sum()),
                      "energy_in_out": [float(img.sum()), float(out.sum())]}))
elif mode == "temporal":
    spec = importlib.util.spec_from_file_location("cc", f"{REPO}/tracks/temporal-glare-2009/compose_common.py")
    cc = importlib.util.module_from_spec(spec); spec.loader.exec_module(cc)
    stack = np.load(f"{REPO}/research-cache/temporal-glare-2009/psf_float_stack.npy").astype(np.float64)
    tfr = np.load(f"{REPO}/research-cache/temporal-glare-2009/psf_float_frames.npy") * cc.STEP_S
    ks = []
    import os
    rr = np.hypot(*np.mgrid[-36:37, -36:37]) / 73.0
    taper = np.clip(np.cos(np.clip((rr - 0.4) / 0.1, 0, 1) * np.pi / 2), 0, 1) ** 2 if os.environ.get("TAPER") == "1" else np.ones_like(rr)
    for a in stack:
        k = cc.rebin_kernel(a, cc.PX_PER_DEG_PSF / 73.0, half=36) * taper[..., None]
        ks.append(k / k.sum(axis=(0, 1), keepdims=True))
    ks = np.array(ks)
    n = int(sys.argv[4])
    times = tfr[0] + np.arange(n) / 24.0
    log = []
    for i, tt in enumerate(times):
        j = np.clip(np.searchsorted(tfr, tt) - 1, 0, len(tfr) - 2)
        f = np.clip((tt - tfr[j]) / (tfr[j + 1] - tfr[j]), 0, 1)
        k = (1 - f) * ks[j] + f * ks[j + 1]
        save(f"{sys.argv[3]}_{i + 1:04d}.exr", conv(img, k))
        log.append({"frame": i + 1, "demo_time_s": float(tt), "kernel_centre_share": float(k[36, 36].mean())})
    json.dump({"frames": log, "psf_px_per_deg": cc.PX_PER_DEG_PSF, "demo_times_s": tfr.tolist()}, open(f"{sys.argv[3]}_frames.json", "w"), indent=1)
    print(f"temporal: {n} frames from demo t={times[0]:.2f}-{times[-1]:.2f} s")
