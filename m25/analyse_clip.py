#!/usr/bin/env python3
"""M2.5: how much does each distant lamp's *appearance* change while the observer walks?

Every lamp is followed along its projected track (M25_TRACKS, from m1/scene.py). Kept: lamps
inside the frame all the time, never within 3 px of a poplar (occluders pass) and with no
other lamp within 6 px (so a window holds one lamp). For each kept lamp and frame, the energy
in a 7x7 window at 960 px, scaled with the resolution (the spot's 3-px Blackman-Harris footprint plus
rounding fits inside) at its tracked position, above the window's median background, is measured in:
  scene    the lamps pass (physics: I * T / d^2, constant to < 0.1 % over 10 m of walking);
  pcond    the pcond (LC) stage, display-linear;
  display  the displayed PNG, decoded to linear light (sRGB EOTF).
Reported per stage: modulation over the clip, (max - min) / mean, as median / p90 / max
over lamps, and the dominant period of the modulation; and the spot's RMS radius (second
moment) in arcmin of the 60 deg scene, median over lamps and frames, with its modulation. With the core of every lamp clipped
at display white, a lamp's displayed energy depends on where it sits on the pixel grid:
this is the "sub-pixel motion" part of any liveliness.
  python3 m25/analyse_clip.py CLIPDIR TRACKS.json [png|png_pbr]
"""
import json, sys
import numpy as np
import OpenImageIO as oiio

D, TR = sys.argv[1], json.load(open(sys.argv[2]))
PNG = sys.argv[3] if len(sys.argv) > 3 else "png"
W, H = TR["res"]
S = W / 960                               # windows scale with resolution (same angular size)
WIN = int(round(7 * S)) | 1               # odd window, 7 px at 960
HW = WIN // 2
Yw = np.array([0.2126, 0.7152, 0.0722])
load = lambda p: oiio.ImageBuf(p).get_pixels(oiio.FLOAT)[..., :3]
srgb = lambda v: np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)
F = len(TR["frames"])
xy = np.array(TR["frames"])                      # F x N x 2, normalised, y up
px, py = xy[..., 0] * W - 0.5, (1 - xy[..., 1]) * H - 0.5
inside = ((px > 4 * S) & (px < W - 5 * S) & (py > 4 * S) & (py < H - 5 * S)).all(0)
occ = np.array([load(f"{D}/occ_{k:04d}.exr")[..., 1] for k in range(1, F + 1)])
ix, iy = np.rint(px).astype(int).clip(0, W - 1), np.rint(py).astype(int).clip(0, H - 1)
near_tree = np.zeros(px.shape[1], bool)
for k in range(F):
    for dy in range(-int(3 * S), int(3 * S) + 1):
        for dx in range(-int(3 * S), int(3 * S) + 1):
            near_tree |= occ[k, (iy[k] + dy).clip(0, H - 1), (ix[k] + dx).clip(0, W - 1)] > 0.02
d = np.hypot(px[0][:, None] - px[0][None], py[0][:, None] - py[0][None]) + np.eye(px.shape[1]) * 99
isolated = d.min(1) > 6 * S
keep = np.flatnonzero(inside & ~near_tree & isolated)
dist = np.linalg.norm(np.array(TR["locs"]) - np.array(TR["cam"]), axis=1)
print(f"{D} ({PNG}): {F} frames, {px.shape[1]} lamps, kept {len(keep)} (inside, not near a poplar, isolated); "
      f"distance {dist[keep].min() / 1000:.1f}-{dist[keep].max() / 1000:.1f} km; "
      f"moves {np.abs(px[-1, keep] - px[0, keep]).min():.2f}-{np.abs(px[-1, keep] - px[0, keep]).max():.2f} px over the clip")

# clipped core: pixels of the displayed PNG at white (max channel >= 250/255) around each
# lamp, as an area in arcmin^2 of the 60 deg scene: a unresolved source shown this way has
# the size and shape of the pixels that clip, not of any optics
core = np.zeros((F, len(keep)))
for k in range(F):
    img = np.pad(load(f"{D}/{PNG}/{k + 1:04d}.png").max(-1), HW)
    for j, n in enumerate(keep):
        core[k, j] = (img[iy[k, n]:iy[k, n] + WIN, ix[k, n]:ix[k, n] + WIN] >= 250 / 255).sum()
a = core * (60 * 60 / W) ** 2
print(f"  clipped core on the display: median {np.median(a):.1f} arcmin^2 of the scene "
      f"(= {np.median(core):.1f} px; a {np.sqrt(np.median(a)):.1f}' square), p90 {np.percentile(a, 90):.1f}; "
      f"its area changes over the clip by median {np.median((a.max(0) - a.min(0)) / np.maximum(a.mean(0), 1e-9)) * 100:.0f} %")

stages = {"scene": lambda k: load(f"{D}/lamps_{k:04d}.exr") @ Yw,
          "pcond": lambda k: load(f"{D}/lc/{k:04d}.exr") @ Yw,
          "display": lambda k: srgb(load(f"{D}/{PNG}/{k:04d}.png")) @ Yw}
for name, get in stages.items():
    E, R = np.zeros((F, len(keep))), np.zeros((F, len(keep)))
    gy, gx = np.mgrid[-HW:HW + 1, -HW:HW + 1]
    for k in range(F):
        img = np.pad(get(k + 1), HW)
        for j, n in enumerate(keep):
            w = img[iy[k, n]:iy[k, n] + WIN, ix[k, n]:ix[k, n] + WIN]
            w = np.maximum(w - np.median(w), 0)                   # spot above the local background
            E[k, j] = w.sum()
            cy, cx = (w * gy).sum() / max(w.sum(), 1e-30), (w * gx).sum() / max(w.sum(), 1e-30)
            R[k, j] = np.sqrt((w * ((gy - cy) ** 2 + (gx - cx) ** 2)).sum() / max(w.sum(), 1e-30))
    mod = (E.max(0) - E.min(0)) / np.maximum(E.mean(0), 1e-30)
    spec = np.abs(np.fft.rfft(E - E.mean(0), axis=0)) ** 2
    fr = np.fft.rfftfreq(F, d=1 / 24)
    peak = fr[1:][spec[1:].sum(1).argmax()] if F > 3 else np.nan
    print(f"  {name:8s} modulation over the clip: median {np.median(mod) * 100:6.2f} %  p90 {np.percentile(mod, 90) * 100:6.2f} %  "
          f"max {mod.max() * 100:6.2f} %   dominant frequency {peak:.2f} Hz;   spot RMS radius "
          f"{np.median(R) * 60 * 60 / W:.2f}' of the scene (modulation {np.median((R.max(0) - R.min(0)) / R.mean(0)) * 100:.0f} %)")
