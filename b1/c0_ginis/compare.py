#!/usr/bin/env python3
"""External validation (no refitting) of B1.1 against the digitized Ginis et al. 2012 reconstructed wide-angle PSF.

  tracks/temporal-glare-2009/py.sh b1/c0_ginis/digitize.py
  tracks/temporal-glare-2009/py.sh b1/c0_ginis/compare.py   -> b1/c0_ginis/result.json, b1/c0_ginis/compare.png

Both sides are log10 PSF in sr^-1 (Ginis Fig. 7/6 'Log(PSF)'; unit identified from Fig. 5b 'PSF ... [sr^-1]' and the
Stiles-Holladay / Vos-van den Berg reference curves drawn in the same axes, see README). No parameter of B1.1 is touched.
"""
import json, os
import numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
d = np.genfromtxt(os.path.join(ROOT, "results", "b1_1_profiles.csv"), delimiter=",", names=True)
gz = np.genfromtxt(os.path.join(HERE, "ginis2012_fig7_grid.csv"), delimiter=",", names=True, skip_header=1)
th_deg = gz["theta_deg"]
MODELS = ("THIBOS_PLUS_ARIAS", "CIE_RAW", "THIBOS_ONLY")


def model_log(nm, deg):
    return np.interp(np.log10(deg * 60), np.log10(d["theta_arcmin"]), np.log10(d[nm]))


# primary GP trace = Fig 6 'Reconstructed PSF' (same subject, no overlapping curves); Fig 7 GP kept as a cross-check
cross = gz["GP"] - gz["GP_RECONSTRUCTED"]
subj = {"GP": (gz["GP_RECONSTRUCTED"], np.hypot(gz["GP_RECONSTRUCTED_unc"], np.abs(np.nan_to_num(cross)))),
        "CS": (gz["CS"], gz["CS_unc"])}
# CS crosses GP and the black reference curves near 0.8-1.2 deg; add the GP cross-figure discrepancy seen there
crossing = (th_deg >= 0.75) & (th_deg <= 1.25)
subj["CS"] = (subj["CS"][0], np.where(crossing, np.hypot(subj["CS"][1], np.nanmax(np.abs(cross[crossing]))), subj["CS"][1]))
subj["MEAN_GP_CS"] = (0.5 * (subj["GP"][0] + subj["CS"][0]), 0.5 * np.hypot(subj["GP"][1], subj["CS"][1]))

RANGES = {"primary_1.0-7.5deg": (1.0, 7.5), "secondary_0.5-7.5deg": (0.5, 7.5)}
AT = (0.5, 1.0, 2.0, 3.0, 5.0, 7.0, 7.5)


def slope(x, y):
    return float(np.polyfit(np.log10(x), y, 1)[0])


res = {"label": "DIGITIZED_EXTERNAL_VALIDATION", "no_refit": "B, beta and all B1.1 settings unchanged; profiles read from b1/results/b1_1_profiles.csv",
       "units": "log10 PSF [sr^-1]", "digitization": {}, "comparisons": {}, "reference_checks": {}}
res["digitization"]["fig7_GP_minus_fig6_GP_log10"] = {"max_abs_0.5-7.5": float(np.nanmax(np.abs(cross))),
                                                       "max_abs_1.25-7.5": float(np.nanmax(np.abs(cross[th_deg >= 1.25]))),
                                                       "at_1.0deg": float(cross[th_deg == 1.0][0])}
res["digitization"]["max_1sigma_unc_log10"] = {k: float(np.nanmax(v[1][(th_deg >= 0.5)])) for k, v in subj.items()}
res["inter_subject"] = {"GP_minus_CS_log10": {str(a): float(subj["GP"][0][th_deg == a][0] - subj["CS"][0][th_deg == a][0]) for a in AT},
                        "slope_GP": slope(th_deg[(th_deg >= 1) & (th_deg <= 7.5)], subj["GP"][0][(th_deg >= 1) & (th_deg <= 7.5)]),
                        "slope_CS": slope(th_deg[(th_deg >= 1) & (th_deg <= 7.5)], subj["CS"][0][(th_deg >= 1) & (th_deg <= 7.5)])}

