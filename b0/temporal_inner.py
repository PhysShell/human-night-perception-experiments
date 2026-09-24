#!/usr/bin/env python3
"""B0 v3: Temporal Glare (Ritschel et al. 2009, Frisvad demo) as an INNER DYNAMIC GLARE SAMPLE.
The demo computes its PSF in a +-0.48 deg window (512 px at ~532 px/deg), so its plateau diameter stops
being a result once the displayed spot approaches the window. What the window can answer is measured
here on the NATIVE float PSF frames (research-cache/temporal-glare-2009/psf_float_stack.npy, 33 frames,
the demo's own time stamps), luminance-weighted, only inside a safe radius of 0.35 deg (0.73 of the
half-window), each frame normalised to unit energy inside that radius:
  * inner radial profile (annuli, arcmin) per frame -> temporal modulation per annulus (max/min - 1, CV);
  * centre of energy (r < 0.35 deg) and of the core (r < 5') per frame -> wander in arcmin;
  * central deformation: core second-moment ellipticity (1 - minor/major) and orientation, EE50 radius;
  * temporal spectrum (uneven sampling -> Lomb-Scargle via numpy) of the core EE50 radius and of the
    energy in 2'-10'; the frame spacing limits it to < 1.9 Hz, and the 8.6 s record to ~0.12 Hz resolution
    (about two cycles at the peak), so only a band is reported, not a frequency.
  tracks/temporal-glare-2009/py.sh b0/temporal_inner.py   -> b0/results/temporal_inner.json (+ png)
"""
import importlib.util, json
import numpy as np

spec = importlib.util.spec_from_file_location("cc", "tracks/temporal-glare-2009/compose_common.py")
cc = importlib.util.module_from_spec(spec); spec.loader.exec_module(cc)
S = np.load("research-cache/temporal-glare-2009/psf_float_stack.npy").astype(np.float64) @ np.array([0.2126, 0.7152, 0.0722])
t = np.load("research-cache/temporal-glare-2009/psf_float_frames.npy") * cc.STEP_S
P = cc.PX_PER_DEG_PSF; n = S.shape[1]
yy, xx = np.mgrid[0:n, 0:n]
cy, cx = np.unravel_index(S.mean(0).argmax(), S.shape[1:])
r = np.hypot(yy - cy, xx - cx) / P * 60                                    # arcmin
SAFE = 0.35 * 60
inside = r < SAFE
edges = np.array([0, 1, 2, 4, 6, 10, 15, 21])
prof, coe, core_c, ell, ori, ee50, e210 = [], [], [], [], [], [], []
for a in S:
    a = np.maximum(a, 0) * inside; a = a / a.sum()
    prof.append([a[(r >= lo) & (r < hi)].sum() / ((r >= lo) & (r < hi)).sum() for lo, hi in zip(edges[:-1], edges[1:])])
    coe.append([(a * (xx - cx)).sum() / P * 60, (a * (yy - cy)).sum() / P * 60])
    c = a * (r < 5); c = c / c.sum()
    mx, my = (c * xx).sum(), (c * yy).sum(); core_c.append([(mx - cx) / P * 60, (my - cy) / P * 60])
    cxx, cyy, cxy = (c * (xx - mx) ** 2).sum(), (c * (yy - my) ** 2).sum(), (c * (xx - mx) * (yy - my)).sum()
    ev = np.linalg.eigvalsh([[cxx, cxy], [cxy, cyy]])
    ell.append(1 - np.sqrt(ev[0] / ev[1])); ori.append(np.degrees(0.5 * np.arctan2(2 * cxy, cxx - cyy)))
    o = np.argsort(r.ravel()); ee = np.cumsum(a.ravel()[o]); ee50.append(r.ravel()[o][np.searchsorted(ee, 0.5)])
    e210.append(a[(r >= 2) & (r < 10)].sum())
prof, coe, core_c = np.array(prof), np.array(coe), np.array(core_c)
ee50, e210 = np.array(ee50), np.array(e210)


