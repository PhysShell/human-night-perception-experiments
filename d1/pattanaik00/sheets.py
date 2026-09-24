#!/usr/bin/env python3
"""Labelled contact sheets (PREVIEW: SDR100 code values as delivered, area-averaged in linear light, re-encoded sRGB;
same method as d0/contact_sheets.py). Labels carry measured emitted numbers from d1/pattanaik00/metrics.jsonl.
  tracks/temporal-glare-2009/py.sh d1/pattanaik00/sheets.py  -> sheet_S1.png, sheet_S1_ladder.png, clip_history.png
"""
import json, os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
os.chdir(ROOT); sys.path.insert(0, "d0")
from display_model import read_code
from contact_sheets import srgb_to_lin, lin_to_srgb, area_down

H = "d1/pattanaik00"; OUT = f"{H}/.cache/out"
MET = {}
for l in open(f"{H}/metrics.jsonl"):
    r = json.loads(l); MET[(r["config"], r["scene"], r["lum"])] = r


def lab(cfg, scene, lum, text):
    r = MET.get((cfg, scene, lum), {})
    f = lambda k, fmt: (fmt % r[k]) if r.get(k) is not None else "–"
    return (f"{text}\nsky {f('sky_median', '%.3g')} cd/m², dark median {f('dark_median', '%.3g')}, silhouette "
            f"{f('silhouette_weber', '%.2f')}, lamp sat. kept {f('lamp_saturation_retention', '%.2f')}, plateaus "
            f"{r.get('plateau_n', '–')} / max {f('plateau_diam_max_arcmin', '%.1f')}′")


def sheet(cells, dest, title):
    cells = [(t, p) for t, p in cells if os.path.exists(p)]
    fig, axs = plt.subplots(len(cells), 1, figsize=(10, 2.6 * len(cells)))
    for ax, (t, p) in zip(np.atleast_1d(axs), cells):
        v = read_code(p); f = max(1, v.shape[1] // 960)
        ax.imshow(lin_to_srgb(area_down(srgb_to_lin(v), f)), interpolation="antialiased")
        ax.set_title(t, fontsize=7.5, loc="left"); ax.axis("off")
    fig.suptitle(title.replace("  |  PHONE", "\nPHONE"), fontsize=8)
    plt.tight_layout(rect=[0, 0, 1, 0.97]); plt.savefig(dest, dpi=110); plt.close(fig)


T = "PHONE, SDR100 (sRGB, 100 / 0.1 cd/m²), DARK  |  PREVIEW of delivered code values; numbers = emitted light (d0/display_model.py)"
sheet([(lab("native_default", "S1", "SDR100", "NATIVE_DEFAULT: pfstmo_pattanaik00 | pfsgamma -g 2.2 (man page), decoded as SDR100"),
        f"{OUT}/native_default/S1__PHONE_SDR100_DARK.png"),
       (lab("target", "S1", "SDR100", "DOCUMENTED_TARGET_CONFIG: absolute cd/m² in, relative out -> sRGB"), f"{OUT}/target/S1__PHONE_SDR100_DARK.png"),
       (lab("sens_abs125", "S1", "SDR100", "SENSITIVITY: output x 125 cd/m² (tool's display white) emitted absolutely"),
        f"{OUT}/sens_abs125/S1__PHONE_SDR100_DARK.png"),
       (lab("sens_local", "S1", "SDR100", "SENSITIVITY: --local"), f"{OUT}/sens_local/S1__PHONE_SDR100_DARK.png"),
       ("REFERENCE ONLY (not combined): pcond V0 native_default (d0): sky 0.32, dark median 0.14, silhouette 0.56, lamp sat. 0.35",
        "d0/work/out/pcond/native_default/S1__PHONE_SDR100_DARK.png")],
      f"{H}/sheet_S1.png", "S1 pfstmo_pattanaik00 (pfstools 2.2.0)  |  " + T)
sheet([(lab(f"sens_ladder_x1e{k}", "S1", "SDR100", f"S1 x 10^{k} (tool -m 1e{k}), relative -> sRGB"), f"{OUT}/sens_ladder_x1e{k}/S1__PHONE_SDR100_DARK.png")
       for k in (0, 2, 4, 6)], f"{H}/sheet_S1_ladder.png", "S1 absolute-level ladder (SENSITIVITY_RUN)  |  " + T)

# clip sky median vs time (per-frame stats from runs.json)
runs = {r["config"]: r for r in json.load(open(f"{H}/runs.json"))["runs"] if r["scene"] == "S2"}
C = {"clip_t24": "#2a78d6", "clip_static": "#52514e", "clip_hist100": "#eb6834", "clip_hist100_long": "#1baf7a"}
fig, ax = plt.subplots(1, 2, figsize=(12, 4))
for cfg, lbl in (("clip_static", "no -t (NATIVE_DEFAULT)"), ("clip_t24", "-t --fps 24 (DOCUMENTED_TARGET_CONFIG)"),
                 ("clip_hist100", "2 s at 100 cd/m², then S2, -t 24")):
    if cfg in runs:
        s = runs[cfg]["per_frame"]; t = np.array(s["t_s"]) - (2.0 if cfg == "clip_hist100" else 0)
        ax[0].plot(t, s["sky_median_SDR100"], color=C[cfg], lw=2, marker="o", ms=3, label=lbl)
ax[0].set_yscale("log"); ax[0].set_xlabel("time in the S2 clip (s); history frames at t < 0"); ax[0].set_ylabel("sky median emitted, SDR100 (cd/m²)")
ax[0].axhline(0.32, color="#8a8984", ls=":", lw=1, label="pcond V0 S1 sky (reference)"); ax[0].legend(fontsize=7.5, frameon=False)
ax[0].set_title("S2 clip, sky median per frame", loc="left", fontsize=10)
if "clip_hist100_long" in runs:
    s = runs["clip_hist100_long"]["per_frame"]; t = np.array(s["t_s"]) - 2.0; m = t > 0
    ax[1].plot(t[m], np.array(s["sky_median_SDR100"])[m], color=C["clip_hist100_long"], lw=2, label="sky median SDR100")
    ax[1].plot(t[m], np.array(s["dark_median_SDR100"])[m], color="#4a3aa7", lw=1.5, ls="--", label="dark (non-source) median SDR100")
    ax[1].set_xscale("log"); ax[1].set_yscale("log"); ax[1].axhline(0.32, color="#8a8984", ls=":", lw=1, label="pcond V0 S1 sky")
    ax[1].set_xlabel("time after leaving the 100 cd/m² field (s)"); ax[1].set_ylabel("emitted cd/m²")
    ax[1].set_title("2 s at 100 cd/m², then S1 held 600 s (480x205, ADAPTED)", loc="left", fontsize=10); ax[1].legend(fontsize=7.5, frameon=False)
for a in ax:
    a.spines[["top", "right"]].set_visible(False); a.grid(color="#e4e4e0", lw=0.6)
plt.tight_layout(); plt.savefig(f"{H}/clip_history.png", dpi=110)
print("ok")
