#!/usr/bin/env python3
"""B0 v3: are two retinal targets with a similar trunk P_det the same retinal image?
The lamp component (C_src1, achromatic layer, 73 px/deg) after each retinal model, expressed as a PSF in ONE
normalisation for all models:
  PSF(r) [sr^-1] = (retinal luminance in the annulus around r / total source luminance) / pixel solid angle,
i.e. the fraction of the source's energy per steradian, the convention of the ocular-straylight literature
(CIE 135/1; Arias, Ginis & Artal 2018 normalise to unit solid angle). The v3 draft divided each profile by
its own peak; that mixed the core into the wing comparison and is replaced here.
Checks recorded: integral of PSF over the 12 x 6 deg field (sum of fractions; < 1 where the field or the donor
kernel cuts the wings), and the CIE99 retinal image against the analytic CIE 135/1 glare spread function
(age 24, pigmentation 0.5, the constants of HDR-VDP's hdrvdp_otf_cie99.m, normalised by its own integral
factor 1 + p (0.0417 + 0.055 (A/70)^4)). ISET's kernel field is +-1.24 deg, so its wings stop there.
  python3 b0/retinal_profiles.py -> b0/results/retinal_profiles.json
"""
import json, math
import numpy as np
import OpenImageIO as oiio

meta = json.load(open("b0/out/stim_ach/meta.json")); sx, sy = meta["source_px"]
PPD = meta["px_per_deg"]; OMEGA = math.radians(1 / PPD) ** 2           # sr per pixel
Yw = np.array([0.2126, 0.7152, 0.0722])
ld = lambda p: oiio.ImageBuf(p).get_pixels(oiio.FLOAT)[..., :3].astype(float) @ Yw


def cie_gsf(theta_deg, age=24.0, p=0.5):
    """CIE 135/1 (Vos & van den Berg 1999) glare spread function, sr^-1, unit integral."""
    t, a4 = np.asarray(theta_deg, float), (age / 70.0) ** 4
    g = ((1 - 0.08 * a4) * (9.2e6 / (1 + (t / 0.0046) ** 2) ** 1.5 + 1.5e5 / (1 + (t / 0.045) ** 2) ** 1.5)
         + (1 + 1.6 * a4) * ((400 / (1 + (t / 0.1) ** 2) + 3e-8 * t ** 2)
                             + p * (1300 / (1 + (t / 0.1) ** 2) ** 1.5 + 0.8 / (1 + (t / 0.1) ** 2) ** 0.5))
         + 2.5e-3 * p)
    return g / (1 + p * (0.0417 + 0.055 * a4))


tot = ld("b0/out/stim_ach/C_src1.exr").sum()
RADII = (3, 10, 18, 30, 60)
res = {"units": {"PSF_sr^-1": "fraction of the source's luminance per steradian (annulus mean, +-0.5')",
                 "energy_within_arcmin": "fraction of the source's luminance in the 73 px/deg pixels whose centres lie within r; a GRID quantity that includes the 3-px source footprint (no optics: 0.75 within 1'), not the continuous EE of the PSF", "pixel_sr": OMEGA, "px_per_deg": PPD},
       "models": {}}
for v, lab in (("V0_none", "none"), ("V1_iset", "ISET wavefront, 550 nm, ZERO_DEFOCUS"),
               ("V3_cie99", "CIE99 straylight"), ("V2_hdrvdpmtf", "HDR-VDP MTF straylight")):
    Y = ld(f"b0/out/comp_ach/{v}_C_src1.exr") / tot
    r = np.hypot(*np.mgrid[0:Y.shape[0], 0:Y.shape[1]] - np.array([sy, sx])[:, None, None]) / PPD * 60
    res["models"][lab] = {
        "integral_PSF_dOmega_over_field": float(Y.sum()),
        "energy_within_arcmin": {a: float(Y[r <= a].sum()) for a in (1, 3, 10, 18, 30, 60)},
        "PSF_sr^-1_at_arcmin": {a: float(Y[(r > a - 0.5) & (r < a + 0.5)].mean() / OMEGA) for a in RADII},
        "peak_fraction_per_pixel": float(Y.max())}
res["analytic_CIE135_GSF_sr^-1_at_arcmin"] = {a: float(cie_gsf(a / 60)) for a in RADII}
m = res["models"]["CIE99 straylight"]["PSF_sr^-1_at_arcmin"]
res["check_CIE99_image_vs_analytic_ratio"] = {a: m[a] / res["analytic_CIE135_GSF_sr^-1_at_arcmin"][a] for a in RADII}
th = np.geomspace(1e-4, 90, 200000); th_r = np.radians(th)
res["check_analytic_GSF_integral_to_90deg"] = float(np.trapezoid(cie_gsf(th) * 2 * np.pi * np.sin(th_r), th_r))
json.dump(res, open("b0/results/retinal_profiles.json", "w"), indent=1)
for k, v in res["models"].items():
    print(f"{k:38s} int {v['integral_PSF_dOmega_over_field']:.3f}  EE(1,3,18') " +
          " ".join(f"{v['energy_within_arcmin'][a]:.3f}" for a in (1, 3, 18)) +
          " | PSF sr^-1 (3,10,18,30,60') " + " ".join(f"{x:.2e}" for x in v["PSF_sr^-1_at_arcmin"].values()))
print("analytic CIE 135/1        ", " ".join(f"{x:.2e}" for x in res["analytic_CIE135_GSF_sr^-1_at_arcmin"].values()))
print("CIE99 image / analytic    ", " ".join(f"{x:.3f}" for x in res["check_CIE99_image_vs_analytic_ratio"].values()))
print("analytic integral to 90 deg", res["check_analytic_GSF_integral_to_90deg"])
