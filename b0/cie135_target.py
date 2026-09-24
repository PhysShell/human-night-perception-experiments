#!/usr/bin/env python3
"""B0 v3 erratum check: the CIE 135/1 straylight target done in 2-D.
HDR-VDP 3.0.7's hdrvdp_otf_cie99 turned out to be the 1-D Fourier transform of the CIE glare spread function
used as a 2-D OTF (b0/cie_otf_check.py), which under-weights the wide terms. Here the published GSF itself
(CIE 135/1, Vos & van den Berg 1999, age 24, p 0.5; b0/retinal_profiles.py cie_gsf, sr^-1, unit integral)
is convolved with the achromatic components directly in space:
  kernel[pixel] = integral of the GSF over the pixel (8x8 sub-samples everywhere, 64x64 in the central 7x7
  pixels where the 0.28' core term lives), extent = the full stimulus field (energy beyond it is lost, not
  renormalised); edge padding as the other donors ('replicate').
Retinal target P_det: HDR-VDP-3 side-by-side, evaluator optics OFF, at x0.1/x1/x10/x100, as the sweep's
RETINAL_TARGET. Our code (ADAPTED: a published closed-form GSF, no donor implementation of it in 2-D here).
  nix develop -c python3 b0/cie135_target.py -> b0/results/cie135_target.json
"""
import json, math, os, subprocess
import numpy as np
import OpenImageIO as oiio
from scipy.signal import fftconvolve

src = open("b0/retinal_profiles.py").read()
ns = {}; exec(src[src.index("def cie_gsf"):src.index("tot = ")], {"np": np}, ns); cie_gsf = ns["cie_gsf"]
S, O = "b0/out/stim_ach", "b0/out/cie135"; os.makedirs(O, exist_ok=True)
meta = json.load(open(f"{S}/meta.json")); PPD = meta["px_per_deg"]; W, H = meta["size_px"]
OM_DEG2_TO_SR = math.radians(1) ** 2
ld = lambda p: oiio.ImageBuf(p).get_pixels(oiio.FLOAT)[..., :3].astype(np.float64)


def save(p, a):
    b = oiio.ImageBuf(oiio.ImageSpec(a.shape[1], a.shape[0], 3, oiio.FLOAT))
    b.set_pixels(oiio.ROI(0, a.shape[1], 0, a.shape[0], 0, 1, 0, 3), np.ascontiguousarray(a, np.float32)); b.write(p)


def pixel_integrated(hy, hx, n):
    """GSF integrated over pixels (dy, dx) in [-hy, hy] x [-hx, hx] with n x n sub-samples each."""
    o = (np.arange(n) + 0.5) / n - 0.5
    ys, xs = np.arange(-hy, hy + 1), np.arange(-hx, hx + 1)
    k = np.zeros((len(ys), len(xs)))
    for a in o:
        for b in o:
            k += cie_gsf(np.hypot(ys[:, None] + a, xs[None, :] + b) / PPD)
    return k / n ** 2 * OM_DEG2_TO_SR / PPD ** 2


hy, hx = H, W
K = pixel_integrated(hy, hx, 8)
K[hy - 3:hy + 4, hx - 3:hx + 4] = pixel_integrated(3, 3, 64)
res = {"kernel_sum_over_field": float(K.sum()), "kernel_centre_pixel": float(K[hy, hx])}
R = {}
for c in ("C_sky_nobar", "C_sky_bar", "C_src1"):
    img = ld(f"{S}/{c}.exr")
    pad = np.pad(img, ((hy, hy), (hx, hx), (0, 0)), mode="edge")
    R[c] = np.stack([fftconvolve(pad[..., i], K, mode="valid") for i in range(3)], -1)
    save(f"{O}/CIE135_{c}.exr", R[c])
tot = ld(f"{S}/C_src1.exr").sum()
sx, sy = meta["source_px"]
r = np.hypot(*np.mgrid[0:H, 0:W] - np.array([sy, sx])[:, None, None]) / PPD * 60
Ysrc = (R["C_src1"].sum(-1) / 3) / (tot / 3)
res["PSF_sr^-1_at_arcmin"] = {a: float(Ysrc[(r > a - 0.5) & (r < a + 0.5)].mean() / (OM_DEG2_TO_SR / PPD ** 2)) for a in (3, 10, 18, 30, 60)}
res["analytic_sr^-1_at_arcmin"] = {a: float(cie_gsf(a / 60)) for a in (3, 10, 18, 30, 60)}
K31 = np.geomspace(0.1, 100, 31); rows = {}
for i in (0, 10, 20, 30):
    k = K31[i]; tag = f"{O}/i{i:02d}"
    for b in ("bar", "nobar"):
        save(f"{tag}_{b}.exr", R[f"C_sky_{b}"] + k * R["C_src1"])
    if not os.path.exists(f"{tag}_RETINAL/run.json"):
        subprocess.run(f"tracks/hdrvdp3/run_hdrvdp.sh {tag}_bar.exr {tag}_nobar.exr PHONE {tag}_RETINAL --display none "
                       f"--mtf none --tasks side-by-side", shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    t = open(f"{tag}_RETINAL/run.json").read()
    rows[f"x{k:.3g}"] = float(t.split('"side-by-side":{"P_det":')[1].split(",")[0])
res["P_det_trunk_RETINAL_TARGET"] = rows
json.dump(res, open("b0/results/cie135_target.json", "w"), indent=1)
print(json.dumps(res, indent=1))
