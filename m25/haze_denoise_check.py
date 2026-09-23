#!/usr/bin/env python3
"""M2.5: is Cycles' OIDN on the haze pass unbiased enough, and does it remove the noise?

Frame 1 of a clip (camera at x = 0) against the same haze pass at 512 spp (no denoiser):
  * lamp-lit ribbon band (rows holding the lamps, +-8 px): energy per 20-column bin and in
    total (a denoiser that blurs or eats the small lit pools under distant lamps shows here);
  * per-pixel relative RMS error in the band where the reference is above 1 % of its max;
  * the rest of the image: median ratio.
  python3 m25/haze_denoise_check.py REF512.exr LAMPS.exr CANDIDATE.exr [CANDIDATE2.exr ...]
"""
import sys
import numpy as np
import OpenImageIO as oiio

Yw = np.array([0.2126, 0.7152, 0.0722])
load = lambda p: oiio.ImageBuf(p).get_pixels(oiio.FLOAT)[..., :3] @ Yw
ref, lamps = load(sys.argv[1]), load(sys.argv[2])
rows = np.flatnonzero((lamps > 0).any(1))
band = slice(rows.min() - 8, rows.max() + 9)
R = ref[band]
rest = np.ones(ref.shape[0], bool); rest[band] = False
print(f"reference {sys.argv[1]}, band rows {band.start}-{band.stop}")
for p in sys.argv[3:]:
    C = load(p)
    Cb = C[band]
    bins = [Cb[:, k:k + 20].sum() / R[:, k:k + 20].sum() for k in range(0, R.shape[1] - 19, 20)]
    m = R > 0.01 * R.max()
    rms = np.sqrt(np.mean((Cb[m] / R[m] - 1) ** 2))
    print(f"{p}\n  band energy {Cb.sum() / R.sum():.4f}; bins min {min(bins):.3f} max {max(bins):.3f}; "
          f"per-pixel rel. RMS (ref > 1 % max) {rms:.3f}; rest median ratio "
          f"{np.median(C[rest] / np.maximum(ref[rest], 1e-12)):.4f}")
