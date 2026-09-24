#!/usr/bin/env python3
"""D0 labelled scientific contact sheets (no ranking, no blind key, no decorative post-processing).
 sheet_<scene>_SDR100.png   PREVIEW: each donor's SDR100 code values as delivered (sRGB), reduced by area averaging
                            in LINEAR light and re-encoded (never nearest-neighbour). What an sRGB screen shows.
 sheet_S1_scenarios.png     MEASUREMENT VIEW, not a preview: log10 of the light each (parametric) display emits,
                            decoded by d0/display_model.py, one colour scale for all panels, per donor x scenario.
Fairchild-derived scenes (S4, S5) go to d0/work/sheets/ only (licence: non-commercial research; not committed).
  tracks/temporal-glare-2009/py.sh d0/contact_sheets.py
"""
import json, os, sys
import numpy as np
import OpenImageIO as oiio
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, "d0")
from display_model import decode, read_code

OUT = "d0/work/out"
ROWS = [("pcond", "native_default", "pcond V0 (frozen, NATIVE_DEFAULT: Ldmax 100, 100:1)"),
        ("controls", "d1a_photometric", "D1a exposure 1 (absolute cd/m^2) + clamp"),
        ("controls", "d1b_key018", "D1b log-average key 0.18 + clamp"),
        ("reinhard02", "defaults", "D2 pfstmo_reinhard02 defaults"),
        ("mantiuk08", "target_whiteauto", "Mantiuk08 pfstmo 2.2.0, SDR100 LUT, WHITE_Y auto"),
        ("mantiuk08", "target_whiteanchor", "Mantiuk08, WHITE_Y = display peak (anchor)"),
        ("aces2", "DOCUMENTED_TARGET_CONFIG", "ACES 2.0 SDR 100 nits Rec.709 (OCIO 2.5.2), ACES 1.0 = 100 cd/m^2"),
        ("icam06", "native_default", "iCAM06 V1.3 native (max_L 20000, p 0.7, gamma 1)"),
        ("icam06", "target_abs_dark_readme", "iCAM06 absolute input, gamma 1.2 (dark surround, Readme)")]


def srgb_to_lin(v):
    return np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)


def lin_to_srgb(x):
    x = np.clip(x, 0, 1); return np.where(x <= 0.0031308, 12.92 * x, 1.055 * x ** (1 / 2.4) - 0.055)


def area_down(a, f):
    h, w = a.shape[0] // f * f, a.shape[1] // f * f
    return a[:h, :w].reshape(h // f, f, w // f, f, -1).mean((1, 3))


def sheet(scene, dest):
    cells = [(lab, f"{OUT}/{d}/{c}/{scene}__PHONE_SDR100_DARK.png") for d, c, lab in ROWS]
    cells = [(l, p) for l, p in cells if os.path.exists(p)]
    fig, axs = plt.subplots(len(cells), 1, figsize=(10, 2.3 * len(cells) * (1 if scene != "S3_bar" else 1.2)))
    for ax, (lab, p) in zip(np.atleast_1d(axs), cells):
        v = read_code(p); f = max(1, v.shape[1] // 960)
        ax.imshow(lin_to_srgb(area_down(srgb_to_lin(v), f)), interpolation="antialiased")
        ax.set_title(lab, fontsize=8, loc="left"); ax.axis("off")
    fig.suptitle(f"{scene}  |  PHONE (73 px/deg), SDR100 (sRGB, 100 / 0.1 cd/m^2), DARK  |  PREVIEW of delivered code values", fontsize=9)
    plt.tight_layout(rect=[0, 0, 1, 0.97]); plt.savefig(dest, dpi=110); plt.close(fig)


def scenarios_sheet(scene, dest):
    donors = [("pcond", {"SDR100": "native_default", "SDR200": "target_SDR200", "BRIGHT500": "target_BRIGHT500"}),
              ("controls", {k: "d1b_key018" for k in ("SDR100", "SDR200", "BRIGHT500", "HDR1000")}),
              ("mantiuk08", {k: "target_whiteauto" for k in ("SDR100", "SDR200", "BRIGHT500", "HDR1000")}),
              ("aces2", {"SDR100": "DOCUMENTED_TARGET_CONFIG", "BRIGHT500_PQ": "DOCUMENTED_TARGET_CONFIG", "HDR1000": "DOCUMENTED_TARGET_CONFIG"})]
    lums = ["SDR100", "SDR200", "BRIGHT500", "BRIGHT500_PQ", "HDR1000"]
    fig, axs = plt.subplots(len(donors), len(lums), figsize=(3.2 * len(lums), 1.6 * len(donors) + 0.8))
    for i, (d, cfgs) in enumerate(donors):
        for j, lum in enumerate(lums):
            ax = axs[i, j]; ax.axis("off")
            p = f"{OUT}/{d}/{cfgs.get(lum, '-')}/{scene}__PHONE_{lum}_DARK.png"
            if lum not in cfgs or not os.path.exists(p):
                ax.set_title(f"{d} / {lum}: not supported", fontsize=6); continue
            Y = decode(read_code(p), lum, "DARK")[0][..., 1]; f = max(1, Y.shape[1] // 480)
            im = ax.imshow(np.log10(np.maximum(area_down(Y[..., None], f)[..., 0], 1e-4)), vmin=-4, vmax=3, cmap="magma", interpolation="antialiased")
            ax.set_title(f"{d} {cfgs[lum]} / {lum}", fontsize=6)
    fig.colorbar(im, ax=axs, fraction=0.015, label="log10 emitted luminance [cd/m^2]")
    fig.suptitle(f"{scene}: MEASUREMENT VIEW (not a preview): light emitted by each parametric display, d0/display_model.py", fontsize=9)
    plt.savefig(dest, dpi=110); plt.close(fig)


if __name__ == "__main__":
    os.makedirs("d0/results/stills", exist_ok=True); os.makedirs("d0/work/sheets", exist_ok=True)
    for s in ("S0", "S1", "S3_bar"):
        sheet(s, f"d0/results/stills/sheet_{s}_SDR100.png")
    for s in ("S4", "S5"):
        sheet(s, f"d0/work/sheets/sheet_{s}_SDR100.png")
    scenarios_sheet("S1", "d0/results/stills/sheet_S1_scenarios.png")
    print("sheets done")
