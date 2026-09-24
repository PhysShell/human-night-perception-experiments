#!/usr/bin/env python3
"""B0-spectral (retinal only, SPD-aware systems only): ISETBio/ISETCam 'wvf human' point image
(Thibos mean eye, focus 550 nm, pupil 6 mm, b0/iset_kernel.m at 4x of 73 px/deg) for each SPD of
tracks/mitsuba-spectral/spectra/test_spectra_unitlum.csv, plus monochromatic 550 nm (the B0-optics
kernel; no LCA). Luminance-weighted illuminance; encircled-energy radii and FWHM (equivalent-area) on
the fine grid, within the 2.5 deg ISET field. No display, no colour judgement.
  python3 b0/spectral_layer.py   -> b0/results/spectral_layer.json
"""
import json
import numpy as np

res = {}
for tag, name in [(t + z, n + d) for z, d in (("z", ", ZERO_DEFOCUS (c4 forced to 0)"), ("", ", THIBOS_NATIVE (c4 +0.335 um, as published)"))
                  for t, n in (("550", "monochromatic 550 nm (B0-optics)"), ("HPS", "HPS (CIE HP1)"), ("LED", "LED warm"),
                               ("E", "equal-energy E"), ("BLUE", "blue test spectrum"))]:
    p = f"b0/out/kernels/iset_kernel_{tag}"
    with open(p + ".raw", "rb") as f:
        h, w, c, _ = np.fromfile(f, "<i4", 4); E = np.fromfile(f, "<f4").reshape(h, w, c)[..., 0].astype(float)
    ss = json.load(open(p + ".json")).get("supersample", 4); ppd = 73 * ss
    E = np.maximum(E - np.median(E[:5, :5]), 0)
    cy, cx = np.unravel_index(E.argmax(), E.shape)
    r = np.hypot(*np.mgrid[-cy:h - cy, -cx:w - cx]) / ppd * 60
    o = np.argsort(r.ravel()); ee = np.cumsum(E.ravel()[o]) / E.sum(); rs = r.ravel()[o]
    res[tag] = {"spd": name, "EE_radius_arcmin": {p_: float(rs[np.searchsorted(ee, p_ / 100)]) for p_ in (50, 80, 95)},
                "FWHM_equiv_arcmin": float(2 * np.sqrt((E >= 0.5 * E.max()).sum() / np.pi) / ppd * 60),
                "energy_within_1arcmin": float(ee[np.searchsorted(rs, 1.0)])}
res["note"] = ("Thibos mean eye (other Zernike terms as shipped, incl. astigmatism j=5 -0.17 um and spherical j=12 +0.094 um), "
               "6 mm pupil, reference wavelength 550 nm, on-axis; radii within the 2.5 deg ISET field")
json.dump(res, open("b0/results/spectral_layer.json", "w"), indent=1)
for k, v in res.items():
    if k != "note": print(f"{k:6s} EE50/80/95 {v['EE_radius_arcmin'][50]:.2f} {v['EE_radius_arcmin'][80]:.2f} {v['EE_radius_arcmin'][95]:.2f}'  FWHM {v['FWHM_equiv_arcmin']:.2f}'  E(<1') {v['energy_within_1arcmin']:.3f}")
