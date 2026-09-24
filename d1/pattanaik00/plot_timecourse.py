#!/usr/bin/env python3
"""Plot d1/pattanaik00/native_timecourse.json -> native_timecourse.png
  tracks/temporal-glare-2009/py.sh d1/pattanaik00/plot_timecourse.py"""
import json, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
d = json.load(open(f"{HERE}/native_timecourse.json"))
R = {r["name"][0]: r for r in d["runs"]}
C = {"A": "#eda100", "B": "#2a78d6", "C": "#eb6834", "D": "#1baf7a", "E": "#4a3aa7"}
LAB = {"A": "A 1000→0.01, 24 fps (rod bleaching diverges)", "B": "B 1000→0.01, 60 fps", "C": "C 100→0.01, 24 fps",
       "D": "D 0.01→1000, T=30 ms (paper title page)", "E": "E static 0.01, no -c (frame-0 init 5×logavg)"}
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.color": "#e4e4e0",
                     "grid.linewidth": 0.6, "axes.edgecolor": "#8a8984", "text.color": "#0b0b0b", "axes.labelcolor": "#52514e"})
fig, ax = plt.subplots(2, 2, figsize=(12, 8.2))
DARK = 30.0

# (a) dark adaptation: background display value after the step down (log time)
a = ax[0, 0]
for k in "ABC":
    s = R[k]["series"]; t = np.array(s["t_s"]) - DARK; m = (t > 0) & (t < 1800)
    a.plot(t[m], np.maximum(np.array(s["out_bg"])[m], 1e-4), color=C[k], lw=2, label=LAB[k])
    if k == "B":
        a.plot(t[m], np.maximum(np.array(s["out_x10"])[m], 1e-4), color=C[k], lw=1.2, ls="--", label="B, 10× test patch")
a.axhline(R["B"]["static_no_t_output_bg"]["0.01"], color="#52514e", lw=1, ls=":", label="static (no -t) render of 0.01 field")
a.set_xscale("log"); a.set_yscale("log"); a.set_xlim(0.03, 1800); a.set_ylim(1e-4, 1.5)
a.set_xlabel("time after step to 0.01 cd/m² (s)"); a.set_ylabel("tool output (relative; 1 = 125 cd/m² display white)")
a.set_title("(a) dark adaptation: black, fast neural recovery, slow rod regeneration", loc="left", fontsize=10)
a.legend(fontsize=7.5, frameon=False, loc="lower right")

# (b) light adaptation, per frame, linear time
a = ax[0, 1]
for k, t_step in (("B", DARK + 1800), ("C", DARK + 1800), ("D", 1.0)):
    s = R[k]["series"]; t = np.array(s["t_s"]) - t_step; m = (t > -0.15) & (t < 1.0)
    a.plot(t[m], np.array(s["out_bg"])[m], color=C[k], lw=2, marker="o", ms=4, label=LAB[k])
a.set_xlabel("time after step up (s)"); a.set_ylabel("tool output, background")
a.set_title("(b) light adaptation: bright first frame, recovery in 0.1–0.3 s", loc="left", fontsize=10)
a.legend(fontsize=7.5, frameon=False)

# (c) state: rod bleaching term
a = ax[1, 0]
for k in "BC":
    s = R[k]["series"]; t = np.array(s["t_s"]) - DARK; m = (t > 0) & (t < 1800)
    a.plot(t[m], np.array(s["Brod"])[m], color=C[k], lw=2, label=LAB[k] + ": B_rod")
tt = np.logspace(-1.5, np.log10(1800), 200)
a.plot(tt, 1 - np.exp(-tt / 400), color="#52514e", lw=1, ls=":", label="1 − exp(−t/400 s) (paper τ_rod)")
a.set_xscale("log"); a.set_xlim(0.03, 1800)
a.set_xlabel("time after step to 0.01 cd/m² (s)"); a.set_ylabel("B_rod (tool --verbose)")
a.set_title("(c) rod pigment regeneration sets the slow phase", loc="left", fontsize=10)
a.legend(fontsize=7.5, frameon=False, loc="upper left")

# (d) instability: B_rod per frame in A (24 fps) and D (T = 30 ms) after the 1000 cd/m^2 onset
a = ax[1, 1]
s = R["A"]["series"]; t = np.array(s["t_s"]); m = t < 2.0
a.plot(t[m], np.array(s["Brod"])[m], color=C["A"], lw=1.5, marker="o", ms=3, label="A: start adapted to 1000, 24 fps")
s = R["D"]["series"]; t = np.array(s["t_s"]) - 1.0; m = (t > -0.1) & (t < 1.0)
a.plot(t[m], np.array(s["Brod"])[m], color=C["D"], lw=1.5, marker="o", ms=3, label="D: 0.01→1000 at t=0, T=30 ms")
a.set_yscale("symlog", linthresh=1e-3); a.set_xlabel("time (s)"); a.set_ylabel("B_rod (symlog)")
a.set_title("(d) explicit update of eq. 7a is unstable when G·T/16 > 2", loc="left", fontsize=10)
a.legend(fontsize=7.5, frameon=False)
fig.suptitle("pfstmo_pattanaik00 -t (pfstools 2.2.0) on uniform-field step sequences: native time-course check", x=0.01, ha="left", fontsize=11)
fig.tight_layout()
fig.savefig(f"{HERE}/native_timecourse.png", dpi=110)
print("ok")
