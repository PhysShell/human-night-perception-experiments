#!/usr/bin/env python3
"""Plots + summary numbers from the NATIVE measurements of gazehdr.mp4 (no model is simulated)."""
import json, numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
O = "results/native/gazehdr-2015"
C = ["#2a78d6", "#eb6834", "#1baf7a"]; INK = "#52514e"
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": INK,
                     "axes.labelcolor": "#0b0b0b", "xtick.color": INK, "ytick.color": INK,
                     "axes.grid": True, "grid.color": "#e6e5e0", "grid.linewidth": 0.6, "font.size": 9})
out = {}
# ---- sunset: adaptation time course around gaze on / off the sun
d = np.genfromtxt(f"{O}/NATIVE_sunset_577-620s_patches.csv", delimiter=",", names=True)
t = d["t_s"]; m = (t > 600.35) & (t < 620.0)
sun = (np.abs(d["dot_x"] - 338) < 12) & (np.abs(d["dot_y"] - 206) < 12)
fig, ax = plt.subplots(figsize=(8, 3.6))
for k, c, lab in [("grass", C[0], "grass (lower field)"), ("sky_upper_right", C[1], "sky, upper right"),
                  ("water_left", C[2], "water, left")]:
    ax.plot(t[m], np.log10(d[f"{k}_Ylin"][m]), color=c, lw=2, label=lab)
on = m & sun
ax.fill_between(t[m], -3, 0.2, where=on[m], color="#d8d6ce", alpha=0.6, lw=0, label="gaze marker on the sun")
ax.set_ylim(-2.6, 0.1); ax.set_xlabel("video time (s), gazehdr.mp4"); ax.set_ylabel("log10 relative display luminance\n(sRGB-decoded code values)")
ax.set_title("NATIVE: sunset demo - global adaptation follows gaze (fixating the sun darkens the whole frame)", fontsize=9, loc="left")
ax.legend(frameon=False, fontsize=8, loc="lower left", ncol=2)
fig.tight_layout(); fig.savefig(f"{O}/NATIVE_sunset_adaptation_timecourse.png", dpi=130); plt.close(fig)
def slope(t0, t1, key="grass_Ylin"):
    s = (t >= t0) & (t <= t1); p = np.polyfit(t[s], np.log10(d[key][s]), 1); return float(p[0])
out["sunset"] = {
  "gaze_to_sun_602.0s_darkening_slope_log10_per_s_grass": slope(602.2, 606.4),
  "gaze_to_sun_614.0s_darkening_slope_log10_per_s_grass": slope(614.0, 616.4),
  "gaze_off_sun_606.6s_brightening_slope_log10_per_s_grass": slope(606.7, 607.8),
  "gaze_off_sun_618.0s_brightening_slope_log10_per_s_grass": slope(618.0, 619.8),
  "grass_log10_before_sun_fixation_601.9s": float(np.log10(d["grass_Ylin"][np.argmin(np.abs(t - 601.9))])),
  "grass_log10_end_of_sun_fixation_606.4s": float(np.log10(d["grass_Ylin"][np.argmin(np.abs(t - 606.4))])),
  "sun_disk_max_code_600.4-601.9_gaze_on_house": float(np.nanmax(d["sun_disk_Ymax_code"][(t > 600.4) & (t < 601.9)])),
  "sun_disk_max_code_606.7-607.9_just_after_sun_fixation": [float(np.nanmin(d["sun_disk_Ymax_code"][(t > 606.7) & (t < 607.9)])), float(np.nanmax(d["sun_disk_Ymax_code"][(t > 606.7) & (t < 607.9)]))],
  "sun_disk_max_code_608-613.8": [float(np.nanmin(d["sun_disk_Ymax_code"][(t > 608) & (t < 613.8)])), float(np.nanmax(d["sun_disk_Ymax_code"][(t > 608) & (t < 613.8)]))],
  "note": "sun_disk patch is masked within 14 px of the gaze marker, so during fixation it is NaN; the max is read before/after",
}
# ---- lamp: three aligned passes
a = np.genfromtxt(f"{O}/NATIVE_lamp_passes_aligned.csv", delimiter=",", names=True)
tr = a["t_rel_s"]
fig, axs = plt.subplots(1, 3, figsize=(10, 3.2))
P = [("P1_global", C[0], "pass 1: global adaptation"), ("P2_afterimages", C[1], "pass 2: + afterimages"),
     ("P3_lowlight", C[2], "pass 3: + low-light effects")]
for key, ttl, ax, lg in [("leftchk_Ylin", "left (dark) checker: mean rel. luminance", axs[0], True),
                         ("leftchk_sat", "left checker: mean HSV saturation", axs[1], False),
                         ("leftchk_edge_rel", "left checker: |Laplacian| / mean (sharpness)", axs[2], False)]:
    for p, c, lab in P:
        ax.plot(tr, a[f"{p}_{key}"], color=c, lw=2, label=lab)
    ax.set_title(ttl, fontsize=8.5, loc="left"); ax.set_xlabel("time since first gaze jump (s)")
    ax.axvspan(0, 8.43, color="#eeede8", lw=0)
    if lg: ax.legend(frameon=False, fontsize=7.5)
fig.suptitle("NATIVE: lamp demo, same scripted gaze path shown three times (shaded: gaze on the dark left half)", fontsize=9, x=0.01, ha="left")
fig.tight_layout(); fig.savefig(f"{O}/NATIVE_lamp_passes_timeseries.png", dpi=130); plt.close(fig)
for nm, (w0, w1) in {"trel_6.0-8.3s_gaze_on_dark_half_afterimage_faded": (6.0, 8.3), "trel_9.0-11.4s_gaze_on_bright_right_checker": (9.0, 11.4)}.items():
    w = (tr > w0) & (tr < w1)
    out["lamp_passes_" + nm] = {p: {k: float(np.nanmean(a[f"{p}_{k}"][w])) for k in ["leftchk_Ylin", "leftchk_sat", "leftchk_edge_rel"]} for p, _, _ in P}
# ---- lamp pass 1 global-adaptation time course (dark background patch), whole-video frame
b = np.genfromtxt(f"{O}/NATIVE_lamp_27-93s_patches.csv", delimiter=",", names=True)
tb = b["t_s"]
def sl(t0, t1, k="bg_dark_Ylin"):
    s = (tb >= t0) & (tb <= t1); return float(np.polyfit(tb[s], np.log10(b[k][s]), 1)[0])
out["lamp_pass1"] = {"gaze_lamp_to_dark_left_28.8-33.6s_brightening_slope_log10_per_s_bg": sl(28.9, 33.5),
                     "gaze_dark_to_bright_right_37.2-37.8s_darkening_slope_log10_per_s_bg": sl(37.25, 37.8),
                     "gaze_to_lamp_44.4-46.2s_darkening_slope_log10_per_s_bg": sl(44.5, 46.2),
                     "bg_log10_range": [float(np.log10(b["bg_dark_Ylin"][(tb > 28) & (tb < 46.2)].min())), float(np.log10(b["bg_dark_Ylin"][(tb > 28) & (tb < 46.2)].max()))]}
json.dump(out, open(f"{O}/NATIVE_measurements_summary.json", "w"), indent=1)
print(json.dumps(out, indent=1))