def lomb(y, f):
    y = y - y.mean(); out = []
    for fr in f:
        w = 2 * np.pi * fr; tau = np.arctan2(np.sin(2 * w * t).sum(), np.cos(2 * w * t).sum()) / (2 * w)
        c, s = np.cos(w * (t - tau)), np.sin(w * (t - tau))
        out.append(0.5 * ((y @ c) ** 2 / (c @ c) + (y @ s) ** 2 / (s @ s)))
    return np.array(out)


dt = np.diff(t); fmax = 0.5 / np.median(dt); f = np.linspace(0.05, fmax, 200)
spec_ee, spec_e = lomb(ee50, f), lomb(e210, f)
ann = [f"{lo}-{hi}'" for lo, hi in zip(edges[:-1], edges[1:])]
res = {
    "what": "Temporal Glare demo PSF, native float frames, luminance-weighted, inside the safe radius only",
    "window_half_deg": n / 2 / P, "safe_radius_deg": SAFE / 60, "frames": int(len(t)),
    "t_s": [float(t[0]), float(t[-1])], "median_frame_step_s": float(np.median(dt)), "spectrum_limit_Hz": float(fmax),
    "inner_profile_modulation": {a: {"max_over_min_minus_1": float(prof[:, i].max() / prof[:, i].min() - 1),
                                     "cv": float(prof[:, i].std() / prof[:, i].mean())} for i, a in enumerate(ann)},
    "centre_of_energy_wander_arcmin": {"inner_0.35deg_rms": float(np.sqrt(((coe - coe.mean(0)) ** 2).sum(1).mean())),
                                       "inner_0.35deg_max": float(np.hypot(*(coe - coe.mean(0)).T).max()),
                                       "core_5arcmin_rms": float(np.sqrt(((core_c - core_c.mean(0)) ** 2).sum(1).mean()))},
    "core_deformation": {"ellipticity_mean": float(np.mean(ell)), "ellipticity_range": [float(min(ell)), float(max(ell))],
                         "orientation_deg_range": [float(min(ori)), float(max(ori))]},
    "core_EE50_radius_arcmin": {"mean": float(ee50.mean()), "min": float(ee50.min()), "max": float(ee50.max()),
                                "modulation_max_over_min_minus_1": float(ee50.max() / ee50.min() - 1)},
    "energy_2_10arcmin": {"mean": float(e210.mean()), "modulation_max_over_min_minus_1": float(e210.max() / e210.min() - 1)},
    "temporal_spectrum_peak_Hz": {"core_EE50": float(f[spec_ee.argmax()]), "energy_2_10arcmin": float(f[spec_e.argmax()])},
    "spectrum_caveat": {"record_length_s": float(t[-1] - t[0]), "frequency_resolution_Hz": float(1 / (t[-1] - t[0])),
                        "cycles_at_peak": float(f[spec_ee.argmax()] * (t[-1] - t[0])),
                        "reading": "a dominant low-frequency component around 0.2-0.3 Hz in this short donor sequence, "
                                   "not a precise frequency; the demo's hippus is a synthetic noise model (Frisvad, after Fry)"},
    "not_measured": "plateau diameter on a display (window-limited) and anything beyond 0.35 deg",
}
json.dump(res, open("b0/results/temporal_inner.json", "w"), indent=1)
print(json.dumps(res, indent=1))
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
fig, ax = plt.subplots(1, 3, figsize=(13, 3.6))
for i, a in enumerate(ann): ax[0].plot(t, prof[:, i] / prof[:, i].mean(), label=a)
ax[0].set(xlabel="t, s", ylabel="annulus mean / time mean", title="inner radial profile over time"); ax[0].legend(fontsize=7)
ax[1].plot(*(coe - coe.mean(0)).T, ".-", label="inner 0.35 deg"); ax[1].plot(*(core_c - core_c.mean(0)).T, ".-", label="core 5'")
ax[1].set(xlabel="x, arcmin", ylabel="y, arcmin", title="centre of energy wander", aspect="equal"); ax[1].legend(fontsize=7)
ax[2].plot(f, spec_ee / spec_ee.max(), label="core EE50"); ax[2].plot(f, spec_e / spec_e.max(), label="energy 2-10'")
ax[2].set(xlabel="Hz", title="temporal spectrum (Lomb-Scargle)"); ax[2].legend(fontsize=7)
fig.tight_layout(); fig.savefig("b0/results/temporal_inner.png", dpi=110)
