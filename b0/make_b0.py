#!/usr/bin/env python3
"""B0 stimuli. All optics used in B0 are linear, so every stimulus is built from components:
  sky_nobar, sky_bar : night sky 4e-4 cd/m^2 (slightly blue), optionally a black bar (trunk)
  src1               : the lamp alone on black, x1 = 800 cd at 3 km
and stimulus(k, bar) = sky + k * src1 exactly (retinal images likewise, after any linear optics).

Source record (for reproduction in other systems):
  luminous intensity 800 cd (the scene's luminaire), distance 3000 m, atmospheric T = 1 (not applied)
  illuminance at the eye E = I / d^2 = 8.89e-5 lx (x1), 8.89e-4 (x10), 8.89e-3 (x100)
  angular subtense of the luminaire (0.5 m sphere, the scene's LAMP_RADIUS 0.25 m) = 0.57 arcmin -> unresolved
  colour: Rec.709 1:0.45:0.08 (sodium-like) for the RGB variants; ISET uses the CIE HP1 HPS SPD
  pupil: not part of the stimulus; each eye model uses its own (ISET 6 mm; HDR-VDP its pupil model)
Grids:
  PHONE display grid 73 px/deg, 12 x 6 deg (876 x 438): the display-side chain
  REAL_SCENE_REFERENCE grids 146 / 292 px/deg (2x / 4x): the world-side chain has no pixel grid,
  so it is computed finer until the evaluator converges (b0/README.md)
Point footprint: Blackman-Harris 3-px window of the respective grid, unit energy (a point is
narrower on finer grids).
  python3 b0/make_b0.py [ppd=73] [neutral]   -> b0/out/stim{PPD}[_ach]/  (components + k=1/10/100 bar/nobar)
  neutral: the achromatic B0-optics layer (neutral source of the same photopic luminance)
"""
import json, math, os, sys
import numpy as np
import OpenImageIO as oiio

PPD = float(sys.argv[1]) if len(sys.argv) > 1 else 73.0
NEUTRAL = len(sys.argv) > 2 and sys.argv[2] == "neutral"     # B0-optics (achromatic) layer
OUT = ("b0/out/stim" if PPD == 73 else f"b0/out/stim{int(PPD)}") + ("_ach" if NEUTRAL else "")
FOV = (12.0, 6.0)
W, H = int(round(FOV[0] * PPD)), int(round(FOV[1] * PPD))
OMEGA = math.radians(1 / PPD) ** 2
E1 = 800.0 / 3000.0 ** 2
Yw = np.array([0.2126, 0.7152, 0.0722])
unit = lambda c: np.asarray(c, float) / (np.asarray(c, float) @ Yw)
SRC = (W / 2, H / 2)                           # pixel corner (phase 0.5), as in the pack
BAR = (int(round(SRC[0] + 0.3 * PPD)), int(round(SRC[0] + 0.45 * PPD)),
       int(round(SRC[1] - 1.5 * PPD)), int(round(SRC[1] + 1.5 * PPD)))


def bh(t):
    v = 2 * np.pi * (t + 0.5)
    return np.where(np.abs(t) <= 0.5, 0.35875 - 0.48829 * np.cos(v) + 0.14128 * np.cos(2 * v) - 0.01168 * np.cos(3 * v), 0)


def save(p, img):
    b = oiio.ImageBuf(oiio.ImageSpec(img.shape[1], img.shape[0], 3, oiio.FLOAT))
    b.set_pixels(oiio.ROI(0, img.shape[1], 0, img.shape[0], 0, 1, 0, 3), np.ascontiguousarray(img, np.float32)); b.write(p)


sky = np.full((H, W, 3), 4e-4, np.float32) * unit([0.85, 0.9, 1.0])
skybar = sky.copy(); skybar[BAR[2]:BAR[3], BAR[0]:BAR[1]] = 0
src = np.zeros_like(sky)
x, y = SRC
xs, ys = np.arange(int(x) - 3, int(x) + 4), np.arange(int(y) - 3, int(y) + 4)
w = np.outer(bh((ys + 0.5 - y) / 3), bh((xs + 0.5 - x) / 3)); w /= w.sum()
src[ys[0]:ys[-1] + 1, xs[0]:xs[-1] + 1] = (w * E1 / OMEGA)[..., None] * unit([1, 1, 1] if NEUTRAL else [1, 0.45, 0.08])
os.makedirs(OUT, exist_ok=True)
save(f"{OUT}/C_sky_nobar.exr", sky); save(f"{OUT}/C_sky_bar.exr", skybar); save(f"{OUT}/C_src1.exr", src)
for k in (1, 10, 100):
    for bar, s in (("bar", skybar), ("nobar", sky)):
        save(f"{OUT}/B0_k{k}_{bar}.exr", s + k * src)
json.dump({"px_per_deg": PPD, "size_px": [W, H], "fov_deg": list(FOV), "source_px": SRC, "bar_px_x0x1y0y1": BAR,
           "sky_cd_m2": 4e-4, "units": "Y cd/m^2, linear Rec.709",
           "source": {"I_cd": 800, "d_m": 3000, "atmospheric_T": 1.0, "E_eye_lx": {"1": E1, "10": 10 * E1, "100": 100 * E1},
                      "angular_subtense_arcmin": math.degrees(0.5 / 3000) * 60, "rgb": "neutral 1:1:1 (achromatic B0-optics)" if NEUTRAL else "Rec.709 1:0.45:0.08",
                      "spd_for_spectral_models": "CIE HP1 (HPS), tracks/mitsuba-spectral/spectra/test_spectra_unitlum.csv"},
           "components": "stimulus(k,bar) = C_sky_{bar|nobar} + k * C_src1 (exact)"},
          open(f"{OUT}/meta.json", "w"), indent=1)
print(OUT, W, H, "E_eye(x1) =", E1)
