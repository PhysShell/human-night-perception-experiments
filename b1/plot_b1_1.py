#!/usr/bin/env python3
"""B1.1 figure + the non-fitted region: THIBOS_ONLY, THIBOS_PLUS_ARIAS (zero and native focus), NAIVE_CONVOLUTION_CONTROL,
CIE (calibration target, 0.5-8 deg only) and IJspeert (O3, not used in the fit), 0.1' .. 10 deg.
  tracks/temporal-glare-2009/py.sh b1/plot_b1_1.py -> b1/results/b1_1.png, b1/results/b1_1_unfitted.json"""
import json
import numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
d = np.genfromtxt("b1/results/b1_1_profiles.csv", delimiter=",", names=True)
ij = np.genfromtxt("b1/results/O3_IJSPEERT_m0.106_6mm.csv", delimiter=",", names=True)
th = d["theta_arcmin"]; ijp = np.interp(th, ij["theta_arcmin"], ij["psf_sr1"])
res = {}
for nm in ("THIBOS_PLUS_ARIAS", "NAIVE_CONVOLUTION_CONTROL", "THIBOS_ONLY"):
    res[nm] = {"log10_vs_CIE": {a: float(np.log10(np.interp(a, th, d[nm]) / np.interp(a, th, d["CIE_RAW"]))) for a in (1, 3, 10, 20)},
               "log10_vs_IJspeert": {a: float(np.log10(np.interp(a, th, d[nm]) / np.interp(a, th, ijp))) for a in (1, 3, 10, 20)}}
json.dump(res, open("b1/results/b1_1_unfitted.json", "w"), indent=1)
print(json.dumps(res, indent=1))
fig, ax = plt.subplots(1, 2, figsize=(14, 5.2))
for nm, st in (("THIBOS_ONLY", "c-"), ("THIBOS_PLUS_ARIAS", "b-"), ("NATIVE_PLUS_ARIAS", "b:"), ("NAIVE_CONVOLUTION_CONTROL", "m--"), ("CIE_RAW", "k-")):
    ax[0].loglog(th, d[nm], st, lw=2 if nm == "THIBOS_PLUS_ARIAS" else 1.2, label=nm + (" (calibration target, 0.5-8 deg)" if nm == "CIE_RAW" else ""))
    ax[1].loglog(th, (th / 60) ** 2 * d[nm], st, lw=2 if nm == "THIBOS_PLUS_ARIAS" else 1.2, label=nm)
ax[0].loglog(th, ijp, "r-", lw=1, label="O3 IJspeert m .106, 6 mm (not used in fit)"); ax[1].loglog(th, (th / 60) ** 2 * ijp, "r-", lw=1)
for a in ax:
    a.axvspan(30, 480, color="k", alpha=0.06); a.set_xlim(0.1, 600); a.grid(True, which="both", lw=0.3); a.set_xlabel("angle [arcmin]  (shaded: calibration range 0.5-8 deg)")
ax[0].set(ylabel="PSF [sr$^{-1}$]", title="B1.1: one pupil (Thibos + Arias screen) vs controls")
ax[1].set(ylabel=r"s = $\theta^2$ PSF [deg$^2$ sr$^{-1}$]", ylim=(1e-2, 1e3), title="straylight parameter")
ax[0].legend(fontsize=7)
plt.tight_layout(); plt.savefig("b1/results/b1_1.png", dpi=95)