for sname, (sy, su) in subj.items():
    res["comparisons"][sname] = {}
    for nm in MODELS:
        my = model_log(nm, th_deg); r = my - sy
        e = {"log10_ratio_model_over_ginis": {str(a): round(float(r[th_deg == a][0]), 3) for a in AT}}
        for rn, (lo, hi) in RANGES.items():
            k = (th_deg >= lo) & (th_deg <= hi) & np.isfinite(r)
            e[rn] = {"n": int(k.sum()), "mean_offset": float(r[k].mean()), "log_rms": float(np.sqrt(np.mean(r[k] ** 2))),
                     "offset_free_log_rms": float(r[k].std()), "max_abs": float(np.abs(r[k]).max()),
                     "loglog_slope_model": slope(th_deg[k], my[k]), "loglog_slope_ginis": slope(th_deg[k], sy[k])}
        res["comparisons"][sname][nm] = e

# units sanity check: black solid 'Vos and van den Berg (1999)' of Fig 7 vs our CIE_RAW (age 24, p 0.5)
k = np.isfinite(gz["VOS_VDB_1999_BLACK_SOLID"])
rv = model_log("CIE_RAW", th_deg[k]) - gz["VOS_VDB_1999_BLACK_SOLID"][k]
res["reference_checks"]["CIE_RAW_minus_fig7_VosVdB_black_solid"] = {"range_deg": [float(th_deg[k].min()), float(th_deg[k].max())],
                                                                    "mean": float(rv.mean()), "min": float(rv.min()), "max": float(rv.max()),
                                                                    "note": "Ginis do not state the age/pigmentation used for this curve; agreement within ~0.1 log confirms Log(PSF) = log10(PSF / sr^-1)"}
json.dump(res, open(os.path.join(HERE, "result.json"), "w"), indent=1)
print(json.dumps(res, indent=1))

# ---------- figure
fig, ax = plt.subplots(1, 2, figsize=(13, 5))
tt = np.linspace(0.3, 8, 300)
col = {"THIBOS_PLUS_ARIAS": ("#1f4e9c", "-", 2.2), "CIE_RAW": ("k", "--", 1.2), "THIBOS_ONLY": ("#2aa6a0", ":", 1.5)}
for nm, (c, ls, lw) in col.items():
    ax[0].plot(tt, model_log(nm, tt), color=c, ls=ls, lw=lw, label=f"B1.1 {nm}" if nm != "CIE_RAW" else "CIE_RAW (B1.1 calibration target)")
for sname, c in (("GP", "#7b6fd0"), ("CS", "#d9605f")):
    y, u = subj[sname]
    ax[0].fill_between(th_deg, y - 2 * u, y + 2 * u, color=c, alpha=0.25, lw=0)
    ax[0].plot(th_deg, y, "o-", ms=3, color=c, lw=1, label=f"Ginis 2012 subject {sname} (digitized, ±2σ)")
ax[0].plot(th_deg[k], gz["VOS_VDB_1999_BLACK_SOLID"][k], color="0.5", lw=1, label="Ginis Fig 7 Vos & vdB 1999 curve (digitized)")
ax[0].axvspan(1.0, 7.5, color="k", alpha=0.05)
ax[0].set(xlabel="angle [deg]  (shaded: primary comparison range 1-7.5 deg)", ylabel="log10 PSF [sr$^{-1}$]", xlim=(0.3, 8), ylim=(-2.2, 3),
          title="B1.1 (not refitted) vs Ginis et al. 2012 Fig. 7")
ax[0].legend(fontsize=7); ax[0].grid(lw=0.3)
for nm, (c, ls, lw) in col.items():
    for sname, mk in (("GP", "o"), ("CS", "s")):
        ax[1].plot(th_deg, model_log(nm, th_deg) - subj[sname][0], color=c, ls=ls, lw=lw, marker=mk, ms=3,
                   label=f"{nm} − {sname}")
ax[1].axhline(0, color="k", lw=0.6); ax[1].axvspan(1.0, 7.5, color="k", alpha=0.05)
ax[1].set(xlabel="angle [deg]", ylabel="log10 (model / Ginis)", xlim=(0.3, 8), title="log residual (positive: model above measurement)")
ax[1].legend(fontsize=6, ncol=2); ax[1].grid(lw=0.3)
plt.tight_layout(); plt.savefig(os.path.join(HERE, "compare.png"), dpi=95)
