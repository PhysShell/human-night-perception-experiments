#!/usr/bin/env python3
"""B0 numerical convergence records.
ISET point image at scene sampling 2x/4x/8x of 73 px/deg: encircled-energy radii (50/80/95 %) and FWHM
in arcmin, on the fine grid (continuous-angle quantities) and after area-binning to 73 px/deg.
CIE99 OTF on a 2x vs 4x grid (b0/hdrvdp_optics.m B0_SS): max and energy-weighted relative difference
of the retinal lamp image (k=1, no bar)."""
import json, glob
import numpy as np
import OpenImageIO as oiio

res = {}
for ss in (2, 4, 8):
    with open(f"b0/out/conv/iset_kernel_ss{ss}.raw", "rb") as f:
        h, w, c, t = np.fromfile(f, "<i4", 4); E = np.fromfile(f, "<f4").reshape(h, w, c)[..., 0].astype(float)
    E = np.maximum(E - np.median(E[:5, :5]), 0)
    cy, cx = np.unravel_index(E.argmax(), E.shape)
    ppd = 73 * ss
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.hypot(yy - cy, xx - cx) / ppd * 60
    o = np.argsort(r.ravel()); ee = np.cumsum(E.ravel()[o]) / E.sum(); rs = r.ravel()[o]
    rad = {p: float(rs[np.searchsorted(ee, p / 100)]) for p in (50, 80, 95)}
    fwhm = float(2 * np.sqrt((E >= 0.5 * E.max()).sum() / np.pi) / ppd * 60)
    res[f"iset_ss{ss}"] = {"EE_radius_arcmin": rad, "FWHM_equiv_arcmin": fwhm, "field_deg": w / ppd}
import subprocess
res["iset_note"] = "EE radii within the 2.5 deg ISET field (energy beyond it is not in the kernel)"
# CIE99 2x vs 4x (retinal images from the earlier test in /tmp are not kept; recompute here)
out = {}
for ss in (2, 4):
    subprocess.run(f"python3 tracks/hdrvdp3/img2raw.py b0/out/stim/B0_k1_nobar.exr b0/out/conv/k1n.raw && "
                   f"REPO=$PWD B0_IN=b0/out/conv/k1n.raw B0_OUT_PREFIX=b0/out/conv/cie_ss{ss} B0_MTF=cie B0_PPD=73 B0_SS={ss} "
                   f"tracks/hdrvdp3/octave.sh b0/hdrvdp_optics.m >/dev/null && python3 b0/raw2exr.py b0/out/conv/cie_ss{ss}_retinal.raw b0/out/conv/cie_ss{ss}.exr",
                   shell=True, check=True)
    out[ss] = oiio.ImageBuf(f"b0/out/conv/cie_ss{ss}.exr").get_pixels(oiio.FLOAT)[..., :3].astype(float) @ [0.2126, 0.7152, 0.0722]
d = np.abs(out[2] - out[4]); m = out[4] > 1e-3
res["cie99_2x_vs_4x"] = {"max_rel_diff_where_L>1e-3": float((d[m] / out[4][m]).max()),
                         "energy_weighted_rel_diff": float(d.sum() / out[4].sum()),
                         "peak_rel_diff": float(abs(out[2].max() - out[4].max()) / out[4].max())}
json.dump(res, open("b0/results/convergence.json", "w"), indent=1)
print(json.dumps(res, indent=1))
